# Registre des empreintes

Chaque ligne est publiée par un commit daté AVANT tout accès aux issues concernées. L'empreinte est le SHA-256 du fichier tel que versé dans ce dépôt ; pour vérifier : `sha256sum <fichier>`.

| Date (UTC) | Document | SHA-256 | Statut |
|---|---|---|---|
| 2026-10-19 | protocole/q1-v1.1.md | 698f39cea16d60ea3899b0eda84432f0b57b08756bfdec05d500f88e3b60994d | Protocole Q1 en vigueur ; aucune donnée lue |
| 2026-10-19 | p0/p0_faisabilite.py | dddda99c9bd803cdfa861a9160c69acfdd6ad459dcc63c56337ddeca4dee71ab | Outil P0, avant sa première exécution |
| 2026-10-19 | p0-rapport-20261019-214418.json (bpm-prod, non versé) | a2daa7b52c2d9f1327798e00e07579373aba16a1b7d6859797bab905fe4ec4b9 | Rapport P0 n° 1 : verdict « arret-sans-date » ; bilans Signaux Faibles sans date de dépôt (6 368 964 lignes, clôtures de 1919 à 2029) ; aucune issue lue |
| 2026-10-19 | p0/p0_faisabilite.py (v1.0.1) | 944d89a88e75b5b811c3d28c0ef029f5c2a6b460368251cb686602336fecc34a | Correctif : réponses gzip des API Opendatasoft (échec du rapport P0 n° 1 sur ratios et BODACC) ; logique de verdict inchangée |
| 2026-10-19 | p0-rapport-20261019-215155.json (bpm-prod, non versé) | a81b6241381c5dbba71d3caf55439ff9a6532fe8baa03e8e786f9eec0aae6af5 | Rapport P0 n° 2 (outil v1.0.1, sources ratios et BODACC) : verdict « arret-sans-date » confirmé ; ratios BCE/INPI 6 813 145 lignes, champ « confidentiality » présent, aucune date de dépôt ; BODACC 51 094 823 annonces du 02/01/2008 au 18/10/2026, champ « depot » présent ; aucune issue lue |
| 2026-10-19 | protocole/q1-v1.2.md | 17a86bcafa65ab56229d410d008d79f266bbde03036694023c9b418fc8d45efb | Protocole Q1 en vigueur, remplace la v1.1 : date d'information = parution de l'avis de dépôt au BODACC C ; amendement fondé sur des métadonnées seules ; aucune issue lue ; validé par Rémi |
| 2026-10-19 | p0/p0_jointure.py | dce7d1ffc692fd5efe4d86efab4677945d881797f29b85dbdba861aeed98a820 | Outil P0 v1.2 (taux de jointure bilans et avis de dépôt), avant sa première exécution |
