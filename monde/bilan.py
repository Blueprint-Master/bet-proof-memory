"""Bilan d'une calibration (spécification v3, §1, §3.6, §3.7, §5.2, §5.3).

Usage : python3 bilan.py DOSSIER   (lit DOSSIER/parties.jsonl et DOSSIER/regle_V.json)
"""

import collections
import json
import os
import statistics
import sys

from scipy import stats

PANEL = ("rapide", "prudente", "ciblee", "essai", "arret")
REFS = ("explore", "bayes", "oracle")


def charger(dossier):
    lignes = [json.loads(x) for x in open(os.path.join(dossier, "parties.jsonl"), encoding="utf-8")]
    V = json.load(open(os.path.join(dossier, "regle_V.json")))["V"]
    return lignes, V


def mondes(lignes):
    """Mondes joués (bases acceptées et jumeaux impossibles), avec leur cellule."""
    out = []
    for l in lignes:
        if "parties" not in l:
            continue
        out.append({"cellule": l["cellule"], "I": 0, "facteurs": l["facteurs"], "budget": l["budget"],
                    "echeance": l["echeance"], "parties": l["parties"]})
        if "jumeau" in l:
            out.append({"cellule": "I", "I": 1, "facteurs": {**l["facteurs"], "I": 1},
                        "budget": l["budget"], "echeance": l["echeance"],
                        "parties": l["jumeau"]["parties"]})
    return out


def bilan(dossier):
    lignes, V = charger(dossier)
    B = {"V": V}
    rejets = collections.Counter()
    for l in lignes:
        for r in l["rejets"]:
            rejets[" / ".join(x for x in r if x)] += 1
    acceptes = [l for l in lignes if "parties" in l]
    B["cellules"] = len(lignes)
    B["acceptes"] = len(acceptes)
    B["non_pourvues"] = sorted({l["cellule"] for l in lignes if "parties" not in l})
    B["rejets"] = dict(rejets.most_common())
    jum = [l["jumeau"] for l in acceptes if "jumeau" in l]
    B["jumeaux"] = {"n": len(jum), "identiques": sum(j["identiques"] for j in jum),
                    "controles_ok": sum(j["controles_ok"] for j in jum)}

    M = mondes(lignes)
    U = {p: [m["parties"][p]["U"] for m in M] for p in PANEL + REFS}
    B["U_moyenne"] = {p: round(statistics.mean(v), 2) for p, v in U.items()}
    B["borne_haute_qmdp"] = round(statistics.mean(m["parties"]["qmdp_racine"] for m in M), 2)
    d = [b - r for b, r in zip(U["bayes"], U["rapide"])]
    G = statistics.mean(d)
    B["G"] = round(G, 2)
    B["G_sur_V"] = round(G / V, 3)
    B["signal_sur_bruit"] = round(G / statistics.stdev(d), 3) if len(d) > 1 else None
    B["sensibilite_part_ecart_0_1V"] = round(sum(abs(x) > 0.1 * V for x in d) / len(d), 3)
    B["plancher_G_tenu"] = G >= 0.15 * V and (B["signal_sur_bruit"] or 0) >= 0.5
    B["sensibilite_tenue"] = B["sensibilite_part_ecart_0_1V"] > 0.30

    # panel : meilleur par cellule, diversité, marge
    par_cell = collections.defaultdict(lambda: collections.defaultdict(list))
    for m in M:
        for p in PANEL + ("bayes",):
            par_cell[m["cellule"]][p].append(m["parties"][p]["U"])
    gagnants = collections.Counter()
    for c, dct in par_cell.items():
        moy = {p: statistics.mean(dct[p]) for p in PANEL}
        top = max(moy.values())
        for p in PANEL:
            if moy[p] >= top - 1e-9:
                gagnants[p] += 1 / sum(1 for q in PANEL if moy[q] >= top - 1e-9)
    n_cell = len(par_cell)
    B["panel_gagnants_part"] = {p: round(gagnants[p] / n_cell, 3) for p in PANEL}
    B["diversite_tenue"] = sum(1 for p in PANEL if gagnants[p] / n_cell >= 0.20) >= 2
    meilleur_panel = max(B["U_moyenne"][p] for p in PANEL)
    B["marge_bayes_sur_panel_en_G"] = round((B["U_moyenne"]["bayes"] - meilleur_panel) / G, 3) if G else None
    B["marge_tenue"] = bool(G) and B["marge_bayes_sur_panel_en_G"] >= 0.10
    B["bayes_domine_chaque_politique"] = all(B["U_moyenne"]["bayes"] >= B["U_moyenne"][p] for p in PANEL)

    # indépendance après rejet : paramètres visibles selon la présence des facteurs
    base = [m for m in M if m["I"] == 0]
    indep = {}
    for vis in ("budget", "echeance"):
        for fac in ("O", "A", "Z"):
            x1 = [m[vis] for m in base if m["facteurs"][fac]]
            x0 = [m[vis] for m in base if not m["facteurs"][fac]]
            if len(x1) > 2 and len(x0) > 2:
                p = stats.mannwhitneyu(x1, x0).pvalue
                indep[f"{vis}~{fac}"] = round(float(p), 3)
    B["independance_p"] = indep

    # résultats par facteur, pour la lecture
    par_fac = {}
    for fac in ("O", "A", "Z"):
        for val in (0, 1):
            sel = [m for m in base if m["facteurs"][fac] == val]
            if sel:
                par_fac[f"{fac}={val}"] = {p: round(statistics.mean(m["parties"][p]["U"] for m in sel), 2)
                                           for p in PANEL + REFS}
    for mg in ("serre", "large"):
        sel = [m for m in base if m["facteurs"]["marge"] == mg]
        if sel:
            par_fac[f"marge={mg}"] = {p: round(statistics.mean(m["parties"][p]["U"] for m in sel), 2)
                                      for p in PANEL + REFS}
    sel = [m for m in M if m["I"] == 1]
    if sel:
        par_fac["I=1"] = {p: round(statistics.mean(m["parties"][p]["U"] for m in sel), 2)
                          for p in PANEL + REFS}
    B["U_par_facteur"] = par_fac
    B["secondes_moyennes"] = {p: round(statistics.mean(m["parties"][p]["secondes"] for m in M), 2)
                              for p in PANEL + REFS}
    B["mondes_joues"] = len(M)
    return B


if __name__ == "__main__":
    print(json.dumps(bilan(sys.argv[1]), ensure_ascii=False, indent=1))
