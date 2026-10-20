"""Tests de P6 ter (perte en cas de défaut, modèle multi-états) et des seuils de P6."""

import datetime as dt
import json
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evaluation"))
import lgd as lg  # noqa: E402

D0 = dt.date(2019, 1, 10)


def j(nature, date="2019-05-01", complement=""):
    return json.dumps({"nature": nature, "date": date, "complementJugement": complement})


class TestClassement(unittest.TestCase):
    def test_natures(self):
        self.assertEqual(lg.classer_transition(j("Jugement de conversion en liquidation judiciaire"))[0], "CONV-LJ")
        self.assertEqual(lg.classer_transition(j("Jugement arrêtant le plan de cession"))[0], "CESSION")
        self.assertEqual(lg.classer_transition(j("Jugement arrêtant le plan de redressement"))[0], "PLAN")
        self.assertEqual(lg.classer_transition(j("Jugement de clôture pour extinction du passif"))[0], "CLOT-EXT")
        self.assertEqual(lg.classer_transition(j("Jugement de clôture pour insuffisance d'actif"))[0], "CLOT")
        self.assertEqual(lg.classer_transition(j("Jugement prononçant la résolution du plan de redressement et la "
                                                 "liquidation judiciaire"))[0], "RESOL-LJ")
        self.assertEqual(lg.classer_transition(j("Jugement d'ouverture d'une procédure de redressement judiciaire"))[0],
                         "OUV-RJ")
        self.assertEqual(lg.classer_transition(j("Jugement fixant la date de cessation des paiements"))[0], "AUTRE")
        self.assertEqual(lg.classer_transition(j("Jugement arrêtant le plan de cession"))[1], dt.date(2019, 5, 1))


class TestParcours(unittest.TestCase):
    def test_redressement_plan_puis_resolution(self):
        ev = [(D0, "OUV-RJ"), (dt.date(2019, 7, 1), "PLAN"), (dt.date(2020, 3, 1), "RESOL-LJ")]
        q = lg.parcours(ev, D0, "OUV-RJ")
        self.assertEqual(q["entree"], lg.O)
        self.assertEqual(q["transitions"], [(172, lg.O, lg.P), (416, lg.P, lg.L)])
        self.assertEqual(q["censure"], (lg.GARDE_SCELLE - D0).days)

    def test_liquidation_directe_et_absorbante(self):
        ev = [(D0, "OUV-LJ"), (dt.date(2019, 7, 1), "PLAN")]
        q = lg.parcours(ev, D0, "OUV-LJ")
        self.assertEqual((q["entree"], q["transitions"]), (lg.L, []))

    def test_conversion_cession_extinction_anomalie(self):
        q = lg.parcours([(dt.date(2019, 3, 1), "CONV-LJ")], D0, "OUV-RJ")
        self.assertEqual(q["transitions"], [(50, lg.O, lg.L)])
        q = lg.parcours([(dt.date(2019, 3, 1), "CESSION")], D0, "OUV-RJ")
        self.assertEqual(q["transitions"][0][2], lg.L)
        q = lg.parcours([(dt.date(2019, 3, 1), "CLOT-EXT")], D0, "OUV-RJ")
        self.assertEqual(q["transitions"], [(50, lg.O, lg.P)])
        q = lg.parcours([(dt.date(2019, 3, 1), "CLOT")], D0, "OUV-RJ")
        self.assertEqual((q["transitions"], q["anomalies_clot_en_O"]), ([], 1))

    def test_meme_jour_et_anterieur(self):
        q = lg.parcours([(dt.date(2019, 3, 1), "PLAN"), (dt.date(2019, 3, 1), "RESOL-LJ")], D0, "OUV-RJ")
        self.assertEqual(q["transitions"], [(50, lg.O, lg.L)])
        q = lg.parcours([(dt.date(2018, 3, 1), "PLAN")], D0, "OUV-RJ")
        self.assertEqual(q["transitions"], [])

    def test_conversion_sauvegarde_en_liquidation_entre_en_L(self):
        self.assertEqual(lg.parcours([], D0, "CONV-SAUV-LJ")["entree"], lg.L)
        self.assertEqual(lg.parcours([], D0, "CONV-SAUV-RJ")["entree"], lg.O)


def proc(entree, trans, censure=5000):
    return {"entree": entree, "transitions": trans, "censure": censure, "anomalies_clot_en_O": 0}


class TestAalenJohansen(unittest.TestCase):
    def test_sans_censure_egale_proportions(self):
        ps = [proc(lg.L, []), proc(lg.O, [(100, lg.O, lg.P)]), proc(lg.O, [(100, lg.O, lg.P), (300, lg.P, lg.L)]),
              proc(lg.O, [])]
        np.testing.assert_allclose(lg.aalen_johansen(ps, 1095), [0.25, 0.25, 0.5])
        np.testing.assert_allclose(lg.aalen_johansen(ps, 200), [0.25, 0.5, 0.25])

    def test_deux_etats_egale_kaplan_meier(self):
        # O -> L seulement : P_L(tau) = 1 - KM. Temps 10 (évt), 20 (censure), 30 (évt), 40 (évt), 50 (censure).
        ps = [proc(lg.O, [(10, lg.O, lg.L)]), proc(lg.O, [], 20), proc(lg.O, [(30, lg.O, lg.L)]),
              proc(lg.O, [(40, lg.O, lg.L)]), proc(lg.O, [], 50)]
        km = (1 - 1 / 5) * (1 - 1 / 3) * (1 - 1 / 2)
        np.testing.assert_allclose(lg.aalen_johansen(ps, 1000)[lg.L], 1 - km)
        self.assertAlmostEqual(lg.aalen_johansen(ps, 1000).sum(), 1.0)

    def test_simulation_coherente(self):
        rng = np.random.default_rng(3)
        ps = []
        for _ in range(4000):
            if rng.random() < 0.6:
                ps.append(proc(lg.L, [], int(rng.integers(200, 1500))))
                continue
            t1 = int(rng.integers(1, 400))
            tr = [(t1, lg.O, lg.P)] if rng.random() < 0.5 else [(t1, lg.O, lg.L)]
            if tr[0][2] == lg.P and rng.random() < 0.3:
                tr.append((t1 + int(rng.integers(1, 600)), lg.P, lg.L))
            c = int(rng.integers(200, 1500))
            ps.append(proc(lg.O, [x for x in tr if x[0] <= c], c))
        p = lg.aalen_johansen(ps, 1095)
        # Vraies probabilités à 1 095 j : P_L = 0,6 + 0,4 (0,5 + 0,5 x 0,3 x P(t1 + u <= 1095)).
        self.assertAlmostEqual(p.sum(), 1.0)
        self.assertLess(abs(p[lg.L] - (0.6 + 0.4 * (0.5 + 0.15))), 0.03)
        self.assertLess(p[lg.O], 0.01)


class TestTauEtLgd(unittest.TestCase):
    def test_tau(self):
        ps = [proc(lg.O, [], c) for c in [2000] * 300 + [500] * 50]
        self.assertEqual(lg.choisir_tau(ps), (1095, 300))
        ps = [proc(lg.O, [], c) for c in [800] * 300 + [2000] * 10]
        self.assertEqual(lg.choisir_tau(ps), (800, 310))
        with self.assertRaises(RuntimeError):
            lg.choisir_tau([proc(lg.O, [], c) for c in [300] * 400])
        with self.assertRaises(RuntimeError):
            lg.choisir_tau([proc(lg.O, [], 2000)] * 10)

    def test_lgd(self):
        r = lg.lgd_depuis(np.array([0.1, 0.3, 0.6]))
        self.assertAlmostEqual(r["w"], 0.6 / 0.9)
        self.assertAlmostEqual(r["lgd"], 0.95 * 0.6 / 0.9 + 0.269 * 0.3 / 0.9)
        self.assertAlmostEqual(r["w_bas"], 0.6)
        self.assertAlmostEqual(r["w_haut"], 0.7)
        self.assertTrue(r["lgd_bas"] < r["lgd"] < r["lgd_haut"])
        self.assertEqual(lg.lgd_depuis(np.array([1.0, 0.0, 0.0]))["w"], 1.0)

    def test_seuils(self):
        s = lg.seuils(0.95, 0.001, 548)
        self.assertEqual((len(s["retenus"]), len(s["retires"])), (6, 0))
        pts = sorted(x["p_t"] for x in s["retenus"])
        self.assertAlmostEqual(pts[0], 0.001 * (548 / 60) / (0.9 * 0.95))
        self.assertAlmostEqual(pts[-1], 0.001 * (548 / 30) / (0.7 * 0.95))
        s = lg.seuils(0.269, 0.02, 548)
        self.assertTrue(all(x["p_t"] >= 1 for x in s["retires"]) and s["retires"])

    def test_procedures_dev_dedoublonne(self):
        d1 = dt.date(2019, 2, 1)
        cas = {"siren": np.array(["1", "1", "2", "3"], dtype=object), "issue": np.array([1, 1, 1, 0]),
               "date_issue": np.array([d1, d1, d1, None], dtype=object)}
        evts = {"1": [(d1, "OUV-RJ"), (dt.date(2019, 6, 1), "PLAN")], "2": [(dt.date(2019, 1, 1), "OUV-RJ")]}
        parc, c = lg.procedures_dev(cas, evts)
        self.assertEqual((c["procedures"], c["sans_nature_retrouvee"], len(parc)), (2, 1, 1))


if __name__ == "__main__":
    unittest.main()
