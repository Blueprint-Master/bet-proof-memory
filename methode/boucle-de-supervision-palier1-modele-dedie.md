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

## 3 bis. Mesures du 22/10/2026 (faits)

**Modèle final** : il n'est pas réduit au témoin. Sa pénalité vaut 0,01 : la valeur 0 a été écartée par le contrôle de séparation pendant la validation croisée. Probabilité moyenne de défaillance prévue pour les cas de 2020 : 2,144 % avec le modèle dédié, contre 2,121 % pour le témoin. Durée du calcul : 21 035 s.

**Prévalence par origine** (cas de `candidats-c1.parquet`, aucune valeur manquante pour C8) :

| Origine | Cas | C10 = 1 | G2 = 1 | C8 > 0 |
|---|---|---|---|---|
| 2018 | 601 493 | 0,12 % | 11,1 % | 50,5 % |
| 2019 | 737 679 | 0,29 % | 23,0 % | 55,7 % |
| 2020 | 807 183 | 0,48 % | 32,7 % | 67,4 % |

**Ce que ces chiffres établissent.**
- **H-a (C10) : la rareté se confirme.** C10 ne concerne que 0,12 % des cas de 2018, soit environ 720 sociétés, et sa fréquence quadruple d'ici 2020. Avec si peu de cas, il est attendu qu'il ne réduise pas la perte sur quatre plis sur cinq. Pourquoi sa fréquence augmente reste à établir.
- **H-b (mesures d'urgence de 2020) : elle ne suffit pas.** La part de G2 double déjà entre 2018 et 2019 (de 11,1 % à 23,0 %). Or l'origine 2019 (30/09/2019) précède toute mesure liée à 2020. Ces mesures peuvent expliquer au plus une partie de la hausse de 2019 à 2020.

**Nouvelle hypothèse H-d : une troncature de la source des ratios, qui biaise la population.** Les ratios ne sont denses qu'à partir des clôtures 2016 (protocole, P4). Or un cas n'existe que si la société a un bilan connu à t0 dans cette source. Conséquence :
- **en 2018**, une société qui a cessé de déposer ses comptes avant 2016 n'a aucun bilan dans la source, donc n'entre pas dans la population ;
- **avec les années**, l'historique s'allonge, et les sociétés silencieuses depuis plus de 450 jours peuvent y rester.

Si H-d est vraie, G2 et C8 ne désignent pas la même sous-population en 2018 et en 2020 : c'est un artefact de la source, pas un fait économique. Le modèle dédié reste alors sain en provenance, mais il transporte vers 2020 un effet appris sur une population différente. Ce glissement touche à l'identique B, T1 et D. Il peut cependant aussi fausser les conclusions du premier cycle sur ces variables.

**Test de H-d.** Comparer, par origine, l'ancienneté du bilan connu à t0, et la part de G2 selon cette ancienneté.

**Test de H-d, 22/10/2026 (faits).** Répartition des cas selon l'ancienneté du bilan connu à t0 (écart entre t0 et sa date de clôture), et part de G2 dans chaque tranche :

| Origine | 1 an au plus : part (G2) | 1 à 2 ans : part (G2) | Plus de 2 ans : part (G2) | Clôture la plus ancienne ; 10e centile |
|---|---|---|---|---|
| 2018 | 36,6 % (0 %) | 52,5 % (9,6 %) | 10,9 % (56,2 %) | 2014 ; 2016 |
| 2019 | 30,8 % (0 %) | 40,1 % (9,4 %) | 29,1 % (65,9 %) | 2014 ; 2016 |
| 2020 | 16,7 % (0 %) | 39,5 % (7,3 %) | 43,8 % (68,1 %) | 2014 ; 2016 |

**Conclusions.**
- **La hausse de G2 est surtout un effet de composition.** Dans chaque tranche d'ancienneté, la part de G2 varie peu. Ce qui change, c'est le poids de la tranche « plus de 2 ans », qui passe de 10,9 % à 43,8 % des cas. G2 et C8 mesurent donc surtout l'ancienneté du dernier bilan connu.
- **H-d est soutenue, mais sous une forme atténuée.** Il n'y a pas de coupure nette à 2016 : des clôtures de 2014 existent à toutes les origines. La source s'épaissit progressivement, et la population de 2018 contient beaucoup moins de sociétés au dernier bilan ancien que celle de 2020.
- **Une seconde cause probable s'ajoute en 2020** (hypothèse). La part des bilans d'un an au plus tombe de 30,8 % à 16,7 % entre 2019 et 2020. C'est cohérent avec un dépôt plus tardif des comptes 2019, mais le texte qui l'aurait permis n'a pas été lu.

**Conséquence pour le palier 1.** Les coefficients de G2 et C8 ont été appris en 2018, sur un groupe rare (11 % des cas au dernier bilan ancien). Ils s'appliquent en 2020 à un groupe quatre fois plus large et probablement moins sélectionné. L'outil risque donc d'être moins bien calibré sur 2020.

L'outil n'est pas modifié, pour trois raisons :
- il suit la spécification gelée ;
- il est le même pour B, T1 et D ;
- le palier 1 mesure la discipline, pas la qualité de l'outil.

Le corriger en regardant les issues de 2020 serait une fuite. Le corriger sur la seule distribution des variables à t0 serait permis, mais ouvrirait un choix de conception après coup : il est renvoyé au juge du réel.

**Conséquence pour le juge du réel.** La composition de la population par ancienneté du bilan glisse fortement d'une origine à l'autre. Ce glissement vient de la densité de la source, pas de l'économie. Il touche tous les plis qui testent 2019 et 2020, donc les conclusions du premier cycle sur les variables liées au dépôt des comptes.

Deux options pour le cycle 2, à décider par amendement du protocole :
- ajouter l'ancienneté du bilan connu à t0 comme variable ;
- ou stratifier l'évaluation par tranche d'ancienneté.

## 4. Suite

1. Extraire du rapport les paramètres du modèle final et la moyenne des prévisions 2020, puis les inscrire ici.
2. Vérifier H-a, par la part de C10 = 1 par origine, et H-b, en lisant les textes de 2020 sur les délais d'approbation et de dépôt des comptes.
3. Construire les outils datés et pseudonymisés du palier 1, puis les auditer avec la même grille que l'outil de prévision.

## 5. Incident d'exécution, corrigé

Une première exécution, lancée avec 6 processus, a porté la charge moyenne du serveur à 46,7 pour 12 cœurs. Chaque processus ouvrait plusieurs fils de calcul. Elle a été arrêtée et relancée avec un seul fil par processus. Le calcul étant déterministe, le résultat ne dépend pas de cette relance.

Pour éviter que l'incident se reproduise, les scripts `modele_dedie.py` et `cycle.py` fixent désormais eux-mêmes un fil par processus, avant le chargement des bibliothèques numériques. Cette correction est postérieure à l'exécution décrite ici, qui a utilisé la version 028a7e64….
