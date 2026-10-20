"""Tests de l'extraction (phase 5, étape 1), sans réseau extérieur."""

import contextlib
import datetime as dt
import functools
import http.server
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
sys.path.insert(0, os.path.dirname(__file__))
import extraire as ex  # noqa: E402
from test_p0 import GestionnaireRange  # noqa: E402


class Reponse(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def silence():
    return contextlib.redirect_stderr(io.StringIO())


class FauxODS:
    """Simule les deux API Opendatasoft : schémas et exports CSV."""

    def __init__(self, procedures_apres_garde=False, famille_vide=None):
        self.urls, self.apres, self.vide = [], procedures_apres_garde, famille_vide

    def __call__(self, requete, timeout=None):
        url = urllib.parse.unquote_plus(requete.full_url)
        self.urls.append(url)
        if "/exports/csv" not in url:
            if "ratios" in url:
                champs = ["siren", "date_cloture_exercice", "confidentiality", "type_bilan", "marge_ebe"]
            else:
                champs = ["dateparution", "familleavis", "registre", "jugement", "depot", "listepersonnes"]
            return Reponse(json.dumps({"fields": [{"name": c} for c in champs]}).encode())
        if "ratios" in url:
            return Reponse(b"siren;date_cloture_exercice;confidentiality;type_bilan;marge_ebe\n"
                           b"302237748;2019-12-31;Public;C;0.12\n310656384;2019-09-30;Public;S;\n")
        if self.vide and f'familleavis="{self.vide}"' in url:
            return Reponse(b"dateparution;familleavis;registre;jugement\n")
        if 'familleavis="dpc"' in url:
            return Reponse(b'dateparution;familleavis;registre;depot\n2020-08-12;dpc;302237748;"{""dateCloture"": ""2019-12-31""}"\n')
        d = "2023-01-05" if self.apres else "2021-03-01"
        return Reponse(f'dateparution;familleavis;registre;jugement\n{d};collective;302237748;"{{}}"\n'.encode())


class TestGarde(unittest.TestCase):
    def test_garde_dans_la_requete(self):
        self.assertEqual(ex.GARDE_SCELLE, dt.date(2022, 9, 30))
        for f in ex.FAMILLES_PROCEDURES:
            self.assertIn("dateparution < date'2022-09-30'", ex.where_bodacc(f))
        self.assertNotIn("dateparution", ex.where_bodacc("dpc"))

    def test_source_qui_viole_la_garde(self):
        with tempfile.TemporaryDirectory() as d, silence():
            with self.assertRaisesRegex(RuntimeError, "garde du scellé"):
                ex.extraire_bodacc(d, ouvrir=FauxODS(procedures_apres_garde=True))

    def test_conciliation_vide_non_bloquante(self):
        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, _ = ex.extraire_bodacc(d, ouvrir=FauxODS(famille_vide="conciliation"))
        self.assertEqual({f["fichier"]: f["lignes"] for f in fichiers}["bodacc-conciliation.parquet"], 0)

    def test_famille_vide(self):
        with tempfile.TemporaryDirectory() as d, silence():
            with self.assertRaisesRegex(RuntimeError, "vide"):
                ex.extraire_bodacc(d, ouvrir=FauxODS(famille_vide="radiation"))

    def test_bodacc_minimise(self):
        import pyarrow.parquet as pq

        faux = FauxODS()
        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_bodacc(d, ouvrir=faux)
            t = pq.read_table(os.path.join(d, "bodacc-collective.parquet"))
            self.assertEqual(t.num_rows, 1)
        self.assertNotIn("listepersonnes", details["champs"])
        self.assertTrue(all("listepersonnes" not in u for u in faux.urls))
        self.assertEqual({f["fichier"] for f in fichiers},
                         {"bodacc-dpc.parquet", "bodacc-collective.parquet", "bodacc-pcl.parquet",
                          "bodacc-conciliation.parquet", "bodacc-radiation.parquet"})

    def test_familles_choisies_et_inconnues(self):
        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_bodacc(d, ouvrir=FauxODS(), familles=("pcl",))
            self.assertEqual([f["fichier"] for f in fichiers], ["bodacc-pcl.parquet"])
            self.assertIn("2022-09-30", details["requetes"]["pcl"])
            with self.assertRaises(ValueError):
                ex.extraire_bodacc(d, ouvrir=FauxODS(), familles=("modification",))


class TestModifications(unittest.TestCase):
    def test_categories_seules(self):
        import pyarrow.parquet as pq

        corps = ('dateparution;registre;modificationsgenerales\n'
                 '2019-01-05;302237748;"{""descriptif"": ""Dissolution anticipée de la société à compter du..."" }"\n'
                 '2019-02-05;310656384;"{""descriptif"": ""Fusion par absorption de la société X""}"\n'
                 '2019-03-05;312411416;"{""descriptif"": ""Nomination de M. Dupont en qualité de gérant""}"\n').encode()
        urls = []

        def ouvrir(req, timeout=None):
            urls.append(urllib.parse.unquote_plus(req.full_url))
            return Reponse(corps)
        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_modifications(d, ouvrir=ouvrir)
            t = pq.read_table(os.path.join(d, "bodacc-modification-evenements.parquet")).to_pydict()
        self.assertEqual(t["evenement"], ["dissolution", "fusion"])
        self.assertEqual(set(t), {"dateparution", "registre", "evenement"})  # aucun descriptif conservé
        self.assertEqual(details["avis_lus"], 3)
        self.assertIn("dateparution < date'2022-09-30'", urls[0])

    def test_garde(self):
        corps = b'dateparution;registre;modificationsgenerales\n2023-01-05;302237748;"{}"\n'
        with tempfile.TemporaryDirectory() as d, silence():
            with self.assertRaisesRegex(RuntimeError, "garde"):
                ex.extraire_modifications(d, ouvrir=lambda req, timeout=None: Reponse(corps))


class TestBdf(unittest.TestCase):
    def test_filtre_des_series(self):
        import pyarrow.parquet as pq

        corps = ("series_key;time_period;time_period_start;obs_value;updated_at;OBS_STATUS\n"
                 "DIREN.M.FR.DE.UL.DF.03.N.ZZ.TT;2015-01;2015-01-01;62865;2024-12-02;A\n"
                 "DIREN.M.FR.DE.UL.DF.03.N.FZ.PM;2015-01;2015-01-01;14000;2024-12-02;A\n"
                 "DIREN.M.FR.DE.UL.DF.04.N.ZZ.TT;2015-01;2015-01-01;5000;2024-12-02;A\n"
                 "DIREN.M.R32.DE.UL.DF.03.N.ZZ.TT;2015-01;2015-01-01;4000;2024-12-02;A\n").encode()
        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_bdf(d, ouvrir=lambda req, timeout=None: Reponse(corps))
            t = pq.read_table(os.path.join(d, "bdf-diren.parquet")).to_pydict()
        self.assertEqual(t["series_key"], ["DIREN.M.FR.DE.UL.DF.03.N.ZZ.TT", "DIREN.M.FR.DE.UL.DF.03.N.FZ.PM"])
        self.assertEqual(t["obs_value"], [62865.0, 14000.0])
        self.assertEqual(t["updated_at"][0], "2024-12-02")


class TestRatios(unittest.TestCase):
    def test_types_et_manifeste(self):
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_ratios(d, [2019], ouvrir=FauxODS())
            t = pq.read_table(os.path.join(d, "ratios-2019.parquet")).to_pydict()
            chemin, h = ex.ecrire_manifeste(d, "ratios", fichiers, details)
            m = json.load(open(chemin))
        self.assertEqual(t["siren"], ["302237748", "310656384"])
        self.assertEqual(t["marge_ebe"], [0.12, None])
        self.assertEqual(m["fichiers"][0]["lignes"], 2)
        self.assertEqual(len(h), 64)


class TestParquets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        typ = pa.map_(pa.string(), pa.int32())
        pq.write_table(pa.table({
            "siren": ["302237748", "312411416", "999999999"],
            "date_cloture_exercice": [dt.date(2019, 12, 31)] * 3,
            "type_bilan": ["C", "S", "C"],
            "confidentiality": ["Public", "Partiellement confidentiel", "Public"],
            "liasse": pa.array([[("EE", 1000), ("CO-1A", 1000), ("FJ", 5)], [("180", 70), ("110-112", 70)], []],
                               type=typ),
        }), os.path.join(cls.dossier, "sf.parquet"), row_group_size=2)
        pq.write_table(pa.table({
            "siren": ["302237748", "302237748", "111111111"],
            "dateDebut": ["2000-01-01", "2018-06-01", "1990-01-01"],
            "dateFin": ["2018-05-31", None, None],
            "categorieJuridiqueUniteLegale": ["5499", "5710", "5710"],
            "activitePrincipaleUniteLegale": ["10.89Z", "10.89Z", "01.11Z"],
            "nomenclatureActivitePrincipaleUniteLegale": ["NAFRev2"] * 3,
        }), os.path.join(cls.dossier, "histo.parquet"))
        pq.write_table(pa.table({"siren": ["302237748", "111111111"],
                                 "dateCreationUniteLegale": ["2000-01-01", "1990-01-01"]}),
                       os.path.join(cls.dossier, "ul.parquet"))
        gest = functools.partial(GestionnaireRange, directory=cls.dossier)
        cls.serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gest)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.serveur.server_port}/"

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def test_sf_totaux_seuls(self):
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as d, silence():
            fichiers, details = ex.extraire_sf(d, url=self.base + "sf.parquet")
            t = pq.read_table(os.path.join(d, "sf-totaux.parquet")).to_pydict()
        self.assertEqual(fichiers[0]["lignes"], 3)
        self.assertEqual(t["EE"], [1000.0, None, None])
        self.assertEqual(t["180"], [None, 70.0, None])
        self.assertEqual(t["110-112"], [None, 70.0, None])
        self.assertNotIn("FJ", t)

    def test_sirene_restreint_aux_ratios(self):
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as d, silence():
            ex.extraire_ratios(d, [2019], ouvrir=FauxODS())
            fichiers, details = ex.extraire_sirene(d, url_ul=self.base + "ul.parquet",
                                                   url_histo=self.base + "histo.parquet")
            h = pq.read_table(os.path.join(d, "sirene-historique.parquet")).to_pydict()
        self.assertEqual(h["siren"], ["302237748", "302237748"])
        self.assertEqual(details["sirens"], 2)
        self.assertEqual(fichiers[1]["lignes"], 1)


if __name__ == "__main__":
    unittest.main()
