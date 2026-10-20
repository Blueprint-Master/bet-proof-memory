"""Tests de l'évaluation des références (phase 5, étape 3) sur un jeu synthétique."""

import contextlib
import datetime as dt
import io
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evaluation"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
import construire as co  # noqa: E402
import references as rf  # noqa: E402


def jeu(n=4000, graine=1):
    """Trois origines ; le risque dépend de la liquidité et de l'indicateur « en plan »."""
    rng = np.random.default_rng(graine)
    lignes = []
    for origine in (2018, 2019, 2020):
        t0 = dt.date(origine, 9, 30)
        for i in range(n):
            liq = rng.normal(1.5, 0.6)
            plan = int(rng.random() < 0.05)
            logit = -3.5 - 1.5 * (liq - 1.5) + 2.0 * plan
            defaut = rng.random() < 1 / (1 + np.exp(-logit))
            jours = int(rng.integers(1, 548)) if defaut else None
            l = {c: None for c in co.schema_cas().names}
            l.update({"siren": f"{origine}{i:05d}", "origine": origine, "t0": t0, "naf2": rng.choice(["41", "47", "62"]),
                      "taille_bdf": rng.choice(["MI", "PM"]), "age_ans": float(rng.uniform(0, 20)),
                      "origine_retenue": 1, "issue": int(defaut),
                      "date_issue": t0 + dt.timedelta(days=jours) if jours else None,
                      "ratio_de_liquidite": float(liq), "taux_d_endettement": float(rng.normal(1, 0.5)),
                      "autonomie_financiere": float(rng.normal(0.3, 0.2)), "ratio_de_vetuste": None,
                      "log_total_bilan": float(rng.normal(13, 1)), "retard_depot_jours": int(rng.integers(150, 400)),
                      "intensite_sectorielle": 1.0, "en_plan": plan, "en_observation_sauvegarde": 0,
                      "total_bilan_absent": 0, "cr_indisponible": 0, "capitaux_propres_negatifs": 0,
                      "vetuste_absente": 1, "confidentiel": 0,
                      "altman_x1": float(0.2 * (liq - 1)), "altman_x2": float(rng.normal(0.1, 0.1)),
                      "altman_x3": None if rng.random() < 0.2 else float(rng.normal(0.05, 0.05)),
                      "altman_x4": float(rng.normal(1, 0.5))})
            for c in co.GROUPE2 + ("log_chiffre_affaires", "resultat_net_sur_total_bilan"):
                l[c] = float(rng.normal(0, 1))
            lignes.append(l)
    return lignes


class TestReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        chemin = os.path.join(cls.dossier, "cas-dev.parquet")
        pq.write_table(pa.Table.from_pylist(jeu(), schema=co.schema_cas()), chemin)
        cls.d = rf.charger(chemin)
        rf.GRILLE_LAMBDA = (1e-3, 1.0)  # grille réduite pour la vitesse du test seulement
        rf.TIRAGES = 200
        with contextlib.redirect_stderr(io.StringIO()):
            cls.r = rf.evaluer(cls.d)

    def test_plis_et_separation(self):
        self.assertTrue(all(rf.separation_respectee(p) for p in rf.PLIS))
        self.assertFalse(rf.separation_respectee({"apprentissage": (2019,), "test": 2020, "horizon": 548}))
        self.assertEqual(set(self.r["plis"]), {p["nom"] for p in rf.PLIS})

    def test_r2_bat_r0_sur_un_signal_reel(self):
        for nom, r in self.r["plis"].items():
            m = r["mesures"]
            self.assertLess(m["R2"]["brier"], m["R0"]["brier"], nom)
            self.assertGreater(m["R2"]["auc"], 0.65, nom)
            g = r["gain_contre_R2"]["R0"]
            self.assertLess(g["G"], 0)  # R0 fait moins bien que la référence
            self.assertLessEqual(g["ic95"][0], g["G"])
            self.assertLessEqual(g["G"], g["ic95"][1])

    def test_horizon_et_personne_periode(self):
        d = rf.sous_ensemble(self.d, (2018,))
        y365, y548 = rf.etiquette(d, 365), rf.etiquette(d, 548)
        self.assertTrue((y365 <= y548).all())
        from scipy import sparse
        x = sparse.csr_matrix(np.ones((3, 1)))
        xp, yp, g, k = rf.personne_periode(x, np.array([100, 400, -1]), np.array([1, 1, 0]), 548)
        self.assertEqual(k, 3)
        self.assertEqual([int(v) for v in g], [0, 1, 1, 1, 2, 2, 2])
        self.assertEqual([int(v) for v in yp], [1, 0, 0, 1, 0, 0, 0])
        xp, yp, g, k = rf.personne_periode(x[:1], np.array([400]), np.array([0]), 365)
        self.assertEqual((k, len(yp)), (2, 2))

    def test_mesures(self):
        y = np.array([0, 0, 1, 1])
        m = rf.mesures(y, np.array([0.1, 0.2, 0.8, 0.9]))
        self.assertAlmostEqual(m["brier"], (0.01 + 0.04 + 0.04 + 0.01) / 4)
        self.assertEqual(m["auc"], 1.0)
        self.assertEqual(m["part_defaillances_decile_risque"], 0.5)

    def test_descriptif(self):
        d = self.r["descriptif_548j"]
        self.assertGreater(d["en_plan"]["taux_548j"], d["ensemble"]["taux_548j"])

    def test_r0_sections(self):
        self.assertEqual(rf.section_naf("47"), "G")
        self.assertEqual(rf.section_naf("hors_NAFRev2"), "?")
        self.assertEqual(rf.tranche_age(None), "?")
        self.assertEqual(rf.tranche_age(4.0), "3-5")


if __name__ == "__main__":
    unittest.main()
