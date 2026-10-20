"""Protocole Q1 v1.7 : témoin et assemblage (P5 bis), critère de jugement (P6).

P5 bis
  eta_k     prédicteur linéaire de R2 (P5) ajusté sur l'espace d'apprentissage, figé.
  Témoin    logit h_k = a_k + b eta_k, sans pénalité.
  Assemblage  logit h_k = a_k + b eta_k + gamma' x, x = mécanismes centrés et réduits sur la
            table des cas à t0 de l'apprentissage ; seul gamma est pénalisé :
            objectif = moyenne des pertes logistiques en personne-période + lambda/2 ||gamma||^2.
            lambda dans la grille de P5, par validation croisée en 5 parts groupées par
            SIREN (critère : log-vraisemblance moyenne en personne-période ; égalité -> plus
            grand lambda). La validation croisée interne utilise l'eta du R2 de l'espace
            entier (contamination interne déclarée).
  Optimiseur  L-BFGS-B de scipy, 2 000 itérations au plus (précision de mise en oeuvre : le
            protocole nomme scikit-learn, qui ne permet pas de laisser a_k et b sans pénalité
            tout en pénalisant gamma ; l'objectif est celui du protocole, C = 1/(lambda n)).
  Contrôles  lambda = 0 retiré si un coefficient de gamma dépasse 50 ou si une probabilité
            ajustée est numériquement 0 ou 1 (v1.7.1, critère de glm.fit) ; toute valeur retirée
            si l'optimiseur atteint sa limite ou si a_k ou b dépasse 50 ; une valeur invalide
            dans l'une des parts est retirée ; si aucune ne reste, l'assemblage est réduit au
            témoin (candidat non admis). Témoin non convergent : arrêt.
  Probabilité  p = 1 - prod(1 - h_k) sur les intervalles de l'horizon.

P6
  Coût réalisé d'un cas, scénario s : pi T_s + (1 - q_s) y LGD si p > p_t,s, y LGD sinon ;
  perte = moyenne sur les cas et les scénarios retenus (lgd.seuils), en euros par euro
  d'encours sur l'horizon. Delta = perte(témoin) - perte(assemblage), calculé par origine
  puis moyenné à poids égaux. Inférence : bootstrap par grappes de divisions NAF
  (multiplicités, réplications sans cas d'une origine retirées), 2 000 réplications,
  intervalle percentile à 95 %. L_min = c (horizon/365) / g pour 100 EUR de c, « sans objet »
  si g <= 0. Décomposition MCB - DSC + UNC par recalibration isotone (Dimitriadis, Gneiting
  et Jordan, 2021).
"""

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from lgd import PI_PRIMAIRE, seuils
from references import GRILLE_LAMBDA, INTERVALLES

MAX_ITER = 2000
SEUIL_COEF = 50.0
EPS = 10 * np.finfo(float).eps
TIRAGES = 2000
COUT_INFORMATION_REFERENCE = 100.0


# --- Personne-période ------------------------------------------------------------

def lignes_pp(jours_issue: np.ndarray, issue: np.ndarray, horizon: int):
    """(indice du cas, intervalle k, événement) ; même règle que references.personne_periode."""
    k_max = sum(1 for _a, b in INTERVALLES if b <= horizon)
    i_, k_, y_ = [], [], []
    for i in range(len(issue)):
        for k in range(k_max):
            a, b = INTERVALLES[k]
            evt = issue[i] == 1 and a < jours_issue[i] <= b
            i_.append(i)
            k_.append(k)
            y_.append(int(evt))
            if evt:
                break
    return np.array(i_), np.array(k_), np.array(y_), k_max


# --- Logistique en décalage ------------------------------------------------------

def ajuster_decalage(k, eta, X, y, k_max, lam=0.0, theta0=None):
    """Minimise moyenne(log(1 + e^z) - y z) + lam/2 ||gamma||^2, z = a_k + b eta + X gamma.

    Retourne (a, b, gamma, converge, extreme), extreme = une probabilité ajustée est
    numériquement 0 ou 1 (critère de glm.fit dans R : 10 epsilon machine)."""
    n, m = len(y), X.shape[1]

    def f(theta):
        a, b, g = theta[:k_max], theta[k_max], theta[k_max + 1:]
        z = a[k] + b * eta + (X @ g if m else 0.0)
        perte = np.mean(np.logaddexp(0.0, z) - y * z) + 0.5 * lam * g @ g
        r = (expit(z) - y) / n
        grad = np.concatenate([np.bincount(k, r, minlength=k_max), [r @ eta], X.T @ r + lam * g if m else []])
        return perte, grad

    theta0 = np.concatenate([np.zeros(k_max), [1.0], np.zeros(m)]) if theta0 is None else theta0
    res = minimize(f, theta0, jac=True, method="L-BFGS-B", options={"maxiter": MAX_ITER, "gtol": 1e-8})
    converge = bool(res.success) and res.nit < MAX_ITER
    a, b, g = res.x[:k_max], float(res.x[k_max]), res.x[k_max + 1:]
    h = expit(a[k] + b * eta + (X @ g if m else 0.0))
    extreme = bool(np.any(h < EPS) or np.any(h > 1 - EPS))
    return a, b, g, converge, extreme


def proba(a, b, g, eta: np.ndarray, X=None) -> np.ndarray:
    """p = 1 - prod(1 - h_k), eta de forme (n, k_max)."""
    survie = np.ones(eta.shape[0])
    lin = X @ g if X is not None and len(g) else 0.0
    for kk in range(eta.shape[1]):
        survie *= 1 - expit(a[kk] + b * eta[:, kk] + lin)
    return 1 - survie


def _pp(eta_cas, y_cas_jours, issue, horizon):
    i, k, y, k_max = lignes_pp(y_cas_jours, issue, horizon)
    return i, k, y, k_max, eta_cas[i, k]


class Temoin:
    def ajuster(self, eta_cas: np.ndarray, jours_issue, issue, horizon: int):
        i, k, y, self.k_max, e = _pp(eta_cas, jours_issue, issue, horizon)
        self.a, self.b, _g, ok, _x = ajuster_decalage(k, e, np.zeros((len(y), 0)), y, self.k_max)
        if not ok or max(np.max(np.abs(self.a)), abs(self.b)) > SEUIL_COEF:
            raise RuntimeError("témoin non convergent : arrêt (P5 bis)")
        return self

    def predire(self, eta_cas: np.ndarray) -> np.ndarray:
        return proba(self.a, self.b, np.zeros(0), eta_cas[:, : self.k_max])


class Assemblage:
    def ajuster(self, eta_cas, X_cas, siren, jours_issue, issue, horizon: int, grille=GRILLE_LAMBDA):
        from sklearn.model_selection import GroupKFold

        X_cas = np.asarray(X_cas, dtype=float).reshape(len(issue), -1)
        self.moy = X_cas.mean(axis=0)
        self.ect = X_cas.std(axis=0)
        self.ect[self.ect == 0] = 1.0
        Z = (X_cas - self.moy) / self.ect
        i, k, y, self.k_max, e = _pp(eta_cas, jours_issue, issue, horizon)
        Xp = Z[i]
        self.scores, self.retraits = {}, []
        for lam in grille:
            pertes, valide = [], True
            for app, val in GroupKFold(n_splits=5).split(Xp, y, siren[i]):
                a, b, g, ok, ext = ajuster_decalage(k[app], e[app], Xp[app], y[app], self.k_max, lam)
                if not self._valide(a, b, g, ok, ext, lam):
                    valide = False
                    break
                z = a[k[val]] + b * e[val] + Xp[val] @ g
                pertes.append(float(np.mean(np.logaddexp(0.0, z) - y[val] * z)))
            if valide:
                self.scores[lam] = float(np.mean(pertes))
            else:
                self.retraits.append({"lambda": lam, "etape": "validation croisee"})
        self.reduit_au_temoin, self.lam = True, None
        for lam in sorted(self.scores, key=lambda l: (self.scores[l], -l)):
            a, b, g, ok, ext = ajuster_decalage(k, e, Xp, y, self.k_max, lam)
            if self._valide(a, b, g, ok, ext, lam):
                self.a, self.b, self.g, self.lam, self.reduit_au_temoin = a, b, g, lam, False
                break
            self.retraits.append({"lambda": lam, "etape": "ajustement final"})
        if self.reduit_au_temoin:
            self.temoin = Temoin().ajuster(eta_cas, jours_issue, issue, horizon)
        return self

    @staticmethod
    def _valide(a, b, g, ok, extreme, lam) -> bool:
        if not ok or max(np.max(np.abs(a)), abs(b)) > SEUIL_COEF:
            return False
        return not (lam == 0 and (extreme or (len(g) and np.max(np.abs(g)) > SEUIL_COEF)))

    def predire(self, eta_cas, X_cas) -> np.ndarray:
        if self.reduit_au_temoin:
            return self.temoin.predire(eta_cas)
        Z = (np.asarray(X_cas, dtype=float).reshape(eta_cas.shape[0], -1) - self.moy) / self.ect
        return proba(self.a, self.b, self.g, eta_cas[:, : self.k_max], Z)


# --- Perte de P6 ----------------------------------------------------------------

def scenarios(lgd: float, horizon: int, pi: float = PI_PRIMAIRE) -> list:
    return seuils(lgd, pi, horizon)["retenus"]


def couts(p: np.ndarray, y: np.ndarray, scen: list) -> np.ndarray:
    """Coût réalisé par cas, moyenné sur les scénarios (n,) ; colonnes par scénario dans couts_par_scenario."""
    return couts_par_scenario(p, y, scen).mean(axis=1)


def couts_par_scenario(p: np.ndarray, y: np.ndarray, scen: list) -> np.ndarray:
    if not scen:
        raise ValueError("aucun scénario retenu")
    out = np.empty((len(y), len(scen)))
    for j, s in enumerate(scen):
        couvrir = p > s["p_t"]
        out[:, j] = np.where(couvrir, s["pi"] * s["T"] + (1 - s["q"]) * y * s["lgd"], y * s["lgd"])
    return out


def delta_par_origine(diff: np.ndarray, origine: np.ndarray, poids=None) -> float:
    """Moyenne à poids égaux, sur les origines, de la moyenne (pondérée) de diff."""
    w = np.ones(len(diff)) if poids is None else poids
    vals = [np.sum(w[origine == o] * diff[origine == o]) / np.sum(w[origine == o]) for o in np.unique(origine)]
    return float(np.mean(vals))


def grappes(siren: np.ndarray, origine: np.ndarray, naf2: np.ndarray) -> np.ndarray:
    """Division NAF de la société à sa première origine ; NAF manquante = grappe « ? »."""
    premiere = {}
    for s, o, n in sorted(zip(siren, origine, naf2), key=lambda x: x[1]):
        premiere.setdefault(s, n if n not in (None, "") else "?")
    return np.array([premiere[s] for s in siren], dtype=object)


def bootstrap_grappes(diff, origine, grappe, poids=None, tirages=TIRAGES, graine=20261020, essais_max=None) -> dict:
    """Delta et intervalle percentile à 95 % ; tirage des grappes avec remise."""
    w = np.ones(len(diff)) if poids is None else np.asarray(poids, dtype=float)
    labels, gi = np.unique(grappe.astype(str), return_inverse=True)
    origines = np.unique(origine)
    G = len(labels)
    S = np.zeros((G, len(origines)))
    N = np.zeros((G, len(origines)))
    for j, o in enumerate(origines):
        m = origine == o
        S[:, j] = np.bincount(gi[m], w[m] * diff[m], minlength=G)
        N[:, j] = np.bincount(gi[m], w[m], minlength=G)
    rng = np.random.default_rng(graine)
    vals, retirees, essais = [], 0, 0
    essais_max = essais_max or 50 * tirages
    while len(vals) < tirages and essais < essais_max:
        essais += 1
        c = np.bincount(rng.integers(0, G, G), minlength=G)
        den = c @ N
        if np.any(den == 0):
            retirees += 1
            continue
        vals.append(float(np.mean((c @ S) / den)))
    if len(vals) < tirages:
        raise RuntimeError("trop de réplications sans cas d'une origine")
    bas, haut = np.percentile(vals, [2.5, 97.5])
    return {"delta": delta_par_origine(diff, origine, w), "ic95": [float(bas), float(haut)],
            "demi_largeur": float((haut - bas) / 2), "grappes": int(G), "replications_retirees": int(retirees)}


def verdict(ic95) -> str:
    bas, haut = ic95
    return "succes" if bas > 0 else "echec" if haut < 0 else "indecis"


def l_min(g: float, horizon: int = 548, c: float = COUT_INFORMATION_REFERENCE):
    return None if g <= 0 else c * (horizon / 365) / g


def decomposition(p: np.ndarray, y: np.ndarray, scen: list) -> dict:
    """S = MCB - DSC + UNC, recalibration isotone (CORP)."""
    from sklearn.isotonic import IsotonicRegression

    p_rc = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit_transform(p, y)
    s = lambda q: float(couts(q, y, scen).mean())  # noqa: E731
    sp, src, sclim = s(p), s(p_rc), s(np.full(len(y), y.mean()))
    return {"perte": sp, "MCB": sp - src, "DSC": sclim - src, "UNC": sclim}
