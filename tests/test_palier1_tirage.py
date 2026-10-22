"""Tests du tirage des cas et des pièges du palier 1 (jeu synthétique de test_construire, t0 2018)."""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "palier1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
sys.path.insert(0, os.path.dirname(__file__))
import construire as co  # noqa: E402
import outils as ou  # noqa: E402
import tirer as ti  # noqa: E402
from test_construire import jeu, jugement  # noqa: E402

T0 = dt.date(2018, 9, 30)
EFF = {"defaillants": 1, "non_defaillants": 2, "piege_avant": 1, "piege_apres": 1}


class TestTirage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = d = tempfile.mkdtemp()
        jeu(d)
        # 100000013, en observation de sauvegarde, voit sa sauvegarde convertie en liquidation avant t0
        chemin = os.path.join(d, "bodacc-collective.parquet")
        t = pq.read_table(chemin).to_pylist()
        t.append({"dateparution": "2018-07-01", "registre": "100000013",
                  "jugement": jugement("Jugement prononçant", "Jugement de conversion en liquidation judiciaire "
                                       "de la procédure de sauvegarde", "2018-06-20")})
        pq.write_table(pa.Table.from_pylist(t), chemin)
        with contextlib.redirect_stderr(io.StringIO()):
            s = co.Sortie(os.path.join(d, "cas-dev.parquet"))
            co.construire(d, s, origines=(2018,), seuil=1, aujourdhui=dt.date(2026, 10, 20))
            s.fermer()
        cas = pq.read_table(os.path.join(d, "cas-dev.parquet"), columns=["siren", "origine"]).to_pylist()
        pq.write_table(pa.table({"siren": [c["siren"] for c in cas], "origine": [2018] * len(cas),
                                 "p_dedie": [0.05] * len(cas)}), os.path.join(d, "prevision-test.parquet"))
        cls.args = (d, os.path.join(d, "cas-dev.parquet"), os.path.join(d, "prevision-test.parquet"), T0)

    def preparer(self, graine=1, eff=EFF, exclus=()):
        with contextlib.redirect_stderr(io.StringIO()):
            return ti.preparer(*self.args, graine, eff, exclus, cle=b"k")

    def test_populations(self):
        pop = ti.population(self.args[1], self.args[2], 2018)
        self.assertEqual(pop, {"100000001": 1, "100000002": 0, "100000006": 0, "100000007": 0,
                               "100000010": 0, "100000012": 1})
        with contextlib.redirect_stderr(io.StringIO()):
            avant, apres = ti.candidats(self.dossier, T0, pop)
        self.assertEqual(avant, ["100000013"])  # 100000005 est en redressement, pas en liquidation
        self.assertEqual(apres, ["100000001", "100000012"])  # liquidation 2019 ; résolution du plan 2019

    def test_tirage_complet_disjoint_et_controle(self):
        r = self.preparer()
        tir = r["tirage"]
        types = [c["type"] for c in tir]
        self.assertEqual(types, ["piege_apres", "eligible", "eligible", "eligible", "piege_avant"])
        sirens = [c["siren"] for c in tir]
        self.assertEqual(len(set(sirens)), len(sirens))
        self.assertEqual({tir[0]["siren"], tir[1]["siren"]}, {"100000001", "100000012"})
        self.assertEqual(tir[1]["y"], 1)
        self.assertTrue(all(c["scenario"] in ou.SCENARIOS for c in tir))
        k_avant = r["correspondance"]["100000013"]
        self.assertNotIn("prevision", r["dossiers"][k_avant])
        self.assertEqual(r["cas"][k_avant], {"type": "piege_avant", "scenario": tir[-1]["scenario"], "t0": T0.isoformat()})

    def test_aucune_issue_ni_siren_dans_les_dossiers(self):
        r = self.preparer()
        texte = json.dumps(r["dossiers"])
        for c in r["tirage"]:
            self.assertNotIn(c["siren"], texte)
        for k in ("issue", "\"y\"", "date_issue", "piege", "eligible"):
            self.assertNotIn(k, texte)

    def test_poids(self):
        r = self.preparer()
        # 2 défaillants sur 6 dans l'origine ; 1 sur 3 dans l'échantillon
        self.assertAlmostEqual(r["resume"]["poids"]["defaillant"], (2 / 6) / (1 / 3))
        self.assertAlmostEqual(r["resume"]["poids"]["non_defaillant"], (4 / 6) / (2 / 3))
        w = {x["y"]: x["w"] for x in r["cas"].values() if x["type"] == "eligible"}
        self.assertAlmostEqual(w[1], 1.0)

    def test_determinisme_et_exclusion(self):
        self.assertEqual(self.preparer(7)["tirage"], self.preparer(7)["tirage"])
        tirages = {json.dumps(self.preparer(g)["tirage"]) for g in range(8)}
        self.assertGreater(len(tirages), 1)
        pop = ti.population(self.args[1], self.args[2], 2018)
        eff = {"defaillants": 0, "non_defaillants": 2, "piege_avant": 0, "piege_apres": 0}
        r = ti.tirer(pop, [], [], 3, eff, exclus={"100000002", "100000006"})
        self.assertEqual({c["siren"] for c in r}, {"100000007", "100000010"})
        with self.assertRaises(ValueError):
            ti.tirer(pop, [], [], 3, eff, exclus={"100000002", "100000006", "100000007"})

    def test_etat_procedure_plan_apres_liquidation(self):
        d = dt.date
        self.assertEqual(ou.etat_procedure([(d(2017, 1, 1), d(2017, 1, 1), "OUV-LJ"),
                                            (d(2017, 6, 1), d(2017, 6, 1), "PLAN")]), "LJ")
        self.assertEqual(ou.etat_procedure([(d(2017, 1, 1), d(2017, 1, 1), "OUV-RJ"),
                                            (d(2017, 6, 1), d(2017, 6, 1), "PLAN")]), "PLAN")
        self.assertIsNone(ou.etat_procedure([(d(2017, 6, 1), d(2017, 6, 1), "PLAN")]))


if __name__ == "__main__":
    unittest.main()
