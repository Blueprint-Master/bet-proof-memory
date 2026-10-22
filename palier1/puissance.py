"""Palier 1 de la boucle de supervision : analyse de puissance après le pilote (section 7.4).

Modèle : la statistique primaire est la moyenne pondérée de Δ = coût(T1) − coût(B) sur les cas
éligibles ; avec un tirage stratifié 50 / 50 et des poids p (défaillants) et 1 − p, elle vaut
p · moyenne(Δ | défaillant) + (1 − p) · moyenne(Δ | non défaillant), de variance
p² s1² / n1 + (1 − p)² s0² / n0. Avec n1 = n0 = n / 2, l'effectif total qui donne une puissance
de 80 % au seuil bilatéral de 5 % pour un effet δ est
    n = 2 (p² s1² + (1 − p)² s0²) (z_0,975 + z_0,80)² / δ².
Les variances par strate sont estimées sur le pilote (plug-in), puis majorées par leur borne
supérieure à 90 % (khi-deux, ddl = n_strate − 1). Une strate sans aucune différence ne permet pas
d'estimer sa variance : elle est signalée, et la décision revient au décideur.
"""

import math

from scipy.stats import chi2, norm

DELTA_UTILE = 0.001  # proposition, à valider avant lecture du pilote : voir le document de puissance


def variances_par_strate(fiches_t1: dict, fiches_b: dict, cas: dict) -> dict:
    out = {}
    for y in (1, 0):
        d = [fiches_t1[k]["cout_realise"] - fiches_b[k]["cout_realise"] for k, f in fiches_t1.items()
             if f["type"] == "eligible" and cas[k]["y"] == y]
        n = len(d)
        m = sum(d) / n if n else math.nan
        s2 = sum((x - m) ** 2 for x in d) / (n - 1) if n > 1 else math.nan
        haut = s2 * (n - 1) / chi2.ppf(0.10, n - 1) if n > 1 else math.nan
        out[y] = {"n": n, "moyenne": m, "variance": s2, "variance_haute_90": haut,
                  "differences_non_nulles": sum(abs(x) > 1e-15 for x in d)}
    return out


def effectif(p: float, s1: float, s0: float, delta: float = DELTA_UTILE, puissance: float = 0.80,
             alpha: float = 0.05) -> float:
    z = norm.ppf(1 - alpha / 2) + norm.ppf(puissance)
    return 2 * (p * p * s1 + (1 - p) ** 2 * s0) * z * z / (delta * delta)


def analyser(fiches_t1: dict, fiches_b: dict, cas: dict, p: float, delta: float = DELTA_UTILE) -> dict:
    v = variances_par_strate(fiches_t1, fiches_b, cas)
    res = {"strates": v, "p": p, "delta_utile": delta}
    if all(v[y]["differences_non_nulles"] == 0 for y in (1, 0)):
        res["conclusion"] = "aucune différence entre T1 et B au pilote : puissance non calculable, décision humaine"
        return res
    res["n_plug_in"] = math.ceil(effectif(p, v[1]["variance"], v[0]["variance"], delta))
    res["n_majore"] = math.ceil(effectif(p, v[1]["variance_haute_90"], v[0]["variance_haute_90"], delta))
    res["strates_sans_difference"] = [y for y in (1, 0) if v[y]["differences_non_nulles"] == 0]
    res["conclusion"] = ("300 cas suffisent" if res["n_majore"] <= 300 else
                         f"300 cas ne suffisent pas : {res['n_majore']} requis (borne majorée)")
    return res
