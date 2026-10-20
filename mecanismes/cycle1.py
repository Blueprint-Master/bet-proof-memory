"""Cycle 1 (protocole Q1 v1.7.1, P7) : calcul des 35 mécanismes candidats retenus.

Définitions : cycles/cycle-1-propositions-brutes.md, complétées par les précisions
d'exécution de cycles/cycle-1-verification.md (règles R-a à R-f). Une variable est une
fonction pure du cas (SIREN, t0) et des seules annonces ou bilans connus avant t0 :
  bilans       connus au sens de P2 (avis de dépôt paru avant t0), classés par clôture ;
  dépôts       avis de dépôt des comptes (BODACC, famille dpc) parus avant t0, première
               parution par (SIREN, clôture) ;
  procédures   jugements de clôture (CLOT) parus avant t0 ;
  conciliations, modifications  annonces parues avant t0 ;
  Sirene       périodes de l'historique, datation de P2 (R-c) ; deux codes NAF ne sont
               comparés que dans la même nomenclature ;
  Banque de France  séries DIREN, mois t0 - 3 et suivants vers le passé (R-d).
Le compte de résultat d'un bilan n'est lu que s'il est disponible au sens de P2 ter
(marge d'EBE renseignée) : chiffre d'affaires, marge d'EBE et résultat d'exploitation.

Valeurs manquantes : règle de l'auteur (C : 0 ; G : 0 et colonne « _absent ») ou, à
défaut, NaN, remplacé à l'évaluation par la médiane d'apprentissage avec un indicateur (R-a).

Écrit candidats-c1.parquet (siren, origine, colonnes des candidats) pour les origines
retenues de cas-dev.parquet, et un rapport de couverture par origine.
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
from construire import (MOTIF_CLOTURE, _date, _lire, _num, _siren, bilans_dates, bdf,  # noqa: E402
                        modifications, procedures, sha256_fichier, sirene)
from extraire import DOSSIER_DEFAUT  # noqa: E402

CANDIDATS = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12",
             "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12", "G13",
             "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M11", "M12")
AVEC_INDICATEUR = {"G1", "G4", "G5", "G6", "G7", "G8", "G9"}
ECART_MIN, ECART_MAX = 270, 550
POSTES = ("total", "cp", "reserves", "rex", "dettes", "dettes_fin")
PAQUET = 200_000
NAN = float("nan")


def colonnes() -> list:
    out = []
    for c in CANDIDATS:
        out.append(c)
        if c in AVEC_INDICATEUR:
            out.append(c + "_absent")
    return out


# --- Outils de date ---------------------------------------------------------------

def moins_mois(t0: dt.date, n: int) -> dt.date:
    a, m = divmod(t0.year * 12 + t0.month - 1 - n, 12)
    jour = min(t0.day, [31, 29 if a % 4 == 0 and (a % 100 or a % 400 == 0) else 28, 31, 30, 31, 30, 31, 31,
                        30, 31, 30, 31][m])
    return dt.date(a, m + 1, jour)


def mois_entre(d: dt.date, t0: dt.date) -> int:
    return (t0.year - d.year) * 12 + (t0.month - d.month) - (1 if t0.day < d.day else 0)


def dans(dates, debut: dt.date, t0: dt.date) -> bool:
    return any(debut <= d < t0 for d in dates)


def pente(xs, ys):
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    xc = x - x.mean()
    den = float(xc @ xc)
    return NAN if den == 0 else float(xc @ (y - y.mean()) / den)


# --- Contexte de calcul -------------------------------------------------------------

class Contexte:
    """Toutes les sources, indexées par SIREN ; rien n'est filtré par t0 ici."""

    def __init__(self, R, bilans, liasse, depots, clotures, conciliations, modifs, periodes, series):
        self.R, self.bilans, self.liasse, self.depots = R, bilans, liasse, depots
        self.clotures, self.conciliations, self.modifs = clotures, conciliations, modifs
        self.periodes, self.series = periodes, series
        self.conciliations_disponibles = conciliations is not None

    # bilans connus à t0 (P2), du plus récent au plus ancien
    def connus(self, s, t0):
        return [b for b in reversed(self.bilans.get(s, [])) if b[1] < t0]

    def ratio(self, b, col):
        return self.R.valeur(col, b[2][0])

    def cr(self, b):
        return self.ratio(b, "marge_ebe") is not None

    def poste(self, s, b, nom):
        x = self.liasse.get((s, b[0].isoformat(), self.R.type[b[2][0]]))
        return None if x is None else x[POSTES.index(nom)]

    def depots_connus(self, s, t0):
        """[(clôture, première parution)] des avis parus avant t0, du plus récent au plus ancien."""
        return sorted(((c, p) for c, p in self.depots.get(s, {}).items() if p < t0), reverse=True)

    def serie(self, cle, t0, decalage):
        s = self.series.get(cle) if cle else None
        a, r = divmod(t0.year * 12 + t0.month - 1 - decalage, 12)
        return None if not s else s.get(f"{a:04d}-{r + 1:02d}")


def ecart_ok(c1: dt.date, c2: dt.date) -> bool:
    return ECART_MIN <= (c1 - c2).days <= ECART_MAX


def changements_sirene(periodes: list, debut: dt.date, t0: dt.date, attribut: str, niveau=None) -> list:
    """Dates de début des périodes, dans [debut, t0[, dont l'attribut diffère de la période précédente."""
    ps = sorted((p for p in periodes if p[0] is not None), key=lambda p: p[0])
    out = []
    for a, b in zip(ps, ps[1:]):
        if not (debut <= b[0] < t0):
            continue
        if attribut == "cj":
            if a[2] and b[2] and str(a[2]) != str(b[2]):
                out.append(b[0])
        else:
            if not (a[3] and b[3]) or a[4] != b[4]:
                continue
            x, y = str(a[3]), str(b[3])
            if niveau == 2:
                x, y = x[:2], y[:2]
            elif niveau == 4:
                x, y = x[:5], y[:5]  # « 47.11 » : quatre chiffres et le point
            if x != y:
                out.append(b[0])
    return out


# --- Les mécanismes -----------------------------------------------------------------

def calculer(ctx: Contexte, s: str, t0: dt.date, cas: dict) -> dict:
    """Valeurs des colonnes pour un cas ; cas porte serie_bdf, taille_bdf, intensite_sectorielle."""
    v = {}
    bl = ctx.connus(s, t0)
    b1 = bl[0] if bl else None
    b2 = bl[1] if len(bl) > 1 else None
    r = lambda b, c: None if b is None else ctx.ratio(b, c)  # noqa: E731
    po = lambda b, n: None if b is None else ctx.poste(s, b, n)  # noqa: E731

    def g(nom, valeur):
        ok = valeur is not None and math.isfinite(valeur)
        v[nom], v[nom + "_absent"] = (float(valeur), 0.0) if ok else (0.0, 1.0)

    def c(nom, valeur):
        v[nom] = float(valeur) if valeur is not None and math.isfinite(valeur) else 0.0

    def m(nom, valeur):
        v[nom] = float(valeur) if valeur is not None and math.isfinite(valeur) else NAN

    paire = b1 is not None and b2 is not None
    paire_ok = paire and ecart_ok(b1[0], b2[0])
    ans = (b1[0] - b2[0]).days / 365.25 if paire else None

    # C1, C2 : variations annualisées
    for nom, col in (("C1", "ratio_de_liquidite"), ("C2", "taux_d_endettement")):
        x1, x2 = r(b1, col), r(b2, col)
        if paire_ok and x1 is not None and x2 is not None:
            c(nom, (x2 - x1) / ans if nom == "C1" else (x1 - x2) / ans)
        else:
            c(nom, None)
    # C3 : consommation des capitaux propres
    cp1, cp2, t2 = po(b1, "cp"), po(b2, "cp"), po(b2, "total")
    c("C3", (cp2 - cp1) / t2 if paire_ok and None not in (cp1, cp2, t2) and t2 > 0 else None)
    # C4 : instabilité de la liquidité sur quatre exercices espacés de 270 à 550 jours
    if len(bl) >= 4 and all(ecart_ok(bl[k][0], bl[k + 1][0]) for k in range(3)):
        ls = [r(b, "ratio_de_liquidite") for b in bl[:4]]
        c("C4", float(np.std(ls)) if None not in ls else None)
    else:
        c("C4", None)
    # C5 : pertes héritées
    res1, tot1 = po(b1, "reserves"), po(b1, "total")
    c("C5", max(0.0, -res1) / tot1 if None not in (res1, tot1) and tot1 > 0 else None)
    # C6 : deux résultats d'exploitation négatifs consécutifs
    if paire_ok and ctx.cr(b1) and ctx.cr(b2) and None not in (po(b1, "rex"), po(b2, "rex")):
        c("C6", float(po(b1, "rex") < 0 and po(b2, "rex") < 0))
    else:
        c("C6", None)
    # Dépôts (BODACC, famille dpc)
    dep = ctx.depots_connus(s, t0)
    retards = [(p - cl).days for cl, p in dep]
    c("C7", (retards[0] - retards[1]) / 365.25 if len(retards) >= 2 else None)
    c("C8", max(0.0, (t0 - dep[0][0]).days / 365.25 - 1.5) if dep else None)
    g("G1", retards[0] - retards[1] if len(retards) >= 2 else None)
    v["G2"] = float(bool(dep) and not any(t0 - dt.timedelta(days=450) <= p < t0 for _cl, p in dep))
    m("M7", float(np.std(retards[:3])) if len(retards) >= 3 else None)
    # Conciliations et procédures closes
    conc = ctx.conciliations.get(s, []) if ctx.conciliations_disponibles else []
    clot = ctx.clotures.get(s, [])
    if ctx.conciliations_disponibles:
        c("C9", float(dans(conc, t0 - dt.timedelta(days=730), t0)))
        v["M4"] = float(dans(conc, moins_mois(t0, 60), t0))
    else:
        v["C9"], v["M4"] = NAN, NAN
    c("C10", float(dans(clot, t0 - dt.timedelta(days=1826), t0)))
    v["G10"] = float(any(d < t0 for d in clot) or any(d < t0 for d in conc))
    # Sirene (R-c)
    per = ctx.periodes.get(s, [])
    nafs = changements_sirene(per, t0 - dt.timedelta(days=1096), t0, "naf", niveau=2)
    c("C11", float(len(nafs)))
    g11 = changements_sirene(per, t0 - dt.timedelta(days=1095), t0, "naf") + \
        changements_sirene(per, t0 - dt.timedelta(days=1095), t0, "cj")
    v["G11"] = float(bool(g11))
    deb = moins_mois(t0, 24)
    v["M5"] = float(bool(changements_sirene(per, deb, t0, "naf", 2) or changements_sirene(per, deb, t0, "naf", 4)))
    v["M6"] = float(bool(changements_sirene(per, moins_mois(t0, 36), t0, "cj")))
    cjs = changements_sirene(per, dt.date(1900, 1, 1), t0, "cj")
    v["M11"] = float(min(60, mois_entre(max(cjs), t0))) if cjs else 60.0
    # Banque de France (R-d)
    a, b = ctx.serie(cas.get("serie_bdf"), t0, 3), ctx.serie(cas.get("serie_bdf"), t0, 15)
    c("C12", math.log((1 + a) / (1 + b)) if None not in (a, b) and a > -1 and b > -1 else None)
    taille = cas.get("taille_bdf") or "TT"
    cle = f"DIREN.M.FR.DE.UL.DF.03.N.ZZ.{'MI' if taille == 'TT' else taille}"
    x0 = ctx.serie(cle, t0, 3)
    passe = [ctx.serie(cle, t0, 3 + i) for i in range(1, 61)]
    m("G13", x0 / (sum(passe) / 60) if x0 is not None and None not in passe and sum(passe) > 0 else None)
    v["G12"] = float(dans(ctx.modifs.get(s, []), t0 - dt.timedelta(days=1095), t0))
    # Variations entre les deux derniers bilans (G4 à G6)
    for nom, col in (("G4", "autonomie_financiere"), ("G5", "ratio_de_liquidite")):
        x1, x2 = r(b1, col), r(b2, col)
        g(nom, x1 - x2 if paire and x1 is not None and x2 is not None else None)
    tt1, tt2 = po(b1, "total"), po(b2, "total")
    g("G6", math.log(tt1) - math.log(tt2) if paire and None not in (tt1, tt2) and tt1 > 0 and tt2 > 0 else None)
    v["G3"] = float(paire and not ctx.cr(b1) and ctx.cr(b2))
    # Dernier bilan (liasse)
    g("G7", res1 / tot1 if None not in (res1, tot1) and tot1 > 0 else None)
    rex1 = po(b1, "rex") if b1 is not None and ctx.cr(b1) else None
    g("G8", rex1 / tot1 if None not in (rex1, tot1) and tot1 > 0 else None)
    df1, dt1 = po(b1, "dettes_fin"), po(b1, "dettes")
    g("G9", df1 / dt1 if None not in (df1, dt1) and dt1 > 0 else None)
    # Séries de bilans (M1, M2, M3, M8)
    def serie_bilans(n, f):
        if len(bl) < n:
            return None
        vals = [f(b) for b in bl[:n]]
        return None if None in vals else vals
    xs = lambda n: [-(bl[0][0] - b[0]).days / 365.25 for b in bl[:n]]  # noqa: E731
    e = serie_bilans(3, lambda b: r(b, "marge_ebe"))
    m("M1", pente(xs(3), e) if e else None)
    lq = serie_bilans(5, lambda b: r(b, "ratio_de_liquidite"))
    m("M2", float(np.std(lq)) if lq else None)
    ca = serie_bilans(5, lambda b: r(b, "chiffre_d_affaires") if ctx.cr(b) else None)
    if ca and min(ca) > 0:
        gr = [ca[k] / ca[k + 1] - 1 for k in range(4)]
        m("M3", (gr[0] + gr[1]) / 2 - (gr[2] + gr[3]) / 2)
    else:
        m("M3", None)
    def ratio_df(b):
        dfi, tot = po(b, "dettes_fin"), po(b, "total")
        return dfi / tot if None not in (dfi, tot) and tot > 0 else None
    d8 = serie_bilans(4, ratio_df)
    m("M8", pente(xs(4), d8) if d8 else None)
    ca2 = serie_bilans(2, lambda b: r(b, "chiffre_d_affaires") if ctx.cr(b) else None)
    inten = cas.get("intensite_sectorielle")
    m("M12", ca2[0] / ca2[1] - 1 - inten if ca2 and ca2[1] > 0 and inten is not None and inten == inten else None)
    return v


# --- Chargement ---------------------------------------------------------------------

def postes_liasse(dossier: str, sirens: set) -> dict:
    """{(siren, clôture, type): {total, cp, reserves, rex, dettes, dettes_fin}} (codes de composantes_liasse)."""
    sf, _c = _lire(dossier, "sf-totaux.parquet")
    g = lambda n: _num(sf, n)  # noqa: E731
    z = lambda a: np.nan_to_num(a, nan=0.0)  # noqa: E731
    typ = np.asarray(sf.column("type_bilan").to_pylist(), dtype=object)
    c = typ == "C"
    postes = {"total": np.where(c, g("EE"), g("180")), "cp": np.where(c, g("DL"), g("142")),
              "reserves": np.where(c, z(g("DD")) + z(g("DE")) + z(g("DF")) + z(g("DG")) + z(g("DH")),
                                   z(g("126")) + z(g("130")) + z(g("132")) + z(g("134"))),
              "rex": np.where(c, g("GG"), g("270")), "dettes": np.where(c, g("EC"), g("176")),
              "dettes_fin": np.where(c, z(g("DS")) + z(g("DT")) + z(g("DU")) + z(g("DV")), z(g("156")))}
    sir = sf.column("siren").to_pylist()
    clo = sf.column("date_cloture_exercice").to_pylist()
    out = {}
    for k in range(sf.num_rows):
        s = str(sir[k]).zfill(9) if sir[k] else None
        if s not in sirens or typ[k] not in ("C", "S"):
            continue
        out[(s, str(clo[k])[:10], typ[k])] = tuple(None if postes[n][k] != postes[n][k] else float(postes[n][k])
                                                  for n in POSTES)
    return out


def depots(dossier: str, sirens: set) -> dict:
    t, _c = _lire(dossier, "bodacc-dpc.parquet", ["dateparution", "registre", "depot"])
    out = {}
    for r, p, d in zip(t.column("registre").to_pylist(), t.column("dateparution").to_pylist(),
                       t.column("depot").to_pylist()):
        s, mt, p = _siren(r), MOTIF_CLOTURE.search(d or ""), _date(p)
        if s in sirens and mt and p:
            cl = dt.date.fromisoformat(mt.group(1))
            if cl <= p:
                dd = out.setdefault(s, {})
                dd[cl] = min(p, dd.get(cl, p))
    return out


def conciliations(dossier: str, sirens: set):
    try:
        t, _c = _lire(dossier, "bodacc-conciliation.parquet", ["dateparution", "registre"])
    except RuntimeError:
        return None
    if t.num_rows == 0:
        return None
    out = {}
    for r, p in zip(t.column("registre").to_pylist(), t.column("dateparution").to_pylist()):
        s, p = _siren(r), _date(p)
        if s in sirens and p:
            out.setdefault(s, []).append(p)
    return out


def charger_contexte(dossier: str, sirens: set) -> Contexte:
    from p0_sources import journal

    journal("bilans")
    R, bil, _m, _e = bilans_dates(dossier, dt.date.today())
    bil = {s: v for s, v in bil.items() if s in sirens}
    journal("liasse")
    li = postes_liasse(dossier, sirens)
    journal("dépôts")
    dep = depots(dossier, sirens)
    journal("procédures, conciliations, modifications")
    evts, _i, _c = procedures(dossier)
    clot = {s: [pe for pe, _dj, n in v if n == "CLOT"] for s, v in evts.items() if s in sirens}
    conc = conciliations(dossier, sirens)
    mods, _c = modifications(dossier)
    mods = {s: [d for d, _e in v] for s, v in mods.items() if s in sirens}
    journal("Sirene, Banque de France")
    per, _cr, _c = sirene(dossier)
    per = {s: v for s, v in per.items() if s in sirens}
    series, _c = bdf(dossier)
    return Contexte(R, bil, li, dep, clot, conc, mods, per, series)


def main(argv=None) -> int:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    from p0_sources import journal

    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--dossier", default=DOSSIER_DEFAUT)
    args = a.parse_args(argv)
    chemin = os.path.join(args.dossier, "cas-dev.parquet")
    t = pq.read_table(chemin, columns=["siren", "origine", "t0", "origine_retenue", "serie_bdf", "taille_bdf",
                                       "intensite_sectorielle"])
    t = t.filter(pc.equal(t.column("origine_retenue"), 1))
    n_cas = t.num_rows
    ctx = charger_contexte(args.dossier, set(t.column("siren").to_pylist()))
    cols = colonnes()
    schema = pa.schema([("siren", pa.string()), ("origine", pa.int64())] + [(k, pa.float64()) for k in cols])
    fichier = os.path.join(args.dossier, "candidats-c1.parquet")
    ecrivain = pq.ParquetWriter(fichier, schema)
    comptes = {}  # (colonne, origine) -> [n, non manquant, non nul]
    for debut in range(0, n_cas, PAQUET):
        lot = t.slice(debut, PAQUET).to_pylist()
        sortie = {k: [] for k in ["siren", "origine"] + cols}
        for x in lot:
            val = calculer(ctx, x["siren"], x["t0"], x)
            sortie["siren"].append(x["siren"])
            sortie["origine"].append(x["origine"])
            for k in cols:
                sortie[k].append(val[k])
                cpt = comptes.setdefault((k, x["origine"]), [0, 0, 0])
                cpt[0] += 1
                cpt[1] += int(val[k] == val[k])
                cpt[2] += int(val[k] == val[k] and val[k] != 0)
        ecrivain.write_table(pa.table(sortie, schema=schema))
        journal(f"{debut + len(lot)} cas sur {n_cas}")
    ecrivain.close()
    couverture = {}
    for (k, o), (n, nm, nn) in comptes.items():
        couverture.setdefault(k, {})[str(o)] = {"non_manquant": nm / n, "non_nul": nn / n}
    rapport = {"cas": n_cas, "conciliations_disponibles": ctx.conciliations_disponibles,
               "couverture": couverture, "sortie": {"fichier": os.path.basename(fichier),
                                                    "sha256": sha256_fichier(fichier)},
               "entree": {"cas-dev.parquet": sha256_fichier(chemin)},
               "code": {"cycle1.py": sha256_fichier(os.path.abspath(__file__))},
               "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    rp = os.path.join(args.dossier, f"candidats-c1-{dt.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(rp, "w", encoding="utf-8") as f:
        f.write(texte)
    origines = sorted({o for d in couverture.values() for o in d})
    print("candidat;" + ";".join(origines) + " (part non nulle)", file=sys.stderr)
    for k in cols:
        print(k + ";" + ";".join(f"{couverture[k][o]['non_nul']:.4f}" for o in sorted(couverture[k])), file=sys.stderr)
    print(f"conciliations disponibles : {ctx.conciliations_disponibles}", file=sys.stderr)
    print(f"\nRapport : {rp}\nSHA-256 : {hashlib.sha256(texte.encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
