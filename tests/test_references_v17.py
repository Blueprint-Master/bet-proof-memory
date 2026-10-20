"""Test de bout en bout de la réévaluation des références sous la v1.7 (jeu synthétique)."""

import contextlib
import io
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evaluation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
sys.path.insert(0, os.path.dirname(__file__))
import construire as co  # noqa: E402
import references as rf  # noqa: E402
import references_v17 as rv  # noqa: E402
from test_references import jeu  # noqa: E402


class TestReferencesV17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        dossier = tempfile.mkdtemp()
        chemin = os.path.join(dossier, "cas-dev.parquet")
        pq.write_table(pa.Table.from_pylist(jeu(n=3000), schema=co.schema_cas()), chemin)
        cls.d = rf.charger(chemin)
        rf.GRILLE_LAMBDA = (0.0, 1e-2)  # grille réduite pour la vitesse du test seulement
        cls.lgd = {"lgd": 0.8, "lgd_bas": 0.6, "lgd_haut": 0.9}
        with contextlib.redirect_stderr(io.StringIO()):
            cls.r = rv.evaluer_pli(cls.d, rf.PLIS[2], cls.lgd)

    def test_eta_coherent_avec_predire(self):
        app = rf.sous_ensemble(self.d, (2018,))
        r2 = rf.R2(548).ajuster(app, rf.etiquette(app, 548))
        eta = r2.eta(app)
        p = 1 - np.prod(1 - 1 / (1 + np.exp(-eta)), axis=1)
        np.testing.assert_allclose(p, r2.predire(app), rtol=1e-9, atol=1e-12)

    def test_structure(self):
        m = self.r["modeles"]
        self.assertEqual(set(m), {"R0", "R1", "R2", "temoin"})
        self.assertEqual(len(self.r["scenarios"]["primaire"]["retenus"]), 6)
        for nom in ("R0", "R1", "R2"):
            e = m[nom]["ecart_au_temoin"]["primaire"]
            self.assertLessEqual(e["ic95"][0], e["ic95"][1])
            self.assertIn("primaire_pondere_bilan", m[nom]["ecart_au_temoin"])
        d = m["temoin"]["decomposition_primaire"]
        self.assertAlmostEqual(d["perte"], d["MCB"] - d["DSC"] + d["UNC"])

    def test_temoin_proche_de_r2(self):
        # Recalibrer R2 sur ses propres données d'apprentissage laisse b proche de 1.
        self.assertLess(abs(self.r["temoin"]["b"] - 1.0), 0.3)
        self.assertIn(self.r["R2_lambda"], (0.0, 1e-2))


if __name__ == "__main__":
    unittest.main()
