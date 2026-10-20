"""P0 v1.2, remplissage des champs des ratios BCE/INPI par niveau de confidentialité.

Question : que cache exactement un bilan « Partiellement confidentiel » ? Pour
chaque champ du jeu de ratios, et pour chaque niveau de confidentialité, la part
des bilans où le champ est renseigné, sur les années de clôture demandées.

Métadonnées de disponibilité seules : des comptages de valeurs non nulles,
jamais une valeur, une moyenne ou une distribution. Aucune issue lue.

Dépendances : Python 3.10+ seul ; réutilise les fonctions HTTP de p0_faisabilite.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0_faisabilite import _agregat, _get_json  # noqa: E402

RATIOS = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/ratios_inpi_bce"
NIVEAUX = ("Public", "Partiellement confidentiel", "Partiellement confidentiel (RAPCAC)")
ANNEES_DEFAUT = "2019,2022"
CLES = {"siren", "date_cloture_exercice", "confidentiality", "type_bilan"}


def mesurer(annees: list[int], ouvrir=urllib.request.urlopen) -> dict:
    champs = [f["name"] for f in _get_json(RATIOS, ouvrir).get("fields", []) if f.get("name") not in CLES]
    res = {}
    for a in annees:
        periode = f"date_cloture_exercice >= date'{a}-01-01' and date_cloture_exercice < date'{a + 1}-01-01'"
        for niv in NIVEAUX:
            base = f"{periode} and confidentiality=\"{niv}\""
            n = _agregat(RATIOS, "count(*) as n", base, ouvrir).get("n") or 0
            ligne = {"bilans": n, "remplissage": {}}
            if n:
                for c in champs:
                    k = _agregat(RATIOS, "count(*) as n", f"{base} and {c} is not null", ouvrir).get("n") or 0
                    ligne["remplissage"][c] = round(k / n, 4)
            res.setdefault(str(a), {})[niv] = ligne
    return {
        "objet": "P0 v1.2, remplissage des champs des ratios par niveau de confidentialité",
        "regle": "comptages de valeurs non nulles seuls ; aucune valeur ; aucune issue",
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "champs": champs,
        "par_annee": res,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--annees", default=ANNEES_DEFAUT)
    a = p.parse_args(argv)
    rapport = mesurer([int(x) for x in a.annees.split(",") if x.strip()])
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)
    chemin = f"p0-remplissage-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + "\n")
    # Tableau lisible : un champ par ligne, une colonne par (année, niveau).
    cols = [(an, niv) for an in rapport["par_annee"] for niv in NIVEAUX]
    print("champ;" + ";".join(f"{an} {niv[:14]}" for an, niv in cols), file=sys.stderr)
    for c in rapport["champs"]:
        vals = [rapport["par_annee"][an][niv]["remplissage"].get(c) for an, niv in cols]
        print(c + ";" + ";".join("" if v is None else f"{v:.0%}" for v in vals), file=sys.stderr)
    print(f"\nRapport : {chemin}\nSHA-256 : {hashlib.sha256((texte + chr(10)).encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
