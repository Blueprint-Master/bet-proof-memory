"""Tests de P0 v1.3 (couverture Sirene et Signaux Faibles), serveur local, sans réseau extérieur."""

import datetime as dt
import functools
import http.server
import io
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "p0"))
sys.path.insert(0, os.path.dirname(__file__))
import p0_sources as ps  # noqa: E402
from test_p0 import GestionnaireRange  # noqa: E402

RATIOS = (
    "siren;date_cloture_exercice;confidentiality;type_bilan\n"
    "302237748;2019-12-31;Public;C\n"
    "310656384;2019-09-30;Public;S\n"
    "312411416;2019-12-31;Partiellement confidentiel;S\n"
    "999999999;2019-06-30;Public;C\n"
)


class Reponse(io.BytesIO):
    pass


class TestSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        pq.write_table(pa.table({
            "siren": ["302237748", "310656384", "312411416", "111111111"],
            "categorieJuridiqueUniteLegale": ["5710", "5499", "6540", "5710"],
            "activitePrincipaleUniteLegale": ["10.89Z", None, "70.10Z", "01.11Z"],
            "dateCreationUniteLegale": ["2000-01-01", "2010-05-05", None, "1990-01-01"],
        }), os.path.join(cls.dossier, "ul.parquet"))
        pq.write_table(pa.table({
            "siren": ["302237748", "302237748", "310656384"],
            "dateDebut": ["2010-01-01", "2018-06-01", "2005-01-01"],
            "changementActivitePrincipaleUniteLegale": ["false", "true", "true"],
            "changementCategorieJuridiqueUniteLegale": ["false", "false", "true"],
        }), os.path.join(cls.dossier, "histo.parquet"))
        pq.write_table(pa.table({
            "siren": ["302237748", "312411416", "312411416"],
            "date_cloture_exercice": [dt.date(2019, 12, 31), dt.date(2019, 12, 31), dt.date(2018, 12, 31)],
            "liasse": [{"a": 1}, {"a": 2}, {"a": 3}],
        }), os.path.join(cls.dossier, "sf.parquet"))
        gest = functools.partial(GestionnaireRange, directory=cls.dossier)
        cls.serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gest)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.serveur.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def test_couverture(self):
        r = ps.executer([2019], ouvrir=lambda req, timeout=None: Reponse(RATIOS.encode()),
                        url_ul=self.base + "ul.parquet", url_histo=self.base + "histo.parquet",
                        url_sf=self.base + "sf.parquet")
        pub = r["par_annee"]["2019"]["Public"]
        self.assertEqual(pub["sirens"], 3)
        self.assertEqual(pub["sirene_ul_trouves"], round(2 / 3, 4))
        self.assertEqual(pub["forme_p1"], round(2 / 3, 4))
        self.assertEqual(pub["naf_renseigne"], round(1 / 3, 4))
        # Changement de NAF en 2018 compté ; celui de 2005 (avant 2014) non.
        self.assertEqual(pub["changement_naf_depuis_2014"], round(1 / 3, 4))
        self.assertEqual(pub["changement_cj_depuis_2014"], 0.0)
        self.assertEqual(pub["signaux_faibles_trouves"], round(1 / 3, 4))
        conf = r["par_annee"]["2019"]["Partiellement confidentiel"]
        self.assertEqual(conf["forme_p1"], 0.0)  # 6540 : société civile, hors P1
        self.assertEqual(conf["creation_renseignee"], 0.0)
        self.assertEqual(conf["signaux_faibles_trouves"], 1.0)  # la clôture 2018 ne compte pas
        self.assertIn("liasse", r["sources"]["signaux_faibles"]["types"])

    def test_forme_p1(self):
        self.assertTrue(ps.forme_p1("5710"))
        self.assertTrue(ps.forme_p1(5499))
        self.assertTrue(ps.forme_p1("5202"))
        self.assertFalse(ps.forme_p1("6540"))
        self.assertFalse(ps.forme_p1(None))


if __name__ == "__main__":
    unittest.main()
