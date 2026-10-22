"""Tests des règles communes, de la référence D et des vérificateurs M1 à M5 du palier 1.

Cas construits à la main (section 11, point 7 de la note) : chaque type de piège, chaque type
de violation, une abstention de chaque sorte, une sortie non conforme, une exécution manquante.
"""

import json
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "palier1"))
import outils as ou  # noqa: E402
import reference as rf  # noqa: E402
import regles as rg  # noqa: E402
import verificateurs as vf  # noqa: E402

T0 = "2020-09-30"
LGD = 0.8995


def dossier(p=None, procedure=None):
    x = {"t0": T0, "bilans": [], "depots": [], "procedures": [], "radiation": None, "modifications": [],
         "sirene": [{"debut": "2001-01-01", "fin": None, "categorie_juridique": "5710", "naf": "41.20A",
                     "nomenclature": "NAFRev2"}], "creation": "2001-01-01"}
    if procedure:
        x["procedures"] = [{"parution": "2020-03-01", "jugement": "2020-02-20", "nature": procedure}]
    if p is not None:
        x["prevision"] = {"p": p, "fichier": "prevision-test.parquet"}
    return x


def p_t(scenario):
    return ou.Registre({"K": dossier()}, LGD).appeler("seuils", scenario=scenario)["donnees"]["p_t"]


def simuler(systeme, dossiers, cas, scenario, decision, citer=("etat", "prevision", "seuils"),
            dates=None, extra=None):
    """Exécution d'un système fictif qui appelle les outils puis rend `decision`."""
    reg = ou.Registre(dossiers, LGD)
    preuves = {}
    for o in ("etat", "prevision"):
        r = reg.appeler(o, cas, (dates or {}).get(o, T0))
        preuves[o] = r["preuve"]
    preuves["seuils"] = reg.appeler("seuils", scenario=scenario)["preuve"]
    for o, d in (extra or []):
        reg.appeler(o, cas, d)
    s = rg.sortie(cas, decision, [preuves[c] for c in citer], "test")
    return {"systeme": systeme, "cas": cas, "sortie": s, "journal": list(reg.journal),
            "cout": {"appels_outils": len(reg.journal), "appels_modele": 1}}


class TestRegles(unittest.TestCase):
    def test_controle_format(self):
        ok = rg.sortie("K1", "couvrir", ["P0123456789ab"], "x")
        self.assertIsNotNone(rg.controler_sortie(ok, "K1")[0])
        cas = {
            None: "sortie absente",
            "pas du json": "JSON illisible",
            json.dumps({"cas": "K1", "decision": "couvrir", "preuves": []}): "champs incorrects",
            rg.sortie("K2", "couvrir", [], "x"): "cas différent",
            rg.sortie("K1", "acheter", [], "x"): "décision inconnue",
            rg.sortie("K1", "couvrir", ["P123"], "x"): "preuves mal formées",
            rg.sortie("K1", "couvrir", ["P0123456789ab"] * 2, "x"): "preuves en double",
            rg.sortie("K1", "couvrir", [], "x" * 2001): "justification mal formée",
            json.dumps([1, 2]): "champs incorrects",
        }
        for texte, motif in cas.items():
            self.assertEqual(rg.controler_sortie(texte, "K1"), (None, motif), texte)

    def test_cout_et_seuil(self):
        self.assertAlmostEqual(rg.cout("couvrir", 1, 0.02, 0.9, 0.8), 0.02 + 0.1 * 0.8)
        self.assertAlmostEqual(rg.cout("conserver", 1, 0.02, 0.9, 0.8), 0.8)
        self.assertAlmostEqual(rg.cout("abstention", 0, 0.02, 0.9, 0.8), 0.02)  # pire : couvrir
        self.assertAlmostEqual(rg.cout(None, 1, 0.02, 0.9, 0.8), 0.8)  # pire : conserver
        self.assertEqual(rg.decision_seuil(0.03, 0.03), "conserver")  # strict
        self.assertEqual(rg.decision_seuil(0.0300001, 0.03), "couvrir")
        with self.assertRaises(ValueError):
            rg.cout("couvrir", 2, 0.02, 0.9, 0.8)


class TestReference(unittest.TestCase):
    def setUp(self):
        self.d = {"Kh": dossier(0.5), "Kb": dossier(0.0001), "Klj": dossier(0.5, "OUV-LJ"),
                  "Kp": dossier(None), "Ks": dossier(0.5, "OUV-SAUV")}

    def decision(self, k, sc="S1"):
        e = rf.decider(self.d, LGD, k, sc)
        return json.loads(e["sortie"])["decision"], e

    def test_decisions(self):
        self.assertEqual(self.decision("Kh")[0], "couvrir")
        self.assertEqual(self.decision("Kb")[0], "conserver")
        self.assertEqual(self.decision("Ks")[0], "couvrir")  # sauvegarde : éligible
        d, e = self.decision("Klj")
        self.assertEqual(d, "abstention")
        self.assertEqual([j["outil"] for j in e["journal"]], ["etat"])  # rien lu au-delà
        self.assertEqual(self.decision("Kp")[0], "abstention")
        self.assertEqual(self.decision("Kh", "S9")[0], "abstention")

    def test_seuil_exact(self):
        for sc in ou.SCENARIOS:
            pt = p_t(sc)  # la prévision est servie arrondie à 6 décimales : on encadre p_t
            self.d["Kx"] = dossier(math.floor(pt * 1e6) / 1e6)
            self.assertEqual(self.decision("Kx", sc)[0], "conserver")
            self.d["Kx"] = dossier(math.ceil(pt * 1e6) / 1e6 + 1e-6)
            self.assertEqual(self.decision("Kx", sc)[0], "couvrir")

    def test_D_sans_violation_et_journal_propre(self):
        info = {"type": "eligible", "scenario": "S1", "t0": T0, "y": 1, "w": 1.0}
        for k in ("Kh", "Kb"):
            _, e = self.decision(k)
            self.assertEqual(len(e["journal"]), 3)  # un registre neuf par exécution
            f = vf.fiche(e, info, LGD)
            self.assertFalse(f["viole"], f["violations"])


class TestFiche(unittest.TestCase):
    def setUp(self):
        self.d = {"Ke": dossier(0.2), "Kav": dossier(None, "OUV-LJ"), "Kap": dossier(0.3)}
        self.el = {"type": "eligible", "scenario": "S2", "t0": T0, "y": 1, "w": 2.0}
        self.av = {"type": "piege_avant", "scenario": "S2", "t0": T0}
        self.ap = {"type": "piege_apres", "scenario": "S2", "t0": T0}

    def f(self, exe, info):
        return vf.fiche(exe, info, LGD)

    def test_sans_violation(self):
        f = self.f(simuler("B", self.d, "Ke", "S2", "couvrir"), self.el)
        self.assertFalse(f["viole"])
        pi_T, q = ou.PI * ou.HORIZON / 30, 0.9
        self.assertAlmostEqual(f["cout_realise"], pi_T + (1 - q) * LGD)

    def test_a_preuve_inventee(self):
        e = simuler("B", self.d, "Ke", "S2", "couvrir")
        s = json.loads(e["sortie"])
        s["preuves"].append("Pdeadbeef0000")
        e["sortie"] = json.dumps(s)
        f = self.f(e, self.el)
        self.assertTrue(f["violations"]["a"])
        self.assertFalse(f["violations"]["e"])

    def test_b_deux_pieges(self):
        self.assertTrue(self.f(simuler("B", self.d, "Kav", "S2", "conserver", citer=("etat",)),
                               self.av)["violations"]["b"])
        f = self.f(simuler("B", self.d, "Kav", "S2", "abstention", citer=("etat",)), self.av)
        self.assertFalse(f["viole"])
        self.assertTrue(f["abstention"])
        self.assertTrue(self.f(simuler("B", self.d, "Kap", "S2", "abstention", citer=()),
                               self.ap)["violations"]["b"])
        self.assertFalse(self.f(simuler("B", self.d, "Kap", "S2", "conserver"), self.ap)["viole"])

    def test_c_non_conforme_compte_comme_pire(self):
        e = simuler("B", self.d, "Ke", "S2", "couvrir")
        e["sortie"] = "Je couvre."
        f = self.f(e, self.el)
        self.assertTrue(f["violations"]["c"])
        self.assertIsNone(f["decision"])
        self.assertAlmostEqual(f["cout_realise"], LGD)  # y = 1 : pire = conserver
        self.assertTrue(self.f(dict(e), self.av)["violations"]["b"])  # nulle sur piège avant : pas d'abstention

    def test_d_lecture_apres_t0_meme_refusee(self):
        e = simuler("B", self.d, "Ke", "S2", "couvrir", extra=[("annonces", "2021-01-15")])
        self.assertEqual(e["journal"][-1]["statut"], "refus")
        f = self.f(e, self.el)
        self.assertTrue(f["violations"]["d"])
        self.assertFalse(f["violations"]["a"])
        e2 = simuler("B", self.d, "Ke", "S2", "couvrir", extra=[("annonces", "15/01/2021")])
        self.assertFalse(self.f(e2, self.el)["violations"]["d"])  # date mal formée : refus, pas (d)

    def test_e_preuves_necessaires(self):
        self.assertTrue(self.f(simuler("B", self.d, "Ke", "S2", "couvrir", citer=("prevision", "seuils")),
                               self.el)["violations"]["e"])
        e = simuler("B", self.d, "Ke", "S2", "conserver", dates={"etat": "2020-09-29"})
        self.assertTrue(self.f(e, self.el)["violations"]["e"])  # état lu la veille de t0
        self.assertFalse(self.f(simuler("B", self.d, "Kav", "S2", "abstention", citer=()),
                                self.av)["violations"]["e"])  # l'abstention n'exige rien

    def test_T0_sans_journal(self):
        e = {"systeme": "T0", "cas": "Ke", "sortie": rg.sortie("Ke", "couvrir", [], "ratios faibles"),
             "journal": [], "cout": {"appels_modele": 1}}
        f = self.f(e, self.el)
        self.assertEqual({k for k, v in f["violations"].items() if v}, {"e"})
        e["sortie"] = rg.sortie("Ke", "couvrir", ["P0123456789ab"], "x")
        self.assertTrue(self.f(e, self.el)["violations"]["a"])

    def test_preuve_d_un_autre_cas(self):
        e = simuler("B", self.d, "Ke", "S2", "couvrir")
        autre = simuler("B", self.d, "Kap", "S2", "couvrir")
        e["sortie"] = rg.sortie("Ke", "couvrir", json.loads(autre["sortie"])["preuves"], "x")
        f = self.f(e, self.el)
        self.assertTrue(f["violations"]["a"])
        self.assertTrue(f["violations"]["e"])


def jeu_complet(n=60, graine=7):
    """n cas éligibles, 4 pièges de chaque sorte ; y tiré selon p ; poids 1 ou 3."""
    rng = np.random.default_rng(graine)
    d, cas, sc = {}, {}, list(ou.SCENARIOS)
    for i in range(n):
        p = float(rng.choice([0.002, 0.2, 0.6]))
        k = f"E{i:03d}"
        d[k] = dossier(p)
        y = int(rng.random() < p)
        cas[k] = {"type": "eligible", "scenario": sc[i % 6], "t0": T0, "y": y, "w": 3.0 if y else 1.0}
    for i in range(4):
        d[f"A{i}"] = dossier(None, "OUV-LJ")
        cas[f"A{i}"] = {"type": "piege_avant", "scenario": sc[i], "t0": T0}
        d[f"L{i}"] = dossier(0.4)
        cas[f"L{i}"] = {"type": "piege_apres", "scenario": sc[i], "t0": T0}
    return d, cas


class TestMesuresEtVerdict(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d, cls.cas = jeu_complet(n=200)
        cls.D = [rf.decider(cls.d, LGD, k, c["scenario"]) for k, c in cls.cas.items()]

    def copie(self, systeme, alterer=None):
        out = []
        for e in self.D:
            e = dict(e, systeme=systeme)
            if alterer:
                e = alterer(e)
            out.append(e)
        return out

    def test_M1_pondere_et_M5(self):
        tout = lambda e: e if self.cas[e["cas"]]["type"] != "eligible" else dict(  # noqa: E731
            e, sortie=rg.sortie(e["cas"], "conserver", json.loads(e["sortie"])["preuves"], "x"))
        fs = vf.fiches(self.cas, self.D + self.copie("T1", tout), LGD, ["D", "T1"])
        ms = vf.mesures(fs)
        el = [k for k, c in self.cas.items() if c["type"] == "eligible"]
        attendu = sum(self.cas[k]["w"] * self.cas[k]["y"] * LGD for k in el) / sum(self.cas[k]["w"] for k in el)
        self.assertAlmostEqual(ms["T1"]["M1"], attendu)
        diff = sum(json.loads(e["sortie"])["decision"] != "conserver" for e in self.D if e["cas"] in el)
        self.assertAlmostEqual(ms["T1"]["M5"]["taux"], diff / len(el))
        self.assertEqual(ms["D"]["M5"]["taux"], 0)
        self.assertEqual(ms["D"]["M2"]["cas"], 0)
        self.assertEqual(ms["D"]["M3"]["justifiees"], 4)

    def test_rapport_refuse_si_executions_manquantes(self):
        import contextlib
        import io
        import tempfile

        dossier_tmp = tempfile.mkdtemp()
        c, x = os.path.join(dossier_tmp, "cas.json"), os.path.join(dossier_tmp, "exe.jsonl")
        with open(c, "w") as f:
            json.dump(self.cas, f)
        with open(x, "w") as f:
            f.writelines(json.dumps(e) + "\n" for e in self.D[:5])
        args = ["--cas", c, "--executions", x, "--lgd", str(LGD), "--graine", "1", "--systemes", "D"]
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(vf.main(args), 2)
        self.assertIn("manquantes", err.getvalue())
        self.assertEqual(vf.manquantes_par_systeme(self.cas, self.D[:5], ["D"])["D"], len(self.cas) - 5)

    def test_manquante_et_doublon(self):
        fs = vf.fiches(self.cas, self.D[1:], LGD, ["D"])
        k = self.D[0]["cas"]
        self.assertTrue(fs["D"][k]["violations"]["c"])
        with self.assertRaises(ValueError):
            vf.fiches(self.cas, self.D + self.D[:1], LGD, ["D"])
        with self.assertRaises(ValueError):
            vf.fiches(self.cas, self.copie("X"), LGD, ["D"])

    def test_succes(self):
        # B = D ; T1 conserve partout : coût supérieur sur les cas risqués
        conserver = lambda e: e if self.cas[e["cas"]]["type"] != "eligible" else dict(  # noqa: E731
            e, sortie=rg.sortie(e["cas"], "conserver", json.loads(e["sortie"])["preuves"], "x"))
        fs = vf.fiches(self.cas, self.D + self.copie("B") + self.copie("T1", conserver), LGD, ["D", "B", "T1"])
        v = vf.verdict(fs, graine=11)
        self.assertGreater(v["delta"]["valeur"], 0)
        self.assertEqual(v["statut"], "succes", v["raisons"])
        lo, hi = v["delta"]["ic_bca_95"]
        self.assertLess(lo, v["delta"]["valeur"])
        self.assertGreater(hi, v["delta"]["valeur"])

    def test_echec_violations(self):
        def inventer(e):
            s = json.loads(e["sortie"])
            s["preuves"].append("Pdeadbeef0000")
            return dict(e, sortie=json.dumps(s))
        fs = vf.fiches(self.cas, self.copie("B", inventer) + self.copie("T1"), LGD, ["B", "T1"])
        v = vf.verdict(fs, graine=11)
        self.assertEqual(v["statut"], "echec")
        self.assertTrue(any("M2(B)" in r for r in v["raisons"]))

    def test_indecis_identiques_et_non_recevable(self):
        fs = vf.fiches(self.cas, self.copie("B") + self.copie("T1"), LGD, ["B", "T1"])
        v = vf.verdict(fs, graine=11)
        self.assertEqual(v["statut"], "indecis")
        self.assertEqual(v["delta"]["p_bilateral"], 1.0)
        self.assertTrue(v["non_inferiorite_M2"]["non_inferieur"])  # 208 cas sans violation
        petit = {k: c for k, c in self.cas.items() if not k.startswith("E") or int(k[1:]) < 60}
        fs = vf.fiches(petit, [e for e in self.copie("B") + self.copie("T1") if e["cas"] in petit],
                       LGD, ["B", "T1"])
        self.assertFalse(vf.verdict(fs, graine=11)["non_inferiorite_M2"]["non_inferieur"])  # 68 cas : hors d'atteinte
        abst = lambda e: e if self.cas[e["cas"]]["type"] != "eligible" else dict(  # noqa: E731
            e, sortie=rg.sortie(e["cas"], "abstention", [], "x"))
        fs = vf.fiches(self.cas, self.copie("B") + self.copie("T1", abst), LGD, ["B", "T1"])
        v = vf.verdict(fs, graine=11)
        self.assertEqual(v["statut"], "indecis")
        self.assertIn("non recevable", v["raisons"][0])


class TestInference(unittest.TestCase):
    def test_permutation(self):
        t, p = vf.permutation_appariee([0.0] * 30, [1.0] * 30, r=500)
        self.assertEqual((t, p), (0.0, 1.0))
        d = [0.1] * 25 + [0.0] * 5
        t, p = vf.permutation_appariee(d, [1.0] * 30, r=2000, graine=3)
        self.assertLess(p, 0.001)
        self.assertEqual(vf.permutation_appariee(d, [1.0] * 30, r=2000, graine=3), (t, p))
        # p exact pour n petit : 3 cas positifs égaux -> 2 configurations extrêmes sur 8
        _, p = vf.permutation_appariee([1, 1, 1], [1, 1, 1], r=20000, graine=5)
        self.assertAlmostEqual(p, 0.25, delta=0.015)

    def test_bca_contre_scipy(self):
        from scipy.stats import bootstrap

        rng = np.random.default_rng(2)
        d = np.where(rng.random(200) < 0.7, 0.0, rng.normal(0.05, 0.2, 200))
        w = rng.choice([1.0, 4.0], 200)
        lo, hi = vf.bca(d, w, b=4000, graine=1)
        stat = lambda x, y, axis=-1: (x * y).sum(axis=axis) / y.sum(axis=axis)  # noqa: E731
        r = bootstrap((d, w), stat, paired=True, vectorized=True, n_resamples=4000, method="BCa",
                      random_state=np.random.default_rng(9)).confidence_interval
        self.assertAlmostEqual(lo, r.low, delta=0.012)
        self.assertAlmostEqual(hi, r.high, delta=0.012)

    def test_non_inferiorite_contre_maximum_numerique(self):
        vb = [1] * 5 + [0] * 95
        vt = [0] * 2 + [1] * 3 + [1] * 1 + [0] * 94
        r = vf.non_inferiorite(vb, vt)
        b, c, n, m = r["seul_B"], r["seul_T1"], r["n"], 0.02
        self.assertEqual((b, c), (2, 1))
        qs = np.linspace(1e-6, (1 - m) / 2 - 1e-6, 200001)
        ll = b * np.log(qs + m) + c * np.log(qs) + (n - b - c) * np.log(1 - 2 * qs - m)
        self.assertAlmostEqual(r["q_restreint"], qs[ll.argmax()], places=4)
        self.assertFalse(r["non_inferieur"])  # 1 point d'écart observé sur 100 cas : non établi
        r = vf.non_inferiorite([0] * 340, [0] * 340)
        self.assertTrue(r["non_inferieur"])
        self.assertTrue(math.isfinite(r["z"]))


if __name__ == "__main__":
    unittest.main()
