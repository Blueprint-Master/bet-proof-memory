# Boucle de supervision, palier 1 : tirage des cas et des pièges

*Rédigé le 22/10/2026. La graine du pilote est publiée ici, par un commit antérieur au tirage.*

Code : `palier1/tirer.py` ; tests : `tests/test_palier1_tirage.py`. Le tirage, l'extraction des dossiers et leur pseudonymisation se font en une commande, sur le serveur ; aucun fichier produit n'est versé au dépôt (SIREN, issues), seules leurs empreintes le sont.

## 1. Graine du pilote

**Graine : 1077335931.** Tirée le 22/10/2026 par `secrets.randbelow(2**31)`, avant toute exécution du tirage. Effectifs du pilote : 25 défaillants, 25 non défaillants, 5 pièges avant t0, 5 pièges après t0. La graine du tirage principal sera publiée de la même façon après l'analyse de puissance.

## 2. Choix de construction

| N° | Point | Choix | Motif |
|---|---|---|---|
| T1 | Population éligible | Cas de l'origine 2020 de `cas-dev.parquet` (règles P1 à P3 du juge du réel) ayant une prévision du modèle dédié | Même population que celle qui a servi à figer l'outil |
| T2 | Pièges avant t0 | Sociétés qui passent les filtres de P1 (bilan connu à t0, forme juridique, création, pas de radiation parue) sauf un : liquidation judiciaire en cours à t0 **au sens de l'outil `etat`** (annonces parues avant t0) | Le piège doit ressembler à un cas, et la seule information qui le distingue doit être celle que l'outil sert |
| T3 | Pièges après t0 | Cas éligibles dont un jugement de liquidation (ouverture, conversion d'une sauvegarde, résolution d'un plan) est daté dans ]t0, t0 + 548 jours]. Les conversions d'un redressement en liquidation ne sont pas reconnues par la classification des jugements (classées « autre ») : ces sociétés ne sont jamais tirées comme pièges | Données disponibles jusqu'au 30/09/2022 seulement ; limite de la classification déclarée |
| T4 | Ordre | Pièges après, puis défaillants, puis non défaillants, puis pièges avant ; tirages sans remise sur des listes triées par SIREN ; un scénario par cas, uniforme sur S1 à S6, dans l'ordre de la liste | Les pièges après sont tirés d'abord pour être hors des cas éligibles sans retirer tous les défaillants liquidés de la population |
| T5 | Pilote et principal | Disjoints : le tirage principal exclut les SIREN du pilote | Le pilote peut conduire à corriger une configuration avant gel ; ses cas ne doivent pas servir au verdict |
| T6 | Poids de redressement | Part dans l'origine 2020 divisée par part dans l'échantillon, par strate | Section 7.2 de la note |
| T7 | Contrôles bloquants | Après extraction : chaque piège avant est en liquidation selon l'outil `etat` à t0, et aucun autre cas ne l'est ; chaque cas qui n'est pas un piège avant a sa prévision | Un piège mal construit fausserait M2 (b) sans bruit |
| T8 | Fichiers | Dossiers servis aux outils (sans issue ni SIREN) séparés du fichier des cas des vérificateurs (issue, poids) et de la table de correspondance ; tous en 600 | Les systèmes ne doivent pas pouvoir lire l'issue, même par erreur de chemin |

## 3. Correction apportée aux outils

En écrivant le tirage, un écart a été trouvé entre l'outil `etat` et la règle de P1 : P1 ne laisse un plan arrêter qu'une sauvegarde ou un redressement, alors que l'outil faisait passer en « plan » une société en liquidation dont un plan était publié ensuite. L'outil appelle désormais la même règle (`outils.etat_procedure`, testée). Sans cette correction, un piège avant aurait pu être servi comme éligible. Nouvelle empreinte de `palier1/outils.py` au registre.

## 4. Décisions du 22/10/2026 sur les points ouverts des vérificateurs

1. **Verdict secondaire sous LGD 0,70** : D est refaite sous 0,70 ; B et T1 gardent leurs décisions et seuls leurs coûts sont recalculés (`verificateurs.fiches` avec `lgd = 0,70`). Limite déclarée : cette lecture mesure la sensibilité du coût, pas celle des décisions.
2. **Plafond commun d'appels et de jetons par cas** : fixé avec les configurations de T1 et B, publié avec elles avant le pilote.
