# Monde simulé : spécification v3 (après gabarits, avant moteur)

*23/10/2026. Intègre la critique des gabarits (`monde-simule-gabarits-1.md`) et la leçon du verdict du palier 1 (`boucle-de-supervision-palier1-verdict.md`). La v2 reste la référence pour ce qui n'est pas modifié ici ; les sections reprises sans changement sont signalées. Non préenregistré : le préenregistrement de l'étape 1 viendra après le moteur, les contrôles et le mini-pilote. Les valeurs marquées **[à fixer en développement]** le seront par la règle indiquée, sur les seuls mondes de développement, et publiées avant la confirmation.*

## 0. Ce qui change par rapport à la v2

| Point | v2 | v3 | Origine |
|---|---|---|---|
| Modèle du monde | Décrit en prose | Modèle formel : partie publique, emplacements latents, transitions déterministes, bruit d'observation seul (§2) | Gabarits, B1, B3, §5 |
| Espace d'hypothèses | « De l'ordre de 16 à 64 » | Produit de quatre emplacements latents à trois modalités au plus : 54 hypothèses par monde (§2.3) | Gabarits, B1 |
| Atteinte | « Y au-dessus de la cible » | Prédicat terminal : une voie au moins satisfaite à l'arrêt ; équivalence vérifiée par construction (§2.4) | Gabarits, B3, B4 |
| Fin de monde | Abstention à part | Une seule action terminale `arrêter(motif)` ; U ne dépend pas du motif (§2.6) | Gabarits, B4 |
| Détection à 80 % | Confiance a posteriori | Exactitude de la décision bayésienne après k mesures, sous la loi a priori réelle (§3.2) | Gabarits, B2 |
| Neutralité | Égalité de deux heuristiques | Panel de cinq politiques en code ; critère de diversité des gagnants et d'écart à R_Bayes (§5.3) | Gabarits, M2 |
| Sensibilité de U | Non contrôlée | Contrôle préalable : les erreurs de décision doivent coûter (§5.2) | Verdict du palier 1 |
| Coût en dollars | Compté | Tarifs inscrits dans le code, coût mesuré et non recalculé après coup (§7) | Verdict du palier 1 |

## 1. Étape 1 : question, hypothèse, verdict

Inchangés (v2, §1) : question, utilité U, hypothèse primaire ΔU = E[U(C)] − E[U(T1c)], gain d'intérêt 0,10 G, marge d'équivalence ± 0,05 G, inférence par grappes de gabarit, verdict à deux niveaux.

**Ajout : plancher de G.** G est fixé sur les mondes de développement (v2). Si G < 0,15 V ou si l'écart apparié R_Bayes − R_naïf a un rapport signal sur bruit (moyenne sur écart-type) inférieur à 0,5, le verdict ne serait pas interprétable : on corrige le générateur sur le développement, ou l'on s'arrête avant la confirmation. Seuils proposés, à confirmer au préenregistrement.

## 2. Modèle formel d'un monde

### 2.1 Partie publique (donnée à tous les systèmes)

- **Variables d'état** x₁ … xₙ (n ≤ 8), entières, domaines petits (de 0 à 4 en général) ; au plus une ressource partagée (stock) qui ne peut devenir négative.
- **Catalogue d'actions** (au plus 3 types par condition) : effet nominal (variable visée, incrément borné aux limites du domaine), effets de bord déclarés, coût, délai d ≥ 1 (l'effet s'applique au terme de d périodes ; d'autres actions peuvent être lancées entre-temps), consommation de la ressource, réversibilité.
- **Réversible** signifie : il existe une action inverse déclarée, de même coût et de même délai, qui ramène la variable visée à sa valeur antérieure. **Irréversible** : aucune action inverse ; l'effet persiste.
- **Voies** : au plus 4, chacune un ensemble d'au plus 4 conditions de la forme xᵢ ≥ s, xᵢ ≤ s ou xᵢ = s (bornes incluses).
- **Paramètres du monde** : état initial, budget B, échéance T (12 à 20 périodes), valeur V de l'atteinte, valeur unitaire de Z.
- **Bruit déclaré** des mesures et des essais (§2.5).
- **Catalogue des sources** consultables par `lire` : au plus 6 noms, avec type de provenance, sans contenu.
- **Avertissement commun** : la description peut être incomplète et contenir une affirmation fausse ; des sources peuvent se contredire. Aucune fréquence n'est donnée.

### 2.2 Ce que la description affirme

La description est générée par un opérateur explicite à partir de la partie publique et de l'hypothèse vraie h* : copie fidèle de tout ce qui n'est pas latent, puis application des seules mutations prévues par h* (omission d'une condition pour l'obstacle caché, inversion d'une valeur pour l'affirmation fausse). Toute affirmation non mutée est vraie. Chaque affirmation porte une provenance : relevé daté récent, rapport daté ancien, ou mémo non daté.

### 2.3 Emplacements latents et espace d'hypothèses

La structure inconnue d'un monde tient en quatre emplacements :

| Emplacement | Modalités | Effet |
|---|---|---|
| O, obstacle caché | absent ; présent sur la condition candidate o₁ ; présent sur o₂ | Une condition supplémentaire, absente de la description, sur la voie évidente (o₁, o₂ fixés par le gabarit) |
| A, affirmation fausse | aucune ; l'affirmation a₁ est fausse ; a₂ est fausse | Une valeur du tableau est inversée (a₁, a₂ fixées par le gabarit, de provenances différentes) |
| Z, occasion | absente ; levier sur l'action z₁ ; sur z₂ | Une action, si elle est exécutée, rapporte une quantité de Z non décrite |
| I, impossibilité | non ; oui | Une condition commune à toutes les voies est rendue insatisfaisable |

D'où |H| = 3 × 3 × 3 × 2 = **54** hypothèses par monde, et au plus une affirmation fausse par monde. Les candidats (o₁, o₂, a₁, a₂, z₁, z₂) sont tirés par le gabarit et ne sont pas révélés ; ils font partie de la loi connue de R_Bayes (§4), pas de la description.

**Loi a priori** : les proportions du plan croisé (v2, §2) donnent la loi marginale de chaque emplacement ; à l'intérieur d'un emplacement présent, les deux candidats sont équiprobables ; la loi est renormalisée après les rejets du contrôle (§3), et c'est cette loi finale que connaît R_Bayes. Les anomalies de pur bruit (facteur 5) relèvent du modèle d'observation, pas de H.

**Provenance et vérité.** La provenance d'une affirmation est faiblement informative, de façon déclarée dans la loi : P(fausse | ancien ou mémo) = 2 × P(fausse | récent) **[rapport à confirmer en développement]**. Le cas « prudence coûteuse 4a » (mémo non daté mais vrai) existe donc par construction, et la provenance seule ne tranche jamais.

### 2.4 Atteinte

L'objectif est atteint si et seulement si, à l'arrêt, au moins une voie a toutes ses conditions satisfaites dans l'état réel (conditions cachées comprises). Il n'y a pas de variable Y distincte : `mesurer(objectif)` rend ce prédicat, bruité comme toute mesure. L'équivalence entre atteinte et disjonction des voies est donc vraie par construction, et un contrôle la vérifie sur l'état final de chaque trajectoire de référence.

### 2.5 Transitions et observations

- **Transitions déterministes** sachant h* et la suite des actions : l'aléa ne porte que sur les observations. C'est ce qui rend la croyance de R_Bayes réductible à une loi sur les 54 hypothèses.
- **Obstacle caché** : l'action qui devrait satisfaire la condition masquée la laisse insatisfaite (effet nul ou partiel selon le gabarit), sans message ; le coût est payé.
- **`mesurer(x)`** : rend la vraie valeur avec la probabilité q, sinon une valeur voisine (± 1, uniforme parmi les valeurs du domaine). q est déclaré dans la description.
- **`essayer(a)`** : simule l'action a à petite échelle sans changer l'état ; rend le changement observé sur la variable visée (−, 0, +), juste avec la probabilité qₑ, déclarée. Possible pour toute action, y compris irréversible : c'est sa raison d'être.
- **`lire(source)`** : déterministe, sans bruit ; rend un passage avec provenance et date. Une source de type relevé de mesure directe est exacte par déclaration ; les autres reprennent les affirmations du tableau, mutations comprises. Limite de portée déclarée : il n'existe pas de source fausse autre que celles qui reprennent l'affirmation fausse.
- **Anomalies de pur bruit** : sur des variables sans rôle causal, des valeurs mesurées qui s'écartent du nominal avec la même loi marginale à la première mesure que le signal d'un obstacle ; elles ne se répètent pas de façon cohérente et n'ont aucune conséquence.
- **Clé d'aléa** (monde, période, action, occurrence), inchangée.

### 2.6 Coûts, budget, fin

- Une action par période, `attendre` compris (coût nul, la période passe).
- Une action dont le coût excède le budget restant, ou qui rendrait la ressource négative, est **refusée** : elle ne consomme pas la période, le refus est rendu à l'agent et compté comme violation de budget.
- **`arrêter(motif)`**, motif ∈ {objectif atteint, abstention, autre} : termine le monde. À l'échéance T, l'arrêt est automatique.
- **U = V × atteinte à l'arrêt + valeur de Z acquise − coût dépensé**, quel que soit le motif. Z acquis est définitivement acquis. Le motif ne sert qu'aux mesures secondaires (abstentions justes ou injustes).
- **L'occasion sur Z consomme une période**, comme toute action : elle est en concurrence avec l'objectif, ce qui est voulu.

## 3. Contrôles à la génération (tout monde qui échoue est rejeté, et le rejet est journalisé)

1. **Cohérence texte et structure** : chaque affirmation du texte et du tableau est soit identique à la partie publique, soit le produit d'une mutation prévue par h* ; aucune autre différence.
2. **Calibrage de la détection** (facteur 1). « Détectable à 80 % en k mesures » signifie : la décision bayésienne sur l'emplacement O (présent ou absent), prise après les k mesures les plus informatives sous la loi a priori réelle, est juste dans 80 % ± 2 % des cas, exactitude calculée par énumération de toutes les suites d'observations. q est réglé par famille et par niveau de difficulté (k = 2 ou 4) pour tenir cette cible. Le même calcul, avec la loi a priori de l'emplacement I (de l'ordre de 10 %), donne la séparabilité des mondes impossibles.
3. **Faisabilité** : sous h* et à information parfaite, une suite d'actions atteint l'objectif dans T et B si I = non ; aucune n'y parvient si I = oui.
4. **Découvrabilité, trois contrôles séparés pour chaque facteur présent** : identifiable (une suite d'outils fait passer la décision bayésienne à la bonne modalité) ; accessible (cette suite tient avant l'échéance en laissant le temps d'agir, sauf dans la case 4b, où l'impossibilité de vérifier à temps est voulue et déclarée) ; utile (la valeur de l'information de cette suite est positive pour R_Bayes).
5. **Jumeaux** : un monde impossible et son jumeau faisable ont des descriptions identiques caractère pour caractère à t = 0 (texte, tableau, budget, échéance, catalogue des sources) ; ils sont toujours placés dans le même espace (développement ou confirmation).
6. **Fuites de surface** : ordre des voies, des conditions et des lignes permuté au hasard ; lexique neutre renouvelé à chaque monde ; longueur et tournures du texte fixées par le gabarit textuel, identiques pour une affirmation vraie et une fausse de même provenance.
7. **Indépendance après rejet** : sur l'ensemble des mondes acceptés, aucune corrélation significative entre les paramètres visibles (B, T, V, nombre de voies, provenances) et les emplacements latents ; la marge d'échéance de la case 4b est visible par nature et tirée indépendamment de O, A, Z et I.

Le contrôle de « non-dégénérescence de la première action » proposé par l'auteur des gabarits est supprimé ; la part des mondes dont la première action optimale est évidente est seulement publiée.

## 4. Systèmes et références

Systèmes à modèle inchangés (v2, §3 et §4 : T1c, C, T1 ; sémantique probabiliste de « vérifié », invalidation temporelle). Références précisées :

| Référence | Définition opérationnelle |
|---|---|
| R_naïf | Exécute la voie de coût total décrit le plus faible (à égalité, le plus court délai), dans l'ordre de ses conditions, sans mesurer ni lire ; `arrêter(objectif atteint)` quand la voie décrite est accomplie |
| R_explore | Lit toutes les sources, mesure une fois chaque variable d'une condition, puis exécute la voie la moins coûteuse compatible avec l'hypothèse la plus probable ; s'abstient si l'impossibilité est l'hypothèse la plus probable |
| R_boucle-code | Inchangée (v2) |
| R_Bayes | Connaît la loi de tirage finale (§2.3) et le modèle d'observation, jamais h*. Exacte par programmation dynamique sur les petits mondes (T ≤ 8) ; au-delà, recherche à profondeur bornée avec valeurs terminales QMDP, publiée comme borne basse. La valeur QMDP (Littman et al. 1995) majore la valeur optimale et la serre davantage que la valeur à information parfaite (Ross et al., « Online Planning Algorithms for POMDPs », JAIR 2008, §2.2.4, lu le 23/10/2026) : elle fournit une borne haute plus serrée que R∞, publiée avec la borne basse |
| R∞ | Connaît h* ; optimum à information parfaite |

## 5. Calibration avant tout appel de modèle

### 5.1 Valeurs du monde **[à fixer en développement]**

- V : règle proposée, V = 3 × coût moyen du chemin optimal sous R∞, pour que l'atteinte domine les coûts sans les rendre négligeables.
- Valeur de l'occasion sur Z : règle proposée, 0,2 V, pour qu'elle vaille d'être saisie sans valoir de sacrifier l'objectif.
- B : 1,5 × coût de la voie décrite la moins chère ; T : délai de cette voie plus une marge m, m ∈ {0, 1} dans la case 4b, m ∈ {3, …, 6} sinon.

### 5.2 Sensibilité de U (leçon du palier 1)

Au palier 1, T0 s'écartait de la référence sur 63 % des cas sans écart de coût significatif : un critère où la plupart des erreurs ne coûtent presque rien ne départage pas. Contrôle préalable : sur les mondes de développement, la part des mondes où U(R_naïf) et U(R_Bayes) diffèrent de plus de 0,1 V doit dépasser 30 % **[seuil proposé]** ; sinon on règle V, B et la loi des facteurs, sur le seul développement.

### 5.3 Panel de politiques et critère de neutralité

Cinq politiques en code, sans modèle de langage : **rapide** (R_naïf), **prudente** (lit tout, mesure trois fois chaque condition de la voie évidente, s'abstient si la probabilité d'impossibilité dépasse 0,5), **inspection ciblée** (ne mesure que ce dont la valeur de l'information myope dépasse le coût), **essai opportuniste** (essaie toute action irréversible avant de l'exécuter), **arrêt adaptatif** (s'arrête quand la valeur espérée de continuer devient négative). Critères, par famille et par case du plan croisé :

1. R_Bayes ≥ chacune des cinq en moyenne (contrôle du code de R_Bayes) ;
2. **diversité** : au moins deux politiques différentes sont la meilleure des cinq, chacune dans au moins 20 % des cases ;
3. **marge** : aucune des cinq n'est à moins de 0,10 G de R_Bayes sur l'ensemble ; sinon le monde est trop facile pour qu'une méthode s'y distingue d'une règle simple.

Résultats publiés case par case. L'action d'accélération coûteuse proposée par l'auteur des gabarits pour la famille « séquencement » n'est ajoutée que si le critère 2 échoue sans elle.

## 6. Familles et ordre de développement

Les quatre familles des gabarits (réglages et seuils ; flux et capacités ; ressources partagées ; séquencement et délais) sont reprises comme premier jet ; leurs valeurs numériques ne sont pas reprises. **Ordre** : « réglages et seuils » d'abord (plus petit espace d'états, effets de bord au cœur), jusqu'à passer §3 et §5 ; puis les trois autres. Corrections déjà connues : bilans matière explicites pour « ressources partagées » ; plus de « cycle » d'effets de bord pour « réglages et seuils » (l'impossibilité y passe par l'emplacement I) ; pas d'indicateur de somme de flux pour « flux et capacités » (l'atteinte est le prédicat du §2.4).

## 7. Mesures, espaces de mondes, budget

Inchangés (v2, §5 à §7), avec deux ajouts :

- les **tarifs** des modèles sont des constantes du code, datées ; le coût en dollars est mesuré pendant l'exécution, pas recalculé après coup (défaut constaté au palier 1) ;
- les **mondes rejetés** par §3 sont comptés par motif et publiés.

Aucune dépense de modèle avant le mini-pilote de T1c, qui sera soumis à accord avec son coût estimé.

## 8. Ce qui n'est pas revendiqué

Inchangé (v2, §8), plus : les sources documentaires ne mentent qu'en reprenant l'affirmation fausse du tableau ; les transitions sont déterministes ; ces deux restrictions servent le calcul exact de R_Bayes et limitent la portée d'un succès.

## 9. Liste de contrôle de la critique (gabarits, §5), état

| Élément | Où |
|---|---|
| États initiaux, budgets, V, valeur de Z | §2.1, §5.1 |
| Seuils stricts ou inclusifs | §2.1 (inclusifs) |
| Loi conjointe des facteurs | §2.3 (produit, renormalisé après rejet) |
| Effets, saturations, conversions | §2.1 (bornes du domaine), §6 (bilans matière) |
| Consommations et remboursements | §2.6 (refus sans remboursement à faire, aucun coût payé) |
| Sens de « réversible » | §2.1 |
| Délais et chevauchements | §2.1 |
| Conséquences des échecs | §2.5 (effet nul ou partiel, coût payé, sans message) |
| Bruit et dépendances | §2.5 (indépendant conditionnellement à la clé) |
| Catalogue et navigation des documents | §2.1, §2.5 |
| Nombre d'affirmations fausses | §2.3 (au plus une) |
| Règles de fin | §2.6 |
| Définition de R_naïf | §4 |
| Calcul et précision de R_Bayes | §4 |
| Critères statistiques et loi après rejet | §1, §2.3, §3.7, §5 |
