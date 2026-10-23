# Monde simulé : moteur de la famille « réglages et seuils », premier lot de calibration

*23/10/2026. Code : `monde/` (modele, plan, observations, bayes, famille_reglages, description, calibrage, controles, politiques, calibrer, bilan) ; tests : `tests/test_monde.py`. Aucun appel de modèle de langage. Les sorties de calibration sont écrites hors du dépôt, leurs empreintes au registre.*

## 1. Ce qui est construit

| Élément | Spécification v3 | État |
|---|---|---|
| Modèle formel : 54 hypothèses (O, A, Z, I), transitions déterministes, A ne change que l'état initial | §2.1 à §2.3 | Fait, testé |
| Atteinte terminale, action `arrêter` unique, refus hors budget sans consommer la période | §2.4, §2.6 | Fait, testé |
| Aléa par (graine, monde, période, commande, occurrence) | §2.5 | Fait, testé |
| Description texte et tableau d'une même source, lexique et ordre tirés par monde, jumeaux identiques | §2.2, §3.1, §3.5, §3.6 | Fait, testé |
| Filtre bayésien exact sur H ; borne haute QMDP ; feuille basse « s'engager » (meilleure de 55 politiques en boucle ouverte) ; R_Bayes approchée en ligne (profondeur 1, macro-mesures de 1 à 4) | §4 | Fait |
| R_Bayes exacte sur petits mondes | §4 | **Non fait** : reportée (voir §4) |
| Contrôles 1 à 5 par monde ; 6 et 7 par lot | §3 | Faits ; 4 approché (voir §3) |
| Panel de cinq politiques, R_explore, R∞ | §4, §5.3 | Fait |
| Audit : aucune politique hors R∞ ne lit l'état caché ni le contenu tiré des sources | §2.5 | Test automatique |

## 2. Amendements à la v3 imposés par la construction

Chacun a été décidé avant tout jeu de politique sur les mondes de développement, sauf mention contraire.

1. **Obstacle caché (§2.3).** La v3 parlait d'une « condition supplémentaire absente de la description ». Dans cette famille, l'obstacle est un **effet de bord caché croisé** : l'action de réglage de l'une des deux variables de la voie évidente éloigne l'autre d'un cran de sa condition. Une première version (effet sur la stabilité) laissait le plan décrit réussir selon l'ordre des actions ; la version croisée le fait échouer quel que soit l'ordre. Les mondes où la variable touchée est en butée (effet nul) sont rejetés avant tout tirage de h.
2. **Modèle de bruit (§2.5).** Une mesure fausse rend une valeur uniforme du domaine (et non une voisine) ; l'essai rend le vrai sens avec la probabilité qₑ, sinon un sens uniforme ; la mesure de l'objectif, le vrai avec la probabilité q, sinon pile ou face. Le modèle « voisine » rendait certaines observations concluantes à elles seules : le niveau « difficile » restait détectable à 90 % même au bruit maximal, donc incalibrable.
3. **Calibrage de la détection (§3.2).** Sous la loi a priori réelle (0,25 pour un candidat d'obstacle, 0,10 pour l'impossibilité), l'exactitude est dégénérée : dire toujours « absent » donne 75 % ou 90 %. La détection est donc calibrée à loi de référence équilibrée (0,5), et la sensibilité et la spécificité sous la loi réelle sont publiées. Résultat : q = 0,4515 (80 % en 2 mesures) et q = 0,3105 (80 % en 4 mesures) ; sous la loi 0,25, sensibilité 0,68 et 0,71, spécificité 0,92 et 0,89.
4. **Échéance (§2.1).** La plage « 12 à 20 périodes » était arbitraire ; l'échéance est fixée par règle : longueur du plan décrit plus une marge (serrée : 1 ou 2 ; large : 4 à 7).
5. **Coûts et budget (§5.1).** Premier jeu (actions de 3 à 5, outils de 1 à 2, budget 1,5 fois le coût du plan décrit) : sur 32 mondes d'essai, presque tous rejetés. Deux causes : un plan « couvrant » sans mesure, qui ajoute une action de correction, valait presque autant que l'information (valeur de l'information parfaite de 0 à 1,7 pour V = 30), et le budget ne couvrait pas le vrai chemin. C'est la leçon du palier 1 rencontrée dans le générateur : quand l'erreur se corrige pour presque rien, l'information ne vaut rien. Second jeu : actions de 4 à 8, outils à 1, budget 2 fois le coût du plan décrit.

## 3. Limites connues du code à ce stade

- **Découvrabilité (contrôle 4)** : « identifiable » vérifie qu'une commande au moins a une loi d'observation différente sous l'hypothèse vraie et sous l'hypothèse sans le facteur, le long de trois plans (décrit, vrai, alternatif) ; « utile » compare la valeur de l'information parfaite sur l'emplacement, à la racine et en boucle ouverte, au coût de la commande identifiante multipliée par le nombre de mesures du niveau de difficulté. C'est une approximation de la définition de la v3, à resserrer.
- **R_Bayes** est une borne basse (politique réalisable) ; la borne haute est QMDP. L'écart entre les deux est publié.

## 4. Premier lot de calibration (un monde par case, 23/10/2026)

Règle de V : coût moyen du chemin optimal 19,81 sur 32 mondes, V = 60. Lot : 32 cases, 29 pourvues (3 non pourvues après 40 essais), 4 jumeaux impossibles, 33 mondes joués. Sorties hors dépôt : `parties.jsonl` (311d2af2…), `regle_V.json` (0cd186aa…).

| Politique | U moyenne |
|---|---|
| rapide (R_naïf) | − 2,9 |
| prudente | − 7,0 |
| inspection ciblée | 30,2 |
| essai opportuniste | − 4,9 |
| arrêt adaptatif | 21,9 |
| R_explore | − 6,2 |
| R_Bayes (approchée, borne basse) | 30,2 |
| R∞ | 39,3 |
| Borne haute QMDP (à la racine) | 40,9 |

- **G** = 33,1, soit 0,55 V ; signal sur bruit 1,07 ; part des mondes où rapide et R_Bayes diffèrent de plus de 0,1 V : 67 %. Plancher de G et sensibilité de U tenus.
- **Panel** : diversité tenue (ciblée meilleure dans 51 % des cases, arrêt adaptatif 28 %, rapide 11 %) ; **marge non tenue** : l'inspection ciblée égale R_Bayes (voir ci-dessous).
- **Indépendance après rejet** : budget et échéance sans lien détectable avec O, A, Z (p de 0,50 à 0,81, 29 mondes : test peu puissant).
- **Par facteur** : la politique rapide tombe à − 17 avec obstacle et − 18 avec ligne fausse ; R_Bayes tient (30 et 37) ; dans les mondes impossibles, R_Bayes fait − 21,5, moins bien que la politique prudente (− 6,8), et R∞ fait 0.

**Constats.**

1. **Le contrôle d'utilité sélectionnait les mondes.** 292 rejets « obstacle non utile » pour 13 mondes à obstacle acceptés (jusqu'à 32 essais pour une case) : les mondes à obstacle retenus étaient une minorité atypique, ce qui biaise le banc. Une valeur de l'information faible est une propriété légitime d'un monde (l'obstacle se répare après coup pour une action), pas un défaut. Les quatre jumeaux impossibles échouent au même contrôle : sous une probabilité a priori de 10 %, identifier l'impossibilité coûte plus que ce qu'elle épargne en espérance ; s'abstenir dès le départ n'est donc pas la conduite optimale, il faut s'arrêter quand l'impossibilité se manifeste en cours de route. **Amendement** (lot 2) : seul un facteur non identifiable entraîne un rejet ; accessibilité et valeur de l'information sont publiées, plus filtrées.
2. **L'essai dominait la mesure.** Au même coût (1), l'essai renseigne sur toutes les variables à la fois ; R_Bayes et l'inspection ciblée n'ont jamais mesuré, les macro-mesures n'ont donc jamais servi et les deux politiques se confondent. **Amendement** (lot 2) : l'essai coûte 2, comme dans le projet initial (« coût moyen »).
3. **R_Bayes approchée est faible.** 30,2 contre une borne haute de 40,9 : l'écart (0,32 G) est du même ordre que les effets à mesurer. Elle échoue surtout dans les mondes impossibles, faute de s'arrêter. G calculé avec elle est donc une borne basse. À traiter avant le préenregistrement : profondeur 2 ciblée, ou feuille en boucle fermée.
4. **La politique prudente telle que spécifiée est condamnée** : quatre lectures et neuf mesures excèdent toujours l'échéance (plan décrit plus 1 à 7 périodes). Elle n'informe sur rien d'autre que cela.
