# Boucle de supervision, palier 1 : résultats du modèle de prévision dédié

Exécution sur bpm-prod le 22/10/2026, de 00:33 à 06:23 UTC (5 h 50), avec 8 processus à un seul fil de calcul. Code : `evaluation/modele_dedie.py` (empreinte 028a7e64…, commit 86a4cfc). Spécification : note gelée, section 7.2. Audit de provenance : `methode/boucle-de-supervision-audit-provenance.md`.

## 1. Faits

**Contrôles de provenance.** Les six contrôles sont au vert. L'apprentissage compte 601 493 cas de l'origine 2018, dont 10 079 défaillants (1,68 %). La dernière issue comptée date du 31/03/2020. Tous les avis de dépôt sont antérieurs à t0, sur l'apprentissage comme sur la cible (807 183 cas de l'origine 2020).

**R2.** La pénalité retenue est λ* = 0, comme dans les évaluations précédentes.

**Répartitions.** Les défaillants se répartissent de façon inégale entre plis : de 1 455 à 2 697 pour la première répartition, de 1 478 à 2 849 pour la vingtième. C'est la conséquence attendue du regroupement par division NAF, déclarée dans le rapport.

**Admissions sur 20 répartitions** (règle : perte moyenne réduite et réduction sur au moins 4 plis sur 5).

| Candidat | Admissions | Candidat | Admissions | Candidat | Admissions |
|---|---|---|---|---|---|
| C1 | 4 | G1 | 20 | M1 | 5 |
| C2 | 6 | G2 | 20 | M2 | 8 |
| C3 | 6 | G3 | 5 | M3 | 3 |
| C4 | 7 | G4 | 20 | M4 | 20 |
| C5 | 6 | G5 | 20 | M5 | 14 |
| C6 | 13 | G6 | 20 | M6 | 2 |
| C7 | 19 | G7 | 4 | M7 | 19 |
| C8 | 20 | G8 | 1 | M8 | 4 |
| C9 | 20 | G9 | 15 | M11 | 5 |
| C10 | 0 | G10 | 13 | M12 | 16 |
| C11 | 17 | G11 | 16 | | |
| C12 | 9 | G12 | 13 | | |
| | | G13 | 12 | | |

**Modèle final** : 14 candidats retenus (au moins 15 admissions sur 20) : C7, C8, C9, C11, G1, G2, G4, G5, G6, G9, G11, M4, M7 et M12.

**Fichiers produits** (conservés sur bpm-prod, non versés au dépôt) :
- `prevision-dediee-2020-20261022-062330.parquet`, SHA-256 ffc5686943efe0138e12bb3107303dfcd1e70013ce16a9c30a53775247a88b21 ;
- `modele-dedie-20261022-062330.json`, SHA-256 9477f1fac185c8618cfac00776cf9776acc465c9dcbfdc89539ba9465c7907f1.

## 2. Comparaison avec les 17 admis du premier cycle

| | Candidats |
|---|---|
| Retenus dans les deux | C7, C9, C11, G1, G4, G5, G6, G9, G11, M4, M7, M12 (12) |
| Admis au premier cycle, écartés ici | C10 (0 sur 20), G3 (5), C4 (7), C6 (13), M5 (14) |
| Retenus ici, non admis au premier cycle | C8 (20 sur 20), G2 (20 sur 20) |

**Ce que la comparaison permet de dire.** Douze candidats sur dix-sept résistent à une sélection faite sur la seule origine 2018. Cinq ne résistent pas.

**Ce qu'elle ne permet pas de dire.** On ne peut pas attribuer tout l'écart à la fuite de spécification, parce que les deux sélections diffèrent aussi par leur forme :
- trois plis temporels contre cinq plis par secteur ;
- une seule évaluation contre vingt répartitions ;
- une admission sur trois plis contre une admission sur quatre plis sur cinq.

L'écart est donc la somme de deux effets : la fuite et le changement de procédure. Les données disponibles ne permettent pas de séparer ces deux effets.

## 3. Interprétations (hypothèses, non vérifiées)

**H-a. C10 (une procédure close dans les cinq ans) n'est admis dans aucune répartition, alors qu'il l'avait été sur les trois plis du premier cycle.** Deux lectures possibles :
- soit son signal n'apparaît qu'après 2018 ;
- soit les jugements de clôture parus entre 2013 et 2018 sont trop rares dans l'instantané pour peser sur l'origine 2018.

Une mesure tranche entre les deux : la part des cas où C10 vaut 1, comparée entre les origines 2018 et 2020.

**H-b. C8 et G2 mesurent tous deux l'absence de dépôt récent des comptes. Ils sont admis dans les 20 répartitions sur 2018, mais n'avaient pas été admis au premier cycle**, qui testait l'origine 2020. Lecture possible : en 2020, les délais d'approbation et de dépôt des comptes ont été allongés par des mesures d'urgence. Si c'est le cas, l'absence de dépôt récent a été plus fréquente sans signaler de difficulté, et le signal s'est affaibli pour les cas de 2020.

Le texte exact de ces mesures n'a pas été lu ici. À lire avant toute conclusion.

Si H-b se vérifie, le modèle dédié est sain du point de vue de la provenance, mais il emporte vers 2020 un signal qui s'est dégradé. C'est une rupture de régime, pas une fuite. Elle touche à l'identique B, T1 et D, et ne fausse donc pas le verdict du palier 1, mais elle réduit la qualité absolue de l'outil.

**H-c. Plusieurs candidats sont proches du seuil.** G9 est retenu de justesse (15 sur 20). M5 (14), C6, G10 et G12 (13 chacun) et G13 (12) sont écartés de peu. La règle de stabilité 15 sur 20 est un choix déclaré. Une autre valeur de seuil changerait la composition du modèle sans changer la provenance.

## 4. Suite

1. Extraire du rapport les paramètres du modèle final et la moyenne des prévisions 2020, puis les inscrire ici.
2. Vérifier H-a, par la part de C10 = 1 par origine, et H-b, en lisant les textes de 2020 sur les délais d'approbation et de dépôt des comptes.
3. Construire les outils datés et pseudonymisés du palier 1, puis les auditer avec la même grille que l'outil de prévision.

## 5. Incident d'exécution, corrigé

Une première exécution, lancée avec 6 processus, a porté la charge moyenne du serveur à 46,7 pour 12 cœurs. Chaque processus ouvrait plusieurs fils de calcul. Elle a été arrêtée et relancée avec un seul fil par processus. Le calcul étant déterministe, le résultat ne dépend pas de cette relance.

Pour éviter que l'incident se reproduise, les scripts `modele_dedie.py` et `cycle.py` fixent désormais eux-mêmes un fil par processus, avant le chargement des bibliothèques numériques. Cette correction est postérieure à l'exécution décrite ici, qui a utilisé la version 028a7e64….
