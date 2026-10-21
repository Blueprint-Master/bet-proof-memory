# Boucle de calcul : matrice des critiques (thèse v0)

Critiques à l'aveugle reçues le 21/10/2026 : ChatGPT (gpt-6-astra, 07:33 UTC), Gemini (gemini-4-argon, 07:34 UTC), Mistral (mistral-large-4-0, 07:36 UTC, après un échec de capacité du fournisseur ; prompt condensé de même substance). Avis non vérifiés de tiers ; chaque point est confronté au calcul, à la source ou laissé ouvert. Aucune moyenne. 4 appels d'IA.

## 1. La faille principale, relevée par les trois : le problème de l'ancrage

**Objection.** La boucle veut soustraire la solution à la plausibilité du modèle de langage. Mais qui construit l'arbre des obstacles, qui estime les probabilités d'obstacles inédits, qui traduit un texte de loi en contrainte ? Si c'est le modèle, l'erreur n'est pas éliminée, elle est déplacée vers le modèle du problème, et la formalisation la rend plus convaincante (Gemini : « Garbage In, Gospel Out » ; ChatGPT : « confondre cohérence interne et validité externe » ; Mistral : « calculer l'optimal sur un modèle tronqué »). Si c'est l'humain, la boucle n'est plus autonome, c'est de l'ingénierie des systèmes assistée.

**Vérification.** Exacte. La thèse v0 contredit son propre point de départ (section 1) : elle demande au modèle de formaliser le monde sans erreur. **Bloquant pour toute prétention de garantie générale ; non bloquant pour un cadre de supervision.**

**Ce qu'il en découle.** La boucle doit distinguer deux rôles, comme les cadres « LLM-Modulo » (Kambhampati et al., 2024, arXiv 2402.01817, vérifié sur OpenAlex) : le modèle de langage **propose** (arbres, hypothèses, candidats) ; des **vérificateurs indépendants du modèle** tranchent (données, solveurs, textes lus, faits). Ce qu'aucun vérificateur ne peut trancher est marqué « inconnu » et bloque l'exécution. C'est déjà ainsi que fonctionne le juge du réel : les IA proposent des mécanismes, les données jugent.

## 2. Erreurs de la thèse, établies et retenues

| N° | Erreur | Relevée par | Vérification | Correction |
|---|---|---|---|---|
| E1 | **Second rang surinterprété.** Le théorème de Lipsey et Lancaster est négatif : si une condition de l'optimum manque, les autres ne garantissent plus l'optimum contraint. Il n'impose pas un calcul conjoint et n'interdit pas une décomposition dont la validité est établie. Le « jamais étape par étape » est faux. De même, INUS décrit la causalité, ce n'est pas un opérateur d'optimisation | Les trois (convergence) | Exact | P3 reformulé : « cohérence globale », pas optimisation monolithique ; décomposition admise sous conditions explicites |
| E2 | **Chiffrage obligatoire (P7) fabrique de la précision.** Certains obstacles n'ont pas de probabilité défendable | ChatGPT | Exact | Autoriser « inconnu », intervalles, scénarios, bornes ; un inconnu structurant bloque l'exécution |
| E3 | **« Rien n'est effacé » (P9) est une règle absolue intenable** (confidentialité, limitation de conservation) | ChatGPT | Exact | Traçabilité des conclusions et des conditions de validité, sans conservation obligatoire des données brutes |
| E4 | **Ordre des étapes 3 et 4 inversé** : on chiffre « l'état attendu de chaque étape » avant d'avoir construit les chemins | Gemini | Exact | La boucle devient une machine à états avec retours, pas une suite linéaire (voir 4) |
| E5 | **« Lue dans sa source » ne rend pas une contrainte applicable.** Le droit a une texture ouverte (Hart, de mémoire) ; une norme peut être ambiguë ou contradictoire ; certaines exigences qualité sont négociables | Les trois | Exact : lire L. 3121-18 ne dit pas si une dérogation s'applique | La traduction d'une source en contrainte est elle-même une proposition à vérifier ; l'ensemble faisable vide appelle une procédure, pas un classement |
| E6 | **Vérification seulement après exécution** : insuffisant pour les actions irréversibles | ChatGPT | Exact | Contrôles avant action, pendant, après ; règle d'abstention |

## 3. Accords sans erreur, à intégrer

- **Redondance P1 / P2 / P4** (Gemini) : remonter de l'état souhaité par un arbre d'obstacles est la branche arrière de la recherche bidirectionnelle. Fusionner.
- **Tension P5** (Gemini) : front de Pareto puis préférences, contre « satisfaisant » au sens de Simon. Choisir selon l'enjeu : Pareto pour une décision lourde, seuil d'acceptabilité pour le courant. À écrire.
- **P8** : un fait observé ne valide pas une probabilité annoncée ; il faut une règle de score et une série (ChatGPT). C'est exactement P6 du protocole du juge du réel.
- **P10** : « battre » doit inclure coût, latence, erreurs graves et abstentions (ChatGPT).
- **Contrat d'outil (P6)** : ajouter version, fraîcheur, droits effectifs, comportement en échec (ChatGPT) ; c'est la conception par contrat de Meyer (Gemini, de mémoire) ; l'échec de la composition automatique de services sémantiques (OWL-S) est un précédent à lire (Gemini, non vérifié).

## 4. Ce qui manque de structurant (convergence des trois)

| Champ | Travaux cités par les critiques | Statut |
|---|---|---|
| Planification automatique | STRIPS (Fikes et Nilsson, 1971), PDDL, planification hiérarchique HTN | Non vérifiés ici, classiques |
| Décision sous incertitude | POMDP (Kaelbling, Littman et Cassandra, *Artificial Intelligence*, 1998, **vérifié**) ; diagrammes d'influence (Howard et Matheson) | L'« état » est souvent une croyance révisable, pas une situation connue |
| Ingénierie des exigences | KAOS (Dardenne, van Lamsweerde, Fickas, 1993), i* (Yu, 1995) | Formalismes de buts, obstacles, agents ; non vérifiés ici |
| Sûreté | Leveson, *Engineering a Safer World* (2011) ; HAZOP, AMDEC | Interactions et contraintes de contrôle, au-delà des défaillances isolées |
| Agents outillés | LLM-Modulo (Kambhampati et al., 2024, **vérifié**) ; ReAct ; Toolformer | Le couplage générateur / vérificateurs est déjà formalisé |
| Composants opérationnels absents | Optimisation robuste, vérification à l'exécution, politiques d'abstention, arbitrage humain | ChatGPT |

**Verdict de Gemini sur P4** : RRT-Connect et les cartes probabilistes supposent un espace métrique ; « l'état de jonction » n'a pas de définition dans un espace symbolique sans formalisation préalable. Exact ; l'analogie reste une image, pas une méthode.

## 5. Le calcul conjoint (question 3)

Convergence : praticable seulement dans un périmètre formalisé (programmation en nombres entiers, par contraintes, stochastique ou robuste, POMDP), **bloquant comme exigence universelle**. Repli proposé : propagation de contraintes par intervalles, ou recherche arborescente Monte-Carlo sous budget, en acceptant la sous-optimalité (Gemini, Mistral) ; replanification à horizon glissant (ChatGPT). Un arbre de probabilités marginales ne suffit pas : les obstacles sont corrélés (ChatGPT).

## 6. Erreurs ou faiblesses dans les critiques

- **Gemini** affirme que toutes les attributions « existent et sont correctes ». Mackie (1965) et Pohl (1971) n'ont pas été retrouvés sur OpenAlex pendant cette session : ils restent de mémoire. Un critique qui valide ce qu'il n'a pas vérifié reproduit le défaut qu'il reproche.
- **Mistral** écrit que ReAct et Toolformer « formalisent l'appel d'outils par contrat ». Ils font appeler des outils ; le contrat au sens de P6 (préconditions, droits, coût) n'y est pas, pour autant que je sache.
- **Mistral** ne connaît pas « PR/FAQ ». Ce n'est pas une erreur, c'est un défaut de la thèse, qui n'a pas défini le terme (communiqué de presse et questions-réponses écrits avant de construire, méthode d'Amazon).

## 7. Ce qui en découle pour la thèse v1

1. **Reformuler l'objet.** Non pas une boucle qui garantit le bon chemin, mais un **cadre de supervision** qui sépare ce que le modèle propose de ce que des vérificateurs indépendants tranchent, avec un domaine de validité et une règle d'abstention : « je ne sais pas, je n'exécute pas ».
2. **Corriger E1 à E6.**
3. **Importer les formalismes existants** au lieu de les réinventer : buts et obstacles (KAOS), actions à préconditions et effets (STRIPS / PDDL), croyances (POMDP), générateur / vérificateurs (LLM-Modulo).
4. **Machine à états** à la place des huit étapes linéaires : états, transitions, retours, arrêts, escalade.
5. **Premier palier = juge du réel**, parce que c'est le seul domaine où l'ancrage est déjà résolu : les données publiques construisent et jugent, le modèle ne fait que proposer. Le cycle 1 en est la démonstration : 35 propositions d'IA, 17 admises par les données, dont plusieurs nuisibles démasquées.
