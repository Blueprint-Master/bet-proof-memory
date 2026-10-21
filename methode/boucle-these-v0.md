# Boucle de calcul : cadre théorique, thèse v0 (soumise à critique à l'aveugle)

Statut : thèse de Claude, 21/10/2026, à critiquer par ChatGPT, Gemini et Mistral avant toute construction. Elle prolonge la note ATLAS du 21/10/2026 et le protocole du juge du réel (v1.7.1). Aucune donnée d'entreprise n'y figure.

## 1. Le problème

Un modèle de langage sait formuler une solution plausible. Il ne sait pas, seul, garantir qu'elle est faisable, légale, chiffrée et vérifiée. Espérer qu'il « trouve la solution » revient à parier sur la plausibilité. La thèse propose l'inverse : une **boucle de calcul** dans laquelle le modèle n'est qu'un composant, et où le chemin, les outils et la preuve sont imposés par une structure explicite.

## 2. Principes

- **P1, remonter de l'état souhaité.** Le point de départ est l'état final mesurable (PR/FAQ), pas le problème tel qu'il est formulé.
- **P2, chercher ce qui empêche.** Pour chaque but, on énumère systématiquement les obstacles et leurs parades, en arbre ET / OU. Sources : analyse des obstacles en ingénierie des exigences (van Lamsweerde et Letier, *IEEE TSE*, 2000, vérifié) ; arbres de défaillances et coupes minimales (pratique industrielle, non vérifiée ici) ; arbre des prérequis de Goldratt.
- **P3, conditions conjointes, pas suffisantes.** Un facteur (par exemple « prévision parfaite ») n'est qu'un élément d'un ensemble de conditions qui, ensemble, suffisent (condition INUS, Mackie, 1965, de mémoire). Et si une condition de l'optimum est hors d'atteinte, les autres ne doivent pas être poussées à leur valeur « parfaite » : elles se réajustent ensemble (second rang, Lipsey et Lancaster, *Review of Economic Studies*, 1956, vérifié). **Conséquence : l'état attendu de chaque étape se fixe conjointement, par calcul, jamais étape par étape.**
- **P4, deux sens de recherche.** Depuis l'état présent (quels effets ont les actions disponibles) et depuis l'état final (quelles conditions le permettent), jusqu'à jonction. Sources : analyse moyens-fins (Newell et Simon, de mémoire) ; recherche bidirectionnelle (Pohl, 1971, de mémoire) ; RRT-Connect et cartes probabilistes (note ATLAS).
- **P5, contraintes dures d'abord, critères ensuite.** Une solution est d'abord filtrée par les contraintes qu'elle ne peut pas violer (droit, sécurité, qualité), chacune lue dans sa source (texte de loi, norme, plan de maîtrise). Les solutions faisables sont ensuite comparées sur plusieurs critères (coût, délai, robustesse) : front de Pareto, puis préférences explicites (analyse multicritère, Keeney et Raiffa, 1976 ; Roy, ELECTRE ; de mémoire). Une solution « satisfaisante » au sens de Simon (*QJE*, 1955, vérifié) suffit souvent.
- **P6, l'outil est choisi par contrat.** Chaque outil est décrit par un contrat (entrées, sorties, unités, préconditions, coût, droits). Un filtre déterministe exclut les outils incompatibles ; le classement n'intervient qu'après.
- **P7, chaque étape est chiffrée.** Un obstacle sans probabilité ni impact est une liste, pas un modèle. Les chiffres viennent de données, de simulateurs ou de précédents, avec leur provenance et leur incertitude.
- **P8, quatre vérifications distinctes.** Fond (est-ce la bonne chose à faire : validation), justesse (le calcul est-il correct : vérification, Boehm, *IEEE Software*, 1984, vérifié), forme (est-ce exécutable et transmissible), coût (sur le cycle complet). Chaque aspect a son vérificateur. Une prévision ne se vérifie que contre les faits : c'est le juge du réel.
- **P9, mémoire des échecs.** Chaque essai, réussi ou non, est conservé avec ses conditions de validité. Rien n'est effacé.
- **P10, la boucle se juge elle-même.** Elle n'est adoptée que si elle bat, sur des cas nouveaux et préenregistrés, le modèle seul et le modèle avec les mêmes outils sans boucle.

## 3. La boucle

1. **État souhaité** : mesurable, daté, avec son critère de réussite (P1).
2. **Arbre des obstacles** : buts, obstacles, parades, contraintes dures, avec leurs sources (P2, P5).
3. **Chiffrage** : probabilité et impact de chaque obstacle ; état attendu de chaque étape, calculé conjointement (P3, P7).
4. **Jonction** : chemins reliant l'état présent à l'état souhaité, par les actions dont les effets sont connus (P4).
5. **Filtre et comparaison** : contraintes dures, puis Pareto, puis préférences (P5).
6. **Exécution outillée** : outils choisis par contrat, résultats avec provenance (P6).
7. **Vérification** : fond, justesse, forme, coût (P8).
8. **Mémoire et retour** : fiche d'expérience ; confrontation aux faits quand ils arrivent (P9) ; le résultat corrige l'arbre et les chiffres.

## 4. Ce qui existe et ce qui manque

- **Existe** : PR/FAQ ; juge du réel (préenregistrement, critique à l'aveugle, registre, scellé) ; compétences de méthode (Goldratt, analyse des causes, enquête) ; accès au droit dans le texte et aux données publiques ; prototype ATLAS 0.1 (exploration et mémoire sur des environnements artificiels).
- **Manque** : une représentation commune (grammaire : but, obstacle, condition, parade, contrainte, critère, preuve, liens ET / OU) ; le chiffrage des obstacles ; le filtre des contraintes avec sources ; l'évaluation de la boucle contre le modèle seul.

## 5. Limites déclarées

- Les arbres explosent ; la boucle doit borner l'exploration par un budget et une valeur attendue de l'information.
- Le second rang interdit l'optimisation branche par branche ; le calcul conjoint est coûteux et dépend de modèles qui peuvent être faux.
- Un modèle de langage qui propose les obstacles peut en omettre : la complétude de l'arbre n'est jamais garantie.
- Le transfert entre domaines (ATLAS) n'est pas traité ici.

## Questions aux critiques

1. Les dix principes sont-ils fondés ? Lesquels sont faux, redondants ou mal attribués ?
2. Que manque-t-il de structurant dans la littérature (planification, décision, ingénierie des exigences, recherche opérationnelle, sûreté de fonctionnement, agents outillés) ?
3. Le calcul conjoint de P3 est-il praticable ? Par quelle méthode ?
4. La boucle en huit étapes est-elle exécutable sans interprétation ? Où est-elle ambiguë ?
5. Quelle est la faille principale ?
