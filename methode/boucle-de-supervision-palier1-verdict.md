# Boucle de supervision, palier 1 : verdict du principal

*23/10/2026. Rapport produit par `palier1/lancer_principal.sh` sur bpm-prod (graine d'analyse 371935227), lu tel quel ; fichiers non versés, empreintes au registre. Aucune analyse supplémentaire n'a été faite pour ce verdict.*

## 1. Verdict

**Indécis.** Raison du rapport : « delta non significatif (p = 1,0000) ». Sur les 300 cas éligibles, les 300 différences appariées entre T1 et B sont nulles : Δ = 0, intervalle BCa à 95 % [0 ; 0]. C'est l'issue P6 de la prédiction enregistrée, et la confirmation, sur 340 cas, de l'effet plafond vu au pilote.

## 2. Résultats (340 cas : 300 éligibles, 20 pièges antérieurs, 20 pièges postérieurs)

| Mesure | D (code) | B (boucle) | T1 (libre, outils) | T0 (sans outil) |
|---|---|---|---|---|
| M1, coût réalisé pondéré | 0,010376 | 0,010376 | 0,010376 | 0,010658 |
| M2, violations | 0 | 0 | 0 | 332 cas (97,6 %) : b 18, c 24, e 308 |
| M3, abstentions justifiées / injustifiées (éligibles) | 20 / 0 | 20 / 0 | 20 / 0 | 2 / 6 (2,0 %) ; 24 sorties nulles |
| M5, écart de décision à D (pondéré) | 0 | 0 | 0 | 62,7 % (52,9 %) |
| Appels de modèle | 0 | 680 | 681 | 340 |
| Jetons entrée / sortie | 0 | 491 668 / 618 562 | 461 729 / 503 254 | 89 709 / 817 237 |

- **Non-infériorité de B sur M2** : aucune violation discordante ; z = − 2,63, p unilatéral = 0,0042 ; établie.
- **Secondaire, décisions communes** : Δ = 0, p = 1.
- **Secondaire, T0 − T1 sur M1** : 0,00028, p bilatéral = 0,75. L'apport des outils au coût réalisé, significatif au pilote (0,0046, p = 0,028), **n'est pas répliqué** au principal.
- **Dérive de T1 en population** : 0 écart à D sur 300 éligibles ; borne supérieure exacte à 95 % du taux d'écart : 0,99 % (0,88 % sur 340).
- **Coût** : 1 701 appels de modèle (plafond 2 000) ; 1 043 106 jetons d'entrée et 1 939 053 de sortie, soit environ 9,5 $ au tarif indicatif utilisé au pilote (1,36 $ et 4,18 $ par million). Le champ « euros » du rapport vaut 0 : le tarif n'était pas renseigné dans le code, ce montant est donc un calcul a posteriori, pas une mesure.

## 3. Lecture

**Faits.** B, T1 et D rendent les mêmes 340 décisions. La boucle n'a rien corrigé, parce qu'il n'y avait rien à corriger ; elle n'a rien coûté en abstentions. T0, privé d'information, viole presque toujours la règle de citation (type e) et s'écarte de D sur près des deux tiers des cas.

**Interprétation.** Le palier 1 mesure la capacité d'un modèle à suivre une règle explicite quand la prévision est fournie : sur cette tâche, Mistral Large 4 en usage libre le fait sans dérive mesurable. Le résultat ne dit rien de la valeur de la boucle là où le modèle peut se tromper, ce que le monde simulé est conçu pour tester.

**Hypothèse, non vérifiée.** Que T0 s'écarte de D sur 63 % des cas sans différence significative de coût réalisé suggère que M1 discrimine mal les décisions quand la défaillance est rare (environ 1 %) : la plupart des erreurs ne coûtent qu'une prime. Si c'est le cas, M1 était un critère primaire peu sensible pour ce palier, indépendamment de l'effet plafond. À examiner, sans réanalyse du palier 1, avant de fixer U dans le monde simulé (la v2 y répond en partie par l'échelle G).

## 4. Prédiction enregistrée du 21/10, scorée

| N° | Énoncé | Probabilité | Issue | Brier |
|---|---|---|---|---|
| P1 | B = D sur au moins 85 % des éligibles | 0,75 | Vrai (100 %) | 0,0625 |
| P2 | T1 = D sur au moins 85 % des éligibles | 0,60 | Vrai (100 %) | 0,1600 |
| P3 | Violations de T1 au-dessus de 2 % | 0,65 | Faux (0 %) | 0,4225 |
| P4 | Violations de B inférieures à celles de T1 | 0,90 | Faux (0 = 0) | 0,8100 |
| P5 | Verdict « succès » | 0,25 | Faux | 0,0625 |
| P6 | Verdict « indécis » ou « non recevable » | 0,60 | Vrai | 0,1600 |
| P7 | Verdict « échec » | 0,15 | Faux | 0,0225 |
| P8 | Abstentions injustifiées de B au-dessus de 5 % | 0,20 | Faux (0 %) | 0,0400 |
| P9 | Sonde de mémorisation au-dessus du hasard | 0,40 | Non scorable : sonde non exécutée | |
| P10 | La puissance conclut que 300 cas ne suffisent pas | 0,55 | Non scorable : l'analyse a conclu que la puissance n'était pas calculable (aucune différence dans aucune strate), ce qui n'est ni l'issue énoncée ni son contraire | |

Score de Brier moyen sur les 8 énoncés scorables : **0,2175**, à peine meilleur que 0,25 (probabilité de 0,5 partout). L'erreur dominante est la même dans P3 et P4 : le concepteur attendait du modèle libre une dérive que la tâche ne lui laissait pas commettre.

## 5. Ce qui reste ouvert

- La sonde de mémorisation (préenregistrée, non exécutée). Sans enjeu pour ce verdict, puisque B et T1 sont identiques ; elle n'est utile que si une suite réutilise ces données.
- Le palier 1 est clos. La suite de la boucle passe par le monde simulé (`monde-simule-v2.md`, `monde-simule-gabarits-1.md`).
