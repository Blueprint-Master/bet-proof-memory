"""Politiques en code (spécification v3, §4 et §5.3) et boucle de jeu.

Toutes les politiques (sauf R∞) ne voient que la partie publique du monde, la loi de la
famille et leurs propres observations, au travers du filtre bayésien ; aucune ne lit
`h_vrai` ni `contenu_sources` (contrôle d'audit dans les tests). R∞ connaît h_vrai par
définition.
"""

from bayes import Evaluateur, choisir, mettre_a_jour, racine
from modele import H_DESCRIPTION, atteinte, initial_sous
from observations import Partie
from plan import Planificateur


def map_h(noeud):
    return max(noeud.b, key=lambda h: noeud.b[h])


def p_impossible(noeud):
    return sum(p for h, p in noeud.b.items() if h[3])


def p_atteint(monde, noeud):
    return sum(p for h, p in noeud.b.items() if atteinte(monde, noeud.etats[h]))


class Politique:
    nom = "?"

    def __init__(self, monde, ev=None):
        self.monde = monde
        self.ev = ev or Evaluateur(monde)

    def plan_map(self, noeud):
        h = map_h(noeud)
        return self.ev.plans[h].plan(noeud.etats[h], noeud.t, noeud.reste)

    def commande(self, noeud):
        raise NotImplementedError


class Rapide(Politique):
    """R_naïf : le plan optimal du monde tel que décrit, sans mesurer ni lire."""
    nom = "rapide"

    def __init__(self, monde, ev=None):
        super().__init__(monde, ev)
        self.plan = Planificateur(monde, H_DESCRIPTION).plan(
            initial_sous(monde, H_DESCRIPTION), 0, monde.budget)

    def commande(self, noeud):
        if self.plan:
            return ("agir", self.plan.pop(0))
        return ("arreter", "atteint")


def variables_evidentes(monde):
    plan = Planificateur(monde, H_DESCRIPTION).plan(initial_sous(monde, H_DESCRIPTION), 0,
                                                    monde.budget)
    vs = []
    for a in plan:
        v = monde.action(a).cible
        if v not in vs:
            vs.append(v)
    return vs


class Prudente(Politique):
    """Lit toutes les sources, mesure trois fois chaque variable de la voie évidente,
    s'abstient si l'impossibilité est plus probable que non, sinon suit le plan de
    l'hypothèse la plus probable, replanifié à chaque période."""
    nom = "prudente"

    def __init__(self, monde, ev=None, repetitions=3):
        super().__init__(monde, ev)
        self.file = [("lire", s) for s in monde.sources]
        self.file += [("mesurer", v) for v in variables_evidentes(monde) for _ in range(repetitions)]

    def commande(self, noeud):
        if self.file:
            return self.file.pop(0)
        if p_impossible(noeud) > 0.5:
            return ("arreter", "abstention")
        plan = self.plan_map(noeud)
        return ("agir", plan[0]) if plan else ("arreter", "atteint")


class Explore(Prudente):
    """R_explore : lit tout, mesure une fois chaque variable d'état, puis comme Prudente."""
    nom = "explore"

    def __init__(self, monde, ev=None):
        Politique.__init__(self, monde, ev)
        self.file = [("lire", s) for s in monde.sources] + [("mesurer", v) for v in monde.variables]


class Ciblee(Politique):
    """Inspection ciblée : valeur de l'information myope, une seule mesure à la fois."""
    nom = "ciblee"

    def commande(self, noeud):
        return choisir(self.ev, noeud, profondeur=1, macros=(1,))


class Essai(Politique):
    """Essai opportuniste : essaie chaque action une fois avant de l'exécuter ; suit le plan
    de l'hypothèse la plus probable, replanifié à chaque période."""
    nom = "essai"

    def __init__(self, monde, ev=None):
        super().__init__(monde, ev)
        self.essayees = set()

    def commande(self, noeud):
        plan = self.plan_map(noeud)
        if not plan:
            return ("arreter", "atteint")
        a = plan[0]
        if a not in self.essayees and noeud.reste >= self.monde.couts_outils["essayer"] + \
                self.monde.action(a).cout:
            self.essayees.add(a)
            return ("essayer", a)
        return ("agir", a)


class ArretAdaptatif(Politique):
    """Suit le plan de l'hypothèse la plus probable sans collecte préalable ; à la fin du plan,
    mesure l'objectif ; s'arrête quand l'objectif est probablement atteint, s'abstient quand
    s'engager ne vaut plus rien."""
    nom = "arret"

    def commande(self, noeud):
        v_eng, plan = self.ev.engager(noeud)
        if v_eng <= 0 and p_atteint(self.monde, noeud) < 0.5:
            return ("arreter", "abstention")
        if plan:
            return ("agir", plan[0])
        if p_atteint(self.monde, noeud) >= 0.9 or noeud.t >= self.monde.echeance - 1 \
                or noeud.reste < self.monde.couts_outils["mesurer"]:
            return ("arreter", "atteint" if p_atteint(self.monde, noeud) >= 0.5 else "abstention")
        return ("mesurer", "objectif")


class Bayes(Politique):
    """R_Bayes approchée : profondeur bornée, macro-mesures, feuille « s'engager »."""
    nom = "bayes"

    def __init__(self, monde, ev=None, profondeur=1):
        super().__init__(monde, ev)
        self.profondeur = profondeur

    def commande(self, noeud):
        return choisir(self.ev, noeud, self.profondeur)


class Oracle(Politique):
    """R∞ : connaît h_vrai (borne de voyant)."""
    nom = "oracle"

    def commande(self, noeud):
        h = self.monde.h_vrai
        plan = self.ev.plans[h].plan(noeud.etats[h], noeud.t, noeud.reste)
        return ("agir", plan[0]) if plan else ("arreter", "atteint")


PANEL = (Rapide, Prudente, Ciblee, Essai, ArretAdaptatif)
REFERENCES = (Explore, Bayes, Oracle)


def jouer(monde, classe, graine, **kw):
    """Joue un monde avec une politique ; rend la partie terminée."""
    pol = classe(monde, **kw)
    partie = Partie(monde, graine)
    noeud = racine(monde)
    while not partie.fini:
        cmd = pol.commande(noeud)
        cout = partie.cout(cmd) if cmd[0] != "arreter" else 0
        obs = partie.jouer(cmd)
        if cmd[0] == "arreter":
            break
        if isinstance(obs, dict) and "refus" in obs:
            # une politique qui insiste sur une commande refusée s'arrête
            partie.jouer(("arreter", "budget"))
            break
        noeud = mettre_a_jour(monde, noeud, cmd, obs, cout)
    return partie
