"""Famille « réglages et seuils » (spécification v3, §6) : générateur de mondes.

Quatre réglages R1..R4 (0 à 4) et une stabilité S (0 à 3) ; actions monter, descendre
(réversibles, inverses l'une de l'autre), verrouiller (irréversible), stabiliser
(irréversible) ; un effet de bord déclaré ; trois voies qui exigent toutes S >= s_req et deux
conditions sur des réglages ; un témoin W sans rôle causal.

Règles de famille (connues de R_Bayes, déterministes à partir de la partie publique) :
- voie évidente : la voie atteinte par le plan optimal du monde tel que décrit ;
- O : effet de bord caché croisé : l'action de réglage de l'une des deux variables de la voie
  évidente éloigne l'autre d'un cran de sa condition et la grippe (elle ne se corrige plus,
  sauf si elle était verrouillée avant) ; seul un essai préalable le révèle avant d'agir ;
- A : la ligne fausse est l'une des deux variables de réglage de la voie évidente, sa valeur
  réelle est éloignée d'un cran de la satisfaction de sa condition ;
- Z : levier sur l'une des deux premières actions (ordre des noms) portant sur les réglages
  hors de la voie évidente ;
- I : la stabilité est plafonnée à s_req - 1, ce qui rend toutes les voies insatisfaisables.
"""

import math
import random

from modele import H_DESCRIPTION, Action, Condition, Monde, initial_sous
from plan import Planificateur

FAMILLE = "reglages"
REGLAGES = ("R1", "R2", "R3", "R4")
VARIABLES = REGLAGES + ("S",)
DOMAINES = {**{r: (0, 4) for r in REGLAGES}, "S": (0, 3), "W": (0, 4)}
COUTS = {"monter": 4, "descendre": 4, "verrouiller": 8, "stabiliser": 6}
COUTS_OUTILS = {"mesurer": 1, "lire": 1, "essayer": 2, "attendre": 0}
SOURCES = ("rapport", "note", "journal")
PROVENANCES = ("recent", "ancien", "memo")
LOI = {"O": 0.5, "A": 0.5, "Z": 0.5, "I": 0.1, "rapport_provenance": 2.0}
NOTE = (0.7, 0.3)  # P(la note signale une anomalie | O présent), idem | O absent
JOURNAL = {"juste": 0.6, "autre": 0.1, "fausse_alerte": 0.3}  # loi du journal (voir bayes)
P_ANOMALIE = 0.2
MARGES = {"serre": (1, 2), "large": (4, 7)}


class Rejet(Exception):
    pass


def _actions(rng):
    x, y = rng.sample(REGLAGES, 2)
    acts = []
    for r in REGLAGES:
        bord = ((y, -1),) if r == x else ()
        acts.append(Action(f"monter:{r}", r, 1, COUTS["monter"], True, f"descendre:{r}",
                           effets_bord=bord))
        acts.append(Action(f"descendre:{r}", r, -1, COUTS["descendre"], True, f"monter:{r}"))
    for v in VARIABLES:
        acts.append(Action(f"verrouiller:{v}", v, 0, COUTS["verrouiller"], False, verrou=True))
    acts.append(Action("stabiliser", "S", 1, COUTS["stabiliser"], False))
    return tuple(acts)


def _condition(rng, var, init):
    lo, hi = DOMAINES[var]
    options = []
    for gap in (1, 2):
        if init + gap <= hi:
            options += [Condition(var, ">=", init + gap), Condition(var, "==", init + gap)]
        if init - gap >= lo:
            options += [Condition(var, "<=", init - gap), Condition(var, "==", init - gap)]
    return rng.choice(options)


def _eloigner(cond, affiche):
    """Valeur réelle d'une ligne fausse : un cran plus loin de la satisfaction."""
    lo, hi = DOMAINES[cond.var]
    if cond.op == ">=":
        cands = [affiche - 1, affiche + 1]
    elif cond.op == "<=":
        cands = [affiche + 1, affiche - 1]
    else:
        cands = [affiche + (1 if affiche >= cond.seuil else -1), affiche - (1 if affiche >= cond.seuil else -1)]
    for c in cands:
        if lo <= c <= hi and c != affiche:
            return c
    raise Rejet("ligne fausse hors domaine")


def _journal(rng, cand_Z, z):
    """Indice bruité sur l'occasion : si elle existe, le journal nomme la bonne action avec la
    probabilité 0,6, l'autre candidate 0,1, rien 0,3 ; sinon il nomme l'une des deux
    candidates (fausse alerte) avec la probabilité 0,3."""
    u = rng.random()
    if z:
        if u < JOURNAL["juste"]:
            return cand_Z[z - 1]
        if u < JOURNAL["juste"] + JOURNAL["autre"]:
            return cand_Z[2 - z]
        return None
    if u < JOURNAL["fausse_alerte"]:
        return cand_Z[0] if rng.random() < 0.5 else cand_Z[1]
    return None


def _lexique(rng):
    lettres = list("BCDFGHJKLMNPQRSTVXZ")
    rng.shuffle(lettres)
    codes = [f"{lettres[i]}{rng.randint(1, 9)}" for i in range(len(VARIABLES) + 1)]
    lex = dict(zip(list(VARIABLES) + ["W"], codes))
    noms_sources = rng.sample(["dossier 1", "dossier 2", "dossier 3", "dossier 4", "dossier 5",
                               "dossier 6"], len(SOURCES))
    lex.update({s: n for s, n in zip(SOURCES, noms_sources)})
    return lex


def generer(graine, facteurs, V=30.0, q=0.8, ident=None, essais=200):
    """Tire un monde de la famille pour une cellule du plan croisé.

    facteurs : {"O": 0|1, "A": 0|1, "Z": 0|1, "marge": "serre"|"large", "I": 0|1,
                "difficulte": "facile"|"difficile"}. La graine fixe tout le tirage sauf I,
    ce qui produit les jumeaux (même graine, I opposé, descriptions identiques).
    """
    rng = random.Random(graine)
    for _ in range(essais):
        try:
            return _tenter(rng, graine, facteurs, V, q, ident)
        except Rejet:
            continue
    raise Rejet(f"aucun monde valide en {essais} essais (graine {graine})")


def _tenter(rng, graine, facteurs, V, q, ident):
    actions = _actions(rng)
    s_req = rng.choice([1, 2])
    affiche = {r: rng.randint(0, 4) for r in REGLAGES}
    affiche["S"] = rng.randint(0, s_req - 1)
    voies = []
    for _ in range(3):
        a, b = sorted(rng.sample(REGLAGES, 2))
        voies.append((_condition(rng, a, affiche[a]), _condition(rng, b, affiche[b]),
                      Condition("S", ">=", s_req)))
    if len({tuple(v) for v in voies}) < 3:
        raise Rejet("voies identiques")
    provenances = {v: rng.choice(PROVENANCES) for v in VARIABLES}
    temoins = {"W": rng.randint(1, 3)}

    # monde provisoire, tel que décrit, pour la voie évidente et le plan décrit
    base = dict(ident=ident or f"{FAMILLE}-{graine}", famille=FAMILLE, variables=VARIABLES,
                domaines=DOMAINES, affiche=affiche, provenances=provenances, actions=actions,
                voies=tuple(voies), budget=80, echeance=10, V=V, valeur_z=0.2 * V, q=q, qe=q,
                couts_outils=COUTS_OUTILS, sources=SOURCES, contenu_sources={},
                vraisemblance_sources={"note": NOTE, "journal": JOURNAL}, temoins=temoins, p_anomalie=P_ANOMALIE,
                cand_O=(("", "S", 0), ("", "S", 0)), cand_A=(("R1", 0), ("R2", 0)),
                cand_Z=("", ""), quantite_z=1, I_effet=("S", s_req - 1), loi=LOI,
                h_vrai=H_DESCRIPTION)
    prov = Monde(**base)
    etat0 = initial_sous(prov, H_DESCRIPTION)
    plan = Planificateur(prov, H_DESCRIPTION).plan(etat0, 0, 80)
    if not plan:
        raise Rejet("aucun plan décrit")
    etat = etat0
    from modele import appliquer
    for a in plan:
        etat, _ = appliquer(prov, H_DESCRIPTION, etat, a)
    evidente = next((v for v in voies
                     if all(c.tient(etat.valeurs[VARIABLES.index(c.var)]) for c in v)), None)
    if evidente is None:
        raise Rejet("plan décrit sans voie atteinte")
    regl = [c for c in evidente if c.var in REGLAGES]
    act_regl = []
    for c in regl:
        noms = [a for a in plan if a.split(":")[-1] == c.var and a.split(":")[0] in ("monter", "descendre")]
        if not noms:
            raise Rejet("condition de la voie évidente sans action de réglage")
        act_regl.append(noms[0])
    def eloigne(c):
        vers = 1 if c.op == ">=" or (c.op == "==" and affiche[c.var] < c.seuil) else -1
        return -vers
    cand_O = ((act_regl[0], regl[1].var, eloigne(regl[1])),
              (act_regl[1], regl[0].var, eloigne(regl[0])))
    for _, var, d in cand_O:
        lo, hi = DOMAINES[var]
        if not lo <= affiche[var] + d <= hi:
            raise Rejet("obstacle sans effet : variable en butée")  # avant tout tirage de h
    cand_A = tuple((c.var, _eloigner(c, affiche[c.var])) for c in regl)
    hors = sorted(a.nom for a in actions if a.nom.split(":")[0] in ("monter", "descendre")
                  and a.cible not in {c.var for c in regl})
    cand_Z = (hors[0], hors[1])

    cout_plan = sum(prov.action(a).cout for a in plan)
    budget = 2 * cout_plan
    lo, hi = MARGES[facteurs["marge"]]
    echeance = len(plan) + rng.randint(lo, hi)

    o = rng.choice([1, 2]) if facteurs["O"] else 0
    if facteurs["A"]:
        w = [LOI["rapport_provenance"] if provenances[v] != "recent" else 1.0 for v, _ in cand_A]
        a_ = 1 if rng.random() < w[0] / sum(w) else 2
    else:
        a_ = 0
    z = rng.choice([1, 2]) if facteurs["Z"] else 0
    h_vrai = (o, a_, z, facteurs["I"])

    note = {"anomalie": rng.random() < (NOTE[0] if o else NOTE[1])}
    vrai0 = initial_sous(prov.__class__(**{**base, "cand_A": cand_A}), (0, a_, 0, 0))
    contenu = {
        "rapport": dict(affiche),
        "note": note,
        "journal": {"sous_produit": _journal(rng, cand_Z, z)},
    }
    lexique = _lexique(rng)
    ordre = {"voies": rng.sample(range(3), 3), "variables": rng.sample(range(len(VARIABLES)), len(VARIABLES)),
             "sources": rng.sample(range(len(SOURCES)), len(SOURCES))}
    base.update(budget=budget, echeance=echeance, cand_O=cand_O, cand_A=cand_A, cand_Z=cand_Z,
                h_vrai=h_vrai, contenu_sources=contenu,
                facteurs=dict(facteurs), lexique=lexique, ordre=ordre)
    base["facteurs"]["s_req"] = s_req
    base["facteurs"]["plan_decrit"] = len(plan)
    return Monde(**base)
