"""Palier 1 de la boucle de supervision : extraction des dossiers de cas, datés et pseudonymisés.

Spécification : methode/boucle-de-supervision.md (note gelée le 21/10/2026), section 7.2.

Pour une liste de SIREN (cas tirés et pièges), lit les mêmes instantanés que la construction
des cas (ingestion/construire.py) et ne conserve, par construction, que l'information parue
STRICTEMENT avant t0 :
  bilans     connus au sens de P2 (avis de dépôt paru avant t0) : clôture, parution, type,
             ratios des groupes 1 et 2, ordre de grandeur du total de bilan (log10 arrondi
             au dixième), indicateur de confidentialité ;
  dépôts     avis de dépôt des comptes parus avant t0 (clôture, première parution) ;
  procédures jugements parus avant t0, classés comme en P1 (nature, date de jugement, parution) ;
  radiations, dissolutions, fusions  parues avant t0 ;
  Sirene     périodes débutant au plus tard à t0 ; une date de fin postérieure à t0 est
             effacée (elle révélerait l'avenir) ; date de création si antérieure à t0.

Pseudonymisation : chaque dossier est indexé par un identifiant opaque, « K » suivi de dix
caractères d'un HMAC-SHA256 du SIREN sous une clé secrète tirée au hasard. Les dossiers ne
contiennent ni SIREN, ni dénomination, ni adresse. La correspondance SIREN -> identifiant et
la clé sont écrites dans des fichiers séparés, qui ne quittent pas le serveur et ne sont
jamais lus par les outils.
"""

import argparse
import datetime as dt
import hashlib
import hmac
import json
import math
import os
import secrets
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "ingestion"))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
import construire as co  # noqa: E402
from extraire import DOSSIER_DEFAUT  # noqa: E402

T0_PALIER1 = dt.date(2020, 9, 30)
RATIOS_SERVIS = co.GROUPE1 + co.GROUPE2


def identifiant(cle: bytes, siren: str) -> str:
    return "K" + hmac.new(cle, siren.encode(), hashlib.sha256).hexdigest()[:10]


def _iso(d):
    return d.isoformat() if d else None


def _ordre(total):
    return None if total is None or total <= 0 else round(math.log10(total), 1)


def extraire(dossier: str, sirens: list, t0: dt.date = T0_PALIER1) -> dict:
    """{siren: dossier} ; toute information parue à t0 ou après est écartée ici."""
    voulus = set(sirens)
    R, par_siren, _m, _c = co.bilans_dates(dossier, t0)
    evts, autres, _c2 = co.procedures(dossier)
    modifs, _c3 = co.modifications(dossier)
    periodes, creation, _c4 = co.sirene(dossier)
    dpc, _c5 = co._lire(dossier, "bodacc-dpc.parquet", ["dateparution", "registre", "depot"])
    depots = {}
    for r, p, d in zip(dpc.column("registre").to_pylist(), dpc.column("dateparution").to_pylist(),
                       dpc.column("depot").to_pylist()):
        s = co._siren(r)
        if s not in voulus:
            continue
        m, p = co.MOTIF_CLOTURE.search(d or ""), co._date(p)
        if m and p and p < t0:
            k = m.group(1)
            if k not in depots.setdefault(s, {}) or p < depots[s][k]:
                depots[s][k] = p
    out = {}
    for s in sirens:
        bilans = []
        for c, p, (i, _zc), tot in par_siren.get(s, []):
            if p >= t0:
                continue
            bilans.append({"cloture": _iso(c), "parution": _iso(p), "type": R.type[i],
                           "confidentiel": bool(co.MOTIF_CONFID.search(str(R.conf[i] or ""))),
                           "ordre_total_bilan": _ordre(tot),
                           "ratios": {k: R.valeur(k, i) for k in RATIOS_SERVIS}})
        per = []
        for d, f, cj, naf, nom in periodes.get(s, []):
            if d is not None and d > t0:
                continue
            per.append({"debut": _iso(d), "fin": _iso(f) if f is not None and f <= t0 else None,
                        "categorie_juridique": cj, "naf": naf, "nomenclature": nom})
        cr = creation.get(s)
        rad = autres["radiations"].get(s)
        out[s] = {
            "t0": t0.isoformat(),
            "bilans": bilans,
            "depots": sorted(({"cloture": c, "parution": _iso(p)} for c, p in depots.get(s, {}).items()),
                             key=lambda x: x["parution"]),
            "procedures": [{"parution": _iso(p), "jugement": _iso(dj), "nature": n}
                           for p, dj, n in evts.get(s, []) if p < t0],
            "radiation": _iso(rad) if rad is not None and rad < t0 else None,
            "modifications": [{"parution": _iso(p), "evenement": e} for p, e in modifs.get(s, []) if p < t0],
            "sirene": per,
            "creation": _iso(cr) if cr is not None and cr <= t0 else None,
        }
    return out


def pseudonymiser(dossiers: dict, cle: bytes) -> tuple[dict, dict]:
    """(dossiers indexés par identifiant opaque, correspondance SIREN -> identifiant)."""
    corr = {s: identifiant(cle, s) for s in dossiers}
    if len(set(corr.values())) != len(corr):
        raise RuntimeError("collision d'identifiants")
    return {corr[s]: v for s, v in dossiers.items()}, corr


def ajouter_previsions(dossiers_siren: dict, chemin_prevision: str, origine: int = 2020) -> int:
    """Ajoute p_dedie (modèle dédié, au seul t0) aux dossiers des SIREN de l'origine cible."""
    import pyarrow.parquet as pq

    t = pq.read_table(chemin_prevision, columns=["siren", "origine", "p_dedie"])
    n = 0
    for s, o, p in zip(t.column("siren").to_pylist(), t.column("origine").to_pylist(),
                       t.column("p_dedie").to_pylist()):
        if int(o) == origine and s in dossiers_siren:
            dossiers_siren[s]["prevision"] = {"p": float(p), "fichier": os.path.basename(chemin_prevision)}
            n += 1
    return n


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dossier", default=DOSSIER_DEFAUT)
    p.add_argument("--sirens", required=True, help="fichier texte, un SIREN par ligne")
    p.add_argument("--prevision", required=True, help="prevision-dediee-2020-*.parquet")
    args = p.parse_args(argv)
    with open(args.sirens, encoding="utf-8") as f:
        sirens = [l.strip() for l in f if l.strip()]
    doss = extraire(args.dossier, sirens)
    n = ajouter_previsions(doss, os.path.join(args.dossier, os.path.basename(args.prevision)))
    cle = secrets.token_bytes(32)
    pseudo, corr = pseudonymiser(doss, cle)
    h = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
    chemins = {}
    for nom, contenu in (("dossiers", pseudo), ("correspondance", corr), ("cle", {"cle": cle.hex()})):
        chemins[nom] = os.path.join(args.dossier, f"palier1-{nom}-{h}.json")
        with open(chemins[nom], "w", encoding="utf-8") as f:
            json.dump(contenu, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.chmod(chemins[nom], 0o600)
    print(f"{len(pseudo)} dossiers, {n} avec prévision", file=sys.stderr)
    for nom, c in chemins.items():
        print(f"{nom} : {c}\nSHA-256 : {co.sha256_fichier(c)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
