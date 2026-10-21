# La boucle de calcul : cadre théorique et protocole de test (v1)

Note de cadrage, 21 octobre 2026. Elle remplace la thèse v0 après la matrice des critiques (`boucle-matrice-v0.md`). Son objet est de fixer, avant toute ligne de code, ce que l'on construit, pourquoi, et comment on saura si cela marche. Après cette note, l'exécution n'est plus qu'une mise en œuvre.

Statut : version 1, rédigée par Claude. Dernière étape avant gel : un tour de critique à l'aveugle sur ce texte, comme pour le protocole v1.7, puis validation de Rémi.

---

## 0. Résumé

**Le problème.** Un modèle de langage produit des solutions plausibles. Il ne peut pas, seul, garantir qu'une solution est faisable, légale, chiffrée et vraie. Espérer qu'il « trouve » revient à parier sur la plausibilité.

**L'idée reçue qu'il faut abandonner.** On ne corrige pas ce défaut en imposant au modèle une structure formelle (arbres, probabilités, contraintes), parce que c'est encore le modèle qui remplirait la structure. L'erreur n'est pas supprimée, elle est déplacée vers le modèle du problème, et la forme mathématique la rend plus convaincante. C'est la faille principale de la thèse v0, relevée par les trois critiques indépendants.

**La proposition.** Une **boucle de supervision** qui sépare deux rôles :
- le modèle de langage **propose** : états souhaités, obstacles, hypothèses, chemins, candidats ;
- des **vérificateurs indépendants du modèle** tranchent : données, calculs, textes lus, faits observés.

Tout élément qu'aucun vérificateur ne peut trancher reçoit le statut **inconnu**. Un inconnu sur le chemin critique interdit l'exécution : la boucle répond « je ne sais pas, je n'exécute pas ».

**La preuve.** La boucle n'est adoptée que si elle bat, sur des cas nouveaux et préenregistrés, deux témoins : le modèle seul, et le modèle avec les mêmes outils mais sans la boucle. Le protocole de test (section 5) fixe les cas, les mesures, le verdict et le budget avant la première exécution.

**Le premier terrain.** Le juge du réel (prévision de défaillance d'entreprise), parce que c'est le seul domaine où l'ancrage est déjà résolu : les données publiques construisent et jugent, le modèle ne fait que proposer.

---

## 1. Point de départ

### 1.1 Ce que nous avons déjà observé

Trois faits tirés du projet « juge du réel » (protocole v1.7.1, cycle 1, 20 octobre 2026) motivent cette note :

1. **Les IA proposent, les données tranchent, et les deux ne coïncident pas.** Sur 35 mécanismes candidats proposés par trois IA, 17 ont été admis par les données ; plusieurs variables jugées plausibles par leurs auteurs se sont révélées nuisibles (jusqu'à −27 % sur un pli pour une intensité de défaillances par taille). Aucun débat entre IA n'aurait démasqué ces variables ; seuls les faits l'ont fait.
2. **Une erreur silencieuse de données a traversé toute la chaîne.** Une série de la Banque de France a été lue vide pendant deux évaluations complètes, sans qu'aucun contrôle ne s'en aperçoive. Le défaut n'a été vu que parce que trois candidats sont sortis exactement nuls. Il a fallu ajouter des arrêts mécaniques. Leçon : une boucle sans vérificateur à chaque étape laisse passer des erreurs que la cohérence interne masque.
3. **Le critère de jugement a demandé quatre tours de critique.** Définir ce qu'est un « succès » sur un seul domaine a exigé une décision explicite du décideur, des sources, et plusieurs corrections d'algèbre. C'est le coût réel de l'ancrage, et il faut l'attendre pour chaque nouveau domaine.

### 1.2 La question de Rémi

Partir de l'état souhaité, chercher ce qui l'empêche, juger une solution sur plusieurs plans (opérationnel, financier, juridique, qualité), la valider sur plusieurs aspects (fond, forme, justesse, coût). Exemple donné : un taux de service insuffisant. « Si la prévision était parfaite, le problème serait réglé » n'est vrai que si tout le reste l'est aussi (ordonnancement respecté, pas de panne, prestataire fiable, production conforme). Il faut donc remonter de l'état final en listant ce qui pourrait l'empêcher, puis définir l'état attendu de chaque étape.

### 1.3 Ce que la critique à l'aveugle a changé

La thèse v0 (dix principes, boucle en huit étapes) a été critiquée par ChatGPT, Gemini et Mistral. Six erreurs ont été retenues et sont corrigées ici :
- le théorème du second rang avait été surinterprété (il n'impose pas un calcul conjoint) ;
- le chiffrage obligatoire fabrique de la précision ;
- « rien n'est effacé » est intenable ;
- deux étapes étaient dans le mauvais ordre ;
- lire une contrainte dans sa source ne la rend pas applicable ;
- vérifier après l'exécution ne suffit pas pour une action irréversible.

Et surtout la faille d'ancrage, qui change l'objet même du projet : non pas une boucle qui garantit le bon chemin, mais une boucle qui **sait ce qu'elle ne sait pas**.

---

## 2. Cadre théorique

Chaque sous-section donne l'idée, sa source, et ce qu'elle impose à la boucle. Les références marquées « vérifié » ont été retrouvées sur OpenAlex ou Légifrance pendant la rédaction ; les autres sont de mémoire et devront être vérifiées avant le gel.

### 2.1 Le problème de l'ancrage

**Idée.** Formaliser un problème ne le rend pas vrai. Si le même modèle produit le plan, ses chiffres et sa validation, une erreur du modèle se propage avec l'apparence de la rigueur. La question n'est pas « le raisonnement est-il cohérent ? » mais « chaque élément du raisonnement a-t-il été confronté à quelque chose d'extérieur au modèle ? ».

**Source.** Convergence des trois critiques de la v0 ; formulation la plus proche dans les cadres « LLM-Modulo » (Kambhampati et al., 2024, arXiv 2402.01817, vérifié) : le modèle de langage génère des candidats, des vérificateurs externes (solveurs, simulateurs, règles) les acceptent ou les rejettent, et la boucle itère.

**Ce que cela impose.** Tout objet produit par le modèle porte un **statut d'ancrage** : *proposé* (par le modèle), *vérifié* (par un vérificateur nommé, avec sa trace), *contredit* (par un vérificateur), *inconnu* (aucun vérificateur disponible). Seuls les objets vérifiés servent à décider. Les inconnus se publient, ils ne se comblent pas.

### 2.2 Buts et obstacles

**Idée.** Un but se décompose en sous-buts (liens ET : tous nécessaires ; liens OU : l'un suffit). Pour chaque but, on cherche systématiquement les **obstacles** (conditions qui empêchent le but) et, pour chaque obstacle, les **parades**. C'est l'analyse des obstacles de l'ingénierie des exigences orientée buts.

**Source.** van Lamsweerde et Letier, *IEEE Transactions on Software Engineering*, 2000 (vérifié) ; méthode KAOS (Dardenne, van Lamsweerde et Fickas, 1993, de mémoire). Même structure dans les arbres de défaillances de la sûreté de fonctionnement (norme CEI 61025, de mémoire), où les « coupes minimales » sont les plus petits ensembles de causes qui suffisent à produire l'échec, et dans l'arbre des prérequis de Goldratt.

**Ce que cela impose.** L'arbre est l'objet central de la boucle. Mais il est **proposé** par le modèle : sa complétude n'est jamais garantie. Chaque nœud doit donc être ancré (2.1), et l'arbre reste ouvert à l'ajout d'obstacles révélés par les faits (section 4, état S9).

**Exemple.** But : « taux de service ≥ 98 % sur le trimestre ». Obstacles (OU : chacun suffit à faire échouer) : prévision fausse ; ordonnancement non respecté ; panne de ligne ; prestataire défaillant ; production non conforme. Une parade par obstacle, et chaque parade a ses propres obstacles.

### 2.3 Conditions conjointes et second rang

**Idée.** « Prévision parfaite » n'est qu'un élément d'un ensemble de conditions qui, ensemble, suffisent. Seule, elle n'est ni nécessaire (d'autres ensembles, avec du stock ou de la flexibilité, atteignent le même taux de service) ni suffisante. C'est la condition INUS de Mackie (1965, de mémoire : élément insuffisant mais nécessaire d'une condition non nécessaire mais suffisante).

Le théorème du second rang (Lipsey et Lancaster, *Review of Economic Studies*, 1956, vérifié) ajoute un résultat négatif : si une condition de l'optimum ne peut pas être remplie, pousser les autres à leur valeur « parfaite » n'est en général plus optimal. **Correction par rapport à la v0** : ce théorème ne prescrit pas un calcul conjoint de tout, et n'interdit pas de découper le problème quand la validité du découpage est établie. Il dit seulement qu'on ne peut pas supposer que les étapes sont indépendantes.

**Ce que cela impose.** L'état attendu de chaque étape ne se fixe pas en isolant l'étape. La boucle doit soit (a) traiter les étapes ensemble dans un modèle formel quand il existe (programmation par contraintes, optimisation stochastique ou robuste), soit (b) déclarer que les étapes sont traitées séparément, avec l'hypothèse d'indépendance écrite et testable, soit (c) marquer l'interaction comme inconnue. Les trois options sont permises ; le silence ne l'est pas.

### 2.4 Actions, états et croyances

**Idée.** Une action se décrit par ses **préconditions** (ce qui doit être vrai avant) et ses **effets** (ce qui devient vrai après). Un chemin est une suite d'actions dont chaque précondition est soit un fait vérifié, soit l'effet d'une action précédente. C'est le formalisme STRIPS de la planification automatique (Fikes et Nilsson, 1971, de mémoire ; langage PDDL).

Quand l'état n'est pas connu avec certitude, ce qu'on manipule est une **croyance** : une distribution sur les états possibles, révisée à chaque observation. C'est le cadre des processus de décision partiellement observables (Kaelbling, Littman et Cassandra, *Artificial Intelligence*, 1998, vérifié). La conséquence pratique : **la meilleure action suivante peut être une mesure**, qui ne change pas le monde mais réduit l'incertitude.

**Ce que cela impose.** Les actions de la boucle sont décrites par contrat (préconditions, effets, coût, durée, réversibilité, droits). La « jonction » entre la recherche en avant (depuis l'état présent) et la recherche en arrière (depuis l'état souhaité) a une définition précise : elle est atteinte quand tout prérequis du but est couvert par un fait vérifié ou par l'effet d'une action du chemin. Sans cette définition, l'analogie du GPS n'est qu'une image (critique de Gemini sur RRT-Connect : ces méthodes supposent un espace métrique que les problèmes symboliques n'ont pas).

### 2.5 Contraintes dures et critères

**Idée.** Deux natures de critères ne se mélangent pas :
- les **contraintes dures** décident de la faisabilité (droit, sécurité des aliments, sécurité des personnes, qualité). Une solution qui en viole une est éliminée, quel que soit son coût ;
- les **critères** départagent les solutions faisables (coût, délai, robustesse). On conserve les solutions qu'aucune autre ne bat sur tous les critères à la fois (front de Pareto), puis on tranche par des préférences explicites (analyse multicritère : Keeney et Raiffa, 1976 ; Roy, méthodes ELECTRE ; de mémoire). Pour une décision courante, une solution « satisfaisante » qui dépasse un seuil suffit (Simon, *Quarterly Journal of Economics*, 1955, vérifié) ; le front de Pareto est réservé aux décisions lourdes.

**La correction de la v0.** Lire une contrainte dans sa source ne la rend pas applicable. Le droit a une texture ouverte (Hart, de mémoire) : un texte connaît des exceptions, des dérogations, des interprétations. Exemple vérifié : le Code du travail limite la durée quotidienne de travail d'un salarié à dix heures (art. L. 3121-18, lu sur Légifrance) et la durée hebdomadaire à quarante-huit heures (art. L. 3121-20). Ces articles ne limitent pas le fonctionnement de l'usine ; une organisation en équipes successives n'est pas exclue par eux, et le travail de nuit relève d'autres textes. Formuler la contrainte « l'usine ne peut pas tourner 24 heures sur 24 » au lieu de « un salarié ne peut pas dépasser 10 heures par jour » élimine à tort une solution valable.

**Ce que cela impose.** Une contrainte dure est un triplet : *source lue par un outil* (texte, norme, plan de maîtrise), *énoncé formel*, *applicabilité*. Les deux derniers sont **proposés** par le modèle et doivent être vérifiés : par un second lecteur, par un juriste, ou par une règle enregistrée. Une contrainte dont l'applicabilité est inconnue bloque la solution concernée. Quand l'ensemble des solutions faisables est vide, la boucle ne classe pas : elle remonte à l'arbre (états S6 → S2) ou s'abstient.

### 2.6 Chiffrage et incertitude

**Idée.** Un obstacle sans probabilité ni impact est une liste, pas un modèle. Mais exiger un chiffre pour tout fabrique de la précision là où elle n'existe pas.

**Ce que cela impose.** Chaque obstacle porte une **estimation typée** : une probabilité avec sa provenance (données, précédent, simulateur), un intervalle, un ensemble de scénarios, ou **inconnu**. Un inconnu sur un obstacle qui appartient à une coupe minimale (2.2) est structurant : il bloque l'exécution. Un inconnu hors du chemin critique est publié et n'arrête rien. Les obstacles peuvent être corrélés (cause commune) ; un arbre de probabilités marginales ne suffit pas, et la corrélation inconnue est elle-même un inconnu à publier.

### 2.7 Vérification et validation

**Idée.** Le génie logiciel distingue depuis longtemps (Boehm, *IEEE Software*, 1984, vérifié) :
- la **vérification** : construit-on la chose correctement ? (justesse du calcul, forme exécutable) ;
- la **validation** : construit-on la bonne chose ? (fond : le but atteint est-il le but voulu ?).

Le **coût** s'ajoute, mesuré sur le cycle complet et non sur la dernière réponse.

**Ce que cela impose.** Quatre vérificateurs distincts, et une règle pour chacun :
- *justesse* : un recalcul indépendant (code déterministe, pas le modèle) ;
- *forme* : un test d'exécutabilité (le livrable tourne, se transmet, respecte le format) ;
- *fond* : la comparaison au critère de l'état souhaité, quand il est observable ; sinon, une **prévision enregistrée** dont le verdict viendra des faits (c'est le juge du réel, avec sa règle de score : une observation isolée ne valide pas une probabilité, il faut une règle de score propre et une série) ;
- *coût* : appels, temps, argent, comptés par la boucle elle-même.

Un vérificateur ne peut pas être le modèle qui a produit l'objet vérifié. Ce point est non négociable : c'est la seule défense contre la faille d'ancrage.

### 2.8 Actions irréversibles et abstention

**Idée.** Vérifier après l'exécution ne protège pas d'une action dommageable. Il faut trois moments de contrôle : avant l'action (préconditions, droits, mandat), pendant (surveillance), après (résultat).

**Ce que cela impose.** Chaque action porte un attribut de **réversibilité**. Une action irréversible exige un mandat explicite du décideur. La boucle dispose d'un état terminal **ABSTENTION**, avec motif, atteignable depuis tout état : inconnu structurant, contrainte d'applicabilité inconnue, ensemble faisable vide, budget épuisé, action hors mandat. L'abstention n'est pas un échec de la boucle ; une abstention justifiée est un résultat correct, et elle est mesurée comme telle (section 5).

### 2.9 Mémoire

**Idée.** Chaque essai, réussi ou non, enseigne quelque chose, à condition de conserver ses conditions de validité. La mémoire négative (ce qui a échoué, et où) vaut autant que la mémoire positive.

**La correction de la v0.** « Rien n'est effacé » est intenable (confidentialité, durées de conservation). Ce qui est conservé sans limite : les conclusions, leur statut d'ancrage, leurs conditions de validité, les empreintes des données. Ce qui peut être effacé selon les règles applicables : les données brutes.

### 2.10 Évaluer une méthode

**Idée.** Une méthode n'est pas adoptée parce qu'elle est cohérente ou parce que plusieurs IA l'approuvent. Elle est adoptée si elle fait mieux que des témoins, sur des cas qu'elle n'a pas vus, selon des mesures et un verdict fixés avant l'exécution. Ce sont les règles fondatrices du juge du réel (préenregistrement, cas point-in-time, référence forte, preuve prospective, mémoire négative).

**Ce que cela impose.** La section 5.

---

## 3. Grammaire commune

Tous les objets manipulés par la boucle appartiennent à l'une des classes suivantes. Chaque objet porte un identifiant, une date, un auteur (modèle, outil ou humain) et un **statut d'ancrage** : `propose`, `verifie(par, trace)`, `contredit(par, trace)`, `inconnu`.

| Classe | Champs | Qui le produit | Qui le vérifie |
|---|---|---|---|
| **Cas** | objet de la décision, décideur, horizon, budget, mandat (actions permises, réversibilité maximale) | humain (demande) ; modèle (mise en forme) | schéma : champs obligatoires présents |
| **État souhaité** | critère mesurable, seuil, date, vérificateur nommé | modèle | existence du vérificateur dans le registre ; sinon `inconnu` |
| **But** | énoncé ; lien avec les sous-buts (ET / OU) | modèle | ancrage de chaque feuille |
| **Obstacle** | énoncé ; but visé ; estimation typée (probabilité avec provenance, intervalle, scénarios, inconnu) ; impact | modèle (énoncé) ; outil ou donnée (estimation) | donnée, précédent, simulateur ; sinon `inconnu` |
| **Parade** | action ou ensemble d'actions ; obstacle visé | modèle | voir Action |
| **Contrainte dure** | source lue (référence, texte, date de lecture, outil) ; énoncé formel ; applicabilité | outil (lecture) ; modèle (énoncé, applicabilité) | second lecteur, règle enregistrée ou humain ; sinon `inconnu` |
| **Critère** | grandeur, unité, sens (à minimiser ou maximiser), poids ou seuil déclarés | humain (préférences) ; modèle (proposition) | déclaration explicite du décideur |
| **Action** | préconditions ; effets ; coût ; durée ; réversibilité ; droits requis | modèle (proposition) ; registre (contrat) | contrat de l'outil qui l'exécute |
| **Outil** | contrat : entrées, sorties, unités, préconditions, coût, droits, version, comportement en échec | registre | tests du registre |
| **Preuve** | objet prouvé ; vérificateur ; trace (données, empreinte, date) | outil, donnée, fait | reproductibilité de la trace |
| **Verdict** | état souhaité ; mesure observée ; date ; règle de score | juge (code) | registre public |
| **Fiche d'expérience** | cas, arbre, chemins, décisions, verdicts, inconnus, coût | boucle | empreinte au registre |

Règles de la grammaire :
1. Un objet `propose` n'entre jamais dans une décision. Il doit devenir `verifie` ou rester `inconnu`.
2. Un objet `contredit` est retiré, et sa contradiction est conservée (mémoire négative).
3. Le vérificateur d'un objet n'est jamais le producteur de cet objet.
4. Un `inconnu` sur une coupe minimale du but est **structurant** ; il interdit l'exécution.
5. Toute contrainte dure a trois statuts d'ancrage distincts : la source (lue ou non), l'énoncé (vérifié ou non), l'applicabilité (vérifiée ou non).

---

## 4. Le processus : une machine à états

La v0 décrivait huit étapes en ligne. La critique a montré que l'ordre était faux (on chiffrait avant d'avoir les chemins) et que la réalité impose des retours. La boucle est donc une **machine à états** : chaque état a une entrée, un producteur, un vérificateur, une sortie, et des transitions, dont une vers ABSTENTION.

```
S0 Réception ─→ S1 État souhaité ─→ S2 Arbre ─→ S3 Ancrage ─→ S4 Chemins
                                        ↑            │            │
                                        └────────────┘ (contredit)│
                                        ↑                         ↓
S9 Mémoire ←─ S8 Vérification ←─ S7 Exécution ←─ S6 Contrôle ←─ S5 Filtre et choix
     │                                                 │              │ (faisable vide)
     └──→ verdict différé (faits)              mandat refusé → ABST   └──→ S2
Depuis tout état : → ABSTENTION (motif) ; → ESCALADE (décision humaine)
```

| État | Entrée | Producteur | Vérificateur | Sortie | Transitions |
|---|---|---|---|---|---|
| **S0 Réception** | demande en langage naturel | modèle : fiche de cas | schéma | cas complet ou questions au décideur | S1 ; ESCALADE si champ obligatoire manquant |
| **S1 État souhaité** | cas | modèle : critère, seuil, date | registre des vérificateurs | état souhaité `verifie` ou `inconnu` | S2 ; si `inconnu` : la boucle continue en mode « proposition non vérifiable », marqué comme tel, sans exécution possible |
| **S2 Arbre** | état souhaité | modèle : buts, obstacles, parades, contraintes dures ; outils : lecture des sources | aucun à ce stade (tout est `propose`) | arbre proposé | S3 |
| **S3 Ancrage** | arbre proposé | outils, données, précédents, lecteurs | chaque nœud reçoit un statut | arbre ancré, liste des inconnus, coupes minimales | S4 ; S2 si un nœud est `contredit` (retrait, nouvel arbre) ; ABSTENTION si un inconnu structurant ne peut pas être levé par une mesure |
| **S4 Chemins** | arbre ancré | modèle : actions proposées ; registre : contrats | jonction : tout prérequis couvert par un fait `verifie` ou l'effet d'une action | ensemble de chemins candidats, avec coût, durée, réversibilité | S5 ; S3 si une action révèle une précondition non ancrée ; ABSTENTION si aucun chemin |
| **S5 Filtre et choix** | chemins candidats | code : contraintes dures ; code : Pareto ; décideur : préférences | contraintes `verifie` seulement ; une contrainte `inconnu` bloque le chemin | chemin retenu, ou front de Pareto soumis au décideur | S6 ; S2 si l'ensemble faisable est vide ; ESCALADE si plusieurs chemins non dominés et préférences non déclarées |
| **S6 Contrôle avant action** | chemin retenu | code : préconditions, droits, mandat, réversibilité | mandat du décideur pour toute action irréversible | autorisation | S7 ; ABSTENTION si mandat refusé ou budget épuisé |
| **S7 Exécution** | autorisation | outils sous contrat | contrat (sorties conformes), surveillance pendant | résultats avec provenance | S8 ; ABSTENTION si un outil échoue hors de son contrat |
| **S8 Vérification** | résultats | justesse : recalcul indépendant ; forme : test d'exécutabilité ; fond : vérificateur de l'état souhaité, ou prévision enregistrée ; coût : compteur | quatre statuts | livrable avec ses quatre statuts | S9 ; S4 si justesse `contredit` |
| **S9 Mémoire** | livrable | boucle : fiche d'expérience | empreinte au registre | fiche ; verdict différé si le fond attend les faits | fin ; retour à S2 quand un verdict révèle un obstacle absent |

Règles transversales :
- **Budget.** Chaque état consomme un budget (appels, temps, argent) fixé en S0. L'épuisement mène à ABSTENTION avec l'état atteint.
- **Journal.** Chaque transition est journalisée (état, objets produits, statuts, coût, horodatage). Le journal est la trace que l'auditeur relit.
- **Mesure comme action.** En S4, « mesurer » est une action admissible dont l'effet est de lever un `inconnu`. C'est souvent le meilleur chemin.
- **Rien n'est décidé par un objet `propose`.** La règle 1 de la grammaire s'applique à chaque transition.

### 4.1 Exemple déroulé : le taux de service

Cas pédagogique, sans donnée d'entreprise.

- **S0.** Demande : « notre taux de service est à 94 %, il faut remonter à 98 % d'ici fin de trimestre, sans recruter ». Fiche : décideur = directeur des opérations ; horizon = 10 semaines ; mandat = réorganisation interne, pas d'investissement ; réversibilité maximale = réversible en une semaine.
- **S1.** Critère : lignes livrées complètes à date sur lignes commandées, seuil 98 %, mesuré par le système de commandes. Vérificateur : le rapport hebdomadaire existe → `verifie`.
- **S2.** Arbre proposé par le modèle. Obstacles (OU) : prévision fausse ; ordonnancement non respecté ; panne ; prestataire logistique en retard ; production non conforme. Contraintes dures proposées : durée du travail (source : Code du travail, lu) ; nettoyage entre séries (source : plan de maîtrise sanitaire de l'usine, à lire).
- **S3.** Ancrage. Les retards du prestataire : `verifie` par les données de livraison (12 % des lignes en retard sont dues au prestataire). Les pannes : `verifie` par le journal de maintenance (3 % des lignes). La prévision fausse : `inconnu`, car l'écart entre prévision et commandes n'est pas historisé. L'applicabilité de la contrainte « nettoyage » : `inconnu` tant que le plan de maîtrise n'est pas lu. Coupe minimale : l'inconnu sur la prévision est structurant si l'on veut imputer les 6 points manquants ; il ne l'est pas pour agir sur le prestataire et les pannes, dont l'effet vérifié couvre déjà une partie de l'écart.
- **S4.** Chemins : (a) renégocier les créneaux du prestataire (précondition : contrat le permet, à vérifier ; effet estimé : +2 points, provenance : données) ; (b) maintenance préventive sur la ligne la plus pannarde (effet +1 point) ; (c) **mesurer** l'erreur de prévision pendant trois semaines (effet : lever l'inconnu). Jonction : (a) + (b) + (c) couvrent les prérequis d'un gain vérifié de 3 points et d'une décision informée sur le reste.
- **S5.** Contraintes : (a) et (b) ne touchent pas à la durée du travail ; la contrainte « nettoyage » reste `inconnu` mais ne concerne aucun des chemins retenus. Critères : coût, délai. (a) et (b) ne sont pas dominés.
- **S6.** Actions réversibles, dans le mandat → autorisation.
- **S7.** Exécution : courrier au prestataire, plan de maintenance, mise en place de la mesure.
- **S8.** Justesse : les +2 et +1 points sont recalculés par un code indépendant sur les mêmes données. Forme : le plan est exécutable. Fond : **prévision enregistrée** : « taux de service ≥ 97 % à la semaine 10, probabilité 0,6 ». Coût : 11 appels, 40 minutes.
- **S9.** Fiche d'expérience avec l'inconnu « erreur de prévision » et le verdict différé. À la semaine 10, le fait tranche. Si le taux est à 95 %, l'arbre est incomplet : retour à S2 avec l'obstacle manquant.

Ce que l'exemple montre : la boucle ne promet pas 98 %. Elle promet de dire ce qu'elle sait (3 points vérifiés), ce qu'elle ne sait pas (la prévision), et comment le savoir (mesurer). C'est la différence avec un modèle seul, qui aurait répondu « améliorez la prévision ».

---

## 5. Protocole de test (préenregistré)

### 5.1 Hypothèse

**H1.** Sur des cas nouveaux, la boucle B produit des décisions dont le coût réalisé est inférieur à celui des deux témoins, sans augmenter les violations, et avec des abstentions justifiées.

**Témoins :**
- **T0**, le modèle seul : même modèle de langage, même question, aucun outil ;
- **T1**, le modèle avec les mêmes outils que B, appelés librement, sans la machine à états ni les statuts d'ancrage.

La comparaison B contre T1 isole la valeur de la structure ; T1 contre T0 isole la valeur des outils.

### 5.2 Palier 1 : le domaine du juge du réel

**Pourquoi ce domaine.** L'ancrage y est résolu : la vérité vient des faits observés (défaillance ou non à 548 jours), pas d'un jugement. Les outils existent (ratios, BODACC, R2 v1.7.1, seuils de P6). Le coût réalisé d'une décision est défini par le protocole v1.7.1 (P6).

**Cas.** Un cas est un couple (SIREN, t0) de l'espace de développement (origines 2018 à 2020), avec la question : « couvrir ou conserver le risque de cette contrepartie, sous le scénario s ». Les six scénarios primaires de P6 (délai 30, 45, 60 jours ; part indemnisée 70 %, 90 % ; prime 0,1 %) sont tirés au hasard par cas.

**Tirage.** N = 300 cas, stratifiés : 150 défaillants à 548 jours, 150 non défaillants, tirés au hasard avec une graine publiée au registre avant le tirage. Les poids de redressement (part réelle des défaillants, 1,31 %) sont appliqués aux mesures. **Pièges inclus** : 30 cas supplémentaires de sociétés en liquidation judiciaire à t0 (exclues de P1), pour lesquels la seule réponse correcte est l'abstention (« la question ne se pose pas »).

**Information fournie aux trois systèmes.** Le SIREN, la date t0, le scénario. Rien d'autre. T1 et B ont accès aux mêmes outils : lecture des ratios à une date, lecture des annonces BODACC à une date, calcul de R2 à t0, lecture des seuils de P6, lecture de l'état Sirene à une date. Chaque outil refuse toute date postérieure à t0 et journalise ses appels.

**Garde du scellé.** Les cas sont tirés dans le développement seulement ; aucune donnée des origines 2022 et 2023 n'est lue.

### 5.3 Mesures

| Mesure | Définition | Système |
|---|---|---|
| **M1, coût réalisé** | Coût de P6 de la décision prise (couvrir : π T + (1 − q) y LGD ; conserver : y LGD ; abstention sur un cas éligible : coût de « conserver », soit l'inaction), moyenné avec les poids de redressement | tous |
| **M2, violations** | Nombre de cas où le système (a) cite une information postérieure à t0, (b) cite une source que le journal des outils ne contient pas, (c) décide « couvrir » ou « conserver » sur un cas piège | tous |
| **M3, abstentions** | Abstentions justifiées (cas piège, ou inconnu structurant réel) et injustifiées (cas éligible avec outils disponibles) | tous |
| **M4, coût de calcul** | Appels d'outils, appels de modèle, jetons, secondes, euros | tous |

Le vérificateur des quatre mesures est **du code**, pas un modèle : M1 par le calcul de P6 sur l'issue observée ; M2 par comparaison du texte de la réponse au journal des outils (dates, sources) ; M3 par la liste des cas pièges ; M4 par les compteurs.

### 5.4 Verdict

- **Statistique primaire.** Δ = M1(T1) − M1(B), différence appariée par cas, poids de redressement.
- **Inférence.** Bootstrap par cas, 2 000 réplications, graine publiée, intervalle percentile à 95 %.
- **Succès** : borne inférieure de Δ au-dessus de 0 **et** M2(B) ≤ M2(T1) **et** abstentions injustifiées de B ≤ 5 % des cas éligibles.
- **Échec** : borne supérieure de Δ au-dessous de 0, ou M2(B) > M2(T1).
- **Indécis** : sinon.
- **Secondaire, publié sans verdict** : T1 contre T0 ; M4 pour les trois ; décomposition de M1 par scénario.

**Ce qu'un succès établirait, et seulement cela** : sur ce domaine, avec ces outils, la structure de la boucle améliore la décision par rapport à un usage libre des mêmes outils. Il n'établirait rien sur d'autres domaines (section 6).

### 5.5 Modèles et reproductibilité

- Le même modèle de langage sert à T0, T1 et B. Le modèle est nommé et, quand le fournisseur le permet, épinglé à une version ; sinon la date d'exécution est consignée et l'absence d'épinglage est déclarée.
- Température fixée ; graine quand le fournisseur l'accepte.
- Les prompts de T0, T1 et B sont figés et leur empreinte publiée avant l'exécution.
- Le journal complet (appels, réponses, statuts, transitions) est conservé ; les réponses des modèles sont des données de tiers, non vérifiées, reproduites telles quelles.

### 5.6 Budget et arrêts

- **Pilote** : 50 cas (25 / 25) plus 10 pièges, pour mesurer le coût réel d'un cas par système, avant de valider le tirage de 300. Le pilote ne compte pas dans le verdict.
- Estimation avant pilote : T0 un appel par cas ; T1 environ 3 appels ; B environ 6 appels (un par état producteur). Pour 330 cas : environ 3 300 appels de modèle. Le coût en euros est inconnu avant le pilote ; il sera mesuré et soumis à validation avant le tirage principal.
- **Arrêts** : violation de la garde du scellé (un outil a servi une date postérieure à t0) → arrêt et correction avant reprise ; coût du pilote supérieur au budget validé → arrêt.

### 5.7 Calendrier des publications au registre

1. Cette note, après critique à l'aveugle et validation : empreinte.
2. Code de la boucle, des témoins, des outils datés et des vérificateurs : empreintes, tests au vert.
3. Prompts figés : empreintes.
4. Graine et liste des cas du pilote : empreinte.
5. Résultats du pilote et coût mesuré : empreinte ; validation du budget.
6. Graine et liste des 330 cas : empreinte, **avant** toute exécution.
7. Résultats et verdict.

---

## 6. Paliers suivants (non préenregistrés ici)

- **Palier 2.** Un domaine opérationnel avec simulateur vérifiable (files d'attente, ordonnancement) : la vérité vient du simulateur, et l'écart simulateur-terrain est déclaré.
- **Palier 3.** Deux domaines reliés par une structure explicite : le transfert est mesuré contre l'absence de transfert.
- **Palier 4.** Essais opérationnels autorisés et observables.

Chaque palier a son propre protocole, écrit et critiqué avant exécution. Rien de cette note ne préjuge de leur résultat.

---

## 7. Ce qui n'est pas revendiqué

- Aucune garantie que la boucle trouve « le bon chemin ». Elle garantit de distinguer ce qui est vérifié de ce qui ne l'est pas, et de s'abstenir sur le second.
- Aucune autonomie hors mandat : toute action irréversible exige une décision humaine.
- Aucun transfert entre domaines avant le palier 3.
- Aucune complétude de l'arbre des obstacles : les faits révèlent les obstacles manquants, et c'est précisément le rôle du verdict différé.
- Aucune supériorité économique générale : le verdict du palier 1 vaut pour son domaine et ses outils.

---

## 8. Ce que l'exécution devra livrer

Pour que l'exécution sur le serveur ne soit que de la mise en œuvre, voici les livrables, dans l'ordre :

1. **Schémas** des objets de la grammaire (section 3), en JSON, avec les statuts d'ancrage.
2. **Registre des outils**, avec leurs contrats, et la version datée de chaque outil (refus de toute date postérieure à t0 ; journal des appels).
3. **Machine à états** (section 4) : un état = une fonction qui prend les objets d'entrée, appelle le producteur, appelle le vérificateur, journalise, et renvoie la transition.
4. **Témoins** T0 et T1 : prompts figés.
5. **Vérificateurs des mesures** M1 à M4 : code déterministe, tests unitaires sur cas construits à la main (un cas piège, une citation post-t0, une source inventée).
6. **Tirage** des cas, avec graine.
7. **Rapport** : journal, mesures, bootstrap, verdict, empreintes.

Chaque livrable est testé et son empreinte publiée avant d'être utilisé.

---

## Annexe A. Références

**Vérifiées pendant la rédaction (OpenAlex ou Légifrance) :**
- Boehm, B. W. (1984). Verifying and Validating Software Requirements and Design Specifications. *IEEE Software*. DOI 10.1109/ms.1984.233702.
- Kaelbling, L. P., Littman, M. L. et Cassandra, A. R. (1998). Planning and acting in partially observable stochastic domains. *Artificial Intelligence*. DOI 10.1016/s0004-3702(98)00023-x.
- Kambhampati, S. et al. (2024). LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks. arXiv 2402.01817.
- Lipsey, R. G. et Lancaster, K. (1956). The General Theory of Second Best. *Review of Economic Studies*. DOI 10.2307/2296233.
- Simon, H. A. (1955). A Behavioral Model of Rational Choice. *Quarterly Journal of Economics*. DOI 10.2307/1884852.
- van Lamsweerde, A. et Letier, E. (2000). Handling obstacles in goal-oriented requirements engineering. *IEEE Transactions on Software Engineering*. DOI 10.1109/32.879820.
- Code du travail, art. L. 3121-18 et L. 3121-20 (Légifrance, lus le 21/10/2026).

**De mémoire, à vérifier avant le gel :**
- Dardenne, van Lamsweerde et Fickas (1993), KAOS ; Fikes et Nilsson (1971), STRIPS ; Mackie (1965), conditions INUS ; Keeney et Raiffa (1976) ; Roy, ELECTRE ; Hart, texture ouverte du droit ; norme CEI 61025, arbres de défaillances ; Newell et Simon, analyse moyens-fins ; Pohl (1971), recherche bidirectionnelle ; Meyer, conception par contrat ; Leveson (2011).

## Annexe B. Erreurs de la thèse v0 et leur correction

| Erreur | Où elle est corrigée |
|---|---|
| Second rang surinterprété | 2.3 |
| Chiffrage obligatoire | 2.6, grammaire (estimation typée) |
| Mémoire absolue | 2.9 |
| Ordre des étapes | 4 (S3 avant S4, retours) |
| Contrainte lue ≠ applicable | 2.5, grammaire (trois statuts) |
| Vérification tardive | 2.8, S6 |
| Faille d'ancrage | 2.1, grammaire (statuts), règle 3 |
