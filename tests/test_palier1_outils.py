"""Tests de l'extraction des dossiers et des outils du palier 1 (jeu synthétique de test_construire)."""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "palier1"))
sys.path.insert(0, os.path.dirname(__file__))
import extraire_cas as ex  # noqa: E402
import outils as ou  # noqa: E402
from test_construire import jeu  # noqa: E402

T0 = dt.date(2018, 9, 30)
SIRENS = ["100000004", "100000006", "100000007", "100000010", "100000012"]


class TestPalier1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = tempfile.mkdtemp()
        jeu(cls.dossier)
        cls._sirene_avec_changement_apres_t0()
        with contextlib.redirect_stderr(io.StringIO()):
            cls.bruts = ex.extraire(cls.dossier, SIRENS, T0)
        cls.cle = b"cle-de-test"
        cls.doss, cls.corr = ex.pseudonymiser(cls.bruts, cls.cle)
        cls.journal = os.path.join(cls.dossier, "journal.jsonl")
        cls.reg = ou.Registre(cls.doss, lgd=0.9, journal=cls.journal)
        cls.k = {s: cls.corr[s] for s in SIRENS}

    @classmethod
    def _sirene_avec_changement_apres_t0(cls):
        """100000006 change de NAF le 01/07/2019 : la fin de sa première période (30/06/2019) et
        la seconde période révéleraient l'avenir."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        chemin = os.path.join(cls.dossier, "sirene-historique.parquet")
        t = pq.read_table(chemin).to_pylist()
        for l in t:
            if l["siren"] == "100000006":
                l["dateFin"] = "2019-06-30"
        t.append({"siren": "100000006", "dateDebut": "2019-07-01", "dateFin": None,
                  "categorieJuridiqueUniteLegale": "5710", "activitePrincipaleUniteLegale": "62.01Z",
                  "nomenclatureActivitePrincipaleUniteLegale": "NAFRev2"})
        pq.write_table(pa.Table.from_pylist(t), chemin)

    # --- extraction : rien après t0, aucun identifiant ---------------------------------
    def test_bilan_paru_apres_t0_absent(self):
        clotures = [b["cloture"] for b in self.bruts["100000007"]["bilans"]]
        self.assertEqual(clotures, ["2016-12-31"])  # la clôture 2017, parue le 15/10/2018, est écartée

    def test_evenements_apres_t0_absents(self):
        self.assertEqual(self.bruts["100000007"]["modifications"], [])  # dissolution parue en 2019
        natures = [p["nature"] for p in self.bruts["100000012"]["procedures"]]
        self.assertEqual(natures, ["OUV-SAUV", "PLAN"])  # résolution parue en 2019 écartée
        self.assertEqual(self.bruts["100000010"]["procedures"], [])  # sauvegarde parue en 2019
        self.assertEqual(self.bruts["100000004"]["radiation"], "2017-03-01")

    def test_toutes_les_dates_avant_t0(self):
        def dates(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("parution", "jugement", "radiation", "creation", "cloture", "debut", "fin") and v:
                        yield v
                    else:
                        yield from dates(v)
            elif isinstance(o, list):
                for v in o:
                    yield from dates(v)
        for s, x in self.bruts.items():
            for v in dates(x):
                self.assertLessEqual(v, T0.isoformat(), (s, v))

    def test_fin_de_periode_sirene_posterieure_effacee(self):
        per = self.bruts["100000006"]["sirene"]
        self.assertEqual(len(per), 1)  # la période débutant le 01/07/2019 est écartée
        self.assertIsNone(per[0]["fin"])  # la fin au 30/06/2019 est effacée
        self.assertEqual(per[0]["naf"], "41.20A")
        e = self.reg.appeler("etat", self.k["100000006"], "2018-09-30")["donnees"]
        self.assertEqual(e["naf"], "41.20A")

    def test_pseudonymisation(self):
        texte = json.dumps(self.doss)
        for s in SIRENS:
            self.assertNotIn(s, texte)
        self.assertTrue(all(k.startswith("K") and len(k) == 11 for k in self.doss))
        autre, _ = ex.pseudonymiser(self.bruts, b"autre-cle")
        self.assertNotEqual(set(autre), set(self.doss))
        self.assertEqual(ex.identifiant(self.cle, "100000007"), self.corr["100000007"])

    # --- outils ---------------------------------------------------------------------------
    def test_refus_apres_t0_journalise(self):
        n0 = len(self.reg.journal)
        r = self.reg.appeler("ratios", self.k["100000007"], "2018-10-31")
        self.assertEqual(r["statut"], "refus")
        self.assertEqual(r["motif"], "date postérieure à t0")
        self.assertEqual(self.reg.journal[n0]["statut"], "refus")
        self.assertIn(r["preuve"], self.reg.preuves("refus"))
        for mauvaise in (None, "30/09/2018", "2018-13-01"):
            self.assertEqual(self.reg.appeler("etat", self.k["100000007"], mauvaise)["statut"], "refus")

    def test_ratios_a_t0(self):
        r = self.reg.appeler("ratios", self.k["100000007"], "2018-09-30")
        b = r["donnees"]["bilan"]
        self.assertEqual(b["cloture"], "2016-12-31")
        self.assertEqual(b["retard_depot_jours"], (dt.date(2017, 7, 1) - dt.date(2016, 12, 31)).days)
        self.assertEqual(b["ratios"]["ratio_de_liquidite"], 1.2)
        avant = self.reg.appeler("ratios", self.k["100000007"], "2017-06-30")
        self.assertIsNone(avant["donnees"]["bilan"])

    def test_etat_procedure(self):
        k = self.k["100000012"]
        self.assertEqual(self.reg.appeler("etat", k, "2016-07-01")["donnees"]["procedure_en_cours"], "SAUV")
        self.assertEqual(self.reg.appeler("etat", k, "2018-09-30")["donnees"]["procedure_en_cours"], "PLAN")
        e = self.reg.appeler("etat", self.k["100000004"], "2018-09-30")["donnees"]
        self.assertTrue(e["radiee"])
        self.assertEqual(e["naf"], "41.20A")

    def test_annonces_codees(self):
        a = self.reg.appeler("annonces", self.k["100000006"], "2018-09-30")["donnees"]["annonces"]
        types = [v["type"] for v in a]
        self.assertIn("PROCEDURE", types)
        self.assertIn("FUSION", types)
        self.assertTrue(all(set(v) <= {"type", "parution", "nature", "cloture"} for v in a))

    def test_prevision_au_seul_t0(self):
        k = self.k["100000007"]
        self.reg.dossiers[k]["prevision"] = {"p": 0.0312345678, "fichier": "prevision-test.parquet"}
        ok = self.reg.appeler("prevision", k, "2018-09-30")
        self.assertEqual(ok["donnees"]["p_defaillance_548j"], 0.031235)
        self.assertEqual(self.reg.appeler("prevision", k, "2018-09-29")["motif"], "prévision disponible au seul t0")
        self.assertEqual(self.reg.appeler("prevision", self.k["100000010"], "2018-09-30")["statut"], "refus")

    def test_seuils(self):
        r = self.reg.appeler("seuils", scenario="S1")["donnees"]
        self.assertAlmostEqual(r["p_t"], 0.001 * (548 / 30) / (0.7 * 0.9), places=8)
        self.assertEqual(self.reg.appeler("seuils", scenario="S9")["statut"], "refus")
        self.assertEqual(len(ou.SCENARIOS), 6)

    def test_preuve_deterministe_et_journal_fichier(self):
        a = self.reg.appeler("etat", self.k["100000010"], "2018-09-30")
        b = self.reg.appeler("etat", self.k["100000010"], "2018-09-30")
        self.assertEqual(a["preuve"], b["preuve"])
        c = self.reg.appeler("etat", self.k["100000010"], "2018-09-29")
        self.assertNotEqual(a["preuve"], c["preuve"])
        with open(self.journal, encoding="utf-8") as f:
            lignes = [json.loads(l) for l in f]
        self.assertEqual(len(lignes), len(self.reg.journal))

    def test_aucun_identifiant_dans_les_reponses(self):
        texte = json.dumps([self.reg.appeler(o, self.k[s], "2018-09-30") for s in SIRENS
                            for o in ("ratios", "annonces", "etat")])
        for s in SIRENS:
            self.assertNotIn(s, texte)

    def test_inconnus(self):
        self.assertEqual(self.reg.appeler("ratios", "K0000000000", "2018-09-30")["motif"], "cas inconnu")
        self.assertEqual(self.reg.appeler("bilan_complet", self.k["100000007"], "2018-09-30")["motif"],
                         "outil inconnu")


if __name__ == "__main__":
    unittest.main()
