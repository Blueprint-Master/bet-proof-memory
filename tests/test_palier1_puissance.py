"""Tests de l'analyse de puissance du palier 1."""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "palier1"))
import puissance as pu  # noqa: E402


def jeu(diffs1, diffs0):
    t1, b, cas = {}, {}, {}
    for y, diffs in ((1, diffs1), (0, diffs0)):
        for i, d in enumerate(diffs):
            k = f"K{y}{i}"
            t1[k] = {"type": "eligible", "cout_realise": 0.5 + d}
            b[k] = {"type": "eligible", "cout_realise": 0.5}
            cas[k] = {"y": y}
    return t1, b, cas


class TestPuissance(unittest.TestCase):
    def test_formule(self):
        z = 1.959964 + 0.841621
        self.assertAlmostEqual(pu.effectif(0.011, 0.04, 0.0004, 0.001), 2 * (0.011 ** 2 * 0.04 + 0.989 ** 2 * 0.0004) * z * z / 1e-6, delta=1e-3)

    def test_aucune_difference(self):
        r = pu.analyser(*jeu([0.0] * 25, [0.0] * 25), p=0.011)
        self.assertIn("non calculable", r["conclusion"])

    def test_majoration_et_conclusion(self):
        r = pu.analyser(*jeu([0.0] * 25, [0.018] * 3 + [0.0] * 22), p=0.011)
        self.assertGreater(r["n_majore"], r["n_plug_in"])
        self.assertEqual(r["strates_sans_difference"], [1])
        s0 = r["strates"][0]["variance"]
        self.assertEqual(r["n_plug_in"], math.ceil(pu.effectif(0.011, 0.0, s0)))

    def test_part_defaillants(self):
        cas = {"a": {"type": "eligible", "y": 1, "w": 0.022}, "b": {"type": "eligible", "y": 0, "w": 1.978},
               "c": {"type": "piege_avant"}}
        self.assertAlmostEqual(pu.part_defaillants(cas), 0.011)


if __name__ == "__main__":
    unittest.main()
