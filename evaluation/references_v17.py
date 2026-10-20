"""Protocole Q1 v1.7 : réévaluation des références sous le critère de P6, sur le développement.

Pour chaque pli de P7 (365 j : 2018 -> 2019, 2018-2019 -> 2020 ; 548 j : 2018 -> 2020) :
R0, R1, R2 (P5, grille avec lambda = 0) et le témoin de P5 bis (R2 recalibré) sont ajustés
sur l'apprentissage du pli et évalués sur l'origine testée :
  - perte de P6 (scénarios primaires, pi = 0,1 %, LGD de P6 ter, T recalculé pour l'horizon) ;
  - sensibilités : pi = 2 %, LGD basse et haute ; pondération par le total de bilan ;
  - écart de perte de chaque modèle au témoin, bootstrap par grappes de divisions NAF ;
  - décomposition MCB - DSC + UNC ; mesures classiques ; G du Brier (critère v1.6).
Aucun mécanisme candidat. Lit cas-dev.parquet et le rapport de lgd.py ; ne lit rien du scellé.

Pondération par le total de bilan : poids = exp(log_total_bilan) ; un cas dont le total est
absent, ou dont log_total_bilan vaut 0 (total <= 1 EUR, la construction ne conservant pas
le signe), est exclu de cette variante.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import critere as cr  # noqa: E402
import references as rf  # noqa: E402
from lgd import PI_SENSIBILITE, seuils  # noqa: E402
from references import DOSSIER_DEFAUT, sha256_fichier  # noqa: E402


def poids_bilan(d: dict) -> np.ndarray:
    ok = (d["total_bilan_absent"] == 0) & (np.nan_to_num(d["log_total_bilan"]) > 0)
    return np.where(ok, np.exp(np.nan_to_num(d["log_total_bilan"])), 0.0)


def evaluer_pli(d: dict, pli: dict, lgd: dict) -> dict:
    h = pli["horizon"]
    app, test = rf.sous_ensemble(d, pli["apprentissage"]), rf.sous_ensemble(d, (pli["test"],))
    y_app, y_test = rf.etiquette(app, h), rf.etiquette(test, h)
    print(f"[{dt.datetime.now():%H:%M:%S}] pli {pli['nom']} : {len(y_app)} / {len(y_test)}", file=sys.stderr, flush=True)
    r0 = rf.R0().ajuster(app, y_app)
    r1 = rf.R1().ajuster(app, y_app)
    r2 = rf.R2(h).ajuster(app, y_app)
    temoin = cr.Temoin().ajuster(r2.eta(app), app["jours_issue"], y_app, h)
    p = {"R0": r0.predire(test), "R1": r1.predire(test), "R2": r2.predire(test), "temoin": temoin.predire(r2.eta(test))}
    jeux = {"primaire": seuils(lgd["lgd"], cr.PI_PRIMAIRE, h),
            "pi_2%": seuils(lgd["lgd"], PI_SENSIBILITE, h),
            "lgd_bas": seuils(lgd["lgd_bas"], cr.PI_PRIMAIRE, h),
            "lgd_haut": seuils(lgd["lgd_haut"], cr.PI_PRIMAIRE, h)}
    grappe = cr.grappes(test["siren"], test["origine"], test["naf2"])
    w = poids_bilan(test)
    res = {"pli": pli, "R2_lambda": r2.lam, "R2_retraits": r2.retraits, "R2_validation_croisee": r2.scores_cv,
           "temoin": {"a": [float(x) for x in temoin.a], "b": temoin.b},
           "scenarios": jeux, "exclus_ponderation_bilan": int((w == 0).sum()), "modeles": {}}
    couts_t = {k: cr.couts(p["temoin"], y_test, v["retenus"]) for k, v in jeux.items() if v["retenus"]}
    for nom, pm in p.items():
        r = {"mesures": rf.mesures(y_test, pm), "pertes": {}, "ecart_au_temoin": {}}
        for k, v in jeux.items():
            if not v["retenus"]:
                r["pertes"][k] = None
                continue
            c = cr.couts(pm, y_test, v["retenus"])
            r["pertes"][k] = {"equipondere": float(c.mean()),
                              "par_scenario": [float(x) for x in cr.couts_par_scenario(pm, y_test, v["retenus"]).mean(axis=0)]}
            if nom != "temoin":
                diff = c - couts_t[k]  # > 0 : le modèle perd plus que le témoin
                r["ecart_au_temoin"][k] = cr.bootstrap_grappes(diff, test["origine"], grappe)
                if k == "primaire":
                    r["ecart_au_temoin"]["primaire_pondere_bilan"] = cr.bootstrap_grappes(
                        diff[w > 0], test["origine"][w > 0], grappe[w > 0], poids=w[w > 0])
        r["decomposition_primaire"] = cr.decomposition(pm, y_test, jeux["primaire"]["retenus"])
        if nom != "temoin":
            r["G_brier_temoin_contre_modele_v16"] = rf.gain_bootstrap(y_test, p["temoin"], pm)
        res["modeles"][nom] = r
    return res


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--dossier", default=DOSSIER_DEFAUT)
    a.add_argument("--lgd", required=True, help="rapport JSON de lgd.py")
    args = a.parse_args(argv)
    with open(args.lgd, encoding="utf-8") as f:
        lgd = json.load(f)["estimation"]
    chemin = os.path.join(args.dossier, "cas-dev.parquet")
    d = rf.charger(chemin)
    rapport = {"plis": {}, "lgd": lgd}
    for pli in rf.PLIS:
        if not rf.separation_respectee(pli):
            raise ValueError(f"pli {pli['nom']} contraire à la règle de séparation")
        rapport["plis"][pli["nom"]] = evaluer_pli(d, pli, lgd)
    rapport["entrees"] = {"cas-dev.parquet": sha256_fichier(chemin), os.path.basename(args.lgd): sha256_fichier(args.lgd)}
    rapport["code"] = {n: sha256_fichier(os.path.join(ICI, n))
                       for n in ("references_v17.py", "critere.py", "references.py", "lgd.py")}
    rapport["execute_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"
    sortie = os.path.join(args.dossier, f"evaluation-references-v17-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(texte)
    print("pli;modele;perte_primaire;ecart_au_temoin;ic95;MCB;DSC;UNC;brier;auc", file=sys.stderr)
    for nom, r in rapport["plis"].items():
        for m, v in r["modeles"].items():
            e = v["ecart_au_temoin"].get("primaire")
            dc = v["decomposition_primaire"]
            ecart = "" if e is None else f"{e['delta']:.6f}"
            ic = "" if e is None else e["ic95"]
            print(f"{nom};{m};{v['pertes']['primaire']['equipondere']:.6f};{ecart};{ic};"
                  f"{dc['MCB']:.6f};{dc['DSC']:.6f};{dc['UNC']:.6f};"
                  f"{v['mesures']['brier']:.6f};{v['mesures']['auc'] or float('nan'):.4f}", file=sys.stderr)
        print(f"{nom} : lambda R2 {r['R2_lambda']}, retraits {r['R2_retraits']}, témoin b = {r['temoin']['b']:.3f}",
              file=sys.stderr)
    print(f"\nRapport : {sortie}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
