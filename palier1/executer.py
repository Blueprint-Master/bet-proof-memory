"""Palier 1 de la boucle de supervision : exécution de D, T0, T1 et B sur une liste de cas.

Lit les dossiers pseudonymisés et, dans le fichier des cas, le seul scénario de chaque cas
(l'issue et le poids n'en sont jamais lus ici). Écrit une exécution par ligne (JSONL), dès
qu'elle est finie ; une reprise saute les couples (système, cas) déjà écrits (clé
d'idempotence). S'arrête avant de dépasser le nombre total d'appels de modèle autorisé.

Exemple (pilote) :
  .venv/bin/python3 palier1/executer.py --dossiers ~/bpm-donnees/palier1-pilote-dossiers-....json \\
      --cas ~/bpm-donnees/palier1-pilote-cas-....json --lgd 0.8995 \\
      --fournisseur compatible --base https://api.mistral.ai/v1 --modele <nom exact> --cle-env MISTRAL_API_KEY \\
      --sortie ~/bpm-donnees/palier1-pilote-executions.jsonl --max-appels 600
"""

import argparse
import json
import os
import sys

import modeles as mo
import reference as rf
import systemes as sy

ORDRE = ("D", "T0", "T1", "B")


def questions(chemin_cas: str) -> list:
    """[(identifiant, scénario)] triés par identifiant ; rien d'autre n'est retenu du fichier."""
    with open(chemin_cas, encoding="utf-8") as f:
        cas = json.load(f)
    return sorted((k, v["scenario"]) for k, v in cas.items())


def deja_faits(chemin: str) -> set:
    if not os.path.exists(chemin):
        return set()
    with open(chemin, encoding="utf-8") as f:
        return {(e["systeme"], e["cas"]) for e in map(json.loads, filter(str.strip, f))}


def executer(modele, dossiers: dict, lgd: float, qs: list, systemes: list, chemin: str, max_appels: int,
             plafond: dict = sy.PLAFOND) -> dict:
    faits, appels, n = deja_faits(chemin), 0, 0
    with open(chemin, "a", encoding="utf-8") as f:
        for k, sc in qs:
            for s in (x for x in ORDRE if x in systemes):
                if (s, k) in faits:
                    continue
                besoin = {"D": 0, "T0": 1}.get(s, plafond["appels_modele"])
                if appels + besoin > max_appels:
                    return {"executions": n, "appels_modele": appels, "arret": "plafond total d'appels atteint"}
                if s == "D":
                    e = rf.decider(dossiers, lgd, k, sc)
                elif s == "T0":
                    e = sy.executer_T0(modele, k, dossiers[k]["t0"], sc)
                elif s == "T1":
                    e = sy.executer_T1(modele, dossiers, lgd, k, sc, plafond)
                else:
                    e = sy.executer_B(modele, dossiers, lgd, k, sc, plafond)
                e["modele"] = None if s == "D" else modele.nom
                appels += e["cout"]["appels_modele"]
                f.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")
                f.flush()
                n += 1
    return {"executions": n, "appels_modele": appels, "arret": None}


def main(argv=None) -> int:
    pa = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    pa.add_argument("--dossiers", required=True)
    pa.add_argument("--cas", required=True)
    pa.add_argument("--lgd", type=float, required=True)
    pa.add_argument("--systemes", default=",".join(ORDRE))
    pa.add_argument("--fournisseur", choices=("compatible", "anthropic"), required=True)
    pa.add_argument("--base", help="URL de base de l'interface compatible")
    pa.add_argument("--modele", required=True, help="nom exact et daté du modèle")
    pa.add_argument("--cle-env", required=True, help="variable d'environnement qui porte la clé")
    pa.add_argument("--sortie", required=True)
    pa.add_argument("--max-appels", type=int, required=True)
    a = pa.parse_args(argv)
    m = (mo.Anthropic(a.modele, a.cle_env) if a.fournisseur == "anthropic"
         else mo.CompatibleOpenAI(a.base, a.modele, a.cle_env))
    with open(a.dossiers, encoding="utf-8") as f:
        dossiers = json.load(f)
    r = executer(m, dossiers, a.lgd, questions(a.cas), a.systemes.split(","), a.sortie, a.max_appels)
    print(json.dumps(r, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
