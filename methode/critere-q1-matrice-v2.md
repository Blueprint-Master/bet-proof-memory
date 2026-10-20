# Critère de jugement de la question 1 : matrice des critiques (thèse v2)

Critiques à l'aveugle reçues le 20/10/2026 :
- ChatGPT (gpt-6-astra), 14:59 UTC (`critere-q1-critiques-v2-chatgpt.md`) ;
- Gemini (gemini-4-argon), 15:09 UTC, sans voir celle de ChatGPT.

Mistral n'a pas répondu : connexion perdue, puis deux dépassements du délai de 230 s, dont un avec un prompt raccourci. Le plafond de nouvelles tentatives fixé d'avance (une) est atteint. La matrice repose donc sur deux critiques ; c'est une limite déclarée.

Ce sont des avis non vérifiés de tiers. Chaque point est confronté au calcul ou à la source, sans moyenne.

## 1. Point bloquant établi par le calcul : la région R est dégénérée

**Objection (Gemini, bloquante ; ChatGPT, B3, en partie).** Avec la rotation, p_t est si élevé que la perte n'est évaluée que dans la queue des probabilités, là où presque aucune société ne se trouve.

**Vérification (calcul, Claude).** p_t = mT / (m(T − 1) + LGD), H = 548 j :

| LGD | D | m = 5 % | 10 % | 20 % | 30 % |
|---|---|---|---|---|---|
| 0,269 (continuation) | 30 | 0,807 | 0,915 | 0,981 | 1,006 |
| 0,269 | 60 | 0,676 | 0,844 | 0,964 | 1,011 |
| 0,95 (liquidation) | 30 | 0,504 | 0,682 | 0,830 | 0,894 |
| 0,95 | 60 | 0,337 | 0,518 | 0,709 | 0,808 |

R ≈ [0,34 ; 1,01]. Le taux de défaillance à 548 jours est de 1,31 % sur le développement. Une perte de Schervish limitée à R ne compare les deux modèles que sur les rares sociétés auxquelles l'un d'eux attribue plus de 34 %. **Conséquence** : S0, tel qu'écrit, mesure presque rien. Le verdict sera indécis, ou gouverné par une poignée de cas.

**Lecture.** Ce n'est pas une erreur d'algèbre ; l'algèbre est juste (vérifiée par les deux critiques et par Claude). C'est un résultat de fond : un fournisseur qui encaisse T marges contre une seule perte a intérêt à servir presque tout le monde. Pour la décision « accorder un encours irrévocable sur 548 jours », une prévision à 548 jours est quasi sans valeur. La décision spécifiée ne permet donc pas de juger la question posée.

**Les deux corrections proposées par Gemini ne tiennent pas (calcul) :**
- *Décider cycle par cycle (T = 1)* : p_t = m / LGD ∈ [0,05 ; 1,1]. Ce seuil s'applique alors à une probabilité de défaillance à 30-60 jours, bien plus petite que celle à 548 jours. La dégénérescence est pire, pas moindre.
- *Compter T/2 marges encaissées avant la défaillance* : cela relève le gain en cas de défaillance, donc p_t. Cette correction aggrave son propre point bloquant n° 1. Elle reste juste sur le fond comme description, mais va dans le mauvais sens pour R.

## 2. Points bloquants établis et retenus

| N° | Point | Relevé par | Vérification | Correction |
|---|---|---|---|---|
| B1 | Convention de marge : m − LGD n'est cohérent que si L est la valeur facturée et m la marge rapportée au chiffre d'affaires | ChatGPT ; Gemini arrive au même résultat par un calcul de trésorerie (1 − LGD) − (1 − m) | Calcul exact | Écrire la convention |
| B2 | LGD pondérée par l'issue finale avec procédures non closes : « censure déclarée » ne suffit pas ; biais vers la liquidation, les plans étant plus longs à aboutir | ChatGPT, Gemini (convergence) | Exact : les issues observées d'une cohorte censurée surreprésentent les issues rapides | Estimateur à risques concurrents (incidence cumulée de type Aalen-Johansen) sur le délai ouverture-issue, sous la garde du scellé |
| B3 | p_t ≥ 1 quand LGD ≤ m (ou presque) | ChatGPT | Calcul : 1,006 et 1,011 dans le tableau | R borné à [0, 1] ; une règle pour les décisions constantes. Ce point est absorbé par le point 1 si la décision change |
| B4 | Annualisation : gain sur 548 jours, coût c annuel | ChatGPT, Gemini (convergence) | Exact | L_min = c × (548 / 365) / g, encours constant |
| B5 | La probabilité comparée à p_t doit être la probabilité cumulée à l'horizon, pas le hasard d'un intervalle | ChatGPT | Exact : R2 rend des hasards par intervalle | p = 1 − ∏(1 − h_k) |

## 3. Point rejeté, avec motif

**Gemini, bloquant n° 2 : « recalibrer R2 sur le développement ne protège pas de la dérive 2022-2023 ; autoriser une mise à jour de l'ordonnée sur la période cible ».**
- Mettre à jour l'ordonnée sur les cohortes du scellé utilise leurs issues : c'est une information future, interdite par la règle du scellé.
- Si un candidat anticipe, avec des données disponibles à t0, le changement de niveau du risque, c'est un vrai gain de prévision, pas un artefact.
- En revanche, il est utile de savoir si un gain vient de la calibration ou de la discrimination. **Retenu en secondaire** : publier la décomposition de la perte en miscalibration, discrimination et incertitude (MCB − DSC + UNC ; Dimitriadis, Gneiting et Jordan, 2021, *PNAS* 118(8), DOI 10.1073/pnas.2016191118, référence vérifiée sur OpenAlex).

## 4. Points non bloquants retenus

- **Méthode d'intervalle du bootstrap** à préspécifier : percentile ou BCa (ChatGPT).
- **Total de bilan** : c'est un indicateur approché de l'exposition, et il est déclaré comme tel (ChatGPT).
- **La prime d'assurance-crédit rémunère un transfert de risque, pas une information** (ChatGPT). C'est exact ; elle ne peut pas servir de coût d'information. Voir le point 5, où elle prend sa vraie place.
- **S0 est un verdict de performance décisionnelle locale**, pas de signal général (ChatGPT).

## 5. Ce qui en découle : la question de valeur à trancher

Le point 1 rend la décision spécifiée inopérante comme support du critère. Choisir la décision que la prévision sert est une spécification du décideur. Ce n'est donc pas à Claude de la trancher. Trois options :

**O1. Garder la décision « accorder l'encours »** et publier le constat : la prévision n'y sert presque à rien. S0 sera indécis par construction. C'est honnête, mais cela ne répond pas à la question 1.

**O2. Décision « couvrir ou conserver le risque de la contrepartie ».** Le fournisseur assure la créance (prime π du chiffre d'affaires réalisé avec la contrepartie) ou garde le risque. On couvre si p × LGD > π × T, d'où **p_t = π T / LGD**. C'est la même décision côté assureur : accepter ou refuser de couvrir un acheteur.

| π | LGD | D = 30 | 45 | 60 |
|---|---|---|---|---|
| 0,1 % (Rémi, clients de la grande distribution ; borne basse de la Banque de France, fiche 604) | 0,95 | 1,9 % | 1,3 % | 0,96 % |
| 0,1 % | 0,269 | 6,8 % | 4,5 % | 3,4 % |
| 2 % (borne haute de la fiche 604) | 0,95 | 38 % | 26 % | 19 % |

Avec π = 0,1 %, R ≈ [1 % ; 7 %] : la zone où se trouvent les sociétés et où se joue la discrimination. La prime trouve ici son rôle exact, celui d'un prix de transfert du risque (objection de ChatGPT). Limites déclarées :
- la quotité garantie est ignorée (la LGD de l'assuré n'est pas nulle) ;
- π est une prime de portefeuille, pas une prime par acheteur ;
- avec π = 2 %, on retombe en partie dans la queue.

**O3. Abandonner l'ancrage décisionnel** pour S0 et revenir à une règle de score propre sur tout [0, 1] (Brier ou log). Cela contredit la matrice v1 : le Brier pèse des seuils qu'aucun décideur n'utilise.

**Recommandation de Claude : O2, avec π ∈ {0,1 % ; 2 %} en scénarios et π = 0,1 % comme scénario central.** Motifs :
- c'est la seule option où la région se tire de sources (spécification de Rémi, Banque de France) et tombe là où la prévision a un objet ;
- elle répond à une décision réelle du même décideur, sur le même encours ;
- elle ne dépend d'aucune donnée du scellé ni d'aucune performance de candidat ; la règle d'amendement est respectée.

Contre-argument : O2 a été formulée après avoir vu que O1 dégénère. Ce choix a été guidé par le calcul des seuils, pas par les prédictions de R2 ni par un candidat. Il est consigné ici comme tel.

## 6. En attente

- **Art. L. 441-10 du Code de commerce.** Introuvable par l'API Légifrance le 20/10/2026 (« aucun article en vigueur sous ce numéro » ; la DILA signale qu'un article à version différée n'est pas trouvé par cette méthode). D = 60 jours reste un scénario, mais la mention « plafond légal » est retirée tant que le texte n'est pas lu.
- **Critique de Mistral** : non obtenue, et son absence est déclarée.
