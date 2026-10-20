"""Tests de P0 v1.4 (structure de la liasse, profondeur), serveur local, sans réseau extérieur."""

import contextlib
import functools
import http.server
import io
import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "p0"))
sys.path.insert(0, os.path.dirname(__file__))
import p0_structure as pst  # noqa: E402
from test_p0 import GestionnaireRange  # noqa: E402


class Reponse(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow as pa
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        typ = pa.map_(pa.string(), pa.int32())
        table = pa.table({
            "type_bilan": ["C", "C", "S", "C"],
            "liasse": pa.array([[("CO_m3", 987654), ("DL_m1", 1)], [("CO_m3", 5)],
                                [("110_m3", 7)], [("FJ_m1", 9)]], type=typ),
        })
        pq.write_table(table, os.path.join(cls.dossier, "sf.parquet"), row_group_size=2)
        gest = functools.partial(GestionnaireRange, directory=cls.dossier)
        cls.serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), gest)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.serveur.server_port}/sf.parquet"

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def ouvrir(self, requete, timeout=None):
        return Reponse(json.dumps({"results": [{"n": 42}]}).encode())

    def test_cles_sans_montants(self):
        with contextlib.redirect_stderr(io.StringIO()):
            r = pst.executer(ouvrir=self.ouvrir, url_sf=self.url, groupes=2, annees=range(2019, 2021))
        self.assertEqual(r["profondeur_ratios"], {"2019": 42, "2020": 42})
        c = r["liasse"]["par_type"]["C"]
        self.assertEqual(c["bilans"], 3)
        self.assertEqual(c["cles"]["CO_m3"], round(2 / 3, 4))
        self.assertEqual(c["codes_attendus"]["CO"], {"CO_m3": round(2 / 3, 4)})
        self.assertEqual(r["liasse"]["par_type"]["S"]["codes_attendus"]["110"], {"110_m3": 1.0})
        # Aucun montant ne sort dans le rapport.
        self.assertNotIn("987654", json.dumps(r))


if __name__ == "__main__":
    unittest.main()
