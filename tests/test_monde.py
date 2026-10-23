"""Tests du moteur du monde simulé (famille « réglages et seuils »)."""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "monde"))
import bayes as by  # noqa: E402
import calibrage as cal  # noqa: E402
import description as de  # noqa: E402
import famille_reglages as fr  # noqa: E402
import modele as mo  # noqa: E402
import observations as ob  # noqa: E402

FACTEURS = {"O": 1, "A": 1, "Z": 1, "marge": "large", "I": 0, "difficulte": "facile"}
DOSSIER = os.path.join(os.path.dirname(__file__), "..", "monde")


def monde(graine=3, **f):
    return fr.generer(graine, {**FACTEURS, **f}, q=0.45, V=60)


class TestModele(unittest.TestCase):
    def test_54_hypotheses_et_loi(self):
        m = monde()
        b = mo.loi_a_priori(m)
        self.assertEqual(len(b), 54)
        self.assertAlmostEqual(sum(b.values()), 1.0)

    def test_transitions_deterministes_et_bornees(self):
        m = monde()
        for h in mo.hypotheses():
            e = mo.initial_sous(m, h)
            for a in m.actions:
                e2, _ = mo.appliquer(m, h, e, a.nom)
                self.assertEqual(e2, mo.appliquer(m, h, e, a.nom)[0])
                for i, v in enumerate(m.variables):
                    lo, hi = m.domaines[v]
                    self.assertTrue(lo <= e2.valeurs[i] <= hi)

    def test_A_ne_change_que_l_etat_initial(self):
        m = monde()
        e = mo.initial_sous(m, (0, 0, 0, 0))
        for a in m.actions:
            self.assertEqual(mo.appliquer(m, (1, 0, 2, 0), e, a.nom),
                             mo.appliquer(m, (1, 2, 2, 0), e, a.nom))

    def test_verrou_bloque_les_effets(self):
        m = monde()
        e = mo.initial_sous(m, (0, 0, 0, 0))
        e, _ = mo.appliquer(m, (0, 0, 0, 0), e, "verrouiller:R1")
        e2, _ = mo.appliquer(m, (0, 0, 0, 0), e, "monter:R1")
        self.assertEqual(e.valeurs, e2.valeurs)

    def test_impossibilite_plafonne_la_stabilite(self):
        m = monde()
        h = (0, 0, 0, 1)
        e = mo.initial_sous(m, h)
        for _ in range(4):
            e, _ = mo.appliquer(m, h, e, "stabiliser")
        self.assertLessEqual(e.valeurs[m.index("S")], m.I_effet[1])
        self.assertFalse(mo.atteinte(m, e))

    def test_z_une_seule_fois(self):
        m = monde()
        h = (0, 0, 1, 0)
        e = mo.initial_sous(m, h)
        e, g1 = mo.appliquer(m, h, e, m.cand_Z[0])
        e, g2 = mo.appliquer(m, h, e, m.cand_Z[0])
        self.assertEqual((g1, g2, e.z), (m.quantite_z, 0, m.quantite_z))


class TestObservations(unittest.TestCase):
    def test_lois_de_mesure_normalisees(self):
        m = monde()
        for v in m.variables:
            lo, hi = m.domaines[v]
            for vrai in range(lo, hi + 1):
                self.assertAlmostEqual(sum(ob.p_mesure(m, v, vrai, o) for o in range(lo, hi + 1)), 1)
        for vrai in (-1, 0, 1):
            self.assertAlmostEqual(sum(ob.p_signe(0.3, vrai, o) for o in (-1, 0, 1)), 1)
        self.assertAlmostEqual(ob.p_objectif(0.3, True, True) + ob.p_objectif(0.3, True, False), 1)

    def test_alea_partage_et_occurrence(self):
        m = monde()
        p1, p2 = ob.Partie(m, 11), ob.Partie(m, 11)
        o1 = [p1.jouer(("mesurer", "R1")) for _ in range(5)]
        o2 = [p2.jouer(("mesurer", "R1")) for _ in range(5)]
        self.assertEqual(o1, o2)

    def test_refus_budget_sans_consommer_la_periode(self):
        m = monde()
        p = ob.Partie(m, 1)
        p.depense = m.budget
        obs = p.jouer(("agir", "monter:R1"))
        self.assertEqual(obs, {"refus": "budget"})
        self.assertEqual((p.t, p.refus), (0, 1))

    def test_utilite_meme_formule_quel_que_soit_le_motif(self):
        m = monde()
        p = ob.Partie(m, 1)
        p.jouer(("lire", "rapport"))
        p.jouer(("arreter", "abstention"))
        self.assertEqual(p.utilite(), -1)


class TestFiltre(unittest.TestCase):
    def test_mise_a_jour_coherente_avec_les_issues(self):
        m = monde()
        n = by.racine(m)
        for cmd in (("mesurer", "R1", 2), ("lire", "note"), ("essayer", "monter:R1")):
            tot = sum(p for p, _ in by.issues(m, n, cmd))
            self.assertAlmostEqual(tot, 1.0)

    def test_lecture_du_releve_revele_A(self):
        m = monde()
        n = by.racine(m)
        contenu = by.contenu_sous(m, "releve", m.h_vrai)
        n2 = by.mettre_a_jour(m, n, ("lire", "releve"), contenu, 1)
        pa = {a: sum(p for h, p in n2.b.items() if h[1] == a) for a in range(3)}
        self.assertAlmostEqual(pa[m.h_vrai[1]], 1.0)


class TestDescription(unittest.TestCase):
    def test_jumeaux_identiques(self):
        m0 = fr.generer(5, {**FACTEURS, "I": 0}, q=0.45, V=60)
        m1 = fr.generer(5, {**FACTEURS, "I": 1}, q=0.45, V=60)
        self.assertEqual(de.texte(m0), de.texte(m1))
        self.assertEqual(de.tableau(m0), de.tableau(m1))
        self.assertNotEqual(m0.h_vrai, m1.h_vrai)

    def test_aucun_champ_latent(self):
        t = de.tableau(monde())
        for cle in ("h_vrai", "cand_O", "cand_A", "cand_Z", "I_effet", "contenu_sources"):
            self.assertNotIn(cle, t)

    def test_lexique_renouvele(self):
        self.assertNotEqual(monde(3).lexique, monde(4).lexique)


class TestCalibrage(unittest.TestCase):
    def test_cible_atteinte(self):
        t = cal.table()
        self.assertAlmostEqual(cal.exactitude(t["facile"], 2)[0], 0.80, delta=0.005)
        self.assertAlmostEqual(cal.exactitude(t["difficile"], 4)[0], 0.80, delta=0.005)


class TestAudit(unittest.TestCase):
    def test_politiques_sans_acces_a_l_etat_cache(self):
        """Seul l'oracle lit h_vrai ; aucune politique ne lit contenu_sources."""
        src = open(os.path.join(DOSSIER, "politiques.py"), encoding="utf-8").read()
        src = re.sub(r'"""(.|\n)*?"""', "", src)  # docstrings exclues
        classes = re.split(r"\nclass ", src)
        for c in classes:
            if c.startswith("Oracle"):
                continue
            self.assertNotIn("h_vrai", c)
            self.assertNotIn("contenu_sources", c)
        bsrc = re.sub(r'"""(.|\n)*?"""', "", open(os.path.join(DOSSIER, "bayes.py"), encoding="utf-8").read())
        self.assertNotIn("h_vrai", bsrc)
        self.assertNotIn("contenu_sources", bsrc)


if __name__ == "__main__":
    unittest.main()
