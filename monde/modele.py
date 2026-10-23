"""Monde simulé : modèle formel d'un monde (spécification v3, §2).

Un monde se compose d'une partie publique (variables, actions, voies, paramètres, bruit
déclaré, catalogue des sources) et de quatre emplacements latents O, A, Z, I. Une hypothèse
h = (o, a, z, i) fixe la modalité de chaque emplacement ; les transitions sont déterministes
sachant h, seules les observations sont bruitées (module observations).

Les candidats de chaque emplacement sont des fonctions déterministes de la partie publique
(règle de la famille, connue de R_Bayes comme partie de la loi) : connaître la loi ne donne
donc rien que la description ne contienne déjà, à la règle près.
"""

from dataclasses import dataclass, field
from itertools import product
from typing import NamedTuple

OPS = (">=", "<=", "==")


@dataclass(frozen=True)
class Action:
    nom: str                    # identifiant interne, ex. "monter:R1"
    cible: str                  # variable visée
    delta: int                  # incrément nominal (0 pour un verrouillage)
    cout: int
    reversible: bool
    inverse: str | None = None
    verrou: bool = False        # verrouille la cible : plus aucun effet ne la modifie
    effets_bord: tuple = ()     # effets de bord déclarés : ((variable, delta), ...)


@dataclass(frozen=True)
class Condition:
    var: str
    op: str
    seuil: int

    def tient(self, valeur):
        if self.op == ">=":
            return valeur >= self.seuil
        if self.op == "<=":
            return valeur <= self.seuil
        return valeur == self.seuil


class Etat(NamedTuple):
    valeurs: tuple              # valeurs des variables d'état, dans l'ordre Monde.variables
    verrous: int = 0            # masque des variables verrouillées (bit i = variable i)
    z: int = 0                  # quantité de Z acquise (définitivement)


@dataclass
class Monde:
    ident: str
    famille: str
    variables: tuple            # variables d'état (ordre canonique interne)
    domaines: dict              # variable -> (min, max)
    affiche: dict               # valeurs initiales affichées dans le tableau
    provenances: dict           # variable -> "recent" | "ancien" | "memo"
    actions: tuple
    voies: tuple                # tuple de tuples de Condition
    budget: int
    echeance: int
    V: float
    valeur_z: float
    q: float                    # probabilité qu'une mesure rende la vraie valeur
    qe: float                   # probabilité qu'un essai rende le bon sens de variation
    couts_outils: dict          # "mesurer", "lire", "essayer", "attendre"
    sources: tuple              # noms des sources consultables
    contenu_sources: dict       # source -> contenu structuré (tiré à la génération)
    vraisemblance_sources: dict  # paramètres de la loi des contenus, connus de R_Bayes
    temoins: dict               # variable témoin -> valeur nominale (sans rôle causal)
    p_anomalie: float           # probabilité d'écart du témoin à une période donnée
    # candidats des emplacements latents (règle de famille)
    cand_O: tuple               # 2 x (action, variable touchée, delta) : effet de bord caché
                                # qui éloigne la variable d'un cran et la grippe (verrou)
    cand_A: tuple               # 2 x (variable, valeur réelle si la ligne est fausse)
    cand_Z: tuple               # 2 x nom d'action qui rapporte Z
    quantite_z: int
    I_effet: tuple              # (variable, plafond) si l'impossibilité est présente
    loi: dict                   # loi a priori des emplacements (proportions du plan)
    h_vrai: tuple               # (o, a, z, i)
    facteurs: dict = field(default_factory=dict)
    lexique: dict = field(default_factory=dict)
    ordre: dict = field(default_factory=dict)

    def __post_init__(self):
        self._act = {a.nom: a for a in self.actions}
        self._idx = {v: i for i, v in enumerate(self.variables)}
        self._voies = tuple(tuple((self._idx[c.var], c.op, c.seuil) for c in v) for v in self.voies)

    def action(self, nom):
        return self._act[nom]

    def index(self, var):
        return self._idx[var]


def hypotheses():
    """Les 54 hypothèses (o, a, z, i)."""
    return list(product(range(3), range(3), range(3), range(2)))


def loi_a_priori(monde):
    """Loi a priori sur les 54 hypothèses : produit des marges du plan (spécification §2.3).

    O, Z : absent avec la proportion du plan, sinon les deux candidats sont équiprobables.
    A : absent avec la proportion du plan ; sinon la ligne de provenance ancienne ou mémo est
    deux fois plus souvent fausse que la ligne récente (rapport déclaré dans la loi).
    """
    L = monde.loi
    pO = [1 - L["O"], L["O"] / 2, L["O"] / 2]
    pZ = [1 - L["Z"], L["Z"] / 2, L["Z"] / 2]
    w = [L["rapport_provenance"] if monde.provenances[v] != "recent" else 1.0
         for v, _ in monde.cand_A]
    pA = [1 - L["A"], L["A"] * w[0] / sum(w), L["A"] * w[1] / sum(w)]
    pI = [1 - L["I"], L["I"]]
    return {h: pO[h[0]] * pA[h[1]] * pZ[h[2]] * pI[h[3]] for h in hypotheses()}


def initial_sous(monde, h):
    """État initial réel sous l'hypothèse h (l'affichage est vrai sauf la ligne fausse)."""
    vals = dict(monde.affiche)
    if h[1]:
        var, reelle = monde.cand_A[h[1] - 1]
        vals[var] = reelle
    if h[3]:
        var, plafond = monde.I_effet
        vals[var] = min(vals[var], plafond)
    return Etat(tuple(vals[v] for v in monde.variables))


def borner(monde, var, x):
    lo, hi = monde.domaines[var]
    return max(lo, min(hi, x))


def appliquer(monde, h, etat, nom):
    """Transition déterministe de l'action `nom` sous h ; rend (nouvel état, Z gagné).
    Ne dépend de h que par O, Z et I (A ne change que l'état initial)."""
    a = monde._act[nom]
    vals = list(etat.valeurs)
    verrous = etat.verrous
    idx = monde._idx
    plafond = monde.I_effet if h[3] else None

    def bouger(var, d):
        i = idx[var]
        if verrous >> i & 1 or d == 0:
            return
        lo, hi = monde.domaines[var]
        x = max(lo, min(hi, vals[i] + d))
        if plafond is not None and var == plafond[0]:
            x = min(x, plafond[1])
        vals[i] = x

    if a.verrou:
        verrous |= 1 << idx[a.cible]
    else:
        bouger(a.cible, a.delta)
        for var, d in a.effets_bord:
            bouger(var, d)
    if h[0]:
        act, var, d = monde.cand_O[h[0] - 1]
        if act == nom and not verrous >> idx[var] & 1:
            bouger(var, d)
            verrous |= 1 << idx[var]  # grippage : la variable touchée ne se corrige plus
    gain = 0
    if h[2] and monde.cand_Z[h[2] - 1] == nom and etat.z == 0:
        gain = monde.quantite_z
    return Etat(tuple(vals), verrous, etat.z + gain), gain


def _tient(op, x, seuil):
    return x >= seuil if op == ">=" else (x <= seuil if op == "<=" else x == seuil)


def atteinte(monde, etat):
    """Une voie au moins a toutes ses conditions satisfaites (spécification §2.4)."""
    v = etat.valeurs
    return any(all(_tient(op, v[i], s) for i, op, s in voie) for voie in monde._voies)


def valeur_terminale(monde, etat):
    return monde.V * atteinte(monde, etat) + monde.valeur_z * etat.z


H_DESCRIPTION = (0, 0, 0, 0)  # le monde tel que la description le dit
