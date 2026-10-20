"""Protocole Q1 v1.7, P6 ter : perte en cas de défaut (LGD) et seuils de décision de P6.

Unité : la procédure (SIREN, date du jugement de défaillance au sens de P3), pour les
défaillances des cas des origines retenues du développement, dédupliquées.

Modèle multi-états (temps en jours depuis le jugement de défaillance, événements datés
par leur jugement, annonces parues avant le 30/09/2022 seulement) :
  O observation (état initial d'une défaillance en redressement)
  P plan
  L liquidation (absorbante ; état initial d'une défaillance qui est elle-même une
    liquidation : ouverture, conversion d'une sauvegarde en liquidation, résolution d'un
    plan avec liquidation)
Transitions :
  O -> P  plan de redressement arrêté hors cession ; clôture pour extinction du passif
  O -> L  ouverture d'une liquidation, conversion en liquidation, plan de cession,
          résolution d'un plan avec liquidation, reprise d'une liquidation
  P -> L  mêmes jugements que O -> L
Tout autre jugement ne change pas l'état ; les clôtures autres que pour extinction du
passif observées en O sont comptées à part (diagnostic). Seuls les jugements datés
strictement après le jugement de défaillance comptent ; deux transitions le même jour
sont réduites à la dernière (O -> P -> L le même jour devient O -> L).

Estimateur : probabilités d'occupation des états à tau par l'estimateur d'Aalen-Johansen
(produit des matrices de transition empiriques aux temps d'événement), censure au
30/09/2022 supposée non informative. tau = 1 095 jours ; si moins de 300 procédures sont
suivies jusqu'à tau (date de défaillance au plus tard le 30/09/2022 moins tau), tau est
ramené au plus grand délai qui l'atteint ; sous 365 jours, arrêt.

LGD = 0,95 w + 0,269 (1 - w), w = P_L / (P_L + P_plan) (w = 1 si le dénominateur est nul) ;
bornes w_bas = P_L, w_haut = P_L + P_obs. Taux de recouvrement chirographaires : 5,0 % en
liquidation, 73,1 % en continuation (Blazy, Petey et Weill, 2018, cités par Banque de
France, document de travail n° 810, note 5).

Seuils de P6 : p_t = pi T / (q LGD), T = horizon / D ; grille pi = 0,1 % (primaire) et
2 % (sensibilité), D = 30, 45, 60 jours, q = 0,7 et 0,9 ; un scénario dont p_t >= 1 est
retiré et rapporté.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "ingestion"))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
from construire import ISSUES, _date, _lire, _siren, classer_jugement, reparer, sha256_fichier  # noqa: E402
from extraire import DOSSIER_DEFAUT, GARDE_SCELLE  # noqa: E402

LGD_LIQUIDATION = 1 - 0.050
LGD_CONTINUATION = 1 - 0.731
TAU = 1095
PLANCHER = 300
TAU_MIN = 365
PI_PRIMAIRE, PI_SENSIBILITE = 0.001, 0.02
DELAIS = (30, 45, 60)
QUOTITES = (0.7, 0.9)
O, P, L = 0, 1, 2
VERS_L = {"OUV-LJ", "CONV-LJ", "CONV-SAUV-LJ", "RESOL-LJ", "CESSION", "REOUV"}
ENTREE_L = {"OUV-LJ", "CONV-SAUV-LJ", "RESOL-LJ"}


def classer_transition(jugement) -> tuple:
    """Nature d'un jugement pour le modèle multi-états : celle de classer_jugement, précisée
    pour les conversions en liquidation, les plans de cession et les clôtures."""
    n, d = classer_jugement(jugement)
    if n not in ("AUTRE", "CLOT"):
        return n, d
    j = jugement
    if isinstance(j, str):
        try:
            j = json.loads(j)
        except ValueError:
            j = {"nature": j}
    j = j or {}
    nature = reparer(f"{j.get('famille', '')} {j.get('nature', '')}").lower()
    complement = reparer(str(j.get("complementJugement") or "")).lower()
    if n == "CLOT":
        return ("CLOT-EXT" if "extinction" in nature or "extinction du passif" in complement else "CLOT"), d
    if "cession" in nature:
        return "CESSION", d
    if "liquidation" in nature and ("conversion" in nature or "prononçant" in nature or "prononce" in nature):
        return "CONV-LJ", d
    return "AUTRE", d


def evenements_bruts(dossier: str) -> tuple[dict, dict, list]:
    """SIREN -> [(date de jugement, nature)] triés ; décompte des natures, dont les libellés AUTRE."""
    ev, chemins, natures, autres = {}, [], {}, {}
    for motif in ("bodacc-collective.parquet", "bodacc-pcl.parquet"):
        try:
            t, c = _lire(dossier, motif, ["dateparution", "registre", "jugement"])
        except RuntimeError:
            continue
        chemins += c
        for r, p, j in zip(t.column("registre").to_pylist(), t.column("dateparution").to_pylist(),
                           t.column("jugement").to_pylist()):
            s, p = _siren(r), _date(p)
            if not s or not p:
                continue
            if p >= GARDE_SCELLE:
                raise RuntimeError("annonce postérieure à la garde du scellé dans les instantanés")
            n, d = classer_transition(j)
            natures[n] = natures.get(n, 0) + 1
            if n == "AUTRE":
                try:
                    jj = json.loads(j) if isinstance(j, str) else (j or {})
                except ValueError:
                    jj = {}
                lib = reparer(str(jj.get("nature") or ""))[:120]
                autres[lib] = autres.get(lib, 0) + 1
            if n not in ("ANNULE", "AUTRE"):
                ev.setdefault(s, []).append((d or p, n))
    if not chemins:
        raise RuntimeError("aucun instantané de procédures collectives")
    for v in ev.values():
        v.sort()
    return ev, {"natures": natures, "libelles_autre": dict(sorted(autres.items(), key=lambda x: -x[1])[:40])}, chemins


def parcours(evts: list, d0: dt.date, nature0: str, fin: dt.date = GARDE_SCELLE) -> dict:
    """Parcours d'une procédure : état d'entrée, transitions [(jours, de, vers)], censure (jours)."""
    entree = L if nature0 in ENTREE_L else O
    etat, trans, anomalies = entree, [], 0
    for dj, n in evts:
        if dj <= d0 or etat == L:
            continue
        t = (dj - d0).days
        if etat == O and n in ("PLAN", "CLOT-EXT"):
            trans.append((t, O, P))
            etat = P
        elif etat in (O, P) and n in VERS_L:
            trans.append((t, etat, L))
            etat = L
        elif etat == O and n == "CLOT":
            anomalies += 1
    # Deux transitions le même jour : on garde O -> L.
    if len(trans) == 2 and trans[0][0] == trans[1][0]:
        trans = [(trans[0][0], O, L)]
    return {"entree": entree, "transitions": trans, "censure": (fin - d0).days, "anomalies_clot_en_O": anomalies}


def aalen_johansen(parcours_: list, tau: int) -> np.ndarray:
    """Probabilités d'occupation (O, P, L) à tau, par produit des matrices de transition empiriques."""
    n = len(parcours_)
    if n == 0:
        raise ValueError("aucune procédure")
    inf = np.iinfo(np.int64).max
    entree = np.array([q["entree"] for q in parcours_])
    cens = np.array([q["censure"] for q in parcours_])
    t1 = np.array([q["transitions"][0][0] if q["transitions"] else inf for q in parcours_])
    v1 = np.array([q["transitions"][0][2] if q["transitions"] else -1 for q in parcours_])
    t2 = np.array([q["transitions"][1][0] if len(q["transitions"]) > 1 else inf for q in parcours_])
    prob = np.bincount(entree, minlength=3) / n
    temps = np.unique(np.concatenate([t1[(t1 <= np.minimum(tau, cens))], t2[(t2 <= np.minimum(tau, cens))]]))
    for t in temps:
        suivi = cens >= t
        avant = np.where(t1 >= t, entree, np.where(t2 >= t, v1, L))
        a_risque = np.bincount(avant[suivi], minlength=3)
        flux = np.zeros((3, 3))
        for tt, de, vers in ((t1, entree, v1), (t2, v1, np.full(n, L))):
            m = (tt == t) & suivi
            np.add.at(flux, (de[m], vers[m]), 1)
        nouvelle = prob.copy()
        for a in (O, P):
            if a_risque[a] > 0:
                for b in (P, L):
                    if flux[a, b]:
                        m = prob[a] * flux[a, b] / a_risque[a]
                        nouvelle[a] -= m
                        nouvelle[b] += m
        prob = nouvelle
    return prob


def choisir_tau(parcours_: list, tau=TAU, plancher=PLANCHER, tau_min=TAU_MIN) -> tuple[int, int]:
    """(tau retenu, procédures suivies jusqu'à tau)."""
    censures = np.sort(np.array([q["censure"] for q in parcours_]))[::-1]
    suivies = int((censures >= tau).sum())
    if suivies >= plancher:
        return tau, suivies
    if len(censures) < plancher:
        raise RuntimeError("moins de procédures que le plancher : arrêt (P6 ter)")
    t = int(censures[plancher - 1])
    if t < tau_min:
        raise RuntimeError(f"tau ramené à {t} jours, sous {tau_min} : arrêt (P6 ter)")
    return t, int((censures >= t).sum())


def lgd_depuis(prob: np.ndarray) -> dict:
    p_obs, p_plan, p_l = (float(x) for x in prob)
    w = p_l / (p_l + p_plan) if p_l + p_plan > 0 else 1.0
    f = lambda w_: LGD_LIQUIDATION * w_ + LGD_CONTINUATION * (1 - w_)  # noqa: E731
    return {"P_obs": p_obs, "P_plan": p_plan, "P_L": p_l, "w": w, "lgd": f(w),
            "w_bas": p_l, "lgd_bas": f(p_l), "w_haut": p_l + p_obs, "lgd_haut": f(p_l + p_obs)}


def seuils(lgd: float, pi: float, horizon: int, delais=DELAIS, quotites=QUOTITES) -> dict:
    """Scénarios de P6 : retenus (p_t < 1) et retirés (décision constante)."""
    retenus, retires = [], []
    for d in delais:
        for q in quotites:
            T = horizon / d
            pt = pi * T / (q * lgd)
            s = {"pi": pi, "D": d, "q": q, "T": T, "lgd": lgd, "p_t": pt}
            (retenus if pt < 1 else retires).append(s)
    return {"retenus": retenus, "retires": retires}


def procedures_dev(cas: dict, evts: dict) -> tuple[list, dict]:
    """Défaillances des cas retenus, dédupliquées par (SIREN, date) ; parcours de chacune."""
    vues, sortie, sans_nature = set(), [], 0
    for s, di, y in zip(cas["siren"], cas["date_issue"], cas["issue"]):
        if y != 1 or di is None or (s, di) in vues:
            continue
        vues.add((s, di))
        liste = evts.get(s, [])
        nature0 = next((n for d, n in liste if d == di and n in ISSUES), None)
        if nature0 is None:
            sans_nature += 1
            continue
        sortie.append(parcours(liste, di, nature0))
    return sortie, {"procedures": len(vues), "sans_nature_retrouvee": sans_nature}


def charger_defauts(chemin: str) -> dict:
    import pyarrow.parquet as pq

    t = pq.read_table(chemin, columns=["siren", "origine_retenue", "issue", "date_issue"])
    r = np.asarray(t.column("origine_retenue").to_numpy(zero_copy_only=False)) == 1
    return {"siren": np.asarray(t.column("siren").to_pylist(), dtype=object)[r],
            "issue": np.asarray(t.column("issue").to_numpy(zero_copy_only=False))[r],
            "date_issue": np.asarray(t.column("date_issue").to_pylist(), dtype=object)[r]}


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--dossier", default=DOSSIER_DEFAUT)
    args = a.parse_args(argv)
    chemin = os.path.join(args.dossier, "cas-dev.parquet")
    cas = charger_defauts(chemin)
    evts, info, entrees = evenements_bruts(args.dossier)
    parc, compte = procedures_dev(cas, evts)
    tau, suivies = choisir_tau(parc)
    prob = aalen_johansen(parc, tau)
    res = lgd_depuis(prob)
    rapport = {"tau_jours": tau, "procedures_suivies_jusqua_tau": suivies, **compte,
               "entrees_en_liquidation": int(sum(q["entree"] == L for q in parc)),
               "anomalies_clot_en_observation": int(sum(q["anomalies_clot_en_O"] for q in parc)),
               "estimation": res, "natures_jugements": info["natures"], "libelles_autre": info["libelles_autre"],
               "seuils": {f"{h}j": {"primaire_pi_0.1%": seuils(res["lgd"], PI_PRIMAIRE, h),
                                    "sensibilite_pi_2%": seuils(res["lgd"], PI_SENSIBILITE, h),
                                    "sensibilite_lgd_bas": seuils(res["lgd_bas"], PI_PRIMAIRE, h),
                                    "sensibilite_lgd_haut": seuils(res["lgd_haut"], PI_PRIMAIRE, h)}
                          for h in (548, 365, 183)},
               "entrees": {os.path.basename(c): sha256_fichier(c) for c in entrees + [chemin]},
               "code": {"lgd.py": sha256_fichier(os.path.abspath(__file__))},
               "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"
    sortie = os.path.join(args.dossier, f"lgd-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(texte)
    print(f"procédures {compte['procedures']} (sans nature retrouvée {compte['sans_nature_retrouvee']}), "
          f"tau {tau} j, suivies {suivies}", file=sys.stderr)
    print("P_obs {P_obs:.4f}  P_plan {P_plan:.4f}  P_L {P_L:.4f}  w {w:.4f}  LGD {lgd:.4f}  "
          "[{lgd_bas:.4f} ; {lgd_haut:.4f}]".format(**res), file=sys.stderr)
    for s in rapport["seuils"]["548j"]["primaire_pi_0.1%"]["retenus"]:
        print(f"  548 j, D {s['D']}, q {s['q']} : p_t = {s['p_t']:.4%}", file=sys.stderr)
    print(f"natures : {info['natures']}", file=sys.stderr)
    print(f"\nRapport : {sortie}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
