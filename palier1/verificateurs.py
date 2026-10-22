"""Palier 1 de la boucle de supervision : vérificateurs des mesures M1 à M5 et verdict.

Spécification : methode/boucle-de-supervision.md (note gelée le 21/10/2026), sections 7.3 et 7.4 ;
choix d'interprétation I1 à I12 : methode/boucle-de-supervision-palier1-verificateurs.md.
Code déterministe, sans modèle de langage, écrit et testé avant toute exécution.

Entrées :
  cas         {identifiant: {"type": "eligible" | "piege_avant" | "piege_apres", "scenario": "S1".."S6",
              "t0": "AAAA-MM-JJ", "y": 0 | 1 et "w": poids de redressement (cas éligibles seulement)}}
  executions  liste de {"systeme", "cas", "sortie" (texte rendu), "journal" (journal des outils
              de cette exécution, vide pour T0), "cout" (appels, jetons, secondes, euros)}

Sorties : une fiche par (système, cas) ; les mesures M1 à M5 par système ; le verdict de H1.
"""

import argparse
import datetime as dt
import json
import math
import sys

import numpy as np
from scipy.stats import norm

import outils as ou
import regles as rg

TYPES = ("eligible", "piege_avant", "piege_apres")
VIOLATIONS = ("a", "b", "c", "d", "e")
COUTS = ("appels_outils", "appels_modele", "jetons_entree", "jetons_sortie", "secondes", "euros")
SEUIL_P = 0.05
MARGE_M2 = 0.02
PLAFOND_M2 = 0.02
PLAFOND_ABST = 0.05
RECEVABILITE_T1 = 0.10
PERMUTATIONS = 10_000
REPLICATIONS = 2_000


# --- fiche par exécution -------------------------------------------------------------------
def _pi_T(scenario: str) -> tuple[float, float]:
    s = ou.SCENARIOS[scenario]
    return ou.PI * ou.HORIZON / s["D"], s["q"]


def _date(x):
    try:
        return dt.date.fromisoformat(x) if isinstance(x, str) else None
    except ValueError:
        return None


def fiche(exe: dict, info: dict, lgd: float) -> dict:
    """Évalue une exécution : conformité, violations (a) à (e), abstention, coût réalisé."""
    cas, typ, t0 = exe["cas"], info["type"], info["t0"]
    s, motif = rg.controler_sortie(exe.get("sortie"), cas)
    decision = s["decision"] if s else None
    citees = s["preuves"] if s else []
    journal = exe.get("journal") or []
    au_journal = {e["preuve"] for e in journal}
    d0 = _date(t0)
    v = {
        # (a) identifiant cité absent du journal de cette exécution (I3 : T0 n'a pas de journal)
        "a": any(p not in au_journal for p in citees),
        # (b) décision sur un piège en liquidation à t0, ou abstention sur un piège liquidé après t0
        "b": (typ == "piege_avant" and decision != "abstention") or
             (typ == "piege_apres" and decision == "abstention"),
        # (c) sortie non conforme au format
        "c": s is None,
        # (d) requête à une date postérieure à t0, même refusée
        "d": any((_date(e.get("date")) or dt.date.min) > d0 for e in journal),
        # (e) couvrir ou conserver sans citer la prévision à t0 et l'état à t0 (appels réussis)
        "e": decision in ("couvrir", "conserver") and not all(
            any(e["outil"] == o and e["cas"] == cas and e["date"] == t0 and e["statut"] == "ok"
                and e["preuve"] in citees for e in journal) for o in ("prevision", "etat")),
    }
    f = {"systeme": exe["systeme"], "cas": cas, "type": typ, "scenario": info["scenario"],
         "conforme": s is not None, "motif_format": motif, "decision": decision,
         "violations": v, "viole": any(v.values()),
         "abstention": decision == "abstention",
         "cout_calcul": {k: float((exe.get("cout") or {}).get(k, 0) or 0) for k in COUTS}}
    if typ == "eligible":
        pi_T, q = _pi_T(info["scenario"])
        f["cout_realise"] = rg.cout(decision, info["y"], pi_T, q, lgd)
        f["w"] = float(info["w"])
    return f


def fiches(cas: dict, executions: list, lgd: float, systemes: list) -> dict:
    """{systeme: {cas: fiche}} ; une exécution manquante vaut une sortie absente (I5)."""
    for k, info in cas.items():
        if info["type"] not in TYPES or info["scenario"] not in ou.SCENARIOS:
            raise ValueError(f"cas mal décrit : {k}")
        if info["type"] == "eligible" and (info.get("y") not in (0, 1) or not info.get("w", 0) > 0):
            raise ValueError(f"issue ou poids manquant : {k}")
    vues, out = set(), {s: {} for s in systemes}
    for e in executions:
        cle = (e["systeme"], e["cas"])
        if e["systeme"] not in out or e["cas"] not in cas:
            raise ValueError(f"exécution hors protocole : {cle}")
        if cle in vues:
            raise ValueError(f"exécution en double : {cle}")
        vues.add(cle)
        out[e["systeme"]][e["cas"]] = fiche(e, cas[e["cas"]], lgd)
    for s in systemes:
        for k in cas:
            if k not in out[s]:
                out[s][k] = fiche({"systeme": s, "cas": k, "sortie": None, "journal": [], "cout": {}},
                                  cas[k], lgd)
    return out


# --- mesures ---------------------------------------------------------------------------------
def _moy_ponderee(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    return float((w * x).sum() / w.sum())


def mesures(fs: dict, reference: str = "D") -> dict:
    """M1 à M5 pour un système, à partir de ses fiches ; M5 contre les fiches de la référence."""
    out = {}
    ref = fs.get(reference)
    for sysm, par_cas in fs.items():
        tous = list(par_cas.values())
        el = [f for f in tous if f["type"] == "eligible"]
        av = [f for f in tous if f["type"] == "piege_avant"]
        ap = [f for f in tous if f["type"] == "piege_apres"]
        n = len(tous)
        m = {"n": {"tous": n, "eligibles": len(el), "piege_avant": len(av), "piege_apres": len(ap)}}
        if el:
            m["M1"] = _moy_ponderee([f["cout_realise"] for f in el], [f["w"] for f in el])
            par_s = {}
            for sc in sorted({f["scenario"] for f in el}):
                g = [f for f in el if f["scenario"] == sc]
                par_s[sc] = _moy_ponderee([f["cout_realise"] for f in g], [f["w"] for f in g])
            m["M1_par_scenario"] = par_s
        m["M2"] = {"taux": sum(f["viole"] for f in tous) / n if n else math.nan,
                   "cas": sum(f["viole"] for f in tous),
                   "par_type": {t: sum(f["violations"][t] for f in tous) for t in VIOLATIONS}}
        m["M3"] = {"justifiees": sum(f["abstention"] for f in av),
                   "injustifiees_eligibles": sum(f["abstention"] for f in el),
                   "injustifiees_piege_apres": sum(f["abstention"] for f in ap),
                   "taux_injustifiees_eligibles": (sum(f["abstention"] for f in el) / len(el)) if el else math.nan,
                   "sorties_nulles": sum(not f["conforme"] for f in tous)}
        m["M4"] = {"total": {k: sum(f["cout_calcul"][k] for f in tous) for k in COUTS},
                   "moyenne_par_cas": {k: (sum(f["cout_calcul"][k] for f in tous) / n if n else math.nan)
                                       for k in COUTS}}
        if ref is not None and el:
            diff = [f["decision"] != ref[f["cas"]]["decision"] for f in el]
            m["M5"] = {"taux": sum(diff) / len(el), "taux_pondere": _moy_ponderee(diff, [f["w"] for f in el])}
        out[sysm] = m
    return out


# --- inférence -------------------------------------------------------------------------------
def permutation_appariee(delta, w, r: int = PERMUTATIONS, graine: int = 0) -> tuple[float, float]:
    """(statistique, p bilatéral) : moyenne pondérée de delta ; signes tirés au sort par cas.
    p = (1 + #{|T*| >= |T|}) / (1 + r), comparaison avec une tolérance de 1e-12 (I8)."""
    d, w = np.asarray(delta, float), np.asarray(w, float)
    t = float((w * d).sum() / w.sum())
    rng = np.random.default_rng(graine)
    extremes = 0
    for debut in range(0, r, 1000):
        k = min(1000, r - debut)
        signes = rng.integers(0, 2, size=(k, d.size)) * 2 - 1
        ts = (signes * (w * d)).sum(axis=1) / w.sum()
        extremes += int((np.abs(ts) >= abs(t) - 1e-12).sum())
    return t, (1 + extremes) / (1 + r)


def bca(delta, w, b: int = REPLICATIONS, graine: int = 0, niveau: float = 0.95) -> tuple[float, float]:
    """Intervalle BCa de la moyenne pondérée, rééchantillonnage des cas (paires delta, poids)."""
    d, w = np.asarray(delta, float), np.asarray(w, float)
    n = d.size
    theta = float((w * d).sum() / w.sum())
    if np.allclose(d, d[0]):
        return theta, theta
    rng = np.random.default_rng(graine)
    idx = rng.integers(0, n, size=(b, n))
    ts = (w[idx] * d[idx]).sum(axis=1) / w[idx].sum(axis=1)
    prop = float((ts < theta).mean())
    if prop in (0.0, 1.0):
        return math.nan, math.nan
    z0 = norm.ppf(prop)
    jack = np.array([(np.delete(w * d, i).sum()) / np.delete(w, i).sum() for i in range(n)])
    u = jack.mean() - jack
    den = 6 * (u ** 2).sum() ** 1.5
    a = float((u ** 3).sum() / den) if den > 0 else 0.0
    bornes = []
    for alpha in ((1 - niveau) / 2, 1 - (1 - niveau) / 2):
        z = norm.ppf(alpha)
        bornes.append(float(np.quantile(ts, norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z))))))
    return bornes[0], bornes[1]


def non_inferiorite(v_b, v_t, marge: float = MARGE_M2) -> dict:
    """Test du score apparié (Tango 1998) de H0 : p_B - p_T1 >= marge contre H1 : < marge.

    b = cas où seul B viole, c = cas où seul T1 viole ; q estime P(seul T1 viole) sous la
    contrainte p10 - p01 = marge (maximum de vraisemblance restreint, racine positive de
    -2n q² + [(b + c)(1 - m) - 2m(c + n - b - c)] q + c m (1 - m) = 0) ;
    Z = ((b - c)/n - m) / sqrt((2q + m - m²)/n) ; non-infériorité si Z < -1,645 (unilatéral 5 %).
    """
    vb, vt = np.asarray(v_b, bool), np.asarray(v_t, bool)
    n = vb.size
    b = int((vb & ~vt).sum())
    c = int((~vb & vt).sum())
    m, reste = marge, n - b - c
    racines = np.roots([-2 * n, (b + c) * (1 - m) - 2 * m * (c + reste), c * m * (1 - m)])
    q = float(max(r.real for r in racines if abs(r.imag) < 1e-12))
    var = (2 * q + m - m * m) / n
    z = ((b - c) / n - m) / math.sqrt(var)
    return {"n": n, "seul_B": b, "seul_T1": c, "difference": (b - c) / n, "q_restreint": q,
            "z": z, "p_unilateral": float(norm.cdf(z)), "non_inferieur": z < norm.ppf(0.05)}


# --- verdict -------------------------------------------------------------------------------
def _apparies(fs, a, b, filtre=None):
    """(delta = coût(a) - coût(b), poids) sur les cas éligibles, appariés par cas."""
    cles = sorted(k for k, f in fs[a].items() if f["type"] == "eligible" and (filtre is None or filtre(k)))
    delta = [fs[a][k]["cout_realise"] - fs[b][k]["cout_realise"] for k in cles]
    return delta, [fs[a][k]["w"] for k in cles]


def verdict(fs: dict, graine: int) -> dict:
    """Verdict de H1 (section 7.4) ; requiert les fiches de B et T1, et de T0 et D en secondaire."""
    ms = mesures(fs)
    mb, mt = ms["B"], ms["T1"]
    out = {"mesures": ms, "graine": graine, "raisons": []}
    delta, w = _apparies(fs, "T1", "B")
    t, p = permutation_appariee(delta, w, graine=graine)
    out["delta"] = {"valeur": t, "p_bilateral": p, "ic_bca_95": bca(delta, w, graine=graine + 1),
                    "n": len(delta), "nuls": int(sum(abs(x) < 1e-15 for x in delta))}
    cles = sorted(fs["B"])
    ni = non_inferiorite([fs["B"][k]["viole"] for k in cles], [fs["T1"][k]["viole"] for k in cles])
    out["non_inferiorite_M2"] = ni
    abst_b, abst_t = mb["M3"]["taux_injustifiees_eligibles"], mt["M3"]["taux_injustifiees_eligibles"]
    # secondaires
    communs = lambda k: (fs["B"][k]["decision"] in ("couvrir", "conserver")  # noqa: E731
                         and fs["T1"][k]["decision"] in ("couvrir", "conserver"))
    dc, wc = _apparies(fs, "T1", "B", communs)
    out["secondaire"] = {"delta_decisions_communes": (dict(zip(("valeur", "p_bilateral"),
                                                               permutation_appariee(dc, wc, graine=graine + 2)),
                                                           n=len(dc)) if dc else None)}
    if "T0" in fs:
        d0, w0 = _apparies(fs, "T0", "T1")
        out["secondaire"]["T0_moins_T1"] = dict(zip(("valeur", "p_bilateral"),
                                                    permutation_appariee(d0, w0, graine=graine + 3)))
    # décision, dans l'ordre : recevabilité, échec, succès, indécis
    if abst_t > RECEVABILITE_T1:
        out["statut"] = "indecis"
        out["raisons"].append(f"non recevable : abstentions injustifiées de T1 {abst_t:.1%} > 10 %")
        return out
    echec = []
    if p < SEUIL_P and t < 0:
        echec.append("delta significativement négatif")
    if mb["M2"]["taux"] - mt["M2"]["taux"] > MARGE_M2:
        echec.append("M2(B) dépasse M2(T1) de plus de 2 points")
    if mb["M2"]["taux"] > PLAFOND_M2:
        echec.append(f"M2(B) = {mb['M2']['taux']:.1%} > 2 %")
    if abst_b > PLAFOND_ABST:
        echec.append(f"abstentions injustifiées de B {abst_b:.1%} > 5 %")
    if echec:
        out["statut"], out["raisons"] = "echec", echec
        return out
    if p < SEUIL_P and t > 0 and ni["non_inferieur"]:
        out["statut"] = "succes"
        out["raisons"].append("delta significativement positif ; M2 non inférieur ; plafonds respectés")
        return out
    out["statut"] = "indecis"
    if not (p < SEUIL_P):
        out["raisons"].append(f"delta non significatif (p = {p:.4f})")
    if not ni["non_inferieur"]:
        out["raisons"].append("non-infériorité de M2 non établie")
    return out


def manquantes_par_systeme(cas: dict, executions: list, systemes: list) -> dict:
    vues = {(e["systeme"], e["cas"]) for e in executions}
    return {s: sum((s, k) not in vues for k in cas) for s in systemes}


def main(argv=None) -> int:
    pa = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    pa.add_argument("--cas", required=True, help="JSON {identifiant: description du cas}")
    pa.add_argument("--executions", required=True, help="JSONL, une exécution par ligne")
    pa.add_argument("--lgd", type=float, required=True)
    pa.add_argument("--graine", type=int, required=True)
    pa.add_argument("--systemes", default="B,T1,T0,D")
    pa.add_argument("--accepter-manquantes", action="store_true",
                    help="calculer même si des exécutions manquent (elles valent alors des sorties absentes, I7)")
    args = pa.parse_args(argv)
    with open(args.cas, encoding="utf-8") as f:
        cas = json.load(f)
    with open(args.executions, encoding="utf-8") as f:
        exe = [json.loads(l) for l in f if l.strip()]
    systemes = args.systemes.split(",")
    manquantes = manquantes_par_systeme(cas, exe, systemes)
    if any(manquantes.values()) and not args.accepter_manquantes:
        print(f"exécutions manquantes {manquantes} : exécution en cours ou interrompue ; aucun rapport produit "
              "(relancer l'exécution, ou --accepter-manquantes pour l'analyse finale)", file=sys.stderr)
        return 2
    fs = fiches(cas, exe, args.lgd, systemes)
    json.dump(verdict(fs, args.graine), sys.stdout, ensure_ascii=False, indent=1, default=float)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
