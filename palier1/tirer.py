"""Palier 1 de la boucle de supervision : tirage des cas et des pièges, avec graine publiée.

Spécification : methode/boucle-de-supervision.md, sections 7.2 et 7.5 ; choix T1 à T8 :
methode/boucle-de-supervision-palier1-tirage.md.

Populations, à t0 = 30/09/2020 :
  éligibles        cas de l'origine 2020 (cas-dev.parquet, règles P1 à P3 du juge du réel) qui
                   ont une prévision du modèle dédié ; issue = défaillance à 548 jours (P3) ;
  pièges avant     sociétés qui passent les filtres de P1 sauf un : une liquidation judiciaire
                   est en cours à t0 au sens de l'outil `etat` (annonces parues avant t0) ;
  pièges après     cas éligibles dont un jugement de liquidation judiciaire (ouverture,
                   conversion d'une sauvegarde, résolution d'un plan) est daté dans
                   ]t0, t0 + 548 jours].

Ordre du tirage, figé : pièges après, puis défaillants, puis non défaillants (tous hors des
pièges après et des exclus), puis pièges avant ; puis un scénario par cas, dans l'ordre de la
liste. Chaque tirage se fait sans remise sur une liste triée par SIREN, avec
numpy.random.default_rng(graine). La phase « pilote » (25 / 25 / 5 / 5) précède la phase
« principal » (150 / 150 / 20 / 20, agrandie avant exécution si l'analyse de puissance
l'exige), qui exclut les SIREN du pilote.

Fichiers écrits dans le dossier de données (jamais versés au dépôt) :
  palier1-<phase>-dossiers-<h>.json        servis aux outils : pseudonymisés, sans issue
  palier1-<phase>-cas-<h>.json             pour les vérificateurs seulement : type, scénario,
                                           issue, poids, par identifiant opaque
  palier1-<phase>-tirage-<h>.json          SIREN, type, scénario, issue ; graine ; effectifs
  palier1-<phase>-correspondance-<h>.json, palier1-<phase>-cle-<h>.json
Tous en lecture seule pour le propriétaire (600).
"""

import argparse
import datetime as dt
import json
import os
import secrets
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "ingestion"))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
import construire as co  # noqa: E402
import extraire_cas as ex  # noqa: E402
import outils as ou  # noqa: E402
from extraire import DOSSIER_DEFAUT  # noqa: E402
from p0_sources import forme_p1  # noqa: E402

NATURES_LJ = {"OUV-LJ", "CONV-SAUV-LJ", "RESOL-LJ"}
EFFECTIFS = {"pilote": {"defaillants": 25, "non_defaillants": 25, "piege_avant": 5, "piege_apres": 5},
             "principal": {"defaillants": 150, "non_defaillants": 150, "piege_avant": 20, "piege_apres": 20}}


def population(chemin_cas: str, chemin_prevision: str, origine: int) -> dict:
    """{siren: issue} des cas de l'origine qui ont une prévision du modèle dédié."""
    import pyarrow.parquet as pq

    cas = pq.read_table(chemin_cas, columns=["siren", "origine", "issue"])
    prev = pq.read_table(chemin_prevision, columns=["siren", "origine"])
    avec = {s for s, o in zip(prev.column("siren").to_pylist(), prev.column("origine").to_pylist())
            if int(o) == origine}
    return {s: int(y) for s, o, y in zip(cas.column("siren").to_pylist(), cas.column("origine").to_pylist(),
                                          cas.column("issue").to_pylist()) if int(o) == origine and s in avec}


def candidats(dossier: str, t0: dt.date, pop: dict) -> tuple[list, list]:
    """(pièges avant, pièges après), triés par SIREN."""
    _R, bilans, _m, _c = co.bilans_dates(dossier, t0)
    periodes, creation, _c2 = co.sirene(dossier)
    evts, info, _c3 = co.procedures(dossier)
    rad = info["radiations"]
    fin = t0 + dt.timedelta(days=co.HORIZON_JOURS)
    avant = []
    for s, liste in bilans.items():
        if not any(p < t0 for _c, p, _i, _t in liste):
            continue
        per = co.periode_a(periodes.get(s, []), t0)
        if per is None or not forme_p1(per[0]):
            continue
        cr = creation.get(s)
        if (cr is not None and cr > t0) or (s in rad and rad[s] < t0):
            continue
        if ou.etat_procedure((p, dj, n) for p, dj, n in evts.get(s, []) if p < t0) == "LJ":
            avant.append(s)
    apres = [s for s in pop if any(n in NATURES_LJ and t0 < dj <= fin for _p, dj, n in evts.get(s, []))]
    return sorted(avant), sorted(apres)


def tirer(pop: dict, avant: list, apres: list, graine: int, effectifs: dict, exclus=()) -> list:
    """[{siren, type, scenario, y}] dans l'ordre du tirage."""
    rng = np.random.default_rng(graine)
    exclus = set(exclus)

    def prendre(liste, k, nom):
        liste = sorted(set(liste) - exclus)
        if len(liste) < k:
            raise ValueError(f"{nom} : {len(liste)} candidats pour {k}")
        choix = [liste[i] for i in rng.choice(len(liste), size=k, replace=False)] if k else []
        exclus.update(choix)
        return choix

    out = [{"siren": s, "type": "piege_apres"} for s in prendre(apres, effectifs["piege_apres"], "pièges après")]
    out += [{"siren": s, "type": "eligible", "y": 1} for s in
            prendre([s for s, y in pop.items() if y == 1], effectifs["defaillants"], "défaillants")]
    out += [{"siren": s, "type": "eligible", "y": 0} for s in
            prendre([s for s, y in pop.items() if y == 0], effectifs["non_defaillants"], "non défaillants")]
    out += [{"siren": s, "type": "piege_avant"} for s in prendre(avant, effectifs["piege_avant"], "pièges avant")]
    sc = sorted(ou.SCENARIOS)
    for c, i in zip(out, rng.integers(0, len(sc), size=len(out))):
        c["scenario"] = sc[int(i)]
    return out


def poids(pop: dict, effectifs: dict) -> dict:
    """Poids de redressement : part dans l'origine divisée par part dans l'échantillon."""
    p = sum(pop.values()) / len(pop)
    n = effectifs["defaillants"] + effectifs["non_defaillants"]
    return {1: p / (effectifs["defaillants"] / n), 0: (1 - p) / (effectifs["non_defaillants"] / n)}


def preparer(dossier: str, chemin_cas: str, chemin_prevision: str, t0: dt.date, graine: int,
             effectifs: dict, exclus=(), cle: bytes = None) -> dict:
    """Tirage, extraction, pseudonymisation et contrôles ; rien n'est écrit."""
    pop = population(chemin_cas, chemin_prevision, t0.year)
    avant, apres = candidats(dossier, t0, pop)
    tir = tirer(pop, avant, apres, graine, effectifs, exclus)
    w = poids(pop, effectifs)
    sirens = [c["siren"] for c in tir]
    bruts = ex.extraire(dossier, sirens, t0)
    n_prev = ex.ajouter_previsions(bruts, chemin_prevision, t0.year)
    cle = cle or secrets.token_bytes(32)
    doss, corr = ex.pseudonymiser(bruts, cle)
    reg = ou.Registre(doss, lgd=1.0)
    for c in tir:
        e = reg.appeler("etat", corr[c["siren"]], t0.isoformat())["donnees"]["procedure_en_cours"]
        a_prev = "prevision" in bruts[c["siren"]]
        if (c["type"] == "piege_avant") != (e == "LJ"):
            raise RuntimeError(f"contrôle : état {e} incohérent avec le type {c['type']}")
        if c["type"] != "piege_avant" and not a_prev:
            raise RuntimeError("contrôle : cas sans prévision")
    cas = {}
    for c in tir:
        x = {"type": c["type"], "scenario": c["scenario"], "t0": t0.isoformat()}
        if c["type"] == "eligible":
            x.update(y=c["y"], w=w[c["y"]])
        cas[corr[c["siren"]]] = x
    resume = {"graine": graine, "t0": t0.isoformat(), "effectifs": effectifs,
              "population": {"cas": len(pop), "defaillants": sum(pop.values()),
                             "candidats_piege_avant": len(avant), "candidats_piege_apres": len(apres)},
              "poids": {"defaillant": w[1], "non_defaillant": w[0]}, "previsions_ajoutees": n_prev,
              "scenarios": {s: sum(c["scenario"] == s for c in tir) for s in sorted(ou.SCENARIOS)}}
    return {"tirage": tir, "dossiers": doss, "cas": cas, "correspondance": corr, "cle": cle, "resume": resume}


def lire_exclus(chemins) -> set:
    out = set()
    for c in chemins or []:
        with open(c, encoding="utf-8") as f:
            out.update(x["siren"] for x in json.load(f)["tirage"])
    return out


def main(argv=None) -> int:
    pa = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    pa.add_argument("--dossier", default=DOSSIER_DEFAUT)
    pa.add_argument("--cas", required=True, help="cas-dev.parquet")
    pa.add_argument("--prevision", required=True, help="prevision-dediee-2020-*.parquet")
    pa.add_argument("--graine", type=int, required=True, help="graine publiée au registre AVANT le tirage")
    pa.add_argument("--phase", choices=sorted(EFFECTIFS), required=True)
    pa.add_argument("--exclure", nargs="*", help="fichiers de tirage antérieurs (le pilote, pour le principal)")
    pa.add_argument("--defaillants", type=int)
    pa.add_argument("--non-defaillants", type=int)
    args = pa.parse_args(argv)
    eff = dict(EFFECTIFS[args.phase])
    if args.defaillants:
        eff["defaillants"] = args.defaillants
    if args.non_defaillants:
        eff["non_defaillants"] = args.non_defaillants
    r = preparer(args.dossier, args.cas, args.prevision, ex.T0_PALIER1, args.graine, eff,
                 lire_exclus(args.exclure))
    h = f"{dt.datetime.now():%Y%m%d-%H%M%S}"
    sorties = {"dossiers": r["dossiers"], "cas": r["cas"], "tirage": {"resume": r["resume"], "tirage": r["tirage"]},
               "correspondance": r["correspondance"], "cle": {"cle": r["cle"].hex()}}
    print(json.dumps(r["resume"], ensure_ascii=False, indent=1), file=sys.stderr)
    for nom, contenu in sorties.items():
        chemin = os.path.join(args.dossier, f"palier1-{args.phase}-{nom}-{h}.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(contenu, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.chmod(chemin, 0o600)
        print(f"{nom} : {chemin}\nSHA-256 : {co.sha256_fichier(chemin)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
