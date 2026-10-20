"""Tests de la construction des cas (phase 5, étape 2) sur un jeu synthétique."""

import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
import construire as co  # noqa: E402

D = dt.date


def jugement(famille, nature, date, typ="initial"):
    return json.dumps({"type": typ, "famille": famille, "nature": nature, "date": date})


def jeu(dossier):
    import pyarrow as pa
    import pyarrow.parquet as pq

    def ecrire(nom, colonnes):
        pq.write_table(pa.table(colonnes), os.path.join(dossier, nom))

    n = None
    lignes = [  # siren, cloture, type, conf, marge_ebe, ca, resultat_net
        ("100000001", "2017-12-31", "C", "Public", 0.10, 1e6, 5e4),
        ("100000001", "2017-12-31", "S", "Public", 0.20, 1e6, 5e4),   # doublon : C préféré
        ("100000002", "2017-12-31", "S", "Partiellement confidentiel", n, 0.0, 0.0),
        ("100000003", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),
        ("100000004", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),
        ("100000005", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),
        ("100000006", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),
        ("100000007", "2016-12-31", "C", "Public", 0.3, 2e6, 1e4),
        ("100000007", "2017-12-31", "C", "Public", 0.9, 2e6, 1e4),   # paru après t0 : ignoré
        ("100000008", "2017-12-31", "K", "Public", 0.1, 1e9, 1e4),   # consolidé seul
        ("100000009", "2018-12-31", "C", "Public", 0.1, 1e6, 1e4),   # clôture après parution
        ("100000010", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),
        ("100000011", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),   # ouverture datée avant t0, parue après
        ("100000012", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),   # en plan de sauvegarde, puis résolution
        ("100000013", "2017-12-31", "C", "Public", 0.1, 1e6, 1e4),   # en observation de sauvegarde
    ]
    cols = {c: [] for c in co.COLONNES_RATIOS}
    for s, c, t, conf, me, ca, rn in lignes:
        for k in co.COLONNES_RATIOS:
            cols[k].append(None)
        cols["siren"][-1], cols["date_cloture_exercice"][-1], cols["type_bilan"][-1] = s, c, t
        cols["confidentiality"][-1], cols["marge_ebe"][-1] = conf, me
        cols["chiffre_d_affaires"][-1], cols["resultat_net"][-1] = ca, rn
        cols["autonomie_financiere"][-1] = -0.1 if s == "100000006" else 0.3
        cols["ratio_de_liquidite"][-1] = 1.2
    tab = pa.table({k: pa.array(v, type=pa.string() if k in co.COLONNES_RATIOS[:4] else pa.float64())
                    for k, v in cols.items()})
    pq.write_table(tab, os.path.join(dossier, "ratios-2017.parquet"))
    avis = [(s, c, "2018-06-01") for s, c, *_ in lignes]
    avis[8] = ("100000007", "2017-12-31", "2018-10-15")
    avis[7] = ("100000007", "2016-12-31", "2017-07-01")
    avis[10] = ("100000009", "2018-12-31", "2018-06-01")
    ecrire("bodacc-dpc.parquet", {
        "dateparution": [p for _, _, p in avis],
        "registre": [f"{s[:3]} {s[3:6]} {s[6:]},{s}" for s, _, _ in avis],
        "depot": [json.dumps({"dateCloture": c, "typeDepot": "Comptes annuels"}) for _, c, _ in avis]})
    ecrire("sf-totaux.parquet", {
        "siren": ["100000001", "100000002"], "date_cloture_exercice": [D(2017, 12, 31)] * 2,
        "type_bilan": ["C", "S"], "confidentiality": ["Public", "Partiellement confidentiel"],
        "EE": [1.5e6, None], "180": [None, 5e5], "CO-1A": [1.5e6, None], "110-112": [None, 5e5],
        "CJ-CK": [9e5, None], "EC": [6e5, None], "DU": [2e5, None], "DD": [1e5, None], "DH": [5e4, None],
        "GG": [7.5e4, None], "DL": [9e5, None],
        "096": [None, 3e5], "176": [None, 2e5], "156": [None, 5e4], "142": [None, 3e5]})
    sirens = [f"1000000{i:02d}" for i in range(1, 14)]
    ecrire("sirene-historique.parquet", {
        "siren": sirens, "dateDebut": ["2000-01-01"] * 13, "dateFin": [None] * 13,
        "categorieJuridiqueUniteLegale": ["6540" if s == "100000003" else "5710" for s in sirens],
        "activitePrincipaleUniteLegale": ["41.20A"] * 13,
        "nomenclatureActivitePrincipaleUniteLegale": ["NAFRev2"] * 13})
    ecrire("sirene-creation.parquet", {"siren": sirens, "dateCreationUniteLegale": ["2005-01-01"] * 13})
    ecrire("bodacc-collective.parquet", {
        "dateparution": ["2019-05-15", "2017-01-20", "2016-03-01", "2017-05-01", "2019-02-01", "2019-03-01",
                         "2018-10-05", "2016-06-01", "2017-06-01", "2019-06-01", "2018-03-01"],
        "registre": ["100000001", "100000005", "100000006", "100000006", "100000010", "100000002",
                     "100000011", "100000012", "100000012", "100000012", "100000013"],
        "jugement": [
            jugement("Jugement d'ouverture", "Jugement d'ouverture de liquidation judiciaire", "2019-05-01"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture d'une procédure de redressement judiciaire",
                     "2017-01-10"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture d'une procédure de redressement judiciaire",
                     "2016-02-20"),
            jugement("Jugement de clôture", "Jugement de clôture pour extinction du passif", "2017-04-20"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture d'une procédure de sauvegarde", "2019-01-20"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture de liquidation judiciaire", "2019-02-20",
                     typ="annule"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture de liquidation judiciaire", "2018-09-20"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture d'une procédure de sauvegarde", "2016-05-20"),
            jugement("Extrait de jugement", "Jugement arrêtant le plan de sauvegarde", "2017-05-20"),
            jugement("Jugement prononçant", "Jugement prononçant la résolution du plan de sauvegarde et la "
                                             "liquidation judiciaire", "2019-05-20"),
            jugement("Jugement d'ouverture", "Jugement d'ouverture d'une procédure de sauvegarde", "2018-02-20")]})
    ecrire("bodacc-modification-evenements.parquet", {
        "dateparution": ["2019-01-10", "2017-01-10"], "registre": ["100000007", "100000006"],
        "evenement": ["dissolution", "fusion"]})
    ecrire("bodacc-radiation.parquet", {"dateparution": ["2017-03-01"], "registre": ["100000004"]})
    mois = [f"{a}-{m:02d}" for a in range(2010, 2019) for m in range(1, 13)]
    ecrire("bdf-diren.parquet", {
        "series_key": ["DIREN.M.FR.DE.UL.DF.03.N.ZZ.TT"] * len(mois), "time_period": mois,
        "obs_value": [120.0 if p == "2018-06" else 100.0 for p in mois],
        "updated_at": ["2024-12-02"] * len(mois), "OBS_STATUS": ["A"] * len(mois)})


class TestConstruire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pyarrow.parquet as pq

        cls.dossier = tempfile.mkdtemp()
        jeu(cls.dossier)
        with contextlib.redirect_stderr(io.StringIO()):
            sortie = co.Sortie(os.path.join(cls.dossier, "cas-dev.parquet"))
            cls.n, cls.rapport = co.construire(cls.dossier, sortie, origines=(2018,), seuil=5,
                                               aujourdhui=D(2026, 10, 20))
            sortie.fermer()
            cls.chemin, cls.h = co.ecrire_rapport(cls.dossier, sortie, cls.n, cls.rapport)
        cls.cas = {r["siren"]: r for r in pq.read_table(sortie.chemin).to_pylist()}

    def test_exclusions_et_couverture(self):
        m = self.rapport["origines"]["2018"]
        self.assertEqual(m["forme_hors_p1"], 1)
        self.assertEqual(m["radiee"], 1)
        self.assertEqual(m["procedure_en_cours"], 1)
        self.assertEqual(m["ouverture_anterieure_publiee_apres_t0"], 1)
        self.assertEqual(m["eligibles"], 7)
        self.assertTrue(m["retenue"])
        self.assertEqual(set(self.cas), {"100000001", "100000002", "100000006", "100000007", "100000010",
                                         "100000012", "100000013"})
        b = self.rapport["bilans_exclus"]
        self.assertEqual((b["consolides"], b["doublon_type"], b["cloture_apres_parution"]), (1, 1, 1))

    def test_issue_et_sauvegarde(self):
        self.assertEqual(self.cas["100000001"]["issue"], 1)
        self.assertEqual(self.cas["100000001"]["date_issue"], D(2019, 5, 1))
        self.assertEqual(self.cas["100000010"]["issue"], 0)
        self.assertEqual(self.cas["100000010"]["sauvegarde"], 1)
        self.assertEqual(self.cas["100000002"]["issue"], 0)  # jugement annulé ignoré
        self.assertEqual(self.rapport["origines"]["2018"]["defaillances"], 2)  # A et la résolution de plan

    def test_bilan_connu_et_variables(self):
        a = self.cas["100000001"]
        self.assertEqual(a["type_bilan"], "C")
        self.assertAlmostEqual(a["marge_ebe"], 0.10)
        self.assertAlmostEqual(a["log_total_bilan"], co.math.log(1.5e6))
        self.assertAlmostEqual(a["resultat_net_sur_total_bilan"], 5e4 / 1.5e6)
        self.assertEqual(a["retard_depot_jours"], (D(2018, 6, 1) - D(2017, 12, 31)).days)
        self.assertEqual(self.cas["100000007"]["cloture"], D(2016, 12, 31))
        self.assertAlmostEqual(self.cas["100000007"]["marge_ebe"], 0.3)
        self.assertEqual(self.cas["100000006"]["capitaux_propres_negatifs"], 1)

    def test_plans_et_sauvegardes_inclus(self):
        p = self.cas["100000012"]
        self.assertEqual((p["en_plan"], p["en_observation_sauvegarde"]), (1, 0))
        self.assertEqual((p["issue"], p["date_issue"]), (1, D(2019, 5, 20)))  # résolution du plan
        o = self.cas["100000013"]
        self.assertEqual((o["en_plan"], o["en_observation_sauvegarde"], o["issue"]), (0, 1, 0))
        self.assertEqual(self.rapport["origines"]["2018"]["exclus_etat_RJ"], 1)

    def test_evenements_concurrents(self):
        self.assertEqual(self.cas["100000007"]["evenement_concurrent"], "dissolution")
        self.assertIsNone(self.cas["100000006"]["evenement_concurrent"])  # fusion avant t0

    def test_altman(self):
        a = self.cas["100000001"]
        self.assertAlmostEqual(a["altman_x1"], (9e5 - (6e5 - 2e5)) / 1.5e6)
        self.assertAlmostEqual(a["altman_x2"], 1.5e5 / 1.5e6)
        self.assertAlmostEqual(a["altman_x3"], 7.5e4 / 1.5e6)
        self.assertAlmostEqual(a["altman_x4"], 9e5 / 6e5)
        b = self.cas["100000002"]
        self.assertAlmostEqual(b["altman_x1"], (3e5 - (2e5 - 5e4)) / 5e5)
        self.assertIsNone(b["altman_x3"])  # compte de résultat masqué : 270 absent

    def test_compte_de_resultat_masque(self):
        b = self.cas["100000002"]
        self.assertEqual(b["cr_indisponible"], 1)
        self.assertEqual(b["marge_ebe"], 0.0)
        self.assertEqual(b["log_chiffre_affaires"], 0.0)
        self.assertEqual(b["confidentiel"], 1)
        self.assertAlmostEqual(b["log_total_bilan"], co.math.log(5e5))

    def test_intensite_sectorielle(self):
        a = self.cas["100000001"]
        self.assertEqual(a["secteur_bdf"], "FZ")
        self.assertEqual(a["taille_bdf"], "MI")
        self.assertEqual(a["serie_bdf"], "DIREN.M.FR.DE.UL.DF.03.N.ZZ.TT")
        self.assertAlmostEqual(a["intensite_sectorielle"], 1.2)

    def test_garde_et_seuil(self):
        with self.assertRaisesRegex(ValueError, "scellé"):
            co.construire(self.dossier, None, origines=(2021,))
        self.assertEqual(len(self.h), 64)
        r = json.load(open(self.chemin))
        self.assertEqual(r["sortie"]["lignes"], 7)
        self.assertIn("ratios-2017.parquet", r["entrees"])

    def test_natures_v101(self):
        cj = lambda f, n, c=None: co.classer_jugement(json.dumps(  # noqa: E731
            {"famille": f, "nature": n, "date": "2020-01-01", "complementJugement": c}))[0]
        self.assertEqual(cj("Jugement de clÃ´ture", "Jugement de clÃ´ture pour insuffisance d'actif"), "CLOT")
        self.assertEqual(cj("Extrait de jugement", "Jugement mettant fin à la procédure de redressement judiciaire"),
                         "CLOT")
        self.assertEqual(cj("Jugement prononçant",
                            "Jugement de conversion en liquidation judiciaire de la procédure de sauvegarde"),
                         "CONV-SAUV-LJ")
        self.assertEqual(cj("Jugement prononçant", "Jugement de conversion en liquidation judiciaire"), "AUTRE")
        self.assertEqual(cj("Extrait de jugement", "Jugement prononçant la résolution du plan de redressement "
                                                   "et la liquidation judiciaire"), "RESOL-LJ")
        self.assertEqual(cj("Extrait de jugement", "Jugement de reprise de la procédure de liquidation judiciaire"),
                         "REOUV")
        self.assertEqual(cj("Jugement d'ouverture", "Autre jugement d'ouverture",
                            "Jugement prononçant l'ouverture d'une procédure de liquidation judiciaire simplifiée"),
                         "OUV-LJ")
        self.assertEqual(cj("Jugement d'ouverture", "Autre jugement d'ouverture", "texte sans procédure"),
                         "OUV-INDET")
        self.assertEqual(cj("Avis de dÃ©pÃ´t", "DÃ©pÃ´t de l'Ã©tat des crÃ©ances"), "AUTRE")
        self.assertIn("OUV-INDET", co.OUVRANTS)
        self.assertNotIn("OUV-INDET", co.ISSUES)

    def test_verification_des_instantanes(self):
        import shutil

        d = tempfile.mkdtemp()
        for f in os.listdir(self.dossier):
            if f.endswith(".parquet") and f != "cas-dev.parquet":
                shutil.copy(os.path.join(self.dossier, f), d)
        with self.assertRaisesRegex(RuntimeError, "sans manifeste"):
            co.verifier_instantanes(d)
        fichiers = [{"fichier": f, "sha256": co.sha256_fichier(os.path.join(d, f))}
                    for f in os.listdir(d) if f.endswith(".parquet")]
        with open(os.path.join(d, "manifeste-test-20261020-000000.json"), "w") as f:
            json.dump({"fichiers": fichiers}, f)
        self.assertIn("sf-totaux.parquet", co.verifier_instantanes(d))
        with open(os.path.join(d, "sf-totaux.parquet"), "ab") as f:
            f.write(b"x")  # réécriture en cours
        with self.assertRaisesRegex(RuntimeError, "ne correspond pas"):
            co.verifier_instantanes(d)
        shutil.copy(os.path.join(self.dossier, "sf-totaux.parquet"), d)
        os.remove(os.path.join(d, "bdf-diren.parquet"))
        with self.assertRaisesRegex(RuntimeError, "manquant"):
            co.verifier_instantanes(d)

    def test_classer_jugement(self):
        self.assertEqual(co.classer_jugement(jugement("Jugement de clôture", "clôture pour insuffisance d'actif",
                                                      "2020-01-01"))[0], "CLOT")
        self.assertEqual(co.classer_jugement("texte libre sans nature")[0], "AUTRE")
        self.assertEqual(co.taille_bdf(5e7, None), "IG")
        self.assertEqual(co.secteur_bdf("47"), "G")
        self.assertIsNone(co.secteur_bdf(None))


if __name__ == "__main__":
    unittest.main()
