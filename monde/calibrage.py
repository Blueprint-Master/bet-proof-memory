"""Calibrage du bruit de mesure (spécification v3, §3.2).

« Détectable à 80 % en k mesures » : la décision bayésienne entre « la variable a bougé d'un
cran » et « elle n'a pas bougé », prise après k mesures, est juste dans 80 % des cas, sous une
loi a priori de référence équilibrée (0,5). Avec la loi réelle, très déséquilibrée dans cette
famille (0,25 pour un candidat d'obstacle, 0,1 pour l'impossibilité), l'exactitude serait
dégénérée (dire toujours « absent » donne déjà 75 % ou 90 %) : la sensibilité et la
spécificité sous la loi réelle sont donc publiées à côté (§3.2 amendé, voir le compte rendu).

Modèle de mesure : vraie valeur avec la probabilité q, sinon une valeur uniforme du domaine
(n valeurs). Un premier modèle (sinon l'une des deux voisines) rendait certaines observations
concluantes à elles seules : quatre mesures détectaient le décalage à 90 % même au bruit maximal,
et le niveau « difficile » était incalibrable. Il a été remplacé avant tout usage.
"""

from itertools import product


def _lois(q, n=5):
    # valeurs 0..n-1 ; sans décalage la vraie valeur est 1, avec décalage 2
    p0 = {x: q * (x == 1) + (1 - q) / n for x in range(n)}
    p1 = {x: q * (x == 2) + (1 - q) / n for x in range(n)}
    return p0, p1


def exactitude(q, k, a_priori=0.5, n=5):
    """Exactitude de la décision bayésienne après k mesures, et sensibilité, spécificité."""
    p0, p1 = _lois(q, n)
    issues = sorted(set(p0) | set(p1))
    juste = sens = spec = 0.0
    for obs in product(issues, repeat=k):
        l0 = l1 = 1.0
        for o in obs:
            l0 *= p0.get(o, 0.0)
            l1 *= p1.get(o, 0.0)
        a1, a0 = a_priori * l1, (1 - a_priori) * l0
        if a1 > a0:
            juste += a1
            sens += l1
        else:
            juste += a0
            spec += l0
    return juste, sens, spec


def q_pour(k, cible=0.80, pas=0.0005, n=5):
    """Plus petit q (au pas près) dont l'exactitude atteint la cible en k mesures."""
    q = 0.0
    while q < 1:
        if exactitude(q, k, n=n)[0] >= cible:
            return round(q, 4)
        q += pas
    raise ValueError("cible inatteignable")


Q = {"facile": None, "difficile": None}


def table():
    if Q["facile"] is None:
        Q["facile"], Q["difficile"] = q_pour(2), q_pour(4)
    return dict(Q)


if __name__ == "__main__":
    t = table()
    for niveau, k in (("facile", 2), ("difficile", 4)):
        q = t[niveau]
        ex, se, sp = exactitude(q, k)
        ex25, se25, sp25 = exactitude(q, k, 0.25)
        ex10, se10, sp10 = exactitude(q, k, 0.10)
        print(f"{niveau} k={k} q={q} exactitude={ex:.3f} ; a priori 0,25 : exactitude {ex25:.3f} "
              f"sensibilité {se25:.3f} spécificité {sp25:.3f} ; a priori 0,10 : exactitude {ex10:.3f} "
              f"sensibilité {se10:.3f}")
