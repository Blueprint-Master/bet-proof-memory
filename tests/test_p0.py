"""Tests de P0 : lecture du pied parquet par Range, agrégats ODS, verdict.

Aucun accès réseau extérieur : un serveur HTTP local qui gère Range, et des
réponses Opendatasoft simulées.
"""

import datetime as dt
import http.server
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "p0"))
import p0_faisabilite as p0  # noqa: E402


class GestionnaireRange(http.server.SimpleHTTPRequestHandler):
    """Sert un fichier en honorant l'en-tête Range (que le serveur standard ignore)."""

    def log_message(self, *args):
        pass

    def _chemin(self):
        return self.translate_path(self.path)

    def do_HEAD(self):
        taille = os.path.getsize(self._chemin())
        self.send_response(200)
        self.send_header("Content-Length", str(taille))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self):
        chemin = self._chemin()
        taille = os.path.getsize(chemin)
        plage = self.headers.get("Range")
        with open(chemin, "rb") as f:
            if plage:
                debut, fin = plage.replace("bytes=", "").split("-")
                debut, fin = int(debut), min(int(fin), taille - 1)
                f.seek(debut)
                corps = f.read(fin - debut + 1)
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {debut}-{fin}/{taille}")
            else:
                corps = f.read()
                self.send_response(200)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)


class TestParquetParRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        n = 50_000
        # Une colonne de remplissage connu (80 % de dates de dépôt), sur 5 groupes de lignes.
        depot = [dt.date(2020, 1, 1) + dt.timedelta(days=i % 365) if i % 5 else None for i in range(n)]
        table = pa.table({
            "siren": [f"{i:09d}" for i in range(n)],
            "date_cloture_exercice": [dt.date(2015 + i % 8, 12, 31) for i in range(n)],
            "date_depot": depot,
            "chiffre_affaires": [float(i) for i in range(n)],
        })
        cls.chemin = os.path.join(cls.dossier, "bilans.parquet")
        pq.write_table(table, cls.chemin, row_group_size=10_000)

        gestionnaire = lambda *a, **k: GestionnaireRange(*a, directory=cls.dossier, **k)  # noqa: E731
        cls.serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gestionnaire)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.serveur.server_port}/bilans.parquet"

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def test_schema_effectif_et_statistiques_depuis_le_pied(self):
        f = p0.FichierHttpRange(self.url)
        m = p0.metadonnees_parquet(f)
        self.assertEqual(m["lignes"], 50_000)
        self.assertEqual(m["groupes_de_lignes"], 5)
        c = m["colonnes"]["date_depot"]
        self.assertEqual(c["nulls"], 10_000)
        self.assertAlmostEqual(c["remplissage"], 0.8)
        self.assertEqual(m["colonnes"]["date_cloture_exercice"]["min"], "2015-12-31")
        self.assertEqual(m["colonnes"]["date_cloture_exercice"]["max"], "2022-12-31")

    def test_seul_le_pied_transite(self):
        f = p0.FichierHttpRange(self.url)
        p0.metadonnees_parquet(f)
        # pyarrow lit le pied par blocs de 64 Ko : borne ABSOLUE, indépendante de la
        # taille du fichier. Sur le parquet réel (2,6 Go), c'est moins d'un dix-millième.
        self.assertLessEqual(f.octets_lus, 256 * 1024)
        self.assertGreater(f.requetes, 0)

    def test_serveur_sans_range_refuse(self):
        class SansRange:
            headers = {"Content-Length": "10"}
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        with self.assertRaisesRegex(RuntimeError, "Range"):
            p0.FichierHttpRange("http://exemple.invalid/x", ouvrir=lambda *a, **k: SansRange())


class FausseReponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestOpendatasoft(unittest.TestCase):
    def setUp(self):
        self.requetes = []

    def _ouvrir(self, requete, timeout=None):
        url = requete.full_url
        self.requetes.append(url)
        if "/records?" not in url:
            corps = {"fields": [
                {"name": "siren", "type": "text", "label": "SIREN"},
                {"name": "date_cloture_exercice", "type": "date", "label": "Date de clôture"},
                {"name": "date_depot_comptes", "type": "date", "label": "Date de dépôt"},
            ]}
        else:
            params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            select, where = params["select"][0], params.get("where", [None])[0]
            if select.startswith("count") and where is None:
                corps = {"results": [{"n": 1000}]}
            elif select.startswith("count"):
                corps = {"results": [{"n": 950 if "depot" in where else 1000}]}
            else:
                corps = {"results": [{"min": "2014-12-31", "max": "2025-12-31"}]}
        return FausseReponse(json.dumps(corps).encode())

    def test_plages_et_remplissage_des_dates(self):
        m = p0.metadonnees_ods("https://ods.invalid/catalog/datasets/x", ouvrir=self._ouvrir)
        self.assertEqual(m["effectif"], 1000)
        self.assertAlmostEqual(m["dates"]["date_depot_comptes"]["remplissage"], 0.95)
        self.assertEqual(m["dates"]["date_cloture_exercice"]["min"], "2014-12-31")

    def test_aucune_requete_ne_lit_une_issue(self):
        p0.metadonnees_ods("https://ods.invalid/catalog/datasets/x", ouvrir=self._ouvrir)
        for url in self.requetes:
            q = urllib.parse.unquote(url).lower()
            for interdit in ("familleavis", "collective", "liquidation", "redressement", "group_by"):
                self.assertNotIn(interdit, q, f"P0 ne doit lire aucune issue : {url}")


class TestVerdict(unittest.TestCase):
    def test_seuils(self):
        self.assertEqual(p0.verdict(0.95)["code"], "principal-dates")
        self.assertEqual(p0.verdict(0.90)["code"], "principal-dates")
        self.assertEqual(p0.verdict(0.70)["code"], "principal-dates-biais-declare")
        self.assertEqual(p0.verdict(0.50)["code"], "principal-dates-biais-declare")
        self.assertEqual(p0.verdict(0.49)["code"], "arret")
        self.assertEqual(p0.verdict(None)["code"], "arret-sans-date")

    def test_reconnaissance_des_champs_de_depot(self):
        self.assertEqual(
            p0.champs_depot({"date_depot": "", "date_cloture_exercice": "Date de clôture", "dt_pub": "Date de publication"}),
            ["date_depot", "dt_pub"],
        )


if __name__ == "__main__":
    unittest.main()
