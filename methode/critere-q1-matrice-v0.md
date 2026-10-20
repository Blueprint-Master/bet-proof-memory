# Critère de jugement de la question 1 : matrice des critiques (thèse v0)

Critiques à l'aveugle reçues le 20/10/2026 :
- ChatGPT (gpt-6-astra) ;
- Gemini (gemini-4-argon, en deux appels, le premier tronqué) ;
- Mistral (mistral-large-4-0).

Les réponses sont des avis non vérifiés de tiers. Aucune moyenne n'est faite : chaque point est confronté aux faits ou à une source, ou laissé ouvert.

## 1. Accords (trois critiques sur trois)

| Point | Conséquence |
|---|---|
| Séparer la question prédictive de la question décisionnelle | Diagnostic de la thèse confirmé |
| Le développement (2018-2020) et le scellé (2022-2023) ne sont pas dans le même régime | Le scellé teste une robustesse à un changement de régime, pas une généralisation sous hypothèse d'indépendance et d'identique distribution. Déjà assumé en v1.4 ; à écrire explicitement dans la portée du verdict. |
| Le bootstrap groupé par société ne capte pas les chocs communs (secteur, date) | Avec deux origines, aucune inférence sur la variabilité entre périodes n'est possible : le verdict du scellé est conditionnel aux cohortes 2022 et 2023 ; la généralité relève du prospectif (règle 5) |
| Le bénéfice net ne s'applique qu'à une décision définie (action, coûts, exposition) | Sans décision documentée, il ne peut être qu'une analyse de sensibilité |
| La règle d'amendement P-E est insuffisante : l'information qui la motive (l'échelle des gains de R2) n'est pas indépendante des données | Renforcer (voir 3) |

## 2. Désaccords

| N° | Sujet | ChatGPT | Gemini | Mistral | Confrontation |
|---|---|---|---|---|---|
| D1 | Règle de score primaire | Brier primaire, log-vraisemblance secondaire | Log-vraisemblance bornée (ε = 10⁻⁶) : elle évalue sur une échelle relative, comme une tarification du risque | Brier, la log-vraisemblance étant « pathologique » pour des événements rares | Les deux règles sont strictement propres (Gneiting et Raftery, 2007, cité par les trois). Le choix dépend de l'usage des probabilités : échelle absolue (Brier) ou relative (log). **C'est la même question que D2 : quelle décision ?** |
| D2 | Seuil de 3 % | Seuil d'importance prédictive légitime mais non justifié ; le remplacer par zéro change la question scientifique | Disproportionné sur un Brier brut ; un SESOI nul est rationnel si le coût marginal est nul | « Mise » contractuelle d'un pari, acceptable | Pas de fait qui tranche : **la valeur du seuil dépend de la décision servie** |
| D3 | Test pour modèles emboîtés | Emboîtement des modèles ≠ emboîtement des performances hors échantillon | Diebold-Mariano dégénéré pour des modèles emboîtés (Clark et McCracken, 2001 ; Clark et West, 2007) ; alternative : test conditionnel aux paramètres estimés (Giacomini et White, 2006) | n/a | Les paramètres sont figés sur le développement puis évalués sur le scellé : c'est le cadre conditionnel de Giacomini et White, où la dégénérescence ne s'applique pas selon Gemini. **Référence à vérifier avant adoption.** |
| D4 | Architecture de l'assemblage | n/a | Prédicteur linéaire de R2 en décalage (offset), seuls les candidats pénalisés | Elastic net | Le décalage isole la contribution marginale des candidats et empêche la pénalité de dégrader R2 : conforme à l'objet de P7 |

## 3. Erreurs relevées dans les critiques (vérifiées)

- **Mistral, sur la puissance.** Il calcule que 3 % du Brier (environ 0,0003) serait sous la demi-largeur de l'intervalle (0,0013).
  - Confusion d'unités : la demi-largeur de 0,13 point porte sur G, rapport sans dimension, soit 0,0013 en valeur de G ; le seuil de 3 % vaut 0,03 en valeur de G.
  - Le seuil est donc détectable : il est grand, pas indétectable. L'ambiguïté vient de la thèse, qui n'a pas donné l'unité.
- **Mistral, sur 2021.** Il propose d'ajouter 2021 comme période de validation intermédiaire. Impossible : 2021 est le tampon imposé par la règle de séparation (v1.4) ; sa fenêtre d'issue recoupe le scellé.
- **Gemini, sur les risques concurrents.** Il suppose les sorties saines traitées comme des censures à droite. En réalité, P3 les compte comme issue 0, les sociétés restant exposées jusqu'à l'horizon. Le choix est écrit, mais sa conséquence sur la calibration absolue devra être rapportée.
- **Gemini, sur le nombre de défaillances.** Il cite environ 18 000 ; le développement en compte 28 106. Sans effet sur son raisonnement.

## 4. Points recevables, sans désaccord

1. **Inclure explicitement λ = 0** (sans pénalité) dans la grille, avec contrôle de séparation (ChatGPT, Gemini). Cela remplace l'extension par décades de P-D.
2. **Rapporter aussi le verdict selon le critère initial** de la v1.6 (ChatGPT). L'amendement reste ainsi visible et réversible à la lecture.
3. **« Défaillances nettes évitées » est faux** : le bénéfice net compte des vrais positifs nets, pas un effet causal (ChatGPT).
4. **La phrase « R2 − R0 mesure toute l'information comptable » est fausse** : elle mesure l'apport d'un modèle particulier (ChatGPT). C'est corrigé.
5. **Amendements** : seuls les amendements déclenchés par des défaillances mécaniques prévues (non-convergence, séparation) passent sans jugement ; les autres suivent la procédure complète, et le verdict initial est rapporté (Gemini, ChatGPT).

## 5. Ce qui reste ouvert, et pourquoi

D1 et D2 ne se tranchent pas par la littérature : ils dépendent de **la décision que la prévision doit servir**. C'est la « mesure décisionnelle » laissée non définie depuis la phase 4. Ce n'est pas une affaire d'avis, c'est la spécification du problème : qui agit, quelle action, quelles conséquences d'une erreur. Une fois spécifiée, le seuil de probabilité et la règle de score s'en déduisent.
