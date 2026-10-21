# Cycle 1 : résultats sur le développement (étape 4)

Exécution du 20/10/2026 sur bpm-prod, après la correction de la lecture des séries de la Banque de France (erratum au registre). Rapports et empreintes : voir le registre. Tous les chiffres sont mesurés sur le développement ; aucune donnée du scellé n'a été lue.

## 1. Les références avec l'intensité sectorielle

**Couverture de l'intensité.** Elle manque pour 800, 966 et 1 076 cas seulement, sur 601 493, 737 679 et 807 183 cas éligibles (origines 2018, 2019, 2020).

**Perte de la décision par modèle :**

| Pli | R0 | R1 | R2 | Témoin |
|---|---|---|---|---|
| 365 j, 2018 vers 2019 | 0,007100 | 0,007102 | 0,006177 | 0,006176 |
| 365 j, 2018-2019 vers 2020 | 0,005882 | 0,005846 | 0,005582 | 0,005610 |
| 548 j, 2018 vers 2020 | 0,009515 | 0,009693 | 0,009148 | 0,009186 |

**Constat.** L'intensité sectorielle **dégrade R2 sur les deux plis qui testent l'origine 2020**. À 548 jours :
- R2 n'est plus que 3,9 % meilleur que R0, contre 11,0 % sans l'intensité ;
- sa miscalibration passe de 0,00024 à 0,00085 ;
- son Brier (0,011142) devient moins bon que celui de R0 (0,010878).

**Interprétation, non démontrée.** Le coefficient est appris en 2018 sur des écarts entre secteurs. Il est appliqué en 2020 à un choc de période : la chute des défaillances enregistrées pendant le régime d'aides. L'annexe A est gelée jusqu'au scellé : la variable reste dans R2.

## 2. Les 35 candidats

**Admission (P7).** 17 candidats réduisent la perte du témoin sur les trois plis : C4, C6, C7, C9, C10, C11, G1, G3, G4, G5, G6, G9, G11, M4, M5, M7, M12. Les 18 autres ne sont pas admis. Tous les chiffres sont au rapport.

**Gains nets.** Seuls quelques admis ont un gain qui dépasse nettement le bruit (en % de la perte du témoin, pour les plis 1, 2 et 3) :

| Candidat | Gain |
|---|---|
| G4, G5, G6 (variations d'autonomie, de liquidité, de total de bilan entre les deux derniers bilans) | environ 0,7 / 1,6 / 2,2 % chacun |
| M12 (croissance du chiffre d'affaires moins l'intensité sectorielle) | 0,43 / 1,05 / 1,29 % |
| G1 (allongement du retard de dépôt) | 0,32 / 0,85 / 0,96 % |
| M7 (irrégularité des retards de dépôt) | 0,35 / 0,43 / 0,41 % |

**Admissions de l'ordre de 10⁻⁷.** Elles sont nombreuses, par exemple C4, G3 et G9. La règle de P7 admet sur l'estimation ponctuelle seule. Ces admissions sont probablement du bruit : la règle, fixée d'avance, les laisse passer. La protection est en aval : le scellé ne teste qu'une hypothèse, l'assemblage figé, et les mécanismes individuels y sont jugés en famille de Holm.

**Effets nuisibles notables, non admis :**
- **G13**, intensité de défaillances toutes branches par taille : −27 % et −16 % sur les plis 2 et 3. C'est le même phénomène que l'intensité sectorielle de R2, amplifié.
- **G2 et C8**, silence de dépôt : positifs sur le pli 1, négatifs sur les plis qui testent 2020.

**Interprétation, non démontrée.** L'effet change de signe avec le régime : les délais d'approbation et de dépôt des comptes ont été modifiés en 2020.

## 3. L'assemblage des 17 admis

| Pli | Gain sur le témoin | Intervalle à 95 % (grappes NAF) | En % de la perte du témoin |
|---|---|---|---|
| 365 j, 2018 vers 2019 | 0,0000710 | [0,0000328 ; 0,0001085] | 1,15 % [0,53 ; 1,75] |
| 365 j, 2018-2019 vers 2020 | 0,0001215 | [0,0000718 ; 0,0001612] | 2,17 % [1,28 ; 2,87] |
| 548 j, 2018 vers 2020 | 0,0002214 | [0,0001355 ; 0,0002975] | 2,41 % [1,48 ; 3,24] |

**Précision indicative (P6).** Demi-largeur de 0,000081 sur le pli 548 j.

**Seuil de rentabilité indicatif.** Il est calculé sur le développement, à titre indicatif seulement : le verdict reste réservé au scellé. Avec un gain de 0,000221 € par euro d'encours sur 548 jours, L_min ≈ 678 000 € d'encours total pour 100 € de coût annuel d'information, soit environ 2,0 M€ pour 300 €.

**Biais déclaré.** Les 17 candidats ont été admis sur ces mêmes plis. Le gain de l'assemblage mesuré ici est donc optimiste par construction (sélection sur l'échantillon d'évaluation). Seul le scellé le mesure sans biais.

## 4. Hypothèses suggérées pour un cycle suivant (à soumettre aux IA, non testées)

1. **Variations G4, G5 et G6.** Leurs gains sont presque identiques et elles partagent leur indicateur d'absence (moins de deux bilans connus). L'information pourrait tenir surtout à cet indicateur : l'absence d'un bilan antérieur dans les ratios, donc la disponibilité des données, plutôt qu'à la variation économique. À tester avec l'indicateur seul.
2. **Variables macroéconomiques** (intensités, silence de dépôt). Leur effet appris en 2018 se retourne en 2020. Toute variable de régime doit être jugée sur ce risque.
