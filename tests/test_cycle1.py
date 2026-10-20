"""Tests des mécanismes du cycle 1 sur un contexte synthétique calculé à la main."""

import datetime as dt
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mecanismes"))
import cycle1 as c1  # noqa: E402

T0 = dt.date(2019, 9, 30)
D = dt.date


class FauxR:
    def __init__(self, lignes):
        cols = ("ratio_de_liquidite", "taux_d_endettement", "autonomie_financiere", "marge_ebe", "chiffre_d_affaires")
        self.num = {c: np.array([l.get(c, np.nan) for l in lignes], float) for c in cols}
        self.type = [l.get("type", "C") for l in lignes]

    def valeur(self, c, i):
        v = self.num[c][i]
        return None if v != v else float(v)


def contexte(conciliations=None):
    # Société A : cinq bilans annuels 2014 à 2018, le dernier paru avant t0 ; un bilan 2019 paru après t0.
    lignes = []
    bil = []
    for k, an in enumerate(range(2014, 2020)):
        lignes.append({"ratio_de_liquidite": 2.0 - 0.2 * k, "taux_d_endettement": 1.0 + 0.1 * k,
                       "autonomie_financiere": 0.4 - 0.05 * k, "marge_ebe": 10.0 - k,
                       "chiffre_d_affaires": 1000.0 * (1.1 ** k)})
        parution = D(an + 1, 6, 30) if an < 2019 else D(2020, 6, 30)
        bil.append((D(an, 12, 31), parution, (k, None), None))
    # le bilan 2018 a un compte de résultat masqué
    lignes[4]["marge_ebe"] = np.nan
    R = FauxR(lignes)
    liasse = {("A", f"{an}-12-31", "C"): (100.0, 50.0 - 10 * k, -5.0 * k, -1.0 if an >= 2017 else 2.0, 60.0, 20.0 + k)
              for k, an in enumerate(range(2014, 2020))}
    depots = {"A": {D(an, 12, 31): D(an + 1, 6, 30) for an in range(2014, 2019)}}
    depots["A"][D(2017, 12, 31)] = D(2018, 8, 31)  # dépôt 2017 plus tardif
    clot = {"A": [D(2016, 3, 1)]}
    mods = {"A": [D(2018, 1, 15)]}
    periodes = {"A": [(D(2000, 1, 1), D(2017, 12, 31), "5710", "47.11F", "NAFRev2"),
                      (D(2018, 1, 1), D(2018, 12, 31), "5710", "56.10A", "NAFRev2"),
                      (D(2019, 1, 1), None, "5499", "56.10B", "NAFRev2")]}
    series = {"S": {f"{a:04d}-{m:02d}": 100.0 + (a - 2010) * 12 + m for a in range(2010, 2021) for m in range(1, 13)},
              "DIREN.M.FR.DE.UL.DF.03.N.ZZ.PM": {f"{a:04d}-{m:02d}": 50.0 for a in range(2010, 2021)
                                                for m in range(1, 13)}}
    return c1.Contexte(R, {"A": bil}, liasse, depots, clot, conciliations, mods, periodes, series)


CAS = {"serie_bdf": "S", "taille_bdf": "PM", "intensite_sectorielle": 1.2}


class TestCycle1(unittest.TestCase):
    def setUp(self):
        self.v = c1.calculer(contexte(conciliations={"A": [D(2018, 5, 1)]}), "A", T0, CAS)

    def test_toutes_les_colonnes(self):
        self.assertEqual(set(self.v), set(c1.colonnes()))
        self.assertEqual(len(c1.CANDIDATS), 35)

    def test_variations_de_ratios(self):
        # b1 = 2018 (k = 4), b2 = 2017 (k = 3), écart 365 jours
        ans = 365 / 365.25
        self.assertAlmostEqual(self.v["C1"], ((2.0 - 0.6) - (2.0 - 0.8)) / ans)
        self.assertAlmostEqual(self.v["C2"], ((1.4) - (1.3)) / ans)
        self.assertAlmostEqual(self.v["G5"], -0.2)
        self.assertEqual(self.v["G5_absent"], 0.0)
        self.assertAlmostEqual(self.v["G4"], -0.05)

    def test_liasse(self):
        # cp 2017 = 20, cp 2018 = 10, total 100 ; réserves 2018 = -20
        self.assertAlmostEqual(self.v["C3"], (20.0 - 10.0) / 100.0)
        self.assertAlmostEqual(self.v["C5"], 20.0 / 100.0)
        self.assertAlmostEqual(self.v["G7"], -0.2)
        self.assertAlmostEqual(self.v["G9"], 24.0 / 60.0)
        self.assertAlmostEqual(self.v["G6"], 0.0)

    def test_compte_de_resultat_masque(self):
        # Le bilan 2018 n'a pas de compte de résultat : C6, G8 manquants, G3 = 1.
        self.assertEqual(self.v["C6"], 0.0)
        self.assertEqual((self.v["G8"], self.v["G8_absent"]), (0.0, 1.0))
        self.assertEqual(self.v["G3"], 1.0)
        self.assertTrue(math.isnan(self.v["M1"]))  # trois marges requises, celle de 2018 manque
        self.assertTrue(math.isnan(self.v["M12"]))

    def test_depots(self):
        # retards : 2018 -> 181 j ; 2017 -> 243 j ; 2016 -> 181 j
        self.assertAlmostEqual(self.v["C7"], (181 - 243) / 365.25)
        self.assertEqual(self.v["G1"], 181 - 243)
        self.assertAlmostEqual(self.v["M7"], float(np.std([181, 243, 181])))
        self.assertEqual(self.v["C8"], 0.0)  # (t0 - 31/12/2018) = 273 j < 1,5 an
        self.assertEqual(self.v["G2"], 0.0)

    def test_evenements(self):
        self.assertEqual(self.v["C9"], 1.0)
        self.assertEqual(self.v["M4"], 1.0)
        self.assertEqual(self.v["C10"], 1.0)
        self.assertEqual(self.v["G10"], 1.0)
        self.assertEqual(self.v["G12"], 1.0)

    def test_sirene(self):
        # NAF : 47.11F -> 56.10A (01/01/2018), 56.10A -> 56.10B (01/01/2019) ; CJ : 5710 -> 5499 (01/01/2019)
        self.assertEqual(self.v["C11"], 1.0)  # une seule transition de division (47 -> 56)
        self.assertEqual(self.v["G11"], 1.0)
        self.assertEqual(self.v["M5"], 1.0)
        self.assertEqual(self.v["M6"], 1.0)
        self.assertEqual(self.v["M11"], 8.0)

    def test_banque_de_france(self):
        # Série S : valeur(a, m) = 100 + (a - 2010) * 12 + m ; t0 - 3 = 2019-06, t0 - 15 = 2018-06
        a, b = 100 + 9 * 12 + 6, 100 + 8 * 12 + 6
        self.assertAlmostEqual(self.v["C12"], math.log((1 + a) / (1 + b)))
        self.assertAlmostEqual(self.v["G13"], 1.0)

    def test_series_longues(self):
        # Cinq bilans connus (2014 à 2018) ; écarts de 365 ou 366 jours.
        ls = [2.0 - 0.2 * k for k in (4, 3, 2, 1, 0)]
        self.assertAlmostEqual(self.v["M2"], float(np.std(ls)))
        self.assertAlmostEqual(self.v["C4"], float(np.std(ls[:4])))
        self.assertTrue(math.isnan(self.v["M3"]))  # le chiffre d'affaires 2018 est masqué
        self.assertGreater(self.v["M8"], 0)  # dettes financières croissantes

    def test_conciliations_absentes(self):
        v = c1.calculer(contexte(conciliations=None), "A", T0, CAS)
        self.assertTrue(math.isnan(v["C9"]) and math.isnan(v["M4"]))
        self.assertEqual(v["G10"], 1.0)  # la procédure close suffit

    def test_aucune_information_posterieure(self):
        # Le bilan 2019 (paru en 2020) n'est jamais lu : b1 reste 2018 même avec t0 tardif dans 2019.
        ctx = contexte()
        self.assertEqual(ctx.connus("A", T0)[0][0], D(2018, 12, 31))
        self.assertEqual(c1.moins_mois(D(2020, 3, 31), 1), D(2020, 2, 29))
        self.assertEqual(c1.mois_entre(D(2019, 1, 1), T0), 8)

    def test_societe_inconnue(self):
        v = c1.calculer(contexte(), "Z", T0, {"serie_bdf": None, "taille_bdf": "TT", "intensite_sectorielle": None})
        self.assertEqual(v["C1"], 0.0)
        self.assertEqual(v["G1_absent"], 1.0)
        self.assertTrue(math.isnan(v["M1"]))
        self.assertEqual(v["M11"], 60.0)


if __name__ == "__main__":
    unittest.main()
