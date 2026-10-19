#!/usr/bin/env python3
"""
P0 v1.2, taux de jointure entre les bilans et les avis de dépôt du BODACC.

Question mesurée, et elle seule : pour chaque année de clôture testée, quelle
part des bilans (ratios BCE/INPI) retrouve son avis de dépôt des comptes au
BODACC partie C, par le couple (SIREN, date de clôture) ? Et avec quel délai
entre la clôture et la parution ?

RÈGLE DE P0 : métadonnées de disponibilité seules. Les bilans ne sont lus que
par leurs clés (SIREN, date de clôture, confidentialité, type de bilan),
jamais par leurs montants. Le BODACC n'est lu que dans la famille des dépôts
de comptes ; aucune annonce de procédure collective n'est lue.

Verdict (protocole Q1 v1.2) sur l'année testée la plus faible :
  >= 90 % : principal-dates ; 50 à 90 % : principal-dates-biais-declare ;
  < 50 % : arret.

Dépendances : Python 3.10+ seul (bibliothèque standard). Le BODACC est lu en
flux, sans stockage : plusieurs millions d'avis, quelques centaines de Mo.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import random
import re
import sys
import urllib.parse
import urllib.request

RATIOS = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/ratios_inpi_bce"
BODACC = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales"
FAMILLE_DEPOT = "dpc"
AGENT = "bet-proof-memory-p0-jointure/1.0"
DELAI_HTTP_S = 600
ANNEES_DEFAUT = "2016,2019,2022,2023,2024"
FENETRE_PARUTION_MOIS = 36
SEUIL_PRINCIPAL, SEUIL_ARRET = 0.90, 0.50

csv.field_size_limit(10**8)

MOIS = {m: i for i, m in enumerate(
    ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
     "septembre", "octobre", "novembre", "décembre"], start=1)}
MOTIF_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
MOTIF_CONFID = re.compile(r"confid", re.I)
MOTIF_FR = re.compile(r"(\d{1,2})(?:er)?\s+(" + "|".join(MOIS) + r")\s+(\d{4})", re.I)


# --- Analyse des champs --------------------------------------------------

def siren_de(registre: str | None) -> int | None:
    """Premier numéro à 9 chiffres du champ registre, espaces retirés."""
    if not registre:
        return None
    for morceau in re.split(r"[,;|\[\]\"]", registre):
        chiffres = re.sub(r"\D", "", morceau)
        if len(chiffres) == 9:
            return int(chiffres)
    return None


def date_cloture_de(depot: str | None) -> dt.date | None:
    """Date de clôture d'un avis de dépôt : champ JSON dateCloture, sinon
    première date ISO, sinon première date en toutes lettres."""
    if not depot:
        return None
    try:
        d = json.loads(depot)
        if isinstance(d, dict):
            for cle in ("dateCloture", "date_cloture", "dateclotureexercice"):
                if isinstance(d.get(cle), str) and MOTIF_ISO.search(d[cle]):
                    a, m, j = MOTIF_ISO.search(d[cle]).groups()
                    return dt.date(int(a), int(m), int(j))
    except (ValueError, TypeError):
        pass
    m = MOTIF_ISO.search(depot)
    if m:
        return dt.date(*map(int, m.groups()))
    m = MOTIF_FR.search(depot)
    if m:
        return dt.date(int(m.group(3)), MOIS[m.group(2).lower()], int(m.group(1)))
    return None


def cle(siren: int, cloture: dt.date) -> int:
    return siren * 100_000_000 + cloture.year * 10_000 + cloture.month * 100 + cloture.day


# --- Flux d'export Opendatasoft -------------------------------------------

def flux_csv(base: str, select: str, where: str, ouvrir=urllib.request.urlopen):
    params = urllib.parse.urlencode({"select": select, "where": where, "delimiter": ";"})
    requete = urllib.request.Request(f"{base}/exports/csv?{params}", headers={"User-Agent": AGENT})
    r = io.BufferedReader(ouvrir(requete, timeout=DELAI_HTTP_S))
    # Flux compressé possible même sans Accept-Encoding (constaté le 19/10/2026) :
    # on se fie à la signature gzip, pas à la politesse du serveur.
    if r.peek(2)[:2] == b"\x1f\x8b":
        r = gzip.GzipFile(fileobj=r)
    texte = io.TextIOWrapper(r, encoding="utf-8-sig", newline="")
    yield from csv.DictReader(texte, delimiter=";")


# --- Mesure ---------------------------------------------------------------

def charger_bilans(annees: list[int], ouvrir=urllib.request.urlopen) -> tuple[dict, dict]:
    """Clés des bilans par année de clôture, et effectifs par confidentialité et type."""
    cles, comptes = {}, {}
    for a in annees:
        ensemble, c = set(), {"total": 0, "sans_siren": 0, "confidentialite": {}, "type_bilan": {}}
        where = f"date_cloture_exercice >= date'{a}-01-01' and date_cloture_exercice < date'{a + 1}-01-01'"
        for ligne in flux_csv(RATIOS, "siren,date_cloture_exercice,confidentiality,type_bilan", where, ouvrir):
            c["total"] += 1
            s = siren_de(ligne.get("siren"))
            m = MOTIF_ISO.search(ligne.get("date_cloture_exercice") or "")
            if s is None or not m:
                c["sans_siren"] += 1
                continue
            k = cle(s, dt.date(*map(int, m.groups())))
            conf = (ligne.get("confidentiality") or "(vide)").strip()
            typ = (ligne.get("type_bilan") or "(vide)").strip()
            c["confidentialite"][conf] = c["confidentialite"].get(conf, 0) + 1
            c["type_bilan"][typ] = c["type_bilan"].get(typ, 0) + 1
            ensemble.add(k)
            cles.setdefault(a, {})[k] = conf
        comptes[a] = c
    return cles, comptes


def parcourir_bodacc(cles: dict, debut: dt.date, fin: dt.date, ouvrir=urllib.request.urlopen,
                     echantillon_max: int = 200_000, graine: int = 19102026) -> dict:
    """Une passe sur les avis de dépôt : appariement et délais clôture-parution."""
    hasard = random.Random(graine)
    trouves = {a: {} for a in cles}
    delais = {a: [] for a in cles}
    vus = {a: 0 for a in cles}
    stats = {"avis_lus": 0, "sans_siren": 0, "sans_cloture": 0, "libelle_famille": None, "exemples": []}
    where = f"familleavis=\"{FAMILLE_DEPOT}\" and dateparution >= date'{debut}' and dateparution < date'{fin}'"
    for ligne in flux_csv(BODACC, "dateparution,familleavis_lib,registre,depot", where, ouvrir):
        stats["avis_lus"] += 1
        if stats["libelle_famille"] is None:
            stats["libelle_famille"] = ligne.get("familleavis_lib")
        if len(stats["exemples"]) < 3:
            stats["exemples"].append({"registre": ligne.get("registre"), "depot": ligne.get("depot")})
        s = siren_de(ligne.get("registre"))
        if s is None:
            stats["sans_siren"] += 1
            continue
        cl = date_cloture_de(ligne.get("depot"))
        if cl is None:
            stats["sans_cloture"] += 1
            continue
        a = cl.year
        if a not in cles:
            continue
        k = cle(s, cl)
        if k not in cles[a]:
            continue
        m = MOTIF_ISO.search(ligne.get("dateparution") or "")
        parution = dt.date(*map(int, m.groups())) if m else None
        precedent = trouves[a].get(k)
        if precedent is None or (parution and parution < precedent):
            trouves[a][k] = parution
        if parution and precedent is None:
            vus[a] += 1
            lag = (parution - cl).days
            if len(delais[a]) < echantillon_max:
                delais[a].append(lag)
            else:
                j = hasard.randrange(vus[a])
                if j < echantillon_max:
                    delais[a][j] = lag
    return {"trouves": trouves, "delais": delais, "stats": stats}


def quantiles(valeurs: list[int]) -> dict:
    if not valeurs:
        return {}
    v = sorted(valeurs)
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]  # noqa: E731
    return {"p10": q(0.10), "p50": q(0.50), "p90": q(0.90), "p99": q(0.99), "n": len(v)}


def verdict(taux: dict[int, float]) -> dict:
    if not taux:
        return {"code": "arret", "regle": "aucune année mesurée"}
    a, t = min(taux.items(), key=lambda kv: kv[1])
    if t >= SEUIL_PRINCIPAL:
        code = "principal-dates"
    elif t >= SEUIL_ARRET:
        code = "principal-dates-biais-declare"
    else:
        code = "arret"
    return {"code": code, "regle": f"année la plus faible {a} : {t:.1%} des bilans retrouvent leur avis de dépôt"}


def executer(annees: list[int], ouvrir=urllib.request.urlopen, aujourdhui: dt.date | None = None) -> dict:
    aujourdhui = aujourdhui or dt.date.today()
    cles, comptes = charger_bilans(annees, ouvrir)
    debut = dt.date(min(annees), 1, 1)
    fin_brute = dt.date(max(annees) + FENETRE_PARUTION_MOIS // 12 + 1, 1, 1)
    fin = min(fin_brute, aujourdhui + dt.timedelta(days=1))
    res = parcourir_bodacc(cles, debut, fin, ouvrir)
    par_annee, taux = {}, {}
    for a in annees:
        n = len(cles.get(a, {}))
        trouves = res["trouves"].get(a, {})
        par_conf = {}
        for k, conf in cles.get(a, {}).items():
            e = par_conf.setdefault(conf, {"bilans": 0, "avec_avis": 0})
            e["bilans"] += 1
            e["avec_avis"] += k in trouves
        for e in par_conf.values():
            e["taux"] = e["avec_avis"] / e["bilans"] if e["bilans"] else None
        # Règle déterministe (protocole v1.2) : est confidentiel tout bilan dont
        # le libellé de confidentialité contient « confid ». Le verdict porte
        # sur les autres, conformément à P1.
        nc = [e for conf, e in par_conf.items() if not MOTIF_CONFID.search(conf)]
        n_nc, t_nc = sum(e["bilans"] for e in nc), sum(e["avec_avis"] for e in nc)
        par_annee[a] = {
            "non_confidentiels": {"bilans": n_nc, "avec_avis": t_nc, "taux": t_nc / n_nc if n_nc else None},
            "bilans_cles_distinctes": n,
            "avec_avis": len(trouves),
            "taux": len(trouves) / n if n else None,
            "par_confidentialite": par_conf,
            "effectifs_lus": comptes[a],
            "delai_cloture_parution_jours": quantiles(res["delais"].get(a, [])),
            "fenetre_parution_incomplete": fin < dt.date(a + FENETRE_PARUTION_MOIS // 12 + 1, 1, 1),
        }
        if n_nc:
            taux[a] = t_nc / n_nc
    return {
        "objet": "P0 v1.2, jointure bilans (ratios BCE/INPI) et avis de dépôt (BODACC C)",
        "regle": "métadonnées de disponibilité seules ; aucun montant ; aucune annonce de procédure collective",
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "annees": annees,
        "fenetre_parution": [debut.isoformat(), fin.isoformat()],
        "bodacc": res["stats"],
        "par_annee": {str(a): v for a, v in par_annee.items()},
        "verdict": verdict(taux),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--annees", default=ANNEES_DEFAUT)
    p.add_argument("--sortie", default=None)
    a = p.parse_args(argv)
    rapport = executer([int(x) for x in a.annees.split(",") if x.strip()])
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)
    chemin = a.sortie or f"p0-jointure-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + "\n")
    print(texte)
    print(f"\nRapport : {chemin}\nSHA-256 : {hashlib.sha256((texte + chr(10)).encode()).hexdigest()}"
          f"\nVerdict : {rapport['verdict']['code']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
