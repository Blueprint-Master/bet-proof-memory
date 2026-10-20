# Cycle 1 : vérification des propositions (étape 2)

Vérificatrice : Claude. Propositions : `cycle-1-propositions-brutes.md` (37 propositions : C1 à C12, G1 à G13, M1 à M12).

## Règles de vérification

Le cahier (section 5) fixe trois contrôles et trois seulement :
1. **la datation** : aucune information postérieure à t0 ;
2. **la redondance avec l'annexe A** : la variable n'est ni une variable de R2 ni une fonction déterministe des seules variables de R2 ;
3. **la calculabilité** sur les données de la liste blanche, avec une définition exacte.

La vraisemblance économique d'une hypothèse n'est pas un motif de rejet : c'est l'évaluation qui juge. Quand une définition laisse un point ouvert, la vérification ne la redessine pas. Elle complète ce point par une règle générale, la même pour tous, et l'écrit :

- **R-a, valeurs manquantes non précisées par l'auteur** : règle de P5, médiane d'apprentissage et indicateur de manquant. Quand l'auteur a fixé sa règle (C : 0 sans indicateur ; G : 0 avec indicateur), sa règle s'applique.
- **R-b, exercices successifs** : les bilans connus à t0 au sens de P2 (avis de dépôt paru avant t0), classés par clôture décroissante. Pour les variations sans règle d'écart propre à l'auteur, deux clôtures consécutives distinctes.
- **R-c, Sirene** : datation de P2 (période de l'historique qui couvre la date considérée). Un changement est une différence entre deux périodes successives dont la seconde commence dans la fenêtre. Le risque d'enregistrement rétroactif est celui que la v1.7.1 accepte déjà pour R2 ; il est déclaré.
- **R-d, Banque de France** : séries du jeu DIREN déjà extraites, avec la même règle de choix de série que l'intensité de R2 (secteur et taille, puis repli).
- **R-e, valeurs extrêmes** : aucun bornage n'est ajouté. P5 bis ne prévoit que le centrage et la réduction pour les mécanismes ; ajouter un bornage serait une modification du protocole.
- **R-f, couverture** : la part des cas où la variable est calculable est publiée par origine. Une faible couverture n'est pas un motif de rejet.

## Rejets motivés

| N° | Motif |
|---|---|
| M9 | **Calculabilité : définition non exacte.** « Écarts relatifs entre ratios successifs » ne désigne pas les ratios, et « seuil > 50 % » ne dit pas si la variable est le maximum ou un indicateur. Compléter ces deux points reviendrait à écrire le mécanisme à la place de l'auteur. |
| M10 | **Calculabilité hors liste blanche.** La définition compte toutes les publications « modification » du BODACC. La liste blanche figée n'en contient que la catégorie dissolution ou fusion. |

## Propositions retenues (35), avec les précisions d'exécution

| N° | Retenu | Précision d'exécution (règles R-a à R-f) |
|---|---|---|
| C1, C2 | oui | Ratios BCE/INPI ; écart de 270 à 550 jours entre clôtures, comme l'auteur le fixe, sinon 0 |
| C3 | oui | Capitaux propres de la liasse (DL ou 142) ; total de bilan B2 (EE ou 180) |
| C4 | oui | Quatre bilans requis ; couverture attendue faible sur 2018 (ratios denses depuis les clôtures 2016), publiée |
| C5 | oui | Réserves et report à nouveau de la liasse (DD à DH, ou 126 à 134), signés |
| C6 | oui | Résultat d'exploitation (GG ou 270) ; un compte de résultat masqué est une donnée absente |
| C7, C8 | oui | Avis de dépôt du BODACC (famille dpc), date de parution avant t0 |
| C9 | **en attente** | Calculable seulement si l'instantané des conciliations contient des annonces (décompte demandé) |
| C10 | oui | Jugements classés CLOT ou CLOT-EXT parus dans [t0 − 1 826 j, t0[ |
| C11 | oui | Selon R-c ; « dates de publication » lues comme dates de début de période, faute de date de publication dans l'historique Sirene |
| C12 | oui | Série retenue pour R2 (même clé) ; cumul au mois t0 − 3 et au mois t0 − 15 |
| G1 | oui | Écart de retard entre le dernier et l'avant-dernier bilan connus |
| G2 | oui | Avis de dépôt : au moins un avant t0 et aucun dans [t0 − 450 j, t0[ |
| G3 | oui | Compte de résultat indisponible au sens de P2 ter (marge d'EBE absente) au dernier bilan, disponible à l'avant-dernier |
| G4, G5, G6 | oui | Variations entre le dernier et l'avant-dernier bilan (R-b) |
| G7, G8 | oui | Composantes X2 et X3 du Z'' de la liasse, absentes de R2 (elles ne servent qu'à R1) |
| G9 | oui | Dettes financières (DS à DV, ou 156) sur dettes totales (EC ou 176) |
| G10 | **en partie en attente** | Procédure close : jugement CLOT ou CLOT-EXT paru avant t0. La partie conciliation dépend du décompte |
| G11 | oui | NAF (code complet) ou catégorie juridique, selon R-c, fenêtre [t0 − 1 095 j, t0[ |
| G12 | oui | Modifications du BODACC, catégorie dissolution ou fusion, parues dans [t0 − 1 095 j, t0[ |
| G13 | **en attente** | Série toutes branches (ZZ) de la taille de la société ; calculable si ces séries existent dans l'instantané (décompte demandé). Non redondante : R2 lit la série du secteur et de la taille, pas la série de la taille seule |
| M1 | oui | Pente des moindres carrés de la marge d'EBE sur les trois derniers bilans, en fonction du temps en années ; R-a |
| M2 | oui | Écart-type sur les cinq derniers bilans ; couverture attendue très faible, publiée ; R-a |
| M3 | oui | Croissance annuelle du chiffre d'affaires : moyenne des deux dernières variations moins moyenne des deux précédentes (cinq bilans) ; couverture attendue très faible ; R-a |
| M4 | **en attente** | Comme C9 |
| M5 | oui | Selon R-c ; changement au niveau 2 (deux premiers chiffres) ou au niveau 4 (quatre premiers caractères), fenêtre de 730 jours |
| M6, M11 | oui | Partie Sirene seule (R-c) : la partie BODACC n'est pas dans la liste blanche pour la catégorie juridique. M6 : fenêtre de 1 095 jours. M11 : durée en mois, plafonnée à 60, manquant = 60 comme l'auteur le fixe |
| M7 | oui | Écart-type des retards de dépôt des trois derniers exercices ; R-a |
| M8 | oui | Pente des moindres carrés de dettes financières / total du passif (liasse) sur les quatre derniers bilans ; R-a |
| M12 | oui | Croissance du chiffre d'affaires entre les deux derniers bilans, moins l'intensité sectorielle de R2, telle que définie par l'auteur. La différence de deux grandeurs sans commune mesure est relevée, mais ce n'est pas un motif de rejet |

## Proximités signalées, sans fusion

Les couples suivants mesurent des idées voisines par des définitions différentes. Les fusionner obligerait à choisir une définition, donc à arbitrer à la place des auteurs. Ils sont évalués séparément, et la proximité est publiée :
- C1 et G5 ;
- C7 et G1 ;
- C3 et G4 ;
- C5 et G7 ;
- C4 et M2 ;
- C2 et M8 ;
- C8 et G2 ;
- C9 et M4 ;
- C10 et G10 ;
- C11, G11, M5, M6 et M11.

## Budget

35 candidats retenus au plus, dans la limite de 50 par cycle. 4 appels d'IA consommés sur 30.
