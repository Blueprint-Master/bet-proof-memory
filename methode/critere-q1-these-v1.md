# Critère de jugement de la question 1 : thèse v1 (soumise à critique à l'aveugle)

Statut : révision de la thèse v0 après la matrice des critiques (`critere-q1-matrice-v0.md`) et la spécification de la décision par Rémi. Aucun mécanisme candidat n'a été évalué. Le protocole v1.6 reste en vigueur tant que cette thèse n'a pas passé la critique.

## 1. La décision servie (spécification, Rémi, 20/10/2026)

**Décision.** Un décideur financier accorde ou plafonne un encours commercial non garanti à une contrepartie (crédit inter-entreprises).

**Coûts d'erreur, par euro d'encours :**
- **Faux négatif** (encours accordé, la contrepartie défaille) : perte en cas de défaut LGD = 1 − taux de recouvrement d'un créancier chirographaire.
- **Faux positif** (encours refusé à une contrepartie saine) : marge m perdue sur la vente non réalisée.

**Seuil d'indifférence**, au sens de l'analyse par courbe de décision (Vickers et Elkin, 2006) :

  p_t = m / (m + LGD)

## 2. Documentation des paramètres (sources, pas de choix)

**LGD.**
- Taux de recouvrement des créanciers chirographaires : 5,0 % en liquidation et 73,1 % en continuation, sur 264 dossiers du tribunal de commerce de Paris (Blazy, Petey et Weill, 2018, *European Journal of Law and Economics*, cité par Banque de France, document de travail n° 810, note 5).
- La LGD retenue est la moyenne de ces deux taux, pondérée par la part des défaillances qui aboutissent à une liquidation ou à une continuation. Cette part est **mesurée sur l'espace de développement**, à partir des jugements du BODACC postérieurs à l'ouverture.
- Limite déclarée : échantillon parisien de taille modeste ; délai de recouvrement non actualisé.

**m.**
- Distribution observée du taux de marge brute (`marge_brute` / `chiffre_d_affaires`) des sociétés du développement dont le compte de résultat est disponible. Le fournisseur type est une société de la même population.
- Bornes : 1er et 3e quartiles.
- Limite déclarée : refuser un encours ne fait pas toujours perdre la vente (paiement comptant, garantie). La marge perdue est un majorant. Une analyse de sensibilité divise m par 2.

**Plage de seuils.** [p_t bas, p_t haut], déduite des deux bornes de m et de la LGD.

## 3. Règle de score primaire, déduite de la décision

**Le principe.**
- Toute règle de score propre est un mélange de pertes de décision à seuil (Schervish, 1989, *Annals of Statistics* ; repris par Dimitriadis, Gneiting, Jordan et Vogel, 2023, « Evaluating Probabilistic Classifiers: The Triptych », arXiv 2301.10803).
- Le Brier correspond à un mélange uniforme sur tous les seuils de 0 à 1. Il compte donc surtout des seuils que ce décideur n'utilise jamais : c'est la raison profonde de son échelle écrasée pour un événement à 1 %.
- La règle cohérente avec la décision est un **Brier pondéré** dont le mélange est concentré sur la plage de seuils documentée (Zhu et al., 2024, « Weighted Brier Score », arXiv 2408.01626).

**La règle retenue.**
- Poids uniforme sur [p_t bas, p_t haut]. C'est la loi d'entropie maximale quand seules les bornes sont connues.
- La perte s'exprime alors en euros perdus par euro d'encours : elle est directement interprétable par le décideur.
- Le Brier et la log-vraisemblance non pondérés deviennent secondaires et sont publiés.

## 4. Affirmation et test (P-A révisé)

- **Affirmation.** Sur les cohortes 2022 et 2023, avec les paramètres figés sur le développement, l'assemblage a une perte espérée (Brier pondéré) inférieure à celle de R2.
- **Cadre.** Test de capacité prédictive conditionnelle aux paramètres estimés (Giacomini et White, 2006, *Econometrica* 74(6)), qui couvre les modèles emboîtés.
- **Statistique.** Différence de perte moyenne, moyenne équipondérée des deux origines.
- **Intervalle à 95 %.** Bootstrap groupé par société (inférence conditionnelle aux cohortes). En robustesse, bootstrap groupé par secteur NAF, pour les chocs communs. Le verdict retient l'intervalle le plus large.
- **Plus petit effet utile (SESOI) = 0.** Justification : le coût marginal de l'assemblage est quasi nul (données publiques, calcul négligeable), donc tout gain positif est rationnel pour le décideur. Le gain est publié en euros pour 1 M€ d'encours, ce qui laisse chacun juger de son ampleur.
- **Verdicts :**
  - succès si la borne inférieure est au-dessus de 0 ;
  - réfutation si la borne supérieure est au-dessous de 0 ;
  - indécis sinon.
- **Portée.** Le verdict vaut pour ces cohortes et ce régime. La généralité relève de la preuve prospective (règle 5).
- **Mémoire.** Le verdict selon le critère de la v1.6 (G du Brier ≥ 3 %) est aussi publié.

## 5. Secondaires

- Diagramme de Murphy (dominance sur tous les seuils, Dimitriadis et al., 2023).
- Courbe de bénéfice net sur la plage de seuils.
- Brier et log-vraisemblance non pondérés.
- Calibration (ordonnée, pente).
- Les mêmes mesures sur la sensibilité « m / 2 ».

## 6. Architecture et estimation

- **Assemblage.** Logit = a + b × (prédicteur linéaire de R2, figé) + γᵀ × (mécanismes candidats). Seul γ est pénalisé. La contribution des candidats est isolée, et la pénalité ne peut pas dégrader R2.
- **Pénalité.** La grille inclut explicitement λ = 0, avec un contrôle de séparation (le maximum de vraisemblance doit exister). La règle est la même pour R2 et pour γ.

## 7. Amendements

- **Sans procédure complète** : les déclenchements mécaniques prévus d'avance (non-convergence, séparation), avec un repli codé.
- **Tous les autres** : thèse, critique à l'aveugle, matrice, journal.
- **Dans tous les cas**, le verdict selon la version précédente est publié à côté.

## Questions aux critiques

1. La déduction « décision → plage de seuils → Brier pondéré » est-elle correcte et complète ?
2. Les paramètres (LGD, m) sont-ils documentés sans arbitraire ? Quelles sources meilleures ou complémentaires ?
3. Un SESOI nul est-il défendable ici ?
4. Le cadre de Giacomini et White et les deux bootstraps conviennent-ils ?
5. Quelle faille reste-t-il ?
