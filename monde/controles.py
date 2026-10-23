"""Contrôles à la génération (spécification v3, §3). Chaque contrôle rend (ok, détail).

Contrôles par monde : 1 cohérence texte et structure, 2 calibrage, 3 faisabilité,
4 découvrabilité (identifiable, accessible, utile) de chaque facteur présent, 5 jumeaux.
Contrôles par lot (calibrer.py) : 6 fuites de surface, 7 indépendance après rejet.
"""

import re

from bayes import Evaluateur, contenu_sous, p_lecture, racine
from calibrage import table as table_q
from description import tableau, texte
from modele import H_DESCRIPTION, appliquer, atteinte, initial_sous
from observations import essai_vrai
from plan import Planificateur

EMPLACEMENTS = {"O": 0, "A": 1, "Z": 2, "I": 3}


def coherence(monde):
    t = tableau(monde)
    tx = texte(monde)
    lex = monde.lexique
    for v in t["variables"]:
        interne = next(k for k, n in lex.items() if n == v["nom"])
        if v["valeur_initiale"] != monde.affiche[interne]:
            return False, f"tableau : {interne}"
        if not re.search(rf"- {re.escape(v['nom'])}, de \d à \d : {v['valeur_initiale']} ", tx):
            return False, f"texte : {interne}"
    vrai = initial_sous(monde, monde.h_vrai)
    diff = [v for v in monde.variables if vrai.valeurs[monde.index(v)] != monde.affiche[v]]
    attendu = []
    if monde.h_vrai[1]:
        attendu.append(monde.cand_A[monde.h_vrai[1] - 1][0])
    if monde.h_vrai[3] and monde.affiche["S"] > monde.I_effet[1]:
        attendu.append("S")
    if sorted(diff) != sorted(attendu):
        return False, f"mutations inattendues {diff} (attendu {attendu})"
    for cle in ("h_vrai", "cand_O", "cand_A", "cand_Z", "I_effet", "contenu_sources"):
        if cle in t:
            return False, f"champ latent dans le tableau : {cle}"
    return True, ""


def calibrage(monde):
    q = table_q()[monde.facteurs["difficulte"]]
    return (abs(monde.q - q) < 1e-9 and abs(monde.qe - q) < 1e-9), f"q={monde.q} attendu {q}"


def faisabilite(monde, ev):
    h = monde.h_vrai
    e0 = initial_sous(monde, h)
    pl = ev.plans[h].plan(e0, 0, monde.budget)
    e, cout = e0, 0
    for a in pl:
        e, _ = appliquer(monde, h, e, a)
        cout += monde.action(a).cout
    ok = atteinte(monde, e) == (not h[3])
    return ok, f"plan optimal {len(pl)} actions, coût {cout}, atteint {atteinte(monde, e)}"


def _differe(monde, h1, h2, e1, e2):
    """Une commande dont la loi d'observation diffère sous h1 et h2, aux états e1, e2."""
    if e1 != e2:
        for i, v in enumerate(monde.variables):
            if e1.valeurs[i] != e2.valeurs[i]:
                return ("mesurer", v)
        return ("mesurer", "état")
    for a in monde.actions:
        if essai_vrai(monde, h1, e1, a.nom) != essai_vrai(monde, h2, e2, a.nom):
            return ("essayer", a.nom)
        if appliquer(monde, h1, e1, a.nom)[1] != appliquer(monde, h2, e2, a.nom)[1]:
            return ("agir", a.nom)
    for s in monde.sources:
        c1 = contenu_sous(monde, s, h1)
        if s == "note":
            if p_lecture(monde, s, {"anomalie": True}, h1) != p_lecture(monde, s, {"anomalie": True}, h2):
                return ("lire", s)
        elif c1 != contenu_sous(monde, s, h2):
            return ("lire", s)
    return None


def _prefixes(monde, ev, h1, h2):
    plans = [Planificateur(monde, H_DESCRIPTION).plan(initial_sous(monde, H_DESCRIPTION), 0, monde.budget),
             ev.plans[h1].plan(initial_sous(monde, h1), 0, monde.budget),
             ev.plans[h2].plan(initial_sous(monde, h2), 0, monde.budget)]
    # pour l'impossibilité, le plan du jumeau faisable est le chemin naturel
    vus = []
    for pl in plans:
        for k in range(len(pl) + 1):
            p = tuple(pl[:k])
            if p not in vus:
                vus.append(p)
    return sorted(vus, key=len)


def decouvrabilite(monde, ev, facteur):
    """Identifiable, accessible, utile, pour un facteur présent dans h_vrai."""
    h = monde.h_vrai
    i = EMPLACEMENTS[facteur]
    alt = list(h)
    alt[i] = 0
    alt = tuple(alt)
    ident = None
    for pref in _prefixes(monde, ev, h, alt):
        e1, e2 = initial_sous(monde, h), initial_sous(monde, alt)
        for a in pref:
            e1, _ = appliquer(monde, h, e1, a)
            e2, _ = appliquer(monde, alt, e2, a)
        cmd = _differe(monde, h, alt, e1, e2)
        if cmd:
            ident = (len(pref) + 1, pref, cmd)
            break
    if ident is None:
        return {"identifiable": False, "accessible": False, "utile": False, "detail": "aucune commande"}
    pl = ev.plans[h].plan(initial_sous(monde, h), 0, monde.budget)
    accessible = ident[0] + len(pl) <= monde.echeance
    # utilité : valeur de l'information parfaite sur l'emplacement, à la racine, sous la loi
    n0 = racine(monde)
    lignes = ev.matrice(n0)
    sans = max(sum(n0.b[x] * col[x] for x in n0.b) for col in lignes.values())
    avec = 0.0
    for modalite in sorted({x[i] for x in n0.b}):
        sous = [x for x in n0.b if x[i] == modalite]
        pm = sum(n0.b[x] for x in sous)
        if pm <= 0:
            continue
        avec += max(sum(n0.b[x] * col[x] for x in sous) for col in lignes.values())
    vpi = avec - sans
    k = {"facile": 2, "difficile": 4}[monde.facteurs["difficulte"]]
    cmd = ident[2]
    if cmd[0] in ("mesurer", "essayer"):
        cout_ident = k * monde.couts_outils[cmd[0]]
    elif cmd[0] == "lire":
        cout_ident = monde.couts_outils["lire"] * (1 if cmd[1] != "note" else k)
    else:
        cout_ident = 0.0  # l'action elle-même révèle (Z) : aucun coût d'information propre
    return {"identifiable": True, "accessible": accessible, "utile": vpi > cout_ident,
            "vpi": round(vpi, 3), "periodes": ident[0], "commande": ident[2]}


def jumeaux(monde, jumeau):
    ok = tableau(monde) == tableau(jumeau) and texte(monde) == texte(jumeau)
    ok = ok and all(contenu_sous(monde, s, monde.h_vrai) == contenu_sous(jumeau, s, jumeau.h_vrai)
                    for s in monde.sources if s != "note")
    ok = ok and monde.contenu_sources["note"] == jumeau.contenu_sources["note"]
    return ok, ""


def controler(monde, ev=None):
    """Contrôles 1 à 4 ; rend (accepté, rapport)."""
    ev = ev or Evaluateur(monde)
    rapport = {}
    for nom, f in (("coherence", lambda: coherence(monde)), ("calibrage", lambda: calibrage(monde)),
                   ("faisabilite", lambda: faisabilite(monde, ev))):
        ok, det = f()
        rapport[nom] = {"ok": ok, "detail": det}
        if not ok:
            return False, rapport
    serre = monde.facteurs["marge"] == "serre"
    for fac, i in EMPLACEMENTS.items():
        if monde.h_vrai[i]:
            d = decouvrabilite(monde, ev, fac)
            rapport[f"decouvrabilite_{fac}"] = d
            if not d["identifiable"] or not d["utile"] or (not d["accessible"] and not serre):
                return False, rapport
    return True, rapport
