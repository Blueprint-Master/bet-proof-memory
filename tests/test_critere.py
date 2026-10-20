"""Tests de P5 bis (témoin, assemblage) et de P6 (perte, bootstrap par grappes)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evaluation"))
import critere as cr  # noqa: E402
import lgd as lg  # noqa: E402


def simuler(n=30000, graine=0, effet_x=0.8, b_vrai=1.0):
    """eta par intervalle (n, 3) ; issue simulée par hasard discret ; x informatif ou non."""
    rng = np.random.default_rng(graine)
    base = rng.normal(-5.0, 1.0, n)
    x = rng.normal(0, 1, n)
    eta = np.column_stack([base, base + 0.1, base + 0.2])
    jours, issue = np.full(n, -1), np.zeros(n, int)
    bornes = ((0, 183), (183, 365), (365, 548))
    for kk, (a, b) in enumerate(bornes):
        h = 1 / (1 + np.exp(-(b_vrai * eta[:, kk] + effet_x * x)))
        evt = (issue == 0) & (rng.random(n) < h)
        issue[evt] = 1
        jours[evt] = rng.integers(a + 1, b + 1, evt.sum())
    siren = np.array([f"{i:09d}" for i in range(n)], dtype=object)
    return eta, x, jours, issue, siren


class TestDecalage(unittest.TestCase):
    def test_recalibration(self):
        eta, x, jours, issue, _s = simuler(effet_x=0.0, b_vrai=1.5)
        t = cr.Temoin().ajuster(eta, jours, issue, 548)
        self.assertLess(abs(t.b - 1.5), 0.2)

    def test_lignes_pp_coherentes_avec_references(self):
        jours, issue = np.array([10, 400, -1]), np.array([1, 1, 0])
        i, k, y, k_max = cr.lignes_pp(jours, issue, 548)
        self.assertEqual(list(i), [0, 1, 1, 1, 2, 2, 2])
        self.assertEqual(list(y), [1, 0, 0, 1, 0, 0, 0])
        self.assertEqual(cr.lignes_pp(jours, issue, 365)[3], 2)

    def test_assemblage_candidat_utile(self):
        eta, x, jours, issue, siren = simuler(effet_x=0.8)
        a = cr.Assemblage().ajuster(eta, x, siren, jours, issue, 548)
        self.assertFalse(a.reduit_au_temoin)
        self.assertGreater(a.g[0] / a.ect[0] * a.ect[0], 0.5)
        t = cr.Temoin().ajuster(eta, jours, issue, 548)
        y = issue
        self.assertLess(np.mean((a.predire(eta, x) - y) ** 2), np.mean((t.predire(eta) - y) ** 2))

    def test_candidat_inutile_gamma_faible(self):
        eta, x, jours, issue, siren = simuler(effet_x=0.0)
        a = cr.Assemblage().ajuster(eta, x, siren, jours, issue, 548)
        self.assertLess(abs(a.g[0]), 0.15)

    def test_separation_retire_lambda_zero(self):
        eta, _x, jours, issue, siren = simuler(n=6000, effet_x=0.0)
        jours = np.where(issue == 1, 100, -1)  # événements dans le premier intervalle : une ligne par défaillance
        x = issue.astype(float) * 10.0  # sépare parfaitement les lignes d'événement
        a = cr.Assemblage().ajuster(eta, x, siren, jours, issue, 548)
        self.assertNotIn(0.0, a.scores)
        self.assertTrue(any(r["lambda"] == 0.0 for r in a.retraits))

    def test_proba_survie(self):
        p = cr.proba(np.zeros(3), 1.0, np.zeros(0), np.zeros((2, 3)))
        np.testing.assert_allclose(p, 1 - 0.5 ** 3)


class TestPerte(unittest.TestCase):
    def setUp(self):
        self.scen = lg.seuils(0.8, 0.001, 548)["retenus"]

    def test_couts_a_la_main(self):
        s = {"pi": 0.001, "T": 10.0, "q": 0.9, "lgd": 0.8, "p_t": 0.001 * 10 / (0.9 * 0.8)}
        p, y = np.array([0.5, 0.5, 0.0, 0.0]), np.array([1, 0, 1, 0])
        c = cr.couts_par_scenario(p, y, [s])[:, 0]
        np.testing.assert_allclose(c, [0.01 + 0.1 * 0.8, 0.01, 0.8, 0.0])

    def test_identite_schervish(self):
        rng = np.random.default_rng(1)
        p, y = rng.random(5000) * 0.1, (rng.random(5000) < 0.03).astype(int)
        for s in self.scen:
            c = cr.couts_par_scenario(p, y, [s])[:, 0]
            elem = (s["p_t"] - y) * (p > s["p_t"])
            np.testing.assert_allclose(c - y * s["lgd"], s["q"] * s["lgd"] * elem)

    def test_modele_parfait_meilleur(self):
        rng = np.random.default_rng(2)
        y = (rng.random(20000) < 0.02).astype(int)
        parfait, constant = y * 0.99, np.full(len(y), 0.02)
        self.assertLess(cr.couts(parfait, y, self.scen).mean(), cr.couts(constant, y, self.scen).mean())

    def test_decomposition(self):
        rng = np.random.default_rng(3)
        p = rng.beta(1, 40, 20000)
        y = (rng.random(20000) < np.clip(1.5 * p, 0, 1)).astype(int)
        d = cr.decomposition(p, y, self.scen)
        self.assertAlmostEqual(d["perte"], d["MCB"] - d["DSC"] + d["UNC"])
        self.assertGreaterEqual(d["MCB"], -1e-12)
        self.assertGreaterEqual(d["DSC"], -1e-12)


class TestInference(unittest.TestCase):
    def test_delta_par_origine_poids_egaux(self):
        diff, orig = np.array([1.0, 1.0, 1.0, 3.0]), np.array([2022, 2022, 2022, 2023])
        self.assertAlmostEqual(cr.delta_par_origine(diff, orig), 2.0)

    def test_grappes_premiere_origine(self):
        g = cr.grappes(np.array(["a", "a", "b", "c"], dtype=object), np.array([2023, 2022, 2023, 2022]),
                       np.array(["47", "41", "62", None], dtype=object))
        self.assertEqual(list(g), ["41", "41", "62", "?"])

    def test_bootstrap(self):
        rng = np.random.default_rng(4)
        n = 20000
        grappe = rng.choice([f"{i:02d}" for i in range(40)], n).astype(object)
        orig = rng.choice([2022, 2023], n)
        diff = rng.normal(0.001, 0.01, n)
        r = cr.bootstrap_grappes(diff, orig, grappe, tirages=500)
        self.assertEqual(r["grappes"], 40)
        self.assertLess(r["ic95"][0], r["delta"])
        self.assertGreater(r["ic95"][1], r["delta"])
        self.assertEqual(r, cr.bootstrap_grappes(diff, orig, grappe, tirages=500))

    def test_replications_sans_origine_retirees(self):
        # Origine 2023 dans une seule grappe sur deux : la moitié des tirages ne la contient pas.
        grappe = np.array(["A"] * 50 + ["B"] * 50, dtype=object)
        orig = np.array([2022] * 50 + [2023] * 50)
        r = cr.bootstrap_grappes(np.ones(100), orig, grappe, tirages=200)
        self.assertGreater(r["replications_retirees"], 0)

    def test_verdict_et_lmin(self):
        self.assertEqual(cr.verdict([0.001, 0.002]), "succes")
        self.assertEqual(cr.verdict([-0.002, -0.001]), "echec")
        self.assertEqual(cr.verdict([-0.001, 0.002]), "indecis")
        self.assertIsNone(cr.l_min(0.0))
        self.assertAlmostEqual(cr.l_min(0.0001), 100 * 548 / 365 / 0.0001)


if __name__ == "__main__":
    unittest.main()
