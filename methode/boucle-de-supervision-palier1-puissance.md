# Boucle de supervision, palier 1 : analyse de puissance après le pilote

*Rédigé le 22/10/2026 pendant l'exécution du pilote, avant toute lecture de ses résultats.*

Code : `palier1/puissance.py` ; tests : `tests/test_palier1_puissance.py`.

## 1. Méthode

La statistique primaire est la moyenne pondérée de Δ = coût(T1) − coût(B) sur les cas éligibles. Avec le tirage stratifié 50 / 50 et les poids de redressement, sa variance vaut p² s1² / n1 + (1 − p)² s0² / n0, où p = 1,10 % est la part des défaillants dans l'origine 2020 et s1², s0² les variances de Δ par strate. L'effectif total qui donne 80 % de puissance au seuil bilatéral de 5 % pour un effet δ est n = 2 (p² s1² + (1 − p)² s0²) (z_0,975 + z_0,80)² / δ². Les variances sont estimées sur le pilote, puis majorées par leur borne supérieure à 90 % ; la décision d'agrandir le tirage se prend sur l'effectif majoré. Approximation déclarée : le calcul est normal, alors que le test primaire est un test de permutation.

## 2. L'effet jugé utile, à fixer avant la lecture du pilote

La note demande d'agrandir le tirage si 300 cas ne suffisent pas « pour un effet jugé utile », sans fixer cet effet. Il doit l'être avant que les résultats du pilote soient lus, sinon il serait choisi en connaissant la variance.

**δ = 0,001 par unité d'encours, validé par le décideur le 22/10/2026 à 17 h 24, avant toute lecture des résultats du pilote**, soit l'équivalent du taux de prime π (0,1 %) : la discipline vaut la peine si elle économise au moins ce que coûte l'assurance elle-même, rapporté à l'encours. Pour mémoire, une couverture inutile sur un non-défaillant coûte πT, de 0,009 à 0,018 selon le délai de paiement.

**Sensibilité, sur un exemple fictif** (pas une donnée du pilote) : si T1 s'écartait de B sur 3 non-défaillants sur 25, chaque fois d'une couverture inutile de 0,018, et jamais sur les défaillants, il faudrait environ 550 cas pour δ = 0,001, et environ 140 pour δ = 0,002. Le choix de δ pèse donc autant que la variance observée.

## 3. Règles de décision, fixées avant le pilote

- Effectif majoré ≤ 300 : le tirage principal reste à 300 cas éligibles.
- Effectif majoré > 300 : le tirage est agrandi à cet effectif, arrondi à la dizaine supérieure, si le coût mesuré au pilote le permet ; sinon la décision revient au décideur, et un verdict sous-dimensionné serait publié comme tel.
- Aucune différence entre T1 et B au pilote : la puissance n'est pas calculable ; le principal est lancé à 300 cas si le décideur le valide, avec la mention que l'effet attendu est peut-être nul.
