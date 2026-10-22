#!/usr/bin/env bash
# Palier 1 : tirage principal, exécution de D, T0, T1, B, puis analyse à la fin de l'exécution.
# Graines publiées avant le tirage (methode/boucle-de-supervision-palier1-tirage.md, section 6).
# À lancer depuis ~/bet-proof-memory, après avoir chargé MISTRAL_API_KEY dans la session.
set -euo pipefail
B=~/bpm-donnees
PY=.venv/bin/python3
[ -n "${MISTRAL_API_KEY:-}" ] || { echo "clé absente : la charger avant le lancement"; exit 1; }
[ -z "$(ls $B/palier1-principal-dossiers-*.json 2>/dev/null)" ] || { echo "un tirage principal existe déjà : arrêt"; exit 1; }
$PY palier1/tirer.py --cas $B/cas-dev.parquet --prevision $B/prevision-dediee-2020-20261022-062330.parquet \
    --graine 729277263 --phase principal --exclure $B/palier1-pilote-tirage-20261022-141456.json \
    > $B/palier1-principal-tirage.log 2>&1
D=$(ls -t $B/palier1-principal-dossiers-*.json | head -1)
C=$(ls -t $B/palier1-principal-cas-*.json | head -1)
X=$B/palier1-principal-executions.jsonl
nohup bash -c "$PY palier1/executer.py --dossiers $D --cas $C --lgd 0.8995 --fournisseur compatible \
    --base https://api.mistral.ai/v1 --modele mistral-large-4-0 --cle-env MISTRAL_API_KEY --sortie $X \
    --max-appels 2000 > $B/palier1-principal-executer.log 2>&1; \
    $PY palier1/verificateurs.py --cas $C --executions $X --lgd 0.8995 --graine 371935227 \
    > $B/palier1-principal-rapport.json 2> $B/palier1-principal-analyse.log; \
    sha256sum $X $B/palier1-principal-rapport.json >> $B/palier1-principal-analyse.log" > /dev/null 2>&1 &
echo "tirage : $B/palier1-principal-tirage.log"
cat $B/palier1-principal-tirage.log
echo "exécution lancée en arrière-plan ; suivi : tail -1 $B/palier1-principal-executer.log ; fin à 1 360 exécutions"
