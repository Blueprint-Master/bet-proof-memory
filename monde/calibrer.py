"""Calibration sur les mondes de développement (spécification v3, §3 et §5), sans modèle de
langage.

Étapes :
  1. règle de V : V = 3 x coût moyen du chemin optimal à information parfaite (R∞), mesuré sur
     un premier lot de mondes de développement ;
  2. génération par cellule du plan croisé, contrôles 1 à 4, motifs de rejet journalisés ;
     jumeaux impossibles pour environ un monde sur neuf (contrôle 5) ;
  3. jeu des politiques du panel et des références sur chaque monde accepté ;
  4. bilan : G, sensibilité de U, critères du panel, indépendance après rejet (contrôle 7),
     fuites de surface (contrôle 6).

Usage : python3 calibrer.py --par-cellule 4 --processus 2 --sortie DOSSIER
Les sorties (mondes, parties, bilan) sont écrites hors du dépôt ; leurs empreintes vont au
registre.
"""

import argparse
import hashlib
import itertools
import json
import os
import signal
import statistics
import time
from multiprocessing import Pool

from bayes import Evaluateur, racine
from calibrage import table as table_q
from controles import controler, jumeaux
from famille_reglages import Rejet, generer
from modele import appliquer, initial_sous
from politiques import PANEL, REFERENCES, jouer

GRAINE_DEV = 20261023
CELLULES = [dict(O=O, A=A, Z=Z, marge=mg, difficulte=d)
            for O, A, Z, mg, d in itertools.product((0, 1), (0, 1), (0, 1), ("serre", "large"),
                                                    ("facile", "difficile"))]


def graine(*cle):
    return int(hashlib.sha256("|".join(map(str, (GRAINE_DEV,) + cle)).encode()).hexdigest()[:12], 16)


def cout_oracle(args):
    c, r = args
    f = {**CELLULES[c], "I": 0}
    try:
        m = generer(graine("V", c, r), f, q=table_q()[f["difficulte"]], V=60.0)
    except Rejet:
        return None
    ev = Evaluateur(m)
    e = initial_sous(m, m.h_vrai)
    pl = ev.plans[m.h_vrai].plan(e, 0, m.budget)
    return sum(m.action(a).cout for a in pl)


def accepter(c, r, V, I=0, essais=40):
    """Premier monde accepté de la cellule c, réplique r ; rend (monde, rapport, rejets)."""
    rejets = []
    for k in range(essais):
        f = {**CELLULES[c], "I": I}
        g = graine("monde", c, r, k)
        try:
            m = generer(g, f, q=table_q()[f["difficulte"]], V=V, ident=f"dev-{c}-{r}-{k}-{I}")
        except Rejet as e:
            rejets.append(("generation", str(e)))
            continue
        ev = Evaluateur(m)
        ok, rap = controler(m, ev)
        if ok:
            return m, ev, rap, rejets, g
        motif = next((n for n, v in rap.items() if not v.get("ok", True)
                      or v.get("identifiable") is False or v.get("utile") is False
                      or v.get("accessible") is False), "?")
        detail = rap.get(motif, {})
        sous = [x for x in ("identifiable", "utile", "accessible") if detail.get(x) is False]
        rejets.append((motif, ",".join(sous)))
    return None, None, None, rejets, None


def jouer_tout(m, ev, g):
    res = {}
    n0 = racine(m)
    res["qmdp_racine"] = ev.qmdp(n0)
    res["engager_racine"] = ev.engager(n0)[0]
    for C in PANEL + REFERENCES:
        t0 = time.time()
        p = jouer(m, C, g, ev=ev)
        res[C.nom] = {"U": p.utilite(), "motif": p.motif, "periodes": p.t, "depense": p.depense,
                      "commandes": [c for _, c, _ in p.journal], "secondes": round(time.time() - t0, 2)}
    return res


PLAFOND_SECONDES = 900  # par monde (contrôles et parties) ; au-delà, journalisé et sauté


class Depassement(Exception):
    pass


def _alarme(signum, frame):
    raise Depassement()


def tache(args):
    signal.signal(signal.SIGALRM, _alarme)
    signal.alarm(PLAFOND_SECONDES)
    try:
        return _tache(args)
    except Depassement:
        c, r, _, _ = args
        return {"cellule": c, "replique": r, "rejets": [("depassement", f"{PLAFOND_SECONDES} s")]}
    finally:
        signal.alarm(0)


def _tache(args):
    c, r, V, avec_jumeau = args
    m, ev, rap, rejets, g = accepter(c, r, V)
    sortie = {"cellule": c, "replique": r, "rejets": rejets}
    if m is None:
        return sortie
    sortie.update(monde=m.ident, graine=g, h_vrai=m.h_vrai, facteurs=m.facteurs, budget=m.budget,
                  echeance=m.echeance, V=m.V, controles=rap, parties=jouer_tout(m, ev, g))
    if avec_jumeau:
        f = {**CELLULES[c], "I": 1}
        jm = generer(g, f, q=m.q, V=V, ident=m.ident.replace("-0", "-1") + "-jumeau")
        ok_j, _ = jumeaux(m, jm)
        jev = Evaluateur(jm)
        ok_c, rap_j = controler(jm, jev)
        sortie["jumeau"] = {"identiques": ok_j, "controles_ok": ok_c, "controles": rap_j,
                            "h_vrai": jm.h_vrai, "parties": jouer_tout(jm, jev, g)}
    return sortie


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--par-cellule", type=int, default=4)
    ap.add_argument("--processus", type=int, default=2)
    ap.add_argument("--lot-V", type=int, default=2)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    t0 = time.time()
    with Pool(a.processus) as pool:
        couts = [x for x in pool.map(cout_oracle, [(c, r) for c in range(len(CELLULES))
                                                    for r in range(a.lot_V)]) if x is not None]
        V = 3 * round(statistics.mean(couts))
        print(f"règle de V : coût moyen du chemin optimal {statistics.mean(couts):.2f} sur "
              f"{len(couts)} mondes ; V = {V}", flush=True)
        taches = []
        n = 0
        for r in range(a.par_cellule):
            for c in range(len(CELLULES)):
                taches.append((c, r, float(V), n % 9 == 0))
                n += 1
        chemin = os.path.join(a.sortie, "parties.jsonl")
        with open(chemin, "w", encoding="utf-8") as fo:
            for i, s in enumerate(pool.imap_unordered(tache, taches)):
                fo.write(json.dumps(s, ensure_ascii=False) + "\n")
                fo.flush()
                print(f"{i + 1}/{len(taches)} {time.time() - t0:.0f} s", flush=True)
    with open(os.path.join(a.sortie, "regle_V.json"), "w") as fo:
        json.dump({"couts_oracle": couts, "V": V}, fo)


if __name__ == "__main__":
    main()
