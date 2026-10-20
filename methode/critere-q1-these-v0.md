# Critère de jugement de la question 1 : thèse v0 (soumise à critique à l'aveugle)

Statut : thèse de Claude, à critiquer avant toute modification du protocole. Aucun mécanisme candidat n'a encore été évalué.

## 1. Constat (développement, protocole v1.6)

- **Taux de défaillance** : 0,7 à 1,1 % selon le pli.
- **Brier de R2** (hasard à temps discret, annexe A) : 0,7 à 0,9 % plus bas que celui du Z'' d'Altman recalibré (R1), 0,4 à 0,7 % plus bas que celui des taux de base par classe (R0). AUC de R2 : 0,74 environ.
- **Seuil de la v1.6** : le gain minimal utile de l'assemblage sur R2 est fixé à 3 % du Brier, soit quatre à huit fois ce que toute l'information comptable apporte par rapport aux références simples.
- **Précision** : la demi-largeur bootstrap de l'intervalle à 95 % du gain est d'environ 0,13 point par pli de 800 000 cas. La puissance n'est pas en cause ; l'échelle du seuil l'est.
- **Pénalité de R2** : elle est retenue à la borne basse de la grille sur les trois plis.

## 2. Diagnostic

1. **Le critère de la v1.6 confond deux questions.**
   - (a) L'assemblage prévoit-il mieux que R2 hors échantillon ? C'est une question statistique.
   - (b) L'amélioration vaut-elle quelque chose pour un décideur ? C'est une question de décision.

   Le seuil de 3 % prétend répondre à (b) sans fonction de perte. La « mesure décisionnelle » est restée non définie depuis la phase 4.
2. **Le Brier dépend de la prévalence et n'évalue pas l'utilité d'une décision.** Assel, Sjoberg et Vickers (2017, *Diagnostic and Prognostic Research*, 1:19, DOI 10.1186/s41512-017-0020-3) montrent que le Brier peut ordonner des modèles à l'inverse de leur valeur décisionnelle, et recommandent le bénéfice net.
3. **L'analyse par courbe de décision** (Vickers et Elkin, 2006, *Medical Decision Making*, 26(6):565-574, DOI 10.1177/0272989X06295361) relie le seuil de probabilité au rapport des coûts d'un faux positif et d'un faux négatif, et donne le bénéfice net du modèle pour chaque seuil.
4. **La comparaison de prévisions concurrentes** se fait classiquement par un test d'égalité de la perte espérée, pour une fonction de perte fixée d'avance (Diebold et Mariano, 1995, *Journal of Business and Economic Statistics*).
5. **La pénalité en butée** révèle une grille mal posée. La correction doit être une règle générale, pas une nouvelle grille choisie à la main.

## 3. Proposition

**P-A. Affirmation statistique (primaire).**
- Test unilatéral d'égalité de la perte espérée entre l'assemblage et R2 sur le scellé.
- Perte : une règle de score propre, fixée d'avance.
- Moyenne équipondérée des deux origines ; bootstrap groupé par société ; α = 0,025.
- Succès si la borne inférieure de l'intervalle à 95 % de la différence de perte est au-dessus de zéro.

**P-B. Utilité (co-primaire).**
- Bénéfice net, au sens de l'analyse par courbe de décision, sur une plage de seuils de probabilité. Cette plage est déduite des coûts d'erreur du décideur financier (perte en cas de défaut d'un client, marge perdue en refusant un bon client) et documentée par des sources, pas choisie.
- Le plus petit effet utile (SESOI) est exprimé en défaillances nettes évitées pour 10 000 sociétés, et fixé à partir de ces mêmes coûts.
- La réfutation n'est possible qu'à travers ce SESOI : l'intervalle du gain de bénéfice net est entièrement sous le SESOI.

**P-C. Choix de la règle de score de P-A.** Question ouverte, qui doit être tranchée par des critères écrits avant de choisir (propriété du score, sensibilité aux probabilités extrêmes, sensibilité aux faibles prévalences), non par préférence :
- le Brier est borné et peu sensible pour des événements rares ;
- la log-vraisemblance est non bornée et sensible à la calibration des faibles probabilités.

**P-D. Pénalité.** Règle générale, appliquée à l'identique à R2 et à l'assemblage :
- grille logarithmique sur plusieurs décades, bornée par une valeur déduite des données (à la manière de glmnet : Friedman, Hastie et Tibshirani, 2010, *Journal of Statistical Software*, 33(1)) ;
- extension automatique d'une décade tant que l'optimum est sur une borne, jusqu'à l'absence de pénalité.

**P-E. Règle d'amendement avant le scellé.** Un amendement est recevable s'il remplit quatre conditions :
- il est motivé par une information indépendante de la performance de tout candidat ;
- il est énoncé comme une règle générale ;
- il est soumis à cette critique à l'aveugle ;
- il est consigné au journal.

## 4. Questions aux critiques

1. Le diagnostic (confusion entre la question statistique et la question d'utilité) est-il juste ? Que manque-t-il ?
2. P-A : quelle règle de score retenir pour des événements à 1 %, selon quels critères, avec quelles références ?
3. P-B : le bénéfice net est-il adapté à un décideur financier (crédit fournisseur, exposition client, investissement) ? Comment documenter la plage de seuils et le SESOI à partir de sources, sans jugement arbitraire ?
4. P-D : la règle de pénalité est-elle correcte ? Existe-t-il une pratique de référence plus défendable ?
5. P-E : la règle d'amendement suffit-elle à empêcher le réglage du protocole sur les données ?
6. Quelle faille majeure vois-tu dans l'ensemble ?

Réponds par une critique argumentée et sourcée. Signale toute affirmation dont tu n'es pas certain. N'invente aucune référence.
