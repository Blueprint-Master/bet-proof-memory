"""Protocole Q1 v1.7.1, P7 : évaluation des mécanismes candidats d'un cycle sur le développement.

Pour chaque pli de P7 (365 j : 2018 -> 2019, 2018-2019 -> 2020 ; 548 j : 2018 -> 2020) :
R2 (P5) et le témoin (P5 bis) sont ajustés sur l'apprentissage du pli ; chaque candidat
est évalué SEUL (P7) : assemblage de P5 bis avec x réduit au candidat, réajusté sur
l'apprentissage du pli. Perte de P6 (scénarios primaires, T recalculé pour l'horizon).
Admission : la perte de l'assemblage est inférieure à celle du témoin sur les trois plis
(estimation ponctuelle) ; l'intervalle bootstrap par grappes NAF est publié à côté.
Un candidat dont une colonne est entièrement manquante sur l'apprentissage d'un pli n'est
pas calculable sur ce pli : il n'est pas admis.

Valeurs manquantes (R-a de la vérification du cycle 1) : une colonne contenant des NaN est
complétée par sa médiane d'apprentissage, et un indicateur de manquant est ajouté.

Enfin, l'assemblage de tous les candidats admis est évalué sur les trois plis, et la demi-
largeur de l'intervalle de Delta sur le pli 548 j est publiée (P6, précision indicative).
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

# Un seul fil de calcul par processus : avec plusieurs processus, les fils des bibliothèques
# numériques se disputent les cœurs (charge 46 pour 12 cœurs observée le 22/10/2026).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import critere as cr  # noqa: E402
import references as rf  # noqa: E402
from lgd import seuils  # noqa: E402
from references import DOSSIER_DEFAUT, sha256_fichier  # noqa: E402

DONNEES = {}


def matrice(cols_app: np.ndarray, cols_test: np.ndarray):
    """R-a : médiane d'apprentissage et indicateur pour les colonnes avec NaN ; None si une colonne est vide."""
    xa, xt = [], []
    for j in range(cols_app.shape[1]):
        a, t = cols_app[:, j], cols_test[:, j]
        manq = np.isnan(a)
        if manq.all():
            return None, None
        if manq.any() or np.isnan(t).any():
            med = float(np.median(a[~manq]))
            xa += [np.where(manq, med, a), manq.astype(float)]
            xt += [np.where(np.isnan(t), med, t), np.isnan(t).astype(float)]
        else:
            xa.append(a)
            xt.append(t)
    return np.column_stack(xa), np.column_stack(xt)


def preparer_pli(d: dict, cand: dict, pli: dict, lgd: float) -> dict:
    h = pli["horizon"]
    m_app, m_test = np.isin(d["origine"], pli["apprentissage"]), d["origine"] == pli["test"]
    app, test = {k: v[m_app] for k, v in d.items()}, {k: v[m_test] for k, v in d.items()}
    y_app, y_test = rf.etiquette(app, h), rf.etiquette(test, h)
    r2 = rf.R2(h).ajuster(app, y_app)
    eta_app, eta_test = r2.eta(app), r2.eta(test)
    temoin = cr.Temoin().ajuster(eta_app, app["jours_issue"], y_app, h)
    scen = seuils(lgd, cr.PI_PRIMAIRE, h)["retenus"]
    p_t = temoin.predire(eta_test)
    return {"pli": pli, "app": app, "y_app": y_app, "y_test": y_test, "eta_app": eta_app, "eta_test": eta_test,
            "scen": scen, "couts_temoin": cr.couts(p_t, y_test, scen),
            "grappe": cr.grappes(test["siren"], test["origine"], test["naf2"]), "origine_test": test["origine"],
            "cand_app": {k: v[m_app] for k, v in cand.items()}, "cand_test": {k: v[m_test] for k, v in cand.items()},
            "R2_lambda": r2.lam, "temoin_b": temoin.b}


def evaluer_candidat(nom: str, colonnes: tuple) -> dict:
    out = {}
    for nom_pli, P in DONNEES["plis"].items():
        ca = np.column_stack([P["cand_app"][c] for c in colonnes])
        ct = np.column_stack([P["cand_test"][c] for c in colonnes])
        xa, xt = matrice(ca, ct)
        if xa is None:
            out[nom_pli] = {"calculable": False}
            continue
        a = cr.Assemblage().ajuster(P["eta_app"], xa, P["app"]["siren"], P["app"]["jours_issue"], P["y_app"],
                                     P["pli"]["horizon"])
        p = a.predire(P["eta_test"], xt)
        diff = P["couts_temoin"] - cr.couts(p, P["y_test"], P["scen"])  # > 0 : l'assemblage coûte moins
        bs = cr.bootstrap_grappes(diff, P["origine_test"], P["grappe"])
        out[nom_pli] = {"calculable": True, "delta": bs["delta"], "ic95": bs["ic95"], "demi_largeur": bs["demi_largeur"],
                        "lambda": a.lam, "reduit_au_temoin": a.reduit_au_temoin, "retraits": a.retraits,
                        "gamma": None if a.reduit_au_temoin else [float(x) for x in a.g],
                        "colonnes_x": int(xa.shape[1])}
    out["admis"] = all(v.get("calculable") and v["delta"] > 0 and not v["reduit_au_temoin"]
                       for k, v in out.items() if k != "admis") and len(out) == len(DONNEES["plis"])
    return out


def _tache(args):
    return args[0], evaluer_candidat(*args)


def groupes_de_colonnes(noms: list) -> dict:
    """Candidat -> ses colonnes (le candidat et son indicateur « _absent » éventuel)."""
    g = {}
    for c in noms:
        g.setdefault(c[:-7] if c.endswith("_absent") else c, []).append(c)
    return {k: tuple(v) for k, v in g.items()}


def main(argv=None) -> int:
    import pyarrow.parquet as pq

    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--dossier", default=DOSSIER_DEFAUT)
    a.add_argument("--lgd", required=True)
    a.add_argument("--candidats", default="candidats-c1.parquet")
    a.add_argument("--processus", type=int, default=2)
    args = a.parse_args(argv)
    with open(args.lgd, encoding="utf-8") as f:
        lgd = json.load(f)["estimation"]["lgd"]
    chemin = os.path.join(args.dossier, "cas-dev.parquet")
    d = rf.charger(chemin)
    chemin_c = os.path.join(args.dossier, args.candidats)
    t = pq.read_table(chemin_c)
    if t.column("siren").to_pylist() != list(d["siren"]) or list(t.column("origine").to_pylist()) != list(d["origine"]):
        raise RuntimeError("candidats et cas non alignés")
    noms = [c for c in t.column_names if c not in ("siren", "origine")]
    cand = {c: np.asarray(t.column(c).to_numpy(zero_copy_only=False), dtype=float) for c in noms}
    groupes = groupes_de_colonnes(noms)
    print(f"[{dt.datetime.now():%H:%M:%S}] {len(groupes)} candidats", file=sys.stderr, flush=True)
    DONNEES["plis"] = {}
    for pli in rf.PLIS:
        if not rf.separation_respectee(pli):
            raise ValueError(pli["nom"])
        DONNEES["plis"][pli["nom"]] = preparer_pli(d, cand, pli, lgd)
        print(f"[{dt.datetime.now():%H:%M:%S}] pli {pli['nom']} prêt", file=sys.stderr, flush=True)
    res = {}
    if args.processus > 1:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(args.processus, mp_context=mp.get_context("fork")) as ex:
            for nom, r in ex.map(_tache, groupes.items()):
                res[nom] = r
                print(f"[{dt.datetime.now():%H:%M:%S}] {nom} admis={r['admis']}", file=sys.stderr, flush=True)
    else:
        for item in groupes.items():
            nom, r = _tache(item)
            res[nom] = r
            print(f"[{dt.datetime.now():%H:%M:%S}] {nom} admis={r['admis']}", file=sys.stderr, flush=True)
    admis = [k for k, v in res.items() if v["admis"]]
    ensemble = evaluer_candidat("ensemble", tuple(c for k in admis for c in groupes[k])) if admis else None
    rapport = {"lgd": lgd, "candidats": res, "admis": admis, "assemblage_des_admis": ensemble,
               "plis": {k: {"R2_lambda": v["R2_lambda"], "temoin_b": v["temoin_b"],
                            "perte_temoin": float(v["couts_temoin"].mean()), "n_test": int(len(v["y_test"]))}
                        for k, v in DONNEES["plis"].items()},
               "entrees": {"cas-dev.parquet": sha256_fichier(chemin), args.candidats: sha256_fichier(chemin_c),
                           os.path.basename(args.lgd): sha256_fichier(args.lgd)},
               "code": {n: sha256_fichier(os.path.join(ICI, n)) for n in ("cycle.py", "critere.py", "references.py",
                                                                         "lgd.py")},
               "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"
    sortie = os.path.join(args.dossier, f"evaluation-cycle-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(texte)
    plis = list(DONNEES["plis"])
    print("candidat;admis;" + ";".join(f"delta_{p}" for p in plis), file=sys.stderr)
    for k, v in res.items():
        print(f"{k};{v['admis']};" + ";".join("" if not v[p].get("calculable") else f"{v[p]['delta']:.7f}"
                                               for p in plis), file=sys.stderr)
    if ensemble:
        print("ensemble des admis;" + ";".join(f"{ensemble[p]['delta']:.7f} {ensemble[p]['ic95']}" for p in plis),
              file=sys.stderr)
    print(f"\nRapport : {sortie}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
