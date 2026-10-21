"""Tests du modèle dédié au palier 1 (jeu synthétique)."""

import contextlib
import datetime as dt
import glob
import io
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evaluation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
sys.path.insert(0, os.path.dirname(__file__))
import construire as co  # noqa: E402
import critere as cr  # noqa: E402
import modele_dedie as md  # noqa: E402
import references as rf  # noqa: E402
from test_references import jeu  # noqa: E402

DIVISIONS = [str(x) for x in (10, 25, 41, 45, 46, 47, 49, 56, 62, 68, 70, 86)]


def jeu_divise(n=2500, graine=7, avis_tardif=False):
    lignes = jeu(n=n, graine=graine)
    rng = np.random.default_rng(graine + 1)
    for l in lignes:
        l["naf2"] = str(rng.choice(DIVISIONS))
        l["parution_avis"] = l["t0"] - dt.timedelta(days=int(rng.integers(30, 300)))
    if avis_tardif:
        lignes[0]["parution_avis"] = lignes[0]["t0"] + dt.timedelta(days=5)
    return lignes


class TestRepartition(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(3)
        self.naf = rng.choice(DIVISIONS, 5000)
        self.y = (rng.random(5000) < 0.05).astype(int)

    def test_une_division_un_pli(self):
        p = md.repartition(self.naf, self.y, 11)
        for dv in DIVISIONS:
            self.assertEqual(len(set(p[self.naf == dv])), 1)
        self.assertEqual(set(p), set(range(md.PLIS_INTERNES)))

    def test_deterministe_et_variable(self):
        a, b, c = md.repartition(self.naf, self.y, 11), md.repartition(self.naf, self.y, 11), md.repartition(self.naf, self.y, 12)
        self.assertTrue(np.array_equal(a, b))
        self.assertFalse(np.array_equal(a, c))

    def test_equilibre(self):
        p = md.repartition(self.naf, self.y, 11)
        charges = [self.y[p == f].sum() for f in range(md.PLIS_INTERNES)]
        par_div = max(self.y[self.naf == dv].sum() for dv in DIVISIONS)
        self.assertLessEqual(max(charges) - min(charges), par_div)

    def test_trop_peu_de_divisions(self):
        with self.assertRaises(ValueError):
            md.repartition(np.array(["41", "47"] * 10), np.zeros(20, int), 1)


class TestAdmission(unittest.TestCase):
    def test_regle(self):
        self.assertTrue(md.admis_repartition([1, 1, 1, 1, -1], 0.2))
        self.assertFalse(md.admis_repartition([1, 1, 1, -1, -1], 0.2))
        self.assertFalse(md.admis_repartition([1, 1, 1, 1, 1], -0.1))
        self.assertFalse(md.admis_repartition([1, 1, 1, None, None], 0.2))


class TestControles(unittest.TestCase):
    def charger(self, lignes):
        import pyarrow as pa
        import pyarrow.parquet as pq

        dossier = tempfile.mkdtemp()
        chemin = os.path.join(dossier, "cas-dev.parquet")
        pq.write_table(pa.Table.from_pylist(lignes, schema=co.schema_cas()), chemin)
        return rf.charger(chemin)

    def test_controles_passent(self):
        d = self.charger(jeu_divise(n=300))
        ctl = md.controles(md.sous(d, d["origine"] == 2018), md.sous(d, d["origine"] == 2020))
        self.assertTrue(all(c["ok"] for c in ctl), ctl)

    def test_apprentissage_hors_2018(self):
        d = self.charger(jeu_divise(n=300))
        ctl = md.controles(md.sous(d, d["origine"] <= 2019), md.sous(d, d["origine"] == 2020))
        self.assertFalse(ctl[0]["ok"])

    def test_avis_tardif(self):
        d = self.charger(jeu_divise(n=300, avis_tardif=True))
        ctl = md.controles(md.sous(d, d["origine"] == 2018), md.sous(d, d["origine"] == 2020))
        self.assertFalse(next(c for c in ctl if c["nom"].endswith("(apprentissage)"))["ok"])


class TestBoutEnBout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        lignes = jeu_divise()
        pq.write_table(pa.Table.from_pylist(lignes, schema=co.schema_cas()), os.path.join(cls.dossier, "cas-dev.parquet"))
        rng = np.random.default_rng(9)
        issue = np.array([l["issue"] for l in lignes], float)
        t = {"siren": [l["siren"] for l in lignes], "origine": [l["origine"] for l in lignes],
             "U1": issue * 2.0 + rng.normal(0, 1, len(lignes)), "B1": rng.normal(0, 1, len(lignes)),
             "V1": np.full(len(lignes), np.nan)}
        pq.write_table(pa.table(t), os.path.join(cls.dossier, "candidats-c1.parquet"))
        cls.lgd = os.path.join(cls.dossier, "lgd.json")
        with open(cls.lgd, "w") as f:
            json.dump({"estimation": {"lgd": 0.9}}, f)
        rf.GRILLE_LAMBDA = (0.0, 1e-2)
        cr.GRILLE_LAMBDA = (0.0, 1e-2)
        with contextlib.redirect_stderr(io.StringIO()):
            cls.code = md.main(["--dossier", cls.dossier, "--lgd", cls.lgd, "--processus", "1", "--repartitions", "2"])
        with open(glob.glob(os.path.join(cls.dossier, "modele-dedie-*.json"))[0]) as f:
            cls.r = json.load(f)

    def test_execution(self):
        self.assertEqual(self.code, 0)
        self.assertTrue(all(c["ok"] for c in self.r["controles_provenance"]))

    def test_candidat_utile_retenu_vide_ecarte(self):
        self.assertEqual(self.r["candidats"]["U1"]["admissions"], 2)
        self.assertIn("U1", self.r["modele_final"]["candidats"])
        self.assertEqual(self.r["candidats"]["V1"]["admissions"], 0)
        self.assertNotIn("V1", self.r["modele_final"]["candidats"])

    def test_previsions_2020(self):
        import pyarrow.parquet as pq

        t = pq.read_table(os.path.join(self.dossier, self.r["cible"]["fichier"]))
        self.assertEqual(set(t.column("origine").to_pylist()), {2020})
        p = np.array(t.column("p_dedie").to_pylist())
        self.assertTrue(np.all((p > 0) & (p < 1)))
        self.assertEqual(md.sha256_fichier(os.path.join(self.dossier, self.r["cible"]["fichier"])),
                         self.r["cible"]["sha256"])

    def test_chrono(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = md.main(["--dossier", self.dossier, "--lgd", self.lgd, "--processus", "1", "--chrono"])
        self.assertEqual(code, 0)
        self.assertIn("estimation pour 20 répartitions", err.getvalue())


if __name__ == "__main__":
    unittest.main()
