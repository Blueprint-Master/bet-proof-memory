# Boucle de supervision : prédiction enregistrée avant le palier 1

Enregistrée le 21/10/2026, avant l'écriture de tout code du palier 1 et avant le pilote. Auteur : Claude. Ce sont des probabilités subjectives, pas des estimations tirées de données ; elles seront scorées au verdict par le score de Brier, comme toute prévision de la boucle. Elles s'appliquent au tirage principal tel que spécifié dans `methode/boucle-de-supervision.md` (note gelée le 21/10/2026).

| N° | Énoncé vérifiable au verdict | Probabilité |
|---|---|---|
| P1 | B prend la même décision que la référence D sur au moins 85 % des cas éligibles | 0,75 |
| P2 | T1 prend la même décision que D sur au moins 85 % des cas éligibles | 0,60 |
| P3 | Le taux de violations de T1 dépasse 2 % des cas | 0,65 |
| P4 | Le taux de violations de B est inférieur à celui de T1 | 0,90 |
| P5 | Le verdict primaire est « succès » | 0,25 |
| P6 | Le verdict primaire est « indécis » ou « non recevable » | 0,60 |
| P7 | Le verdict primaire est « échec » | 0,15 |
| P8 | Les abstentions injustifiées de B dépassent 5 % des cas éligibles | 0,20 |
| P9 | La sonde de mémorisation donne un rappel significativement au-dessus du hasard | 0,40 |
| P10 | L'analyse de puissance après pilote conclut que 300 cas ne suffisent pas pour détecter l'écart attendu | 0,55 |

P5, P6 et P7 sont exclusives et somment à 1. Raisonnement résumé : la tâche est presque déterministe, donc B et T1 suivront souvent D, et Δ se jouera sur peu de désaccords ; une partie de l'avantage de B sur les violations est acquise par construction (P4) ; l'information nouvelle tiendra dans P1, P2 et P8.
