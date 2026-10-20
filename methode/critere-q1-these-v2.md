# Critère de jugement de la question 1 : thèse v2 (dernier tour de critique avant amendement)

Statut : révision après la matrice v1 (sept erreurs corrigées, désaccord S0 / S+). Aucun mécanisme candidat évalué. Le protocole v1.6 reste en vigueur jusqu'à l'amendement.

## 1. Décision et modèle de coûts

**Décision (spécification de Rémi).** Un fournisseur accorde, ou refuse, un encours commercial non garanti L à une contrepartie, sur l'horizon H = 548 jours.

**Modèle par euro d'encours.** Paramètres : délai de paiement D, d'où une rotation T = H / D ; marge sur coûts variables m du fournisseur ; perte en cas de défaut LGD sur l'encours ouvert.
- Pas de défaillance : gain m × T.
- Défaillance : gain (m − LGD). C'est une approximation prudente, qui néglige les marges encaissées avant la défaillance.
- Refus : 0.

On accorde si (1 − p) m T + p (m − LGD) > 0, d'où :

  **p_t = m T / (m (T − 1) + LGD)**

Avec T = 1, on retrouve p_t = m / LGD (correction E1).

**Paramètres en scénarios déclarés** (aucun n'est mesurable sur la population évaluée, correction E3) :

| Paramètre | Scénarios | Source |
|---|---|---|
| D (délai de paiement) | 30, 45, 60 jours | 60 jours = plafond légal (C. com., art. L. 441-10, à vérifier dans le texte) ; 30 et 45 en scénarios |
| m (marge sur coûts variables du fournisseur) | 5, 10, 20, 30 % | Aucune source publique ne mesure la marge sur coûts variables : grille déclarée |
| LGD | 1 − recouvrement moyen, pondéré par l'issue finale observée sur le développement (liquidation : recouvrement 5,0 % ; continuation : 73,1 %) | Blazy, Petey et Weill (2018), cité par Banque de France WP 810 ; issues finales lues au BODACC sous la garde du scellé, censure déclarée (correction E7) |

**Région de décision R** : l'enveloppe des p_t de tous les scénarios. Elle est calculée et publiée avant tout candidat.

## 2. Verdict de signal (S0, primaire)

- **Témoin.** R2 recalibré : ordonnée et pente réestimées sur le développement, sans candidat (correction E4).
- **Assemblage.** Logit = a + b × (prédicteur de R2 figé) + γᵀ × candidats ; seul γ est pénalisé ; la grille inclut λ = 0, avec contrôle de séparation.
- **Perte.** Moyenne des pertes de décision élémentaires (au sens de Schervish) sur les seuils de R, à poids uniforme. Elle est présentée comme une perte de décision normalisée, pas en euros (correction E2). Propre, mais non strictement propre hors de R : c'est assumé, la décision ne s'exerce que dans R.
- **Statistique.** Différence appariée de perte moyenne (témoin − assemblage) sur les cohortes 2022 et 2023, chacune pesant pour moitié. Une seule inférence, fixée d'avance : bootstrap par grappes de divisions NAF, 2 000 tirages (corrections E5 et E6).
- **Verdicts :**
  - **succès** : borne inférieure de l'intervalle à 95 % au-dessus de 0 ;
  - **échec** : borne supérieure au-dessous de 0 ;
  - **indécis** : sinon.
- **Portée.** Verdict conditionnel aux cohortes et au chemin macroéconomique réalisé ; la généralité relève du prospectif.
- **Mémoire.** On publie aussi la comparaison avec R2 non recalibré et le verdict selon le critère v1.6 (G du Brier ≥ 3 %).

## 3. Verdict de pertinence (S+, sans seuil arbitraire)

**Gain monétaire par scénario.** Pour chaque scénario (m, D, LGD), gain de l'assemblage sur le témoin, en euros pour 1 € d'encours sur l'horizon, calculé par la règle de décision p < p_t.

**Deux pondérations de l'exposition :**
- équipondérée par contrepartie ;
- proportionnelle à une grandeur de taille (total de bilan).

**Seuil de rentabilité du décideur.** Au lieu de fixer un plus petit effet utile, on publie le seuil de rentabilité : l'encours annuel minimal à partir duquel le gain couvre le coût de l'information, c / gain annualisé. Valeurs de référence de c :
- **quelques centaines d'euros par an** pour un service de notation (spécification de Rémi, non vérifiée sur une grille publique) ;
- en échelle haute, la prime d'assurance-crédit, **0,1 % à 2 % du chiffre d'affaires assurable** (Banque de France, Référentiel des financements des entreprises, fiche 604, juin 2021, citant le Vernimmen) ; environ 0,1 % pour une PME dont les clients sont la grande distribution (spécification de Rémi).

**Pas de verdict binaire.** Le lecteur sait pour quelle taille de décideur l'assemblage paie son coût.

## 4. Inchangé depuis la v1.6

- Population, issue, espaces, garde du scellé, annexe A.
- Les horizons de 183 et 365 jours en sensibilité.

## Questions aux critiques

1. Les sept corrections sont-elles correctement faites ?
2. Le modèle de coûts (rotation T) et la formule de p_t sont-ils justes ?
3. La région R, l'enveloppe des scénarios, est-elle défendable comme support de la perte ?
4. Le verdict de pertinence par seuil de rentabilité est-il une réponse correcte au désaccord S0 / S+ ?
5. Reste-t-il une erreur bloquante avant amendement ?
