"""Phase 5, étape 3 : évaluation des références R0, R1, R2 sur l'espace de développement (protocole Q1 v1.6).

Plis temporels (P7), qui respectent la règle de séparation de P4 (la fenêtre d'issue
des origines d'apprentissage se clôt au plus tard à l'origine testée) :
  365 jours : 2018 -> 2019 ; 2018 et 2019 -> 2020
  548 jours : 2018 -> 2020

Références (P5) :
  R0  taux de base par classe NAF niveau 2 x taille Banque de France x âge (moins de 3 ans,
      3 à 5, 5 à 10, 10 et plus), lissé vers le taux de la section NAF par un estimateur
      bêta-binomial ; la force du lissage m est choisie dans une grille fixe par maximum de
      vraisemblance marginale sur l'apprentissage.
  R1  Z'' d'Altman, Z = 6,56 X1 + 3,26 X2 + 6,72 X3 + 1,05 X4, composantes bornées aux 1er et
      99e centiles d'apprentissage (même règle que R2) et complétées par leur médiane
      d'apprentissage, recalibré par régression logistique sans pénalité (ordonnée et pente).
  R2  hasard à temps discret, intervalles ]0, 183], ]183, 365], ]365, 548] jours ; régression
      logistique L2 sur les variables de l'annexe A ; variables continues bornées aux 1er et
      99e centiles, médiane et indicateur pour les valeurs manquantes, centrées réduites ;
      NAF niveau 2 en indicatrices ; pénalité choisie par validation croisée en 5 parts
      groupées par SIREN dans la grille {1e-4, ..., 100}. La pénalité lambda s'applique à
      la log-vraisemblance MOYENNE : objectif = moyenne des pertes + lambda/2 ||w||^2,
      soit C = 1 / (lambda x nombre de lignes) dans scikit-learn.

Mesures (P6) : Brier (primaire), log-loss, AUC, calibration (ordonnée et pente), part des
défaillances dans le décile le plus risqué, courbe de fiabilité en 10 classes ; gain
G = 1 - Brier(modèle) / Brier(R2) avec intervalle bootstrap à 95 % groupé par SIREN
(1 000 tirages, graine fixée).

Lit cas-dev.parquet (étape 2) ; n'utilise que les origines retenues ; ne lit aucune donnée
du scellé.
"""

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "ingestion"))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
from construire import GROUPE1, GROUPE2, sha256_fichier  # noqa: E402
from extraire import DOSSIER_DEFAUT  # noqa: E402

PLIS = (
    {"nom": "365j-2018-vers-2019", "apprentissage": (2018,), "test": 2019, "horizon": 365},
    {"nom": "365j-2018-2019-vers-2020", "apprentissage": (2018, 2019), "test": 2020, "horizon": 365},
    {"nom": "548j-2018-vers-2020", "apprentissage": (2018,), "test": 2020, "horizon": 548},
)
INTERVALLES = ((0, 183), (183, 365), (365, 548))
GRILLE_LAMBDA = (1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0)
GRILLE_M = (1, 3, 10, 30, 100, 300, 1000, 3000)
ALTMAN = (6.56, 3.26, 6.72, 1.05)
TIRAGES = 1000
GRAINE = 20261020

CONTINUES = GROUPE1 + GROUPE2 + ("log_total_bilan", "age_ans", "retard_depot_jours", "log_chiffre_affaires",
                                 "resultat_net_sur_total_bilan", "intensite_sectorielle")
BINAIRES = ("total_bilan_absent", "cr_indisponible", "capitaux_propres_negatifs", "vetuste_absente",
            "confidentiel", "en_plan", "en_observation_sauvegarde")
SECTIONS_NAF = ((1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"),
                (45, 47, "G"), (49, 53, "H"), (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"),
                (69, 75, "M"), (77, 82, "N"), (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"),
                (94, 96, "S"), (97, 98, "T"), (99, 99, "U"))


def separation_respectee(pli: dict) -> bool:
    """Toute fenêtre d'issue d'apprentissage se clôt au plus tard à l'origine testée (P4)."""
    t_test = dt.date(pli["test"], 9, 30)
    return all(dt.date(a, 9, 30) + dt.timedelta(days=pli["horizon"]) <= t_test for a in pli["apprentissage"])


# --- Données -----------------------------------------------------------------

def charger(chemin: str) -> dict:
    import pyarrow.parquet as pq

    t = pq.read_table(chemin)
    d = {}
    for c in t.column_names:
        col = t.column(c)
        if c in CONTINUES + ("altman_x1", "altman_x2", "altman_x3", "altman_x4"):
            d[c] = np.asarray(col.to_numpy(zero_copy_only=False), dtype="float64")
        elif c in BINAIRES + ("origine", "issue", "origine_retenue"):
            d[c] = np.asarray(col.to_numpy(zero_copy_only=False), dtype="int64")
        else:
            d[c] = np.asarray(col.to_pylist(), dtype=object)
    retenue = d["origine_retenue"] == 1
    d = {k: v[retenue] for k, v in d.items()}
    t0 = np.array([dt.date(int(a), 9, 30) for a in d["origine"]], dtype=object)
    d["jours_issue"] = np.array([(di - t).days if di is not None else -1
                                 for di, t in zip(d["date_issue"], t0)], dtype="int64")
    return d


def sous_ensemble(d: dict, origines) -> dict:
    m = np.isin(d["origine"], list(origines))
    return {k: v[m] for k, v in d.items()}


def etiquette(d: dict, horizon: int) -> np.ndarray:
    return ((d["issue"] == 1) & (d["jours_issue"] > 0) & (d["jours_issue"] <= horizon)).astype("int64")


def section_naf(naf2) -> str:
    try:
        n = int(naf2)
    except (TypeError, ValueError):
        return "?"
    for a, b, s in SECTIONS_NAF:
        if a <= n <= b:
            return s
    return "?"


def tranche_age(age) -> str:
    if age is None or age != age:
        return "?"
    return "<3" if age < 3 else "3-5" if age < 5 else "5-10" if age < 10 else "10+"


# --- R0 -------------------------------------------------------------------------

class R0:
    def ajuster(self, d: dict, y: np.ndarray):
        from scipy.special import betaln

        cles = [(n, t, tranche_age(a)) for n, t, a in zip(d["naf2"], d["taille_bdf"], d["age_ans"])]
        cellules, sections = {}, {}
        for k, yi in zip(cles, y):
            c = cellules.setdefault(k, [0, 0])
            c[0] += int(yi)
            c[1] += 1
            s = sections.setdefault(section_naf(k[0]), [0, 0])
            s[0] += int(yi)
            s[1] += 1
        self.global_ = (y.sum() + 0.5) / (len(y) + 1)
        self.sections = {s: (k + 0.5) / (n + 1) for s, (k, n) in sections.items()}
        meilleur = None
        for m in GRILLE_M:
            ll = 0.0
            for (naf, _t, _a), (k, n) in cellules.items():
                p = self.sections.get(section_naf(naf), self.global_)
                a, b = m * p, m * (1 - p)
                ll += betaln(k + a, n - k + b) - betaln(a, b)
            if meilleur is None or ll > meilleur[0]:
                meilleur = (ll, m)
        self.m = meilleur[1]
        self.cellules = cellules
        return self

    def predire(self, d: dict) -> np.ndarray:
        out = np.empty(len(d["naf2"]))
        for i, (n, t, a) in enumerate(zip(d["naf2"], d["taille_bdf"], d["age_ans"])):
            p = self.sections.get(section_naf(n), self.global_)
            k, nn = self.cellules.get((n, t, tranche_age(a)), (0, 0))
            out[i] = (k + self.m * p) / (nn + self.m)
        return out


# --- Préparation commune (R1, R2) -----------------------------------------------

class Bornes:
    """Bornes aux 1er et 99e centiles, médiane pour les manquants, centrage-réduction ; tout appris sur l'apprentissage."""

    def ajuster(self, x: np.ndarray):
        ok = ~np.isnan(x)
        v = x[ok] if ok.any() else np.array([0.0])
        self.bas, self.haut = np.percentile(v, [1, 99])
        self.mediane = float(np.median(np.clip(v, self.bas, self.haut)))
        z = np.clip(np.where(ok, x, self.mediane), self.bas, self.haut)
        self.moyenne, self.ecart = float(z.mean()), float(z.std()) or 1.0
        return self

    def transformer(self, x: np.ndarray, reduire=True) -> np.ndarray:
        z = np.clip(np.where(np.isnan(x), self.mediane, x), self.bas, self.haut)
        return (z - self.moyenne) / self.ecart if reduire else z


# --- R1 -------------------------------------------------------------------------

class R1:
    def _z(self, d):
        cols = ("altman_x1", "altman_x2", "altman_x3", "altman_x4")
        return sum(c * self.bornes[n].transformer(d[n], reduire=False) for c, n in zip(ALTMAN, cols))

    def ajuster(self, d: dict, y: np.ndarray):
        from sklearn.linear_model import LogisticRegression

        self.bornes = {n: Bornes().ajuster(d[n]) for n in ("altman_x1", "altman_x2", "altman_x3", "altman_x4")}
        z = self._z(d)
        self.modele = LogisticRegression(C=np.inf, max_iter=1000).fit(z.reshape(-1, 1), y)
        return self

    def predire(self, d: dict) -> np.ndarray:
        return self.modele.predict_proba(self._z(d).reshape(-1, 1))[:, 1]


# --- R2 : hasard à temps discret ----------------------------------------------------

class Matrice:
    """Annexe A en matrice creuse : continues bornées et réduites, indicateurs de manquants, binaires, NAF."""

    def ajuster(self, d: dict):
        self.bornes = {c: Bornes().ajuster(d[c]) for c in CONTINUES}
        self.manquants = [c for c in CONTINUES if np.isnan(d[c]).any()]
        self.naf = sorted(set(d["naf2"]))
        self.index_naf = {n: i for i, n in enumerate(self.naf)}
        return self

    def construire(self, d: dict):
        from scipy import sparse

        blocs = [np.column_stack([self.bornes[c].transformer(d[c]) for c in CONTINUES]),
                 np.column_stack([np.isnan(d[c]).astype(float) for c in self.manquants])
                 if self.manquants else np.zeros((len(d["naf2"]), 0)),
                 np.column_stack([d[c].astype(float) for c in BINAIRES])]
        dense = sparse.csr_matrix(np.hstack(blocs))
        lignes, cols = [], []
        for i, n in enumerate(d["naf2"]):
            j = self.index_naf.get(n)
            if j is not None:
                lignes.append(i)
                cols.append(j)
        naf = sparse.csr_matrix((np.ones(len(lignes)), (lignes, cols)), shape=(len(d["naf2"]), len(self.naf)))
        return sparse.hstack([dense, naf]).tocsr()


def personne_periode(x, jours_issue: np.ndarray, issue: np.ndarray, horizon: int):
    """Une ligne par intervalle à risque ; l'événement est porté par l'intervalle qui le contient."""
    from scipy import sparse

    k_max = sum(1 for _a, b in INTERVALLES if b <= horizon)
    lignes, y, k_col, groupes = [], [], [], []
    for i in range(x.shape[0]):
        for k in range(k_max):
            a, b = INTERVALLES[k]
            evt = issue[i] == 1 and a < jours_issue[i] <= b
            lignes.append(i)
            y.append(int(evt))
            k_col.append(k)
            groupes.append(i)
            if evt:
                break
    lignes = np.array(lignes)
    indic = sparse.csr_matrix((np.ones(len(k_col)), (np.arange(len(k_col)), k_col)), shape=(len(k_col), k_max))
    return sparse.hstack([x[lignes], indic]).tocsr(), np.array(y), np.array(groupes), k_max


class R2:
    def __init__(self, horizon: int):
        self.horizon = horizon

    def ajuster(self, d: dict, y_horizon: np.ndarray):
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GroupKFold

        self.matrice = Matrice().ajuster(d)
        x = self.matrice.construire(d)
        issue = y_horizon  # l'événement n'est compté que s'il tombe dans l'horizon
        xp, yp, g, self.k_max = personne_periode(x, d["jours_issue"], issue, self.horizon)
        sirens = d["siren"][g]
        scores = {}
        for lam in GRILLE_LAMBDA:
            pertes = []
            for app, val in GroupKFold(n_splits=5).split(xp, yp, sirens):
                m = LogisticRegression(C=1.0 / (lam * len(app)), max_iter=2000, fit_intercept=False)
                m.fit(xp[app], yp[app])
                p = np.clip(m.predict_proba(xp[val])[:, 1], 1e-12, 1 - 1e-12)
                pertes.append(float(-np.mean(yp[val] * np.log(p) + (1 - yp[val]) * np.log(1 - p))))
            scores[lam] = float(np.mean(pertes))
        self.lam = min(scores, key=scores.get)
        self.scores_cv = scores
        self.modele = LogisticRegression(C=1.0 / (self.lam * xp.shape[0]), max_iter=2000, fit_intercept=False)
        self.modele.fit(xp, yp)
        return self

    def predire(self, d: dict) -> np.ndarray:
        from scipy import sparse

        x = self.matrice.construire(d)
        survie = np.ones(x.shape[0])
        for k in range(self.k_max):
            indic = sparse.csr_matrix((np.ones(x.shape[0]), (np.arange(x.shape[0]), np.full(x.shape[0], k))),
                                      shape=(x.shape[0], self.k_max))
            h = self.modele.predict_proba(sparse.hstack([x, indic]).tocsr())[:, 1]
            survie *= 1 - h
        return 1 - survie


# --- Mesures ------------------------------------------------------------------------

def mesures(y: np.ndarray, p: np.ndarray) -> dict:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    p = np.clip(p, 1e-9, 1 - 1e-9)
    logit = np.log(p / (1 - p)).reshape(-1, 1)
    cal = LogisticRegression(C=np.inf, max_iter=1000).fit(logit, y)
    ordre = np.argsort(-p, kind="stable")
    decile = ordre[: max(1, len(p) // 10)]
    bins = np.minimum((np.argsort(np.argsort(p, kind="stable"), kind="stable") * 10) // len(p), 9)
    fiabilite = [{"classe": int(b), "p_moyenne": float(p[bins == b].mean()), "taux_observe": float(y[bins == b].mean()),
                  "n": int((bins == b).sum())} for b in range(10) if (bins == b).any()]
    return {"n": int(len(y)), "defaillances": int(y.sum()), "taux": float(y.mean()),
            "brier": float(np.mean((p - y) ** 2)),
            "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
            "auc": float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else None,
            "calibration_ordonnee": float(cal.intercept_[0]), "calibration_pente": float(cal.coef_[0][0]),
            "part_defaillances_decile_risque": float(y[decile].sum() / max(1, y.sum())),
            "fiabilite": fiabilite}


def gain_bootstrap(y, p_mod, p_ref, tirages=TIRAGES, graine=GRAINE) -> dict:
    """G = 1 - Brier(modèle) / Brier(référence) ; un SIREN par ligne dans un pli de test : bootstrap par ligne = par SIREN."""
    a, b = (p_mod - y) ** 2, (p_ref - y) ** 2
    g = 1 - a.mean() / b.mean()
    rng = np.random.default_rng(graine)
    tir = np.empty(tirages)
    for t in range(tirages):
        w = rng.poisson(1.0, len(y))
        tir[t] = 1 - (w @ a) / (w @ b)
    bas, haut = np.percentile(tir, [2.5, 97.5])
    return {"G": float(g), "ic95": [float(bas), float(haut)]}


# --- Exécution ------------------------------------------------------------------------

def evaluer(d: dict) -> dict:
    res = {}
    for pli in PLIS:
        if not separation_respectee(pli):
            raise ValueError(f"pli {pli['nom']} contraire à la règle de séparation")
        app, test = sous_ensemble(d, pli["apprentissage"]), sous_ensemble(d, (pli["test"],))
        y_app, y_test = etiquette(app, pli["horizon"]), etiquette(test, pli["horizon"])
        print(f"[{dt.datetime.now():%H:%M:%S}] pli {pli['nom']} : {len(y_app)} cas d'apprentissage, "
              f"{len(y_test)} de test", file=sys.stderr, flush=True)
        r0 = R0().ajuster(app, y_app)
        r1 = R1().ajuster(app, y_app)
        r2 = R2(pli["horizon"]).ajuster(app, y_app)
        p = {"R0": r0.predire(test), "R1": r1.predire(test), "R2": r2.predire(test)}
        res[pli["nom"]] = {
            "pli": pli,
            "mesures": {k: mesures(y_test, v) for k, v in p.items()},
            "gain_contre_R2": {k: gain_bootstrap(y_test, p[k], p["R2"]) for k in ("R0", "R1")},
            "R0_force_lissage": r0.m, "R2_lambda": r2.lam, "R2_validation_croisee": r2.scores_cv,
        }
    # Description des sous-populations (développement seulement) : taux à 548 jours, toutes origines.
    y548 = etiquette(d, 548)
    desc = {}
    for nom, masque in (("en_plan", d["en_plan"] == 1), ("en_observation_sauvegarde", d["en_observation_sauvegarde"] == 1),
                        ("cr_indisponible", d["cr_indisponible"] == 1), ("ensemble", np.ones(len(y548), bool))):
        desc[nom] = {"n": int(masque.sum()), "taux_548j": float(y548[masque].mean()) if masque.any() else None}
    return {"plis": res, "descriptif_548j": desc}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dossier", default=DOSSIER_DEFAUT)
    a = p.parse_args(argv)
    chemin = os.path.join(a.dossier, "cas-dev.parquet")
    d = charger(chemin)
    rapport = evaluer(d)
    rapport["entree"] = {"cas-dev.parquet": sha256_fichier(chemin)}
    rapport["code"] = {"references.py": sha256_fichier(os.path.abspath(__file__))}
    rapport["execute_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    sortie = os.path.join(a.dossier, f"evaluation-references-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(texte)
    print("pli;modele;brier;logloss;auc;cal_ordonnee;cal_pente;decile;G_contre_R2;ic95", file=sys.stderr)
    for nom, r in rapport["plis"].items():
        for m, v in r["mesures"].items():
            g = r["gain_contre_R2"].get(m)
            print(f"{nom};{m};{v['brier']:.6f};{v['logloss']:.5f};{v['auc'] or float('nan'):.4f};"
                  f"{v['calibration_ordonnee']:.3f};{v['calibration_pente']:.3f};"
                  f"{v['part_defaillances_decile_risque']:.3f};"
                  f"{'' if g is None else round(g['G'], 4)};{'' if g is None else g['ic95']}", file=sys.stderr)
        print(f"{nom} : taux {r['mesures']['R2']['taux']:.4f}, lambda R2 {r['R2_lambda']}, m R0 {r['R0_force_lissage']}",
              file=sys.stderr)
    print("descriptif 548 j : " + json.dumps(rapport["descriptif_548j"]), file=sys.stderr)
    print(f"\nRapport : {sortie}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
