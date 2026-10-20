"""P0 v1.4, structure de la liasse et profondeur des bilans.

Deux questions, sur métadonnées seules :
1. Liasse des bilans détaillés (Signaux Faibles) : sous quels noms de clés sont
   rangés les postes ? Pour chaque type de bilan (C, S, K), part des bilans où
   chaque clé est présente, sur quelques groupes de lignes répartis dans le
   fichier. Les montants sont lus par le décodeur parquet mais jamais conservés
   ni rapportés : seuls les NOMS des clés sortent.
2. Profondeur des ratios : nombre de bilans par année de clôture, de 2000 à
   l'année en cours (effectifs seuls), pour fixer la première origine effective
   du développement (v1.4).

Codes attendus, selon la documentation technique des comptes annuels de l'INPI
(v1.8, avril 2021) : total de l'actif CO (complet, consolidé) et 110 (simplifié),
colonne m3 « Net année N » ; total I du passif DL (complet, consolidé, colonne
m1) et 142 (simplifié, colonne m3) ; chiffre d'affaires net FJ (complet,
consolidé), sans total équivalent en simplifié.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0_faisabilite import SOURCE_SF_PARQUET, _agregat  # noqa: E402
from p0_sources import FichierAvecReprise, avec_reprise, journal  # noqa: E402

RATIOS = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/ratios_inpi_bce"
CODES_ATTENDUS = ("CO", "110", "DL", "142", "FJ")
GROUPES_LUS = 5


def cles_liasse(url: str = SOURCE_SF_PARQUET, groupes: int = GROUPES_LUS) -> dict:
    import pyarrow.parquet as pq

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    n = pf.metadata.num_row_groups
    indices = sorted({round(i * (n - 1) / max(1, groupes - 1)) for i in range(groupes)})
    par_type = {}
    for g in indices:
        journal(f"groupe de lignes {g + 1}/{n}")
        t = avec_reprise(pf.read_row_group, g, columns=["type_bilan", "liasse"])
        for typ, liasse in zip(t.column("type_bilan").to_pylist(), t.column("liasse").to_pylist()):
            e = par_type.setdefault(typ or "(vide)", {"bilans": 0, "cles": {}})
            e["bilans"] += 1
            for cle_, _montant in (liasse or []):  # le montant est ignoré
                e["cles"][cle_] = e["cles"].get(cle_, 0) + 1
    sortie = {}
    for typ, e in sorted(par_type.items()):
        parts = {k: round(v / e["bilans"], 4) for k, v in sorted(e["cles"].items())}
        sortie[typ] = {
            "bilans": e["bilans"],
            "cles_distinctes": len(parts),
            "codes_attendus": {c: {k: p for k, p in parts.items() if k == c or k.startswith(c + "_")
                                   or k.startswith(c + ".") or k.endswith("_" + c)}
                               for c in CODES_ATTENDUS},
            "cles": parts,
        }
    return {"groupes_lus": [i + 1 for i in indices], "groupes_total": n,
            "octets_lus": f.octets_lus, "par_type": sortie}


def profondeur(annees: range, ouvrir=urllib.request.urlopen) -> dict:
    res = {}
    for a in annees:
        where = f"date_cloture_exercice >= date'{a}-01-01' and date_cloture_exercice < date'{a + 1}-01-01'"
        res[str(a)] = avec_reprise(_agregat, RATIOS, "count(*) as n", where, ouvrir).get("n")
    return res


def executer(ouvrir=urllib.request.urlopen, url_sf=SOURCE_SF_PARQUET, groupes=GROUPES_LUS,
             annees=None) -> dict:
    annees = annees or range(2000, dt.date.today().year + 1)
    journal("profondeur des ratios par année de clôture")
    p = profondeur(annees, ouvrir)
    journal("clés de la liasse")
    liasse = cles_liasse(url_sf, groupes)
    return {
        "objet": "P0 v1.4, structure de la liasse (noms de clés) et profondeur des ratios",
        "regle": "noms de clés et effectifs seuls ; aucun montant rapporté ; aucune issue",
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "profondeur_ratios": p,
        "liasse": liasse,
    }


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.split("\n\n")[0]).parse_args(argv)
    rapport = executer()
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)
    chemin = f"p0-structure-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + "\n")
    print("profondeur : " + " ".join(f"{a}:{n}" for a, n in rapport["profondeur_ratios"].items()), file=sys.stderr)
    for typ, e in rapport["liasse"]["par_type"].items():
        print(f"type {typ} : {e['bilans']} bilans, {e['cles_distinctes']} clés ; codes attendus : "
              + json.dumps(e["codes_attendus"], ensure_ascii=False), file=sys.stderr)
        print(f"  20 premières clés : {list(e['cles'])[:20]}", file=sys.stderr)
    print(f"\nRapport : {chemin}\nSHA-256 : {hashlib.sha256((texte + chr(10)).encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
