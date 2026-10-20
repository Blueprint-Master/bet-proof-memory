# Cycle 1 : cahier des charges des mécanismes candidats (protocole Q1 v1.7.1, P7)

Destinataires : les IA génératrices (ChatGPT, Gemini, Mistral) et l'IA vérificatrice (Claude). Version figée et horodatée au registre avant tout envoi.

## 1. La question

Prédire la défaillance (redressement ou liquidation judiciaire, au sens de P3) d'une société commerciale française dans les 548 jours suivant une origine t0 (30 septembre), mieux que la référence R2.

**La décision servie.** Un fournisseur choisit, pour chaque client, d'assurer sa créance par une assurance-crédit ou de garder le risque. Il assure si la probabilité de défaillance dépasse un seuil compris entre **1,13 % et 2,90 %** (selon le délai de paiement et la part indemnisée), pour un taux moyen de 1,31 %. Un mécanisme utile est donc un mécanisme qui **range mieux les sociétés de part et d'autre de cette zone**, pas seulement qui améliore la moyenne.

R2 est un modèle de hasard à temps discret, ajusté par régression logistique (sans pénalité, selon la validation croisée), sur les variables de l'annexe A :
- ratios du dernier bilan connu à t0 ;
- total de bilan ;
- retard de dépôt ;
- âge ;
- secteur ;
- confidentialité ;
- indicateurs « compte de résultat indisponible », « en plan », « en observation de sauvegarde » ;
- intensité sectorielle des défaillances de la Banque de France.

Un mécanisme n'est utile que s'il apporte une information **que R2 n'a pas déjà**.

## 2. Ce qu'est un mécanisme candidat

Une fonction pure, calculable pour chaque cas (SIREN, t0), qui ne lit **que des données publiées avant t0**, et qui traduit une hypothèse causale ou comportementale explicite. Chaque proposition comporte six rubriques :

1. **Nom**, court.
2. **Hypothèse** : le mécanisme réel supposé, en deux phrases au plus.
3. **Définition exacte** : la formule, les sources de l'annexe B utilisées, la règle de datation qui garantit la lecture avant t0, et le traitement des valeurs manquantes.
4. **Sens attendu** : le risque monte-t-il ou baisse-t-il avec la variable ?
5. **Pourquoi R2 ne le capte pas déjà.**
6. **Ce qui le réfuterait** : un résultat sur le développement qui conduirait à l'abandonner.

## 3. Données autorisées (annexe B, liste blanche)

Toutes datées par leur publication, et lues avant t0 seulement.

| Source | Contenu |
|---|---|
| Ratios BCE/INPI | Tous les bilans antérieurs de la société, connus à t0 : séries, tendances, ruptures |
| Liasse (totaux) | Total du passif, actif circulant, réserves et report à nouveau, capitaux propres, dettes totales et financières, résultat d'exploitation |
| BODACC, dépôts des comptes | Historique des dépôts : retards, exercices manquants, régularité |
| BODACC, procédures collectives | Procédures antérieures closes, plans, sauvegardes, conversions |
| BODACC, conciliations | Conciliations antérieures publiées |
| BODACC, radiations | Radiations antérieures |
| BODACC, modifications | Dissolutions et fusions antérieures (catégorie seule) |
| Sirene, historique | Changements de catégorie juridique et de NAF, date de création |
| Banque de France | Séries de défaillances par secteur et par taille |

**Interdits.**
- Toute variable liée à l'identité d'un magistrat ou d'un greffier (article 33 de la loi n° 2019-222).
- Toute donnée publiée après t0.
- Toute donnée nominative sur des personnes physiques.
- Toute source hors de cette liste.

## 4. Règle d'admission (non négociable)

Le mécanisme est évalué seul : il est ajouté au prédicteur figé de R2, avec une ordonnée par intervalle et une pente recalibrées (P5 bis), et seul son coefficient est pénalisé. Il est **admis** si et seulement s'il réduit le coût réalisé de la décision (P6 : coût moyen par euro d'encours, sous les six scénarios de seuil) par rapport au témoin, R2 recalibré, sur chacun des trois plis temporels du développement :
- 2018 vers 2019, à 365 jours ;
- 2018 et 2019 vers 2020, à 365 jours ;
- 2018 vers 2020, à 548 jours.

**Aucune proposition n'est admise parce que plusieurs IA la proposent ou la jugent bonne.** Seul le gain hors période compte. Toutes les propositions sont enregistrées, admises ou non, avec leur résultat.

## 5. Budget et déroulement

- **Budget.** 50 candidats au plus par cycle, 4 cycles au plus avant le scellé. 30 appels d'IA et 5 $ au plus par cycle.
- **Étape 1, génération à l'aveugle.** Chaque IA propose de 10 à 20 candidats sans voir ceux des autres.
- **Étape 2, vérification.** Claude contrôle chaque proposition sur trois points : la règle de datation (aucune information postérieure à t0), la redondance avec l'annexe A, la calculabilité sur les données de la liste blanche. Un rejet est motivé par écrit.
- **Étape 3, enregistrement.** La liste retenue est figée et son empreinte publiée au registre avant toute évaluation.
- **Étape 4, évaluation et publication.** Les candidats sont évalués sur les trois plis. Tous les résultats sont publiés, admis ou non : c'est la mémoire négative.

## 6. Ce qui ne sera pas transmis aux IA

- Aucun cas individuel.
- Aucune issue individuelle.
- Aucune donnée du scellé.

Seuls sont transmis ce cahier, le protocole public, et les mesures agrégées de R0, R1 et R2 sur le développement :

| Pli | Perte R0 | Perte R1 | Perte R2 | AUC R2 |
|---|---|---|---|---|
| 365 j, 2018 vers 2019 | 0,00710 | 0,00710 | 0,00621 | 0,747 |
| 365 j, 2018-2019 vers 2020 | 0,00588 | 0,00585 | 0,00519 | 0,748 |
| 548 j, 2018 vers 2020 | 0,00952 | 0,00969 | 0,00847 | 0,741 |

À 548 jours, la perte de R2 se décompose en miscalibration 0,00024, discrimination 0,00167 et incertitude 0,00990. R2 capte environ 17 % de l'incertitude : la marge de progrès est surtout dans la discrimination.
