"""Test de bout en bout de l'évaluation d'un cycle (jeu synthétique)."""

import contextlib
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
import cycle as cy  # noqa: E402
import references as rf  # noqa: E402
from test_references import jeu  # noqa: E402


class TestCycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        lignes = jeu(n=3000, graine=5)
        pq.write_table(pa.Table.from_pylist(lignes, schema=co.schema_cas()), os.path.join(cls.dossier, "cas-dev.parquet"))
        rng = np.random.default_rng(9)
        # « utile » : liée à l'issue au-delà de R2 (bruit + issue) ; « bruit » : indépendante ; « vide » : NaN partout.
        issue = np.array([l["issue"] for l in lignes], float)
        utile = issue * 1.5 + rng.normal(0, 1, len(lignes))
        bruit = rng.normal(0, 1, len(lignes))
        partiel = np.where(rng.random(len(lignes)) < 0.3, np.nan, bruit)
        t = {"siren": [l["siren"] for l in lignes], "origine": [l["origine"] for l in lignes],
             "U1": utile, "B1": bruit, "B1_absent": (rng.random(len(lignes)) < 0.1).astype(float),
             "P1": partiel, "V1": np.full(len(lignes), np.nan)}
        pq.write_table(pa.table(t), os.path.join(cls.dossier, "candidats-c1.parquet"))
        with open(os.path.join(cls.dossier, "lgd.json"), "w") as f:
            json.dump({"estimation": {"lgd": 0.9}}, f)
        rf.GRILLE_LAMBDA = (0.0, 1e-2)
        cr.GRILLE_LAMBDA = (0.0, 1e-2)
        with contextlib.redirect_stderr(io.StringIO()):
            cy.main(["--dossier", cls.dossier, "--lgd", os.path.join(cls.dossier, "lgd.json"), "--processus", "1"])
        with open(glob.glob(os.path.join(cls.dossier, "evaluation-cycle-*.json"))[0]) as f:
            cls.r = json.load(f)

    def test_groupes(self):
        self.assertEqual(cy.groupes_de_colonnes(["G1", "G1_absent", "C1"]), {"G1": ("G1", "G1_absent"), "C1": ("C1",)})
        self.assertEqual(set(self.r["candidats"]), {"U1", "B1", "P1", "V1"})

    def test_candidat_utile_admis(self):
        u = self.r["candidats"]["U1"]
        self.assertTrue(u["admis"])
        self.assertTrue(all(u[p]["delta"] > 0 for p in self.r["plis"]))
        self.assertIn("U1", self.r["admis"])
        self.assertIsNotNone(self.r["assemblage_des_admis"])

    def test_colonne_vide_non_calculable(self):
        v = self.r["candidats"]["V1"]
        self.assertFalse(v["admis"])
        self.assertTrue(all(not v[p]["calculable"] for p in self.r["plis"]))

    def test_indicateur_de_manquant(self):
        p = self.r["candidats"]["P1"]
        self.assertTrue(all(p[k]["colonnes_x"] == 2 for k in self.r["plis"]))
        self.assertTrue(all(self.r["candidats"]["B1"][k]["colonnes_x"] == 2 for k in self.r["plis"]))

    def test_matrice(self):
        xa, xt = cy.matrice(np.array([[1.0], [np.nan], [3.0]]), np.array([[np.nan], [5.0]]))
        np.testing.assert_allclose(xa, [[1, 0], [2, 1], [3, 0]])
        np.testing.assert_allclose(xt, [[2, 1], [5, 0]])
        self.assertEqual(cy.matrice(np.array([[np.nan]]), np.array([[1.0]])), (None, None))


if __name__ == "__main__":
    unittest.main()
