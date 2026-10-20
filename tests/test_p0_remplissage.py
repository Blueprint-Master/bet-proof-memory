"""Tests de P0 v1.2 (remplissage par confidentialité), sans réseau."""

import io
import json
import os
import sys
import unittest
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "p0"))
import p0_remplissage as pr  # noqa: E402


class FausseReponse(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestRemplissage(unittest.TestCase):
    def setUp(self):
        self.urls = []

    def ouvrir(self, requete, timeout=None):
        url = urllib.parse.unquote_plus(requete.full_url)
        self.urls.append(url)
        if "/records?" not in url:
            corps = {"fields": [{"name": "siren"}, {"name": "chiffre_d_affaires"}, {"name": "total_bilan"}]}
        elif "chiffre_d_affaires is not null" in url:
            corps = {"results": [{"n": 0 if "Partiellement" in url else 90}]}
        elif "is not null" in url:
            corps = {"results": [{"n": 100 if "Partiellement" in url else 95}]}
        else:
            corps = {"results": [{"n": 100}]}
        return FausseReponse(json.dumps(corps).encode())

    def test_parts_par_niveau(self):
        r = pr.mesurer([2019], ouvrir=self.ouvrir)
        self.assertEqual(r["champs"], ["chiffre_d_affaires", "total_bilan"])
        self.assertEqual(r["par_annee"]["2019"]["Public"]["remplissage"]["chiffre_d_affaires"], 0.9)
        self.assertEqual(r["par_annee"]["2019"]["Partiellement confidentiel"]["remplissage"]["chiffre_d_affaires"], 0.0)
        self.assertEqual(r["par_annee"]["2019"]["Partiellement confidentiel"]["remplissage"]["total_bilan"], 1.0)

    def test_que_des_comptages(self):
        pr.mesurer([2019], ouvrir=self.ouvrir)
        for url in self.urls:
            if "/records?" in url:
                self.assertIn("select=count(*) as n", url)
            for interdit in ("avg(", "sum(", "min(", "max(", "group_by", "familleavis"):
                self.assertNotIn(interdit, url)


if __name__ == "__main__":
    unittest.main()
