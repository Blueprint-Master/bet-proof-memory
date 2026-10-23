"""Observations bruitées, leurs vraisemblances, et la partie (interface commune à tous les
systèmes). Spécification v3, §2.5 et §2.6.

Aléa déterministe : clé (graine, monde, période, commande, occurrence, sous-clé) ; tous les
systèmes voient les mêmes aléas, et une mesure répétée n'est pas une copie de la précédente.
"""

import hashlib
from collections import Counter

from modele import appliquer, atteinte, initial_sous

SIGNES = (-1, 0, 1)


def alea(*cle):
    d = hashlib.sha256("|".join(str(c) for c in cle).encode()).digest()
    return int.from_bytes(d[:8], "big") / 2**64


def valeurs_domaine(monde, var):
    lo, hi = monde.domaines[var]
    return list(range(lo, hi + 1))


def tirer_mesure(monde, var, v, u1, u2):
    """Vraie valeur avec la probabilité q, sinon une valeur uniforme du domaine (qui peut
    retomber sur la vraie) : aucune observation n'est à elle seule concluante."""
    if u1 < monde.q:
        return v
    vs = valeurs_domaine(monde, var)
    return vs[min(int(u2 * len(vs)), len(vs) - 1)]


def p_mesure(monde, var, v, obs):
    lo, hi = monde.domaines[var]
    n = hi - lo + 1
    if not lo <= obs <= hi:
        return 0.0
    return monde.q * (obs == v) + (1 - monde.q) / n


def tirer_signe(qe, vrai, u1, u2):
    """Vrai sens de variation avec la probabilité qe, sinon un sens uniforme parmi les trois."""
    if u1 < qe:
        return vrai
    return SIGNES[min(int(u2 * 3), 2)]


def p_objectif(q, vrai, obs):
    """Mesure de l'objectif : le vrai avec la probabilité q, sinon pile ou face."""
    return q * (obs == vrai) + (1 - q) / 2


def p_signe(qe, vrai, obs):
    return qe * (obs == vrai) + (1 - qe) / 3


def signe(x):
    return (x > 0) - (x < 0)


def essai_vrai(monde, h, etat, nom):
    """Variation vraie (en signe) de chaque variable d'état si l'action était exécutée."""
    suivant, _ = appliquer(monde, h, etat, nom)
    return {v: signe(suivant.valeurs[i] - etat.valeurs[i])
            for i, v in enumerate(monde.variables)}


def temoin_vrai(monde, graine, var, t):
    u = alea(graine, monde.ident, t, "temoin", var)
    if u < monde.p_anomalie:
        return max(monde.domaines[var][0], min(monde.domaines[var][1],
                   monde.temoins[var] + (1 if u < monde.p_anomalie / 2 else -1)))
    return monde.temoins[var]


class Partie:
    """Un monde en cours de jeu. Les commandes : ("mesurer", var | "objectif"),
    ("essayer", action), ("lire", source), ("agir", action), ("attendre",),
    ("arreter", motif)."""

    def __init__(self, monde, graine):
        self.monde = monde
        self.graine = graine
        self.h = monde.h_vrai
        self.etat = initial_sous(monde, self.h)
        self.t = 0
        self.depense = 0
        self.occ = Counter()
        self.journal = []
        self.fini = False
        self.motif = None
        self.refus = 0

    @property
    def reste(self):
        return self.monde.budget - self.depense

    def cout(self, cmd):
        if cmd[0] == "agir":
            return self.monde.action(cmd[1]).cout
        return self.monde.couts_outils.get(cmd[0], 0)

    def jouer(self, cmd):
        assert not self.fini, "monde terminé"
        m = self.monde
        if cmd[0] == "arreter":
            self.fini, self.motif = True, cmd[1]
            self.journal.append((self.t, cmd, None))
            return None
        c = self.cout(cmd)
        if c > self.reste:
            self.refus += 1
            obs = {"refus": "budget"}
            self.journal.append((self.t, cmd, obs))
            return obs
        cle = (cmd[0], cmd[1] if len(cmd) > 1 else "")
        k = self.occ[cle]
        self.occ[cle] += 1
        u = lambda sous: alea(self.graine, m.ident, self.t, cle[0], cle[1], k, sous)  # noqa: E731
        if cmd[0] == "mesurer":
            var = cmd[1]
            if var == "objectif":
                vrai = atteinte(m, self.etat)
                obs = vrai if u(1) < m.q else (u(2) < 0.5)
            elif var in m.temoins:
                obs = tirer_mesure(m, var, temoin_vrai(m, self.graine, var, self.t), u(1), u(2))
            else:
                obs = tirer_mesure(m, var, self.etat.valeurs[m.index(var)], u(1), u(2))
        elif cmd[0] == "essayer":
            vrai = essai_vrai(m, self.h, self.etat, cmd[1])
            obs = {v: tirer_signe(m.qe, s, u(("a", v)), u(("b", v))) for v, s in vrai.items()}
        elif cmd[0] == "lire":
            obs = m.contenu_sources[cmd[1]]
        elif cmd[0] == "agir":
            self.etat, gain = appliquer(m, self.h, self.etat, cmd[1])
            obs = {"z_gain": gain}
        elif cmd[0] == "attendre":
            obs = {}
        else:
            raise ValueError(cmd)
        self.depense += c
        self.journal.append((self.t, cmd, obs))
        self.t += 1
        if self.t >= m.echeance:
            self.fini, self.motif = True, "echeance"
        return obs

    def utilite(self):
        m = self.monde
        return m.V * atteinte(m, self.etat) + m.valeur_z * self.etat.z - self.depense
