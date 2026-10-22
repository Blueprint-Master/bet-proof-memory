"""Palier 1 de la boucle de supervision : modèle de prévision dédié, sans information postérieure à t0.

Spécification : methode/boucle-de-supervision.md (note gelée le 21/10/2026), section 7.2.

L'outil de prévision servi aux systèmes B, T1 et D pour les cas du 30/09/2020 ne doit avoir
vu aucune issue postérieure à cette date, ni dans son ajustement ni dans sa spécification.
Toute la chaîne est donc refaite sur la seule origine 2018 (issues closes le 31/03/2020) :

  1. Contrôles de provenance automatiques (dates des apprentissages, des issues, des avis
     de dépôt) ; un contrôle en échec arrête le calcul.
  2. R2 (P5) ajusté sur l'origine 2018, horizon 548 jours ; sa pénalité lambda* est choisie
     par sa propre validation croisée, interne à 2018.
  3. Validation croisée interne : 5 plis formés par grappes de division NAF ; répartition des
     divisions tirée avec une graine, équilibrée sur le nombre de défaillants (ordre aléatoire,
     chaque division va au pli qui compte le moins de défaillants). Dans chaque pli, R2 (lambda*
     fixé) et le témoin (P5 bis) sont réajustés sur les quatre autres plis ; chaque candidat
     du premier cycle est évalué seul, comme en P7.
  4. Admission d'un candidat pour une répartition : perte moyenne réduite sur l'ensemble des
     plis ET perte réduite sur au moins 4 plis sur 5. Stabilité : 20 répartitions ; entrent
     dans le modèle dédié les candidats admis dans au moins 15 répartitions sur 20.
  5. Modèle final : R2 et assemblage des candidats retenus, ajustés sur toute l'origine 2018 ;
     prévisions à t0 pour les cas de l'origine 2020, écrites avec leur empreinte.

Choix de conception déclarés : lambda* de R2 est choisi une fois sur toute l'origine 2018 puis
fixé dans les plis (sélection interne à 2018, sans fuite temporelle, avec un léger optimisme) ;
la perte est celle de P6 avec la LGD fournie, traitée comme paramètre du scénario.

Mode --chrono : un pli, R2, le témoin et un candidat, pour estimer la durée totale avant de
lancer le calcul complet. Aucun fichier de prévision n'est écrit dans ce mode.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time

# Un seul fil de calcul par processus : avec plusieurs processus, les fils des bibliothèques
# numériques se disputent les cœurs (charge 46 pour 12 cœurs observée le 22/10/2026).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import critere as cr  # noqa: E402
import references as rf  # noqa: E402
from cycle import groupes_de_colonnes, matrice  # noqa: E402
from lgd import seuils  # noqa: E402
from references import DOSSIER_DEFAUT, sha256_fichier  # noqa: E402

ORIGINE_APP = 2018
ORIGINE_CIBLE = 2020
HORIZON = 548
PLIS_INTERNES = 5
ADMISSION_PLIS = 4
REPARTITIONS = 20
STABILITE = 15
GRAINE = 20261022
T0_CIBLE = dt.date(ORIGINE_CIBLE, 9, 30)

DONNEES = {}


# --- Contrôles de provenance ----------------------------------------------------------

def controles(d_app: dict, d_cible: dict) -> list:
    """Contrôles automatiques ; chacun : nom, résultat (bool), détail."""
    out = []
    origines = sorted(set(int(o) for o in d_app["origine"]))
    out.append({"nom": "apprentissage limité à l'origine 2018", "ok": origines == [ORIGINE_APP],
                "detail": f"origines lues : {origines}"})
    fin = dt.date(ORIGINE_APP, 9, 30) + dt.timedelta(days=HORIZON)
    out.append({"nom": "fenêtre d'issue de l'apprentissage close avant t0 cible", "ok": fin < T0_CIBLE,
                "detail": f"fin de fenêtre {fin.isoformat()}, t0 cible {T0_CIBLE.isoformat()}"})
    y = rf.etiquette(d_app, HORIZON)
    dates = [di for di, yy in zip(d_app["date_issue"], y) if yy == 1 and di is not None]
    dmax = max(dates) if dates else None
    out.append({"nom": "issues d'apprentissage toutes antérieures à t0 cible",
                "ok": dmax is None or dmax < T0_CIBLE, "detail": f"issue la plus tardive comptée : {dmax}"})
    for nom, dd in (("apprentissage", d_app), ("cible", d_cible)):
        par, t0 = dd.get("parution_avis"), dd.get("t0")
        if par is None or t0 is None:
            out.append({"nom": f"avis de dépôt antérieurs à t0 ({nom})", "ok": False, "detail": "colonne absente"})
            continue
        connus = [(p, t) for p, t in zip(par, t0) if p is not None]
        tardifs = sum(1 for p, t in connus if not p < t)
        out.append({"nom": f"avis de dépôt antérieurs à t0 ({nom})", "ok": tardifs == 0,
                    "detail": f"{tardifs} avis non antérieurs sur {len(connus)} renseignés ; "
                              f"{len(par) - len(connus)} non renseignés"})
    origines_c = sorted(set(int(o) for o in d_cible["origine"]))
    out.append({"nom": "cible limitée à l'origine 2020", "ok": origines_c == [ORIGINE_CIBLE],
                "detail": f"origines cibles : {origines_c}"})
    return out


# --- Répartitions par division NAF ------------------------------------------------------

def repartition(naf2: np.ndarray, y: np.ndarray, graine: int, k: int = PLIS_INTERNES) -> np.ndarray:
    """Numéro de pli (0..k-1) par cas ; une division NAF entière va dans un seul pli.

    Ordre des divisions aléatoire (graine) ; chaque division va au pli qui compte le moins de
    défaillants, puis le moins de cas."""
    div = np.array([n if n not in (None, "") else "?" for n in naf2], dtype=object)
    labels, inv = np.unique(div.astype(str), return_inverse=True)
    if len(labels) < k:
        raise ValueError(f"{len(labels)} divisions NAF pour {k} plis")
    defauts = np.bincount(inv, y, minlength=len(labels))
    cas = np.bincount(inv, minlength=len(labels))
    ordre = np.random.default_rng(graine).permutation(len(labels))
    pli_div, charge_d, charge_n = np.zeros(len(labels), int), np.zeros(k), np.zeros(k)
    for j in ordre:
        f = min(range(k), key=lambda q: (charge_d[q], charge_n[q], q))
        pli_div[j] = f
        charge_d[f] += defauts[j]
        charge_n[f] += cas[j]
    return pli_div[inv]


def admis_repartition(deltas: list, pooled: float) -> bool:
    """Perte moyenne réduite et perte réduite sur au moins ADMISSION_PLIS plis."""
    return pooled > 0 and sum(1 for x in deltas if x is not None and x > 0) >= ADMISSION_PLIS


# --- R2 à pénalité fixée ------------------------------------------------------------------

class R2Fixe(rf.R2):
    """R2 avec lambda imposé ; si le contrôle de séparation échoue, valeur suivante de la grille."""

    def __init__(self, horizon: int, lam: float):
        super().__init__(horizon)
        self.lam_impose = lam

    def ajuster(self, d: dict, y_horizon: np.ndarray):
        import warnings

        from sklearn.exceptions import ConvergenceWarning

        self.matrice = rf.Matrice().ajuster(d)
        x = self.matrice.construire(d)
        xp, yp, _g, self.k_max = rf.personne_periode(x, d["jours_issue"], y_horizon, self.horizon)
        self.retraits = []
        for lam in [l for l in rf.GRILLE_LAMBDA if l >= self.lam_impose]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                m = self._logit(lam, xp.shape[0]).fit(xp, yp)
            if self._valide(m, lam) and not (lam == 0 and self._extreme(m, xp)):
                self.lam, self.modele = lam, m
                break
            self.retraits.append({"lambda": lam, "etape": "ajustement de pli"})
        else:
            raise RuntimeError("R2 non ajustable dans un pli")
        self.p_x = x.shape[1]
        return self


# --- Préparation des plis -------------------------------------------------------------------

def sous(d: dict, m: np.ndarray) -> dict:
    return {k: v[m] for k, v in d.items()}


def preparer(app: dict, cand_app: dict, plis: np.ndarray, lam: float, scen: list) -> list:
    """Pour chaque pli : R2 (lambda fixé) et témoin réajustés hors du pli, coûts du témoin dans le pli."""
    out = []
    y = rf.etiquette(app, HORIZON)
    for f in range(PLIS_INTERNES):
        mv, ma = plis == f, plis != f
        a, v = sous(app, ma), sous(app, mv)
        r2 = R2Fixe(HORIZON, lam).ajuster(a, y[ma])
        ea, ev = r2.eta(a), r2.eta(v)
        tem = cr.Temoin().ajuster(ea, a["jours_issue"], y[ma], HORIZON)
        out.append({"ma": ma, "mv": mv, "y_a": y[ma], "y_v": y[mv], "eta_a": ea, "eta_v": ev,
                    "siren_a": a["siren"], "jours_a": a["jours_issue"],
                    "couts_temoin": cr.couts(tem.predire(ev), y[mv], scen), "r2_lambda": r2.lam,
                    "r2_retraits": r2.retraits})
    return out


def evaluer_candidat_plis(colonnes: tuple, plis_prep: list, cand_app: dict, scen: list) -> dict:
    deltas, num, den = [], 0.0, 0
    for P in plis_prep:
        ca = np.column_stack([cand_app[c][P["ma"]] for c in colonnes])
        cv = np.column_stack([cand_app[c][P["mv"]] for c in colonnes])
        xa, xv = matrice(ca, cv)
        if xa is None:
            deltas.append(None)
            continue
        a = cr.Assemblage().ajuster(P["eta_a"], xa, P["siren_a"], P["jours_a"], P["y_a"], HORIZON)
        diff = P["couts_temoin"] - cr.couts(a.predire(P["eta_v"], xv), P["y_v"], scen)
        deltas.append(None if a.reduit_au_temoin else float(diff.mean()))
        if not a.reduit_au_temoin:
            num += float(diff.sum())
        den += len(diff)
    pooled = num / den if den else 0.0
    return {"deltas": deltas, "pooled": pooled, "admis": admis_repartition(deltas, pooled)}


def _tache(args):
    nom, colonnes = args
    return nom, evaluer_candidat_plis(colonnes, DONNEES["plis"], DONNEES["cand_app"], DONNEES["scen"])


def carte(fonction, items, processus: int):
    if processus > 1:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(processus, mp_context=mp.get_context("fork")) as ex:
            yield from ex.map(fonction, items)
    else:
        yield from map(fonction, items)


# --- Programme ----------------------------------------------------------------------------

def journal(msg: str):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def main(argv=None) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dossier", default=DOSSIER_DEFAUT)
    p.add_argument("--lgd", required=True)
    p.add_argument("--candidats", default="candidats-c1.parquet")
    p.add_argument("--processus", type=int, default=2)
    p.add_argument("--repartitions", type=int, default=REPARTITIONS)
    p.add_argument("--chrono", action="store_true")
    args = p.parse_args(argv)
    debut = time.time()

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

    m_app, m_cib = d["origine"] == ORIGINE_APP, d["origine"] == ORIGINE_CIBLE
    app, cib = sous(d, m_app), sous(d, m_cib)
    cand_app = {k: v[m_app] for k, v in cand.items()}
    cand_cib = {k: v[m_cib] for k, v in cand.items()}
    ctl = controles(app, cib)
    for c in ctl:
        journal(f"contrôle {'OK ' if c['ok'] else 'ÉCHEC'} {c['nom']} : {c['detail']}")
    if not all(c["ok"] for c in ctl):
        journal("arrêt : un contrôle de provenance a échoué")
        return 2

    scen = seuils(lgd, cr.PI_PRIMAIRE, HORIZON)["retenus"]
    y_app = rf.etiquette(app, HORIZON)
    journal(f"apprentissage : {len(y_app)} cas, {int(y_app.sum())} défaillants ; cible : {len(cib['siren'])} cas")
    t1 = time.time()
    r2 = rf.R2(HORIZON).ajuster(app, y_app)
    t_r2_cv = time.time() - t1
    journal(f"R2 sur 2018 : lambda* = {r2.lam} ({t_r2_cv:.0f} s)")

    DONNEES["cand_app"], DONNEES["scen"] = cand_app, scen
    n_rep = 1 if args.chrono else args.repartitions
    resultats = {k: [] for k in groupes}
    infos_rep = []
    for r in range(n_rep):
        plis = repartition(app["naf2"], y_app, GRAINE + r)
        t1 = time.time()
        DONNEES["plis"] = preparer(app, cand_app, plis, r2.lam, scen)
        t_prep = time.time() - t1
        infos_rep.append({"graine": GRAINE + r,
                          "defaillants_par_pli": [int(y_app[plis == f].sum()) for f in range(PLIS_INTERNES)],
                          "cas_par_pli": [int((plis == f).sum()) for f in range(PLIS_INTERNES)],
                          "r2_lambda_par_pli": [P["r2_lambda"] for P in DONNEES["plis"]]})
        journal(f"répartition {r + 1}/{n_rep} préparée ({t_prep:.0f} s) : défaillants par pli "
                f"{infos_rep[-1]['defaillants_par_pli']}")
        if args.chrono:
            nom0 = next(iter(groupes))
            t1 = time.time()
            _tache((nom0, groupes[nom0]))
            t_cand = time.time() - t1
            total = t_r2_cv + args.repartitions * (t_prep + len(groupes) * t_cand / max(1, args.processus))
            journal(f"chrono : préparation d'une répartition {t_prep:.0f} s ; un candidat sur 5 plis {t_cand:.0f} s")
            journal(f"estimation pour {args.repartitions} répartitions, {len(groupes)} candidats, "
                    f"{args.processus} processus : {total / 3600:.1f} h")
            return 0
        for nom, res in carte(_tache, groupes.items(), args.processus):
            resultats[nom].append(res)
        journal(f"répartition {r + 1}/{n_rep} évaluée")

    stab = {k: sum(1 for x in v if x["admis"]) for k, v in resultats.items()}
    retenus = [k for k in groupes if stab[k] >= STABILITE * n_rep / REPARTITIONS]
    journal(f"retenus ({STABILITE}/{REPARTITIONS} au moins) : {retenus}")

    # modèle final sur toute l'origine 2018
    eta_app, eta_cib = r2.eta(app), r2.eta(cib)
    tem = cr.Temoin().ajuster(eta_app, app["jours_issue"], y_app, HORIZON)
    p_tem = tem.predire(eta_cib)
    cols = tuple(c for k in retenus for c in groupes[k])
    final = {"candidats": retenus, "colonnes": list(cols), "reduit_au_temoin": True}
    p_ded = p_tem
    if cols:
        ca = np.column_stack([cand_app[c] for c in cols])
        cc = np.column_stack([cand_cib[c] for c in cols])
        xa, xc = matrice(ca, cc)
        a = cr.Assemblage().ajuster(eta_app, xa, app["siren"], app["jours_issue"], y_app, HORIZON)
        p_ded = a.predire(eta_cib, xc)
        final.update({"reduit_au_temoin": a.reduit_au_temoin, "lambda": a.lam, "retraits": a.retraits,
                      "gamma": None if a.reduit_au_temoin else [float(x) for x in a.g],
                      "moyennes": [float(x) for x in a.moy], "ecarts_types": [float(x) for x in a.ect],
                      "a": None if a.reduit_au_temoin else [float(x) for x in a.a],
                      "b": None if a.reduit_au_temoin else float(a.b)})

    horodatage = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
    sortie_p = os.path.join(args.dossier, f"prevision-dediee-2020-{horodatage}.parquet")
    pq.write_table(pa.table({"siren": list(cib["siren"]), "origine": [int(o) for o in cib["origine"]],
                             "p_temoin": p_tem, "p_dedie": p_ded}), sortie_p)
    rapport = {
        "specification": "methode/boucle-de-supervision.md, section 7.2 (note gelée le 21/10/2026)",
        "controles_provenance": ctl,
        "apprentissage": {"origine": ORIGINE_APP, "cas": int(len(y_app)), "defaillants": int(y_app.sum()),
                          "horizon_jours": HORIZON},
        "R2": {"lambda": r2.lam, "scores_cv": {str(k): v for k, v in r2.scores_cv.items()}, "retraits": r2.retraits},
        "temoin": {"a": [float(x) for x in tem.a], "b": float(tem.b)},
        "lgd_parametre_du_scenario": lgd, "scenarios": scen,
        "regles": {"plis": PLIS_INTERNES, "admission": f"perte moyenne réduite et {ADMISSION_PLIS} plis sur "
                   f"{PLIS_INTERNES}", "repartitions": n_rep, "stabilite": f"{STABILITE} sur {REPARTITIONS}",
                   "graine": GRAINE},
        "repartitions": infos_rep,
        "candidats": {k: {"admissions": stab[k], "par_repartition": v} for k, v in resultats.items()},
        "modele_final": final,
        "cible": {"origine": ORIGINE_CIBLE, "cas": int(len(p_ded)), "p_dedie_moyenne": float(np.mean(p_ded)),
                  "p_temoin_moyenne": float(np.mean(p_tem)), "fichier": os.path.basename(sortie_p),
                  "sha256": sha256_fichier(sortie_p)},
        "entrees": {"cas-dev.parquet": sha256_fichier(chemin), args.candidats: sha256_fichier(chemin_c),
                    os.path.basename(args.lgd): sha256_fichier(args.lgd)},
        "code": {n: sha256_fichier(os.path.join(ICI, n)) for n in ("modele_dedie.py", "cycle.py", "critere.py",
                                                                  "references.py", "lgd.py")},
        "duree_secondes": round(time.time() - debut),
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"
    sortie = os.path.join(args.dossier, f"modele-dedie-{horodatage}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(texte)
    print("candidat;admissions_sur_" + str(n_rep), file=sys.stderr)
    for k in groupes:
        print(f"{k};{stab[k]}", file=sys.stderr)
    print(f"\nModèle final : {retenus or 'témoin seul'}", file=sys.stderr)
    print(f"Prévisions 2020 : {sortie_p}\nSHA-256 : {rapport['cible']['sha256']}", file=sys.stderr)
    print(f"Rapport : {sortie}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
