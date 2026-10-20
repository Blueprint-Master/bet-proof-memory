# Critère de jugement de la question 1 : matrice des critiques (thèse v1)

Critiques à l'aveugle reçues le 20/10/2026 de ChatGPT (gpt-6-astra), Gemini (gemini-4-argon) et Mistral (mistral-large-4-0). Ce sont des avis non vérifiés de tiers : chaque point est confronté au calcul ou à la source, sans moyenne.

## 1. Erreurs de la thèse v1, établies et retenues

| N° | Erreur | Relevée par | Vérification | Correction |
|---|---|---|---|---|
| E1 | **Formule du seuil fausse.** p_t = m / (m + LGD) traite la perte en cas de défaut et la marge comme deux coûts qui s'additionnent. | Gemini | Calcul. Accorder 1 € de vente à crédit rapporte m si le client paie, m − LGD s'il défaille ; refuser rapporte 0. On accorde si m − p × LGD > 0, d'où **p_t = m / LGD**. | Remplacer la formule |
| E2 | **Fausse monétisation.** Un Brier pondéré est sans dimension ; l'échelle (m, LGD) varie d'un seuil à l'autre, il ne s'exprime pas « en euros ». | Les trois | Calcul : la perte élémentaire en euros vaut (échelle) × perte à seuil ; un mélange uniforme de pertes à seuil n'est pas une perte en euros. | Ne plus parler d'euros pour le score ; un calcul en euros exige un modèle monétaire explicite (voir 3) |
| E3 | **m mesuré sur la mauvaise société.** m est la marge du fournisseur qui décide, pas celle de la contrepartie évaluée ; la marge pertinente est la marge sur coûts variables, pas la marge brute comptable. | Les trois | Exact par définition de la décision | m ne peut pas être tiré de la population évaluée ; il devient un paramètre de scénario documenté |
| E4 | **Confusion entre gain des candidats et recalibration.** L'assemblage réestime ordonnée et pente : il peut battre R2 par simple recalibration. | ChatGPT, Gemini | Exact : l'assemblage a deux degrés de liberté que R2 figé n'a pas | Ajouter un bras témoin : R2 recalibré (ordonnée et pente), sans candidat ; l'assemblage se compare à ce témoin |
| E5 | **Giacomini et White mal invoqués.** Leur théorie asymptotique porte sur le nombre de périodes ; ici deux périodes et un grand nombre de sociétés. Une différence de moyennes sans instruments n'est pas leur test conditionnel. | ChatGPT, Gemini | Le résumé de l'article (Econometrica, 2006) mentionne la couverture des modèles emboîtés ; le cadre asymptotique n'a pas été lu dans le texte intégral. Retenu par prudence. | Retirer la référence ; décrire le test comme une différence appariée de pertes sur deux coupes transversales, avec dépendance par grappes |
| E6 | **« L'intervalle le plus large fait foi » n'a pas de couverture garantie.** | Les trois | Exact | Une seule inférence préspécifiée |
| E7 | **LGD pondérée par l'ouverture et non par l'issue finale.** Beaucoup de redressements finissent en liquidation ; les issues récentes sont censurées. | Gemini, ChatGPT | Exact. Le BODACC permet de suivre les conversions, mais sous la garde du scellé (parutions avant le 30/09/2022). | Pondérer par l'issue finale observée, censure déclarée, données sous garde seulement |

## 2. Accords sans erreur à corriger, mais à intégrer

- **Grappes sectorielles.** Avec deux origines, aucune variabilité entre régimes n'est estimable ; l'inférence est conditionnelle au chemin macroéconomique réalisé. Gemini propose de grouper au niveau de la **division NAF (environ 88 grappes)** : assez de grappes pour le bootstrap, assez larges pour les chocs sectoriels. Aucune objection des deux autres.
- **Pondération par l'exposition.** Un score équipondéré par société sous-pèse les contreparties qui portent l'essentiel de l'encours (Gemini). À traiter en scénario : équipondéré, ou pondéré par une grandeur de taille.
- **Horizon de 548 jours et maturité des encours** (ChatGPT, Mistral). L'horizon reste celui du protocole : un encours renouvelé expose au risque sur la durée de la relation. Les horizons de 183 et 365 jours, déjà prévus, servent de sensibilité.

## 3. Désaccord restant : que faut-il pour déclarer un succès ?

| Position | Tenants | Argument |
|---|---|---|
| **S0 : supériorité seule.** Succès si l'assemblage a une perte inférieure à R2 recalibré (seuil nul), l'ampleur économique étant publiée en scénarios, sans verdict binaire | ChatGPT (sous réserve de séparer supériorité et pertinence) | C'est la seule affirmation que les données publiques permettent d'établir sans paramètre non identifiable |
| **S+ : supériorité et pertinence.** Succès seulement si le gain dépasse un seuil économique positif | Gemini (1 point de base de l'encours, soit 100 € par million : proposition non sourcée), Mistral (coût annuel de déploiement rapporté à l'encours) | Avec des millions de cas, un gain infime devient significatif ; le déploiement d'un modèle a un coût réel |

**Pourquoi ce désaccord ne se tranche pas par une source.** Le seuil de pertinence est le coût d'adoption d'un outil de notation pour le décideur. Aucune des trois critiques ne cite de source pour ce coût, et aucune donnée publique ne le mesure. C'est **une question de valeur sur la nature de l'affirmation** :
- S0 répond à la question « y a-t-il un signal réel au-delà de R2 ? » ;
- S+ répond à la question « vaut-il la peine de l'utiliser ? ».

## 4. Erreurs relevées dans les critiques

- **Mistral** :
  - « Selon Schervish, minimiser le Brier conduit à la meilleure décision pour toute perte convexe » : faux. La représentation de Schervish dit que toute règle propre est un mélange de pertes à seuil, et qu'un Brier pondéré concentré sur un seuil est la perte à ce seuil.
  - « R2 = taux de défaillance historique constant » : faux. R2 contient les ratios comptables, et le logit simple sur ratios qu'il réclame existe déjà : c'est R2.
- **Gemini** : il recommande la distribution empirique de m plutôt qu'une loi uniforme, ce qui est juste ; mais cette distribution empirique est précisément celle de la mauvaise société (E3).
- **ChatGPT** : rien de faux relevé ; il signale à raison qu'un poids limité à un intervalle donne un score propre mais non strictement propre sur tout [0, 1].

## 5. Ce qui en découle pour la thèse v2

1. **Affirmation statistique.** Différence appariée de pertes entre l'assemblage et R2 recalibré, sur les cohortes du scellé, avec bootstrap par grappes de divisions NAF.
2. **Perte.** Score à seuil intégré sur la plage p_t = m / LGD, la plage étant tirée de scénarios documentés de m et de LGD. Il est présenté comme une perte de décision normalisée, pas comme des euros.
3. **Économie.** Perte monétaire calculée sous scénarios explicites (m, LGD par issue finale, pondération par l'exposition), publiée en sensibilité.
4. **Critère de succès.** S0 ou S+ : c'est l'arbitrage restant.
