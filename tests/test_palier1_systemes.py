"""Tests des configurations T0, T1 et B du palier 1, avec un modèle factice scripté."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "palier1"))
sys.path.insert(0, os.path.dirname(__file__))
import regles as rg  # noqa: E402
import systemes as sy  # noqa: E402
import verificateurs as vf  # noqa: E402
from test_palier1_verificateurs import LGD, T0, dossier  # noqa: E402


class Factice(sy.Modele):
    """Rend des réponses dans l'ordre ; une réponse peut être une fonction des messages."""

    nom = "factice"

    def __init__(self, reponses, jetons=100):
        self.reponses, self.jetons, self.vus = list(reponses), jetons, []

    def appeler(self, messages):
        self.vus.append([dict(m) for m in messages])
        r = self.reponses.pop(0) if self.reponses else "{}"
        texte = r(messages) if callable(r) else r
        return {"texte": texte, "jetons_entree": self.jetons, "jetons_sortie": 10}


def appels(*l):
    return json.dumps({"appels": list(l)})


def preuves_vues(messages):
    """Identifiants de preuve des résultats d'outils renvoyés au modèle."""
    out = []
    for m in messages:
        if m["role"] == "user" and "\"preuve\"" in m["content"]:
            txt = m["content"]
            i = 0
            while (i := txt.find("\"preuve\": \"", i)) >= 0:
                out.append(txt[i + 11:i + 24])
                i += 24
    return out


ETAT = {"outil": "etat", "date": T0}
PREV = {"outil": "prevision", "date": T0}
SEUIL = {"outil": "seuils", "scenario": "S1"}
INFO_EL = {"type": "eligible", "scenario": "S1", "t0": T0, "y": 0, "w": 1.0}


class TestT0T1(unittest.TestCase):
    def setUp(self):
        self.d = {"Kh": dossier(0.5), "Klj": dossier(None, "OUV-LJ")}

    def test_T0_un_appel_sans_outil(self):
        m = Factice([rg.sortie("Kh", "conserver", [], "aucune information")])
        e = sy.executer_T0(m, "Kh", T0, "S1")
        self.assertEqual(e["cout"]["appels_modele"], 1)
        self.assertNotIn("Outils", m.vus[0][0]["content"])
        self.assertIn(rg.REGLES_METIER, m.vus[0][0]["content"])
        f = vf.fiche(e, INFO_EL, LGD)
        self.assertEqual({k for k, v in f["violations"].items() if v}, {"e"})

    def test_T1_bonne_conduite(self):
        fin = lambda msgs: rg.sortie("Kh", "couvrir", preuves_vues(msgs), "p > p_t")  # noqa: E731
        m = Factice([appels(ETAT, PREV, SEUIL), fin])
        e = sy.executer_T1(m, self.d, LGD, "Kh", "S1")
        self.assertEqual(len(e["journal"]), 3)
        self.assertEqual(e["cout"]["appels_modele"], 2)
        self.assertFalse(vf.fiche(e, INFO_EL, LGD)["viole"])

    def test_T1_lecture_apres_t0_journalisee(self):
        fin = lambda msgs: rg.sortie("Kh", "couvrir", preuves_vues(msgs)[:3], "x")  # noqa: E731
        m = Factice([appels(ETAT, PREV, SEUIL, {"outil": "annonces", "date": "2021-06-30"}), fin])
        e = sy.executer_T1(m, self.d, LGD, "Kh", "S1")
        self.assertEqual(e["journal"][-1]["statut"], "refus")
        self.assertTrue(vf.fiche(e, INFO_EL, LGD)["violations"]["d"])

    def test_T1_plafond_atteint_sortie_nulle(self):
        m = Factice([appels(ETAT)] * 10)
        e = sy.executer_T1(m, self.d, LGD, "Kh", "S1")
        self.assertIsNone(e["sortie"])
        self.assertEqual(e["cout"]["appels_modele"], sy.PLAFOND["appels_modele"])
        self.assertTrue(vf.fiche(e, INFO_EL, LGD)["violations"]["c"])
        m = Factice([appels(ETAT)] * 10, jetons=30_000)
        self.assertEqual(sy.executer_T1(m, self.d, LGD, "Kh", "S1")["cout"]["appels_modele"], 2)

    def test_T1_texte_libre_non_conforme(self):
        m = Factice(["```json\n" + rg.sortie("Kh", "couvrir", [], "x") + "\n```"])
        e = sy.executer_T1(m, self.d, LGD, "Kh", "S1")
        self.assertTrue(vf.fiche(e, INFO_EL, LGD)["violations"]["c"])

    def test_meme_prompt_systeme_T1_B(self):
        m1, m2 = Factice([rg.sortie("Kh", "conserver", [], "")]), Factice([appels()])
        sy.executer_T1(m1, self.d, LGD, "Kh", "S1")
        sy.executer_B(m2, self.d, LGD, "Kh", "S1")
        self.assertEqual(m1.vus[0][:2], m2.vus[0][:2])


class TestB(unittest.TestCase):
    def setUp(self):
        self.d = {"Kh": dossier(0.5), "Kb": dossier(0.0001), "Klj": dossier(None, "OUV-LJ"),
                  "Kp": dossier(None)}

    def b(self, cas, reponses, scenario="S1"):
        return sy.executer_B(Factice(reponses), self.d, LGD, cas, scenario)

    def decision(self, e):
        return json.loads(e["sortie"])["decision"]

    def test_bloque_apres_t0_sans_toucher_l_outil(self):
        e = self.b("Kh", [appels({"outil": "annonces", "date": "2021-01-01"}, {"outil": "ratios", "date": "30/09/2020"},
                                 {"outil": "bilan_complet", "date": T0}),
                          rg.sortie("Kh", "couvrir", [], "p > p_t")])
        self.assertEqual(len(e["bloques"]), 3)
        self.assertTrue(all(j["statut"] == "ok" for j in e["journal"]))  # l'outil n'a rien vu d'illégal
        self.assertEqual(self.decision(e), "couvrir")
        f = vf.fiche(e, INFO_EL, LGD)
        self.assertFalse(f["viole"], f["violations"])
        self.assertEqual([t["etat"] for t in e["trace"]][:6], ["S0", "S1", "S2", "S3", "S11", "S8"])

    def test_S11_complete_les_preuves_manquantes(self):
        e = self.b("Kb", [appels(), rg.sortie("Kb", "conserver", [], "p <= p_t")])
        self.assertEqual({j["outil"] for j in e["journal"]}, {"etat", "prevision", "seuils"})
        self.assertEqual(self.decision(e), "conserver")
        self.assertEqual(len(json.loads(e["sortie"])["preuves"]), 3)

    def test_contredit_puis_corrige(self):
        e = self.b("Kh", [appels(ETAT, PREV, SEUIL), rg.sortie("Kh", "conserver", [], "x"),
                          rg.sortie("Kh", "couvrir", [], "corrigé")])
        self.assertEqual(self.decision(e), "couvrir")
        s8 = [t for t in e["trace"] if t["etat"] == "S8"]
        self.assertEqual([t["verdict"] for t in s8], ["contredit", "verifie"])

    def test_persistance_mene_a_l_abstention(self):
        e = self.b("Kh", [appels(), *[rg.sortie("Kh", "conserver", [], "x")] * 3])
        self.assertEqual(self.decision(e), "abstention")
        self.assertEqual(e["trace"][-2]["etat"], "ABSTENTION")
        self.assertEqual(e["cout"]["appels_modele"], 4)
        self.assertTrue(vf.fiche(e, INFO_EL, LGD)["abstention"])

    def test_non_conforme_puis_conforme(self):
        e = self.b("Kh", [appels(), "Je couvre.", rg.sortie("Kh", "couvrir", [], "x")])
        self.assertEqual(self.decision(e), "couvrir")

    def test_liquidation_abstention_imposee(self):
        info = {"type": "piege_avant", "scenario": "S1", "t0": T0}
        e = self.b("Klj", [appels(ETAT), rg.sortie("Klj", "couvrir", [], "x"),
                           rg.sortie("Klj", "abstention", [], "liquidation")])
        self.assertEqual(self.decision(e), "abstention")
        self.assertNotIn("prevision", {j["outil"] for j in e["journal"]})  # rien d'inutile n'est lu
        self.assertFalse(vf.fiche(e, info, LGD)["viole"])

    def test_prevision_absente(self):
        e = self.b("Kp", [appels(ETAT, PREV, SEUIL)])
        self.assertEqual(self.decision(e), "abstention")
        self.assertIn("inconnu", e["trace"][-2]["motif"])

    def test_budget(self):
        e = sy.executer_B(Factice([appels()] + ["x"] * 9), self.d, LGD, "Kh", "S1",
                          plafond={"appels_modele": 2, "jetons": 40_000})
        self.assertEqual(self.decision(e), "abstention")
        self.assertEqual(e["cout"]["appels_modele"], 2)
        self.assertIn("budget", e["trace"][-2]["motif"])

    def test_seuil_d_un_autre_scenario_ne_vaut_pas(self):
        e = self.b("Kh", [appels(ETAT, PREV, {"outil": "seuils", "scenario": "S6"}),
                          rg.sortie("Kh", "couvrir", [], "x")], scenario="S1")
        s11 = [j for j in e["journal"] if j["outil"] == "seuils"]
        self.assertEqual([j["args"]["scenario"] for j in s11], ["S6", "S1"])


if __name__ == "__main__":
    unittest.main()


class TestExecuteurEtAdaptateurs(unittest.TestCase):
    def test_reprise_et_plafond_total(self):
        import tempfile

        import executer as ex

        d = {"Ka": dossier(0.5), "Kb": dossier(0.0001)}
        qs = [("Ka", "S1"), ("Kb", "S2")]
        chemin = os.path.join(tempfile.mkdtemp(), "exe.jsonl")
        bon = lambda msgs: rg.sortie(msgs[1]["content"][6:8], "conserver", [], "x")  # noqa: E731
        r = ex.executer(Factice([bon] * 2), d, LGD, qs, ["D", "T0"], chemin, max_appels=1)
        self.assertEqual((r["executions"], r["arret"]), (3, "plafond total d'appels atteint"))
        r = ex.executer(Factice([bon]), d, LGD, qs, ["D", "T0"], chemin, max_appels=10)
        self.assertEqual(r["executions"], 1)  # seul T0 sur Kb restait
        with open(chemin) as f:
            lignes = [json.loads(l) for l in f]
        self.assertEqual(sorted((e["systeme"], e["cas"]) for e in lignes),
                         [("D", "Ka"), ("D", "Kb"), ("T0", "Ka"), ("T0", "Kb")])

    def test_questions_ne_lit_que_le_scenario(self):
        import tempfile

        import executer as ex

        chemin = os.path.join(tempfile.mkdtemp(), "cas.json")
        with open(chemin, "w") as f:
            json.dump({"Kb": {"type": "eligible", "scenario": "S2", "t0": T0, "y": 1, "w": 0.02},
                       "Ka": {"type": "piege_avant", "scenario": "S5", "t0": T0}}, f)
        self.assertEqual(ex.questions(chemin), [("Ka", "S5"), ("Kb", "S2")])

    def test_adaptateurs(self):
        from unittest import mock

        import modeles as mo

        vus = []

        class Rep:
            def __init__(self, corps):
                self.corps = corps

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps(self.corps).encode()

        def faux(req, timeout):
            vus.append((req.full_url, json.loads(req.data), dict(req.headers)))
            if "anthropic" in req.full_url:
                return Rep({"content": [{"type": "text", "text": "ok"}], "usage": {"input_tokens": 7,
                                                                                    "output_tokens": 2}, "model": "m"})
            return Rep({"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 7,
                                                                               "completion_tokens": 2}})

        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "a"}, {"role": "user", "content": "b"}]
        with mock.patch.dict(os.environ, {"CLE": "x"}), mock.patch("urllib.request.urlopen", faux):
            r1 = mo.CompatibleOpenAI("https://h/v1", "m-1", "CLE").appeler(msgs)
            r2 = mo.Anthropic("m-2", "CLE").appeler(msgs)
        self.assertEqual((r1["texte"], r1["jetons_entree"], r2["jetons_sortie"]), ("ok", 7, 2))
        self.assertEqual(vus[0][1]["temperature"], 0)
        self.assertEqual(len(vus[0][1]["messages"]), 2)  # deux messages utilisateur fusionnés
        self.assertEqual(vus[1][1]["system"], "s")
        self.assertEqual(vus[1][1]["messages"], [{"role": "user", "content": "a\n\nb"}])
