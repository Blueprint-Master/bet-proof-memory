# Critère de jugement de la question 1 : thèse v3 (soumise à critique à l'aveugle)

Statut : révision après la matrice v2. Rémi a choisi, le 20/10/2026, la décision servie « couvrir ou conserver le risque de la contrepartie » (option O2). Les corrections B1 à B5 sont intégrées. Aucun mécanisme candidat n'a été évalué. Le protocole v1.6 reste en vigueur jusqu'à l'amendement.

## 1. Décision et modèle de coûts

**Décision (spécification de Rémi).** Un fournisseur détient sur une contrepartie un encours commercial L, constant sur l'horizon H = 548 jours. Il choisit, à t0, de couvrir ce risque par une assurance-crédit ou de le conserver.

**Conventions (B1).**
- L est la valeur facturée de l'encours.
- D est le délai de paiement et T = H / D la rotation, donc le chiffre d'affaires réalisé avec la contrepartie sur l'horizon vaut L × T.
- π est la prime d'assurance-crédit, rapportée au chiffre d'affaires assuré.
- LGD est la perte en cas de défaillance, rapportée à L.

**Coûts par euro d'encours, sur l'horizon :**
- couvrir : π × T, que la contrepartie défaille ou non ;
- conserver : LGD si la contrepartie défaille, 0 sinon.

On couvre si p × LGD > π × T, d'où :

  **p_t = π × T / LGD**

Ici p est la **probabilité cumulée de défaillance à 548 jours** (B5). Elle se déduit des hasards par intervalle de R2 et de l'assemblage par p = 1 − ∏(1 − h_k).

**Paramètres :**

| Paramètre | Valeurs | Source |
|---|---|---|
| π | **0,1 % (scénario central)** ; 2 % (sensibilité) | 0,1 % : spécification de Rémi pour une PME dont les clients sont la grande distribution, et borne basse de la Banque de France (Référentiel des financements des entreprises, fiche 604, juin 2021, citant le Vernimmen : 0,1 % à 2 % du chiffre d'affaires assurable) ; 2 % : borne haute de la même fiche |
| D | 30, 45, 60 jours | Scénarios déclarés. La qualification « plafond légal » de 60 jours (C. com., art. L. 441-10) est retirée tant que le texte n'est pas lu |
| LGD | 1 − recouvrement moyen chirographaire, pondéré par l'issue finale : liquidation (recouvrement 5,0 %) ou continuation (73,1 %) | Blazy, Petey et Weill (2018), cité par Banque de France, document de travail n° 810. Pondération par l'**incidence cumulée de type Aalen-Johansen** de la liquidation et de la continuation, sur le délai ouverture-issue, en risques concurrents. Calcul sur le développement, annonces parues avant le 30/09/2022 seulement (B2) |

**Région de décision.**
- **R primaire** : enveloppe des p_t pour π = 0,1 %, sur D et LGD. Avec la LGD bornée par ses deux valeurs extrêmes, R ≈ [0,96 % ; 6,8 %]. La région définitive sera recalculée avec la LGD estimée, puis publiée avant tout candidat.
- **R de sensibilité** : la même enveloppe pour π = 2 %, environ [19 % ; 100 %].
- **Bornes (B3).** Tout p_t ≥ 1 est un scénario à décision constante (couvrir n'est jamais rentable) : il est retiré de R et rapporté comme tel.

**Limites déclarées :**
- la quotité garantie par l'assureur est ignorée : sous couverture, la perte résiduelle de l'assuré est supposée nulle ;
- π est une prime de portefeuille, appliquée ici par contrepartie ;
- les délais de recouvrement ne sont pas actualisés.

## 2. Verdict de signal (S0, primaire)

- **Témoin.** R2 recalibré (ordonnée et pente réestimées sur le développement, sans candidat).
- **Assemblage.** Logit = a + b × (prédicteur de R2 figé) + γᵀ × candidats ; seul γ est pénalisé ; la grille inclut λ = 0, avec contrôle de séparation.
- **Perte.** Moyenne uniforme des pertes de décision élémentaires de Schervish sur les seuils de la R primaire, appliquée à la probabilité cumulée. Elle est présentée comme une perte de décision normalisée. Elle est propre, mais non strictement propre hors de R, et c'est assumé.
- **Statistique.** Différence appariée de perte moyenne (témoin − assemblage) sur les cohortes 2022 et 2023, chacune pesant pour moitié.
- **Inférence, unique et préspécifiée.** Bootstrap par grappes de divisions NAF (environ 88 grappes), 2 000 tirages, **intervalle percentile à 95 %**.
- **Verdicts :**
  - **succès** : borne inférieure au-dessus de 0 ;
  - **échec** : borne supérieure au-dessous de 0 ;
  - **indécis** : sinon.
- **Portée.** Verdict de performance décisionnelle locale, sur ces cohortes et pour le chemin macroéconomique réalisé.
- **Publiés aussi, sans valeur de verdict :**
  - le même calcul sur la R de sensibilité ;
  - la comparaison avec R2 non recalibré ;
  - le verdict selon le critère de la v1.6 ;
  - la décomposition de la perte en miscalibration, discrimination et incertitude (MCB − DSC + UNC, Dimitriadis, Gneiting et Jordan, 2021, *PNAS* 118(8)).

## 3. Verdict de pertinence (S+, sans seuil arbitraire)

**Gain monétaire.** Pour chaque scénario (π, D, LGD), on calcule la différence de coût réalisé moyen entre le témoin et l'assemblage, par euro d'encours sur l'horizon. Le coût réalisé d'une société vaut π T si le modèle dit « couvrir » (p > p_t), et y × LGD sinon, y étant l'issue observée.

**Deux pondérations de l'exposition :**
- équipondérée par contrepartie ;
- proportionnelle au total de bilan, indicateur approché de l'exposition.

**Seuil de rentabilité (B4).** L_min = c × (548 / 365) / g, avec :
- g, le gain par euro d'encours sur 548 jours ;
- c, le coût annuel de l'information, quelques centaines d'euros par an pour un service de notation (spécification de Rémi, non vérifiée sur une grille publique) ;
- un encours supposé constant.

La prime d'assurance n'est plus utilisée comme coût d'information : elle est le prix du transfert de risque, paramètre de la décision.

**Pas de verdict binaire.**

## 4. Inchangé depuis la v1.6

- Population, issue, espaces, garde du scellé, annexe A.
- Les horizons de 183 et 365 jours servent de sensibilité ; pour eux, T et p_t sont recalculés avec H égal à l'horizon.

## Questions aux critiques

1. Le modèle de coûts « couvrir ou conserver » et la formule p_t = π T / LGD sont-ils justes ?
2. Les corrections B1 à B5 sont-elles correctement intégrées ?
3. La R primaire tirée du scénario π = 0,1 % est-elle défendable, la sensibilité à π = 2 % étant publiée sans valeur de verdict ?
4. Reste-t-il une erreur bloquante avant amendement du protocole ?
