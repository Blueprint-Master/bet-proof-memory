"""Tests de P0 v1.2 (jointure bilans et avis de dépôt), sans réseau."""

import datetime as dt
import gzip
import io
import os
import sys
import unittest
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "p0"))
import p0_jointure as pj  # noqa: E402

RATIOS_2019 = (
    "siren;date_cloture_exercice;confidentiality;type_bilan\n"
    "302237748;2019-12-31;Public;C\n"
    "310656384;2019-09-30;Public;S\n"
    "312411416;2019-12-31;Confidentiel;S\n"
    "999999999;2019-06-30;Public;C\n"
)
BODACC = (
    "dateparution;familleavis_lib;registre;depot\n"
    # trouvé : SIREN avec espaces, JSON
    '2020-08-12;Dépôts des comptes;302 237 748,302237748;"{""dateCloture"": ""2019-12-31"", ""typeDepot"": ""Comptes annuels""}"\n'
    # trouvé : date en toutes lettres
    "2021-01-05;Dépôts des comptes;310656384;Comptes annuels et rapports de l'exercice clos le 30 septembre 2019\n"
    # doublon plus tardif : la première parution fait foi
    '2021-03-01;Dépôts des comptes;302237748;"{""dateCloture"": ""2019-12-31""}"\n'
    # clôture qui ne correspond à aucun bilan : ignoré
    '2020-08-12;Dépôts des comptes;312411416;"{""dateCloture"": ""2018-12-31""}"\n'
    # sans SIREN exploitable
    '2020-08-12;Dépôts des comptes;RCS inconnu;"{""dateCloture"": ""2019-12-31""}"\n'
)


class FausseReponse(io.BytesIO):
    pass


class TestAnalyse(unittest.TestCase):
    def test_siren(self):
        self.assertEqual(pj.siren_de("302 237 748,302237748"), 302237748)
        self.assertEqual(pj.siren_de('["302 237 748"]'), 302237748)
        self.assertIsNone(pj.siren_de("RCS inconnu"))
        self.assertIsNone(pj.siren_de(None))

    def test_date_cloture(self):
        self.assertEqual(pj.date_cloture_de('{"dateCloture": "2019-12-31"}'), dt.date(2019, 12, 31))
        self.assertEqual(pj.date_cloture_de("exercice clos le 1er janvier 2012"), dt.date(2012, 1, 1))
        self.assertEqual(pj.date_cloture_de("clos le 30 septembre 2011"), dt.date(2011, 9, 30))
        self.assertIsNone(pj.date_cloture_de("sans date"))

    def test_verdict(self):
        self.assertEqual(pj.verdict({2019: 0.95, 2022: 0.91})["code"], "principal-dates")
        self.assertEqual(pj.verdict({2019: 0.95, 2022: 0.70})["code"], "principal-dates-biais-declare")
        self.assertEqual(pj.verdict({2019: 0.95, 2024: 0.40})["code"], "arret")


class TestExecution(unittest.TestCase):
    def setUp(self):
        self.urls = []

    def ouvrir(self, requete, timeout=None):
        url = urllib.parse.unquote(requete.full_url)
        self.urls.append(url)
        if "ratios_inpi_bce" in url:
            corps = RATIOS_2019.encode()
        else:
            # Le BODACC renvoie ici un flux gzip non annoncé.
            return FausseReponse(gzip.compress(BODACC.encode()))
        return FausseReponse(corps)

    def test_jointure_et_regles(self):
        r = pj.executer([2019], ouvrir=self.ouvrir, aujourdhui=dt.date(2026, 10, 19))
        a = r["par_annee"]["2019"]
        self.assertEqual(a["bilans_cles_distinctes"], 4)
        self.assertEqual(a["avec_avis"], 2)
        self.assertAlmostEqual(a["taux"], 0.5)
        self.assertEqual(a["par_confidentialite"]["Public"], {"bilans": 3, "avec_avis": 2, "taux": 2 / 3})
        # Le verdict porte sur les non confidentiels (« Confidentiel » exclu) : 2 sur 3.
        self.assertEqual(a["non_confidentiels"], {"bilans": 3, "avec_avis": 2, "taux": 2 / 3})
        self.assertEqual(a["delai_cloture_parution_jours"]["n"], 2)
        self.assertEqual(r["bodacc"]["avis_lus"], 5)
        self.assertEqual(r["bodacc"]["sans_siren"], 1)
        self.assertEqual(r["bodacc"]["libelle_famille"], "Dépôts des comptes")
        self.assertEqual(r["verdict"]["code"], "principal-dates-biais-declare")

    def test_aucune_issue_lue(self):
        pj.executer([2019], ouvrir=self.ouvrir, aujourdhui=dt.date(2026, 10, 19))
        for url in self.urls:
            q = url.lower()
            for interdit in ("collective", "liquidation", "redressement", "jugement"):
                self.assertNotIn(interdit, q, url)
            if "annonces-commerciales" in q:
                self.assertIn('familleavis="dpc"', q)
            if "ratios_inpi_bce" in q:
                # Les clés seules, jamais un montant.
                self.assertIn("select=siren,date_cloture_exercice,confidentiality,type_bilan", q)

    def test_premiere_parution_fait_foi(self):
        res = pj.parcourir_bodacc(
            {2019: {pj.cle(302237748, dt.date(2019, 12, 31)): "Public"}},
            dt.date(2019, 1, 1), dt.date(2023, 1, 1), ouvrir=self.ouvrir,
        )
        self.assertEqual(res["trouves"][2019][pj.cle(302237748, dt.date(2019, 12, 31))], dt.date(2020, 8, 12))


if __name__ == "__main__":
    unittest.main()
