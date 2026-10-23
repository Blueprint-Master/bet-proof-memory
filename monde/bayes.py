"""Filtre bayésien sur les 54 hypothèses, bornes et politique R_Bayes approchée.

Spécification v3, §4. Les transitions étant déterministes sachant h, la croyance est une loi
sur H et l'état réel sous chaque h se reconstitue en rejouant les actions `agir`.

- Borne haute (QMDP, Littman et al. 1995 ; Ross et al. 2008, §2.2.4) : sum_h b(h) V*_h.
- Feuille basse (« s'engager ») : la meilleure des 55 politiques en boucle ouverte (le plan
  optimal de chaque hypothèse, ou l'arrêt immédiat), évaluée sous la croyance ; politique
  réalisable, donc valeur atteignable.
- R_Bayes : recherche à profondeur bornée sur les commandes (mesures répétées groupées en
  macro-commandes de 1 à 4 mesures), feuille basse, rejouée en ligne à chaque période.
"""

from itertools import combinations_with_replacement, product
from math import comb, prod

from modele import appliquer, atteinte, hypotheses, initial_sous, loi_a_priori, valeur_terminale
from observations import essai_vrai, p_mesure, p_objectif, p_signe, valeurs_domaine
from plan import Planificateur, evaluer_plan

EPS = 1e-12


# ---------------------------------------------------------------- lectures

def contenu_sous(monde, source, h):
    """Contenu déterministe d'une source sous h (None si le contenu est aléatoire)."""
    if source == "releve":
        etat = initial_sous(monde, h)
        return {v: etat.valeurs[monde.index(v)] for v, _ in monde.cand_A}
    if source == "rapport":
        return dict(monde.affiche)
    return None


def p_lecture(monde, source, contenu, h):
    if source == "journal":
        J = monde.vraisemblance_sources["journal"]
        nom = contenu["sous_produit"]
        if h[2]:
            juste = monde.cand_Z[h[2] - 1]
            return J["juste"] if nom == juste else (J["autre"] if nom is not None else
                                                     1 - J["juste"] - J["autre"])
        return J["fausse_alerte"] / 2 if nom is not None else 1 - J["fausse_alerte"]
    if source == "note":
        p1, p0 = monde.vraisemblance_sources["note"]
        p = p1 if h[0] else p0
        return p if contenu["anomalie"] else 1 - p
    return 1.0 if contenu_sous(monde, source, h) == contenu else 0.0


def issues_lecture(monde, source, support):
    if source == "note":
        return [{"anomalie": True}, {"anomalie": False}]
    if source == "journal":
        return [{"sous_produit": x} for x in (None,) + tuple(monde.cand_Z)]
    vus = []
    for h in support:
        c = contenu_sous(monde, source, h)
        if c not in vus:
            vus.append(c)
    return vus


# ---------------------------------------------------------------- filtre

class Noeud:
    """Croyance et états par hypothèse à une période donnée."""

    def __init__(self, b, etats, t, reste):
        self.b, self.etats, self.t, self.reste = b, etats, t, reste

    def support(self):
        return [h for h, p in self.b.items() if p > EPS]


def racine(monde):
    b = loi_a_priori(monde)
    s = sum(b.values())
    b = {h: p / s for h, p in b.items()}
    return Noeud(b, {h: initial_sous(monde, h) for h in hypotheses()}, 0, monde.budget)


def vraisemblance(monde, noeud, cmd, obs, h):
    etat = noeud.etats[h]
    if cmd[0] == "mesurer":
        var = cmd[1]
        if var == "objectif":
            return p_objectif(monde.q, atteinte(monde, etat), obs)
        if var in monde.temoins:
            return 1.0  # sans rôle causal : même loi sous toute hypothèse
        return p_mesure(monde, var, etat.valeurs[monde.index(var)], obs)
    if cmd[0] == "essayer":
        vrai = essai_vrai(monde, h, etat, cmd[1])
        return prod(p_signe(monde.qe, vrai[v], s) for v, s in obs.items())
    if cmd[0] == "lire":
        return p_lecture(monde, cmd[1], obs, h)
    if cmd[0] == "agir":
        _, gain = appliquer(monde, h, etat, cmd[1])
        return 1.0 if gain == obs["z_gain"] else 0.0
    return 1.0


def mettre_a_jour(monde, noeud, cmd, obs, cout):
    """Nouvelle croyance et nouveaux états après la commande et son observation."""
    if isinstance(obs, dict) and "refus" in obs:
        return noeud
    b = {h: p * vraisemblance(monde, noeud, cmd, obs, h) if p > EPS else 0.0
         for h, p in noeud.b.items()}
    s = sum(b.values())
    if s <= 0:
        raise ValueError(f"observation impossible sous toutes les hypothèses : {cmd} {obs}")
    b = {h: p / s for h, p in b.items()}
    etats = noeud.etats
    if cmd[0] == "agir":
        etats = {h: appliquer(monde, h, e, cmd[1])[0] for h, e in etats.items()}
    return Noeud(b, etats, noeud.t + 1, noeud.reste - cout)


# ---------------------------------------------------------------- bornes et feuille

class Evaluateur:
    """Planificateurs par hypothèse et matrices d'engagement mises en cache."""

    def __init__(self, monde):
        self.monde = monde
        partages = {}
        self.plans = {}
        for h in hypotheses():
            cle = (h[0], h[2], h[3])  # A ne change que l'état initial : planificateur partagé
            if cle not in partages:
                partages[cle] = Planificateur(monde, (h[0], 0, h[2], h[3]))
            self.plans[h] = partages[cle]
        self.cache = {}

    def qmdp(self, noeud):
        return sum(p * self.plans[h].valeur(noeud.etats[h], noeud.t, noeud.reste)[0]
                   for h, p in noeud.b.items() if p > EPS)

    def matrice(self, noeud):
        cle = (tuple(noeud.etats[h] for h in hypotheses()), noeud.t, noeud.reste)
        if cle not in self.cache:
            m = self.monde
            lignes = {None: {h: valeur_terminale(m, noeud.etats[h]) for h in hypotheses()}}
            for hp in hypotheses():
                actions = tuple(self.plans[hp].plan(noeud.etats[hp], noeud.t, noeud.reste))
                if actions in lignes:
                    continue
                lignes[actions] = {h: evaluer_plan(m, h, noeud.etats[h], noeud.t, noeud.reste,
                                                   actions) for h in hypotheses()}
            self.cache[cle] = lignes
        return self.cache[cle]

    def engager(self, noeud):
        """Meilleure politique en boucle ouverte sous la croyance : (valeur, plan)."""
        sup = noeud.support()
        meilleur = None
        for actions, col in self.matrice(noeud).items():
            v = sum(noeud.b[h] * col[h] for h in sup)
            if meilleur is None or v > meilleur[0] + 1e-12:
                meilleur = (v, actions)
        return meilleur


# ---------------------------------------------------------------- R_Bayes

def commandes(monde, noeud, macros=(1, 2, 3, 4)):
    """Commandes candidates au nœud (mesures groupées en macro de n mesures)."""
    cmds = []
    for v in list(monde.variables) + ["objectif"]:
        for n in macros:
            cmds.append(("mesurer", v, n))
    for a in monde.actions:
        cmds.append(("essayer", a.nom))
        cmds.append(("agir", a.nom))
    for s in monde.sources:
        cmds.append(("lire", s))
    return cmds


def cout_cmd(monde, cmd):
    if cmd[0] == "agir":
        return monde.action(cmd[1]).cout
    n = cmd[2] if cmd[0] == "mesurer" else 1
    return n * monde.couts_outils[cmd[0]]


def issues(monde, noeud, cmd):
    """Issues possibles d'une commande : liste de (probabilité, nœud suivant)."""
    sup = noeud.support()
    c = cout_cmd(monde, cmd)
    sorties = []
    if cmd[0] == "mesurer":
        var, n = cmd[1], cmd[2]
        if var == "objectif":
            valeurs = [True, False]
            lik = lambda h, o: p_objectif(monde.q, atteinte(monde, noeud.etats[h]), o)  # noqa: E731
        else:
            i = monde.index(var)
            valeurs = valeurs_domaine(monde, var)
            lik = lambda h, o: p_mesure(monde, var, noeud.etats[h].valeurs[i], o)  # noqa: E731
        for multi in combinations_with_replacement(valeurs, n):
            compte = {o: multi.count(o) for o in set(multi)}
            perm = comb(n, 0)
            reste_n = n
            for o, k in compte.items():
                perm *= comb(reste_n, k)
                reste_n -= k
            post = {h: (noeud.b[h] * perm * prod(lik(h, o) ** k for o, k in compte.items())
                        if h in sup else 0.0) for h in noeud.b}
            p = sum(post.values())
            if p > EPS:
                b = {h: x / p for h, x in post.items()}
                sorties.append((p, Noeud(b, noeud.etats, noeud.t + n, noeud.reste - c)))
        return sorties
    if cmd[0] == "essayer":
        vrais = {h: essai_vrai(monde, h, noeud.etats[h], cmd[1]) for h in sup}
        discr = [v for v in monde.variables if len({vrais[h][v] for h in sup}) > 1]
        for combo in product((-1, 0, 1), repeat=len(discr)):
            obs = dict(zip(discr, combo))
            post = {h: (noeud.b[h] * prod(p_signe(monde.qe, vrais[h][v], s) for v, s in obs.items())
                        if h in sup else 0.0) for h in noeud.b}
            p = sum(post.values())
            if p > EPS:
                sorties.append((p, Noeud({h: x / p for h, x in post.items()}, noeud.etats,
                                         noeud.t + 1, noeud.reste - c)))
        return sorties
    if cmd[0] == "lire":
        for contenu in issues_lecture(monde, cmd[1], sup):
            post = {h: (noeud.b[h] * p_lecture(monde, cmd[1], contenu, h) if h in sup else 0.0)
                    for h in noeud.b}
            p = sum(post.values())
            if p > EPS:
                sorties.append((p, Noeud({h: x / p for h, x in post.items()}, noeud.etats,
                                         noeud.t + 1, noeud.reste - c)))
        return sorties
    if cmd[0] == "agir":
        suivants = {h: appliquer(monde, h, e, cmd[1]) for h, e in noeud.etats.items()}
        etats = {h: s[0] for h, s in suivants.items()}
        for gain in sorted({suivants[h][1] for h in sup}):
            post = {h: (noeud.b[h] if h in sup and suivants[h][1] == gain else 0.0)
                    for h in noeud.b}
            p = sum(post.values())
            if p > EPS:
                sorties.append((p, Noeud({h: x / p for h, x in post.items()}, etats,
                                         noeud.t + 1, noeud.reste - c)))
        return sorties
    raise ValueError(cmd)


def admissible(monde, noeud, cmd):
    n = cmd[2] if cmd[0] == "mesurer" else 1
    return noeud.t + n <= monde.echeance and cout_cmd(monde, cmd) <= noeud.reste


def valeur_noeud(ev, noeud, profondeur, macros=(1, 2, 3, 4)):
    """Valeur (gains futurs moins coûts futurs) à profondeur bornée, feuille « s'engager »."""
    m = ev.monde
    v_eng = ev.engager(noeud)[0]
    if profondeur == 0 or noeud.t >= m.echeance:
        return v_eng
    meilleur = v_eng
    for cmd in commandes(m, noeud, macros):
        if not admissible(m, noeud, cmd):
            continue
        v = -cout_cmd(m, cmd) + sum(p * valeur_noeud(ev, s, profondeur - 1, macros)
                                    for p, s in issues(m, noeud, cmd))
        meilleur = max(meilleur, v)
    return meilleur


def choisir(ev, noeud, profondeur=1, macros=(1, 2, 3, 4)):
    """Commande élémentaire à jouer maintenant : ("arreter", ...), ou la première commande de
    la meilleure option (première action du plan d'engagement, ou première mesure d'une
    macro)."""
    m = ev.monde
    v_eng, plan = ev.engager(noeud)
    meilleur = (v_eng, ("engager",))
    if noeud.t < m.echeance:
        for cmd in commandes(m, noeud, macros):
            if cmd[0] == "agir" or not admissible(m, noeud, cmd):
                continue  # agir est couvert par les plans d'engagement et leur première action
            v = -cout_cmd(m, cmd) + sum(p * valeur_noeud(ev, s, profondeur - 1, macros)
                                        for p, s in issues(m, noeud, cmd))
            if v > meilleur[0] + 1e-9:
                meilleur = (v, cmd)
    cmd = meilleur[1]
    if cmd[0] == "engager":
        if not plan:
            return ("arreter", "abstention" if not _atteint_probable(m, noeud) else "atteint")
        return ("agir", plan[0])
    if cmd[0] == "mesurer":
        return ("mesurer", cmd[1])
    return cmd


def _atteint_probable(monde, noeud):
    return sum(p for h, p in noeud.b.items() if atteinte(monde, noeud.etats[h])) >= 0.5
