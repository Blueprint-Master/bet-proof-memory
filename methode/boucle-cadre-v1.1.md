# La boucle de calcul : cadre théorique et protocole de test (v1.1)

Note de cadrage, 21 octobre 2026. Elle remplace la thèse v0 après la matrice des critiques (`boucle-matrice-v0.md`). Son objet est de fixer, avant toute ligne de code, ce que l'on construit, pourquoi, et comment on saura si cela marche. Après cette note, l'exécution n'est plus qu'une mise en œuvre.

Statut : version 1.1, rédigée par Claude après le tour de critique à l'aveugle du texte v1 (ChatGPT, Gemini, Mistral ; matrice dans `boucle-matrice-v1.md`, douze corrections F1 à F12). Dernière étape avant gel : validation de Rémi, puis empreinte au registre.

---

## 0. Résumé

**Le problème.** Un modèle de langage produit des solutions plausibles. Il ne peut pas, seul, garantir qu'une solution est faisable, légale, chiffrée et vraie. Espérer qu'il « trouve » revient à parier sur la plausibilité.

**L'idée reçue qu'il faut abandonner.** On ne corrige pas ce défaut en imposant au modèle une structure formelle (arbres, probabilités, contraintes), parce que c'est encore le modèle qui remplirait la structure. L'erreur n'est pas supprimée, elle est déplacée vers le modèle du problème, et la forme mathématique la rend plus convaincante. C'est la faille principale de la thèse v0, relevée par les trois critiques indépendants.

**La proposition.** Une **boucle de supervision** qui sépare deux rôles :
- le modèle de langage **propose** : états souhaités, obstacles, hypothèses, chemins, candidats ;
- des **vérificateurs indépendants du modèle** tranchent : données, calculs, textes lus, faits observés.

Tout élément qu'aucun vérificateur ne peut trancher reçoit le statut **inconnu**. Un inconnu sur le chemin critique interdit l'exécution : la boucle répond « je ne sais pas, je n'exécute pas ».

**Ce que la boucle ne peut pas faire, et le dit.** Elle contrôle ce qui est représenté, pas ce qui devait l'être : un obstacle que personne n'a proposé n'existe pour aucun vérificateur. Elle réduit ce risque par des générateurs multiples et indépendants, et elle le détecte après coup par le verdict des faits. Elle ne le supprime pas.

**La preuve.** La boucle n'est adoptée que si elle bat, sur des cas nouveaux et préenregistrés, deux témoins : le modèle seul, et le modèle avec les mêmes outils mais sans la boucle. Le protocole de test (section 5) fixe les cas, les mesures, le verdict et le budget avant la première exécution.

**Le premier terrain.** Le juge du réel (prévision de défaillance d'entreprise), parce que la vérité y vient des faits et que les outils existent. Ce palier teste la discipline d'ancrage (dates, preuves, abstention), pas la construction d'arbres complexes, qui relève du palier 1 bis sur des cas de décision réels.

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

**Ce que cela impose.** Tout champ structurant d'un objet produit par le modèle porte un **statut d'ancrage** : *proposé* (par le modèle), *vérifié* (par un vérificateur nommé, avec sa trace et la portée de ce qu'il établit), *contredit* (par un vérificateur), *inconnu* (aucun vérificateur disponible). Seuls les champs vérifiés servent à décider. Les inconnus se publient, ils ne se comblent pas.

**Ce que cela ne règle pas.** L'ancrage porte sur ce qui est représenté. La structure de l'arbre (quels obstacles, quels liens) est elle aussi proposée par le modèle ; ses liens reçoivent un statut et se vérifient par des tests de cohérence, mais une **omission** n'a pas de statut. Deux parades partielles : multiplier les générateurs indépendants jusqu'à saturation (section 4, S2), et laisser les faits révéler les obstacles manquants (S9). Un vérificateur, enfin, n'est fiable que par une base de confiance déclarée (outils testés, données à empreintes, humain nommé) ; les vérificateurs sont eux-mêmes jugés par les faits : celui dont les « vérifié » sont contredits par les issues est retiré du registre.

### 2.2 Buts et obstacles

**Idée.** Un but se décompose en sous-buts (liens ET : tous nécessaires ; liens OU : l'un suffit). Pour chaque but, on cherche systématiquement les **obstacles** (conditions qui empêchent le but) et, pour chaque obstacle, les **parades**. C'est l'analyse des obstacles de l'ingénierie des exigences orientée buts.

**Source.** van Lamsweerde et Letier, *IEEE Transactions on Software Engineering*, 2000 (vérifié) ; méthode KAOS (Dardenne, van Lamsweerde et Fickas, 1993, de mémoire). Même structure dans les arbres de défaillances de la sûreté de fonctionnement (norme CEI 61025, de mémoire), où les « coupes minimales » sont les plus petits ensembles de causes qui suffisent à produire l'échec, et dans l'arbre des prérequis de Goldratt.

**Ce que cela impose.** L'arbre est l'objet central de la boucle. Mais il est **proposé** par le modèle : sa complétude n'est jamais garantie. Chaque nœud doit donc être ancré (2.1), et l'arbre reste ouvert à l'ajout d'obstacles révélés par les faits (section 4, état S9). Pour réduire les omissions, la génération de l'arbre suit les règles de la boîte noire du skill `raison-comite` : plusieurs générateurs indépendants (modèles différents, angles différents, sans voir les dépôts des autres), aucune critique pendant la génération, arrêt à **saturation** (un tour n'apporte plus de famille nouvelle), **axes de couverture** déclarés d'avance (une case vide l'est pour une raison écrite), et aucune mise à mort d'une branche sauf sur contrainte dure vérifiée. Le tri, le rangement et les liens de cause à conséquence produits par les générateurs restent `propose` jusqu'à S3.

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

Tous les objets manipulés par la boucle appartiennent à l'une des classes suivantes. Chaque objet porte un identifiant, une date, un auteur (modèle, outil ou humain). Chaque **champ structurant** porte un statut d'ancrage : `propose`, `verifie(par, trace, portee)`, `contredit(par, trace)`, `inconnu`. La colonne « contrôle » dit **quelle assertion** le contrôle établit ; un contrôle de présence ou d'intégrité n'établit pas l'exactitude.

| Classe | Champs | Qui le produit | Contrôle et portée |
|---|---|---|---|
| **Cas** | objet de la décision, décideur, horizon, budget, mandat (actions permises, réversibilité maximale) | humain (demande) ; modèle (mise en forme) | schéma : présence des champs ; **relecture par le décideur** : fidélité de la mise en forme |
| **État souhaité** | critère mesurable, seuil, date, vérificateur nommé | modèle | registre : existence du vérificateur ; décideur : acceptation du critère ; sinon ESCALADE |
| **But** | énoncé ; liens avec les sous-buts (ET / OU), chacun avec son statut | modèle (générateurs multiples) | feuilles : ancrage ; liens : test de cohérence par code (un parent OU n'est `verifie` que si une branche vérifiée suffit **et** que la suffisance est elle-même vérifiée ; un parent ET exige toutes ses branches) ; couverture : nombre de générateurs ayant proposé le nœud |
| **Obstacle** | énoncé ; but visé ; existence ; estimation typée (probabilité avec provenance, intervalle, scénarios, inconnu) ; impact | modèle (énoncé) ; outil ou donnée (existence, estimation) | existence : donnée ou fait ; estimation : donnée, précédent, simulateur ; chaque champ a son statut |
| **Parade** | action ou ensemble d'actions ; obstacle visé | modèle | voir Action |
| **Contrainte dure** | source lue (référence, texte, date de lecture, outil) ; énoncé formel ; applicabilité | outil (lecture) ; modèle (énoncé, applicabilité) | source : outil de lecture (intégrité et date) ; énoncé et applicabilité : règle enregistrée, lecteur humain nommé ou code ; **jamais un autre modèle de langage** ; sinon `inconnu` |
| **Critère** | grandeur, unité, sens, poids ou seuil déclarés | humain (préférences) ; modèle (proposition) | déclaration explicite du décideur |
| **Action** | préconditions ; effets ; coût ; durée ; réversibilité ; droits requis ; clé d'idempotence | modèle (proposition) ; registre (contrat) | préconditions : vérifiées avant chaque exécution ; effets : **anticipés** jusqu'à observation après exécution ; coût et droits : contrat |
| **Outil** | contrat : entrées, sorties, unités, préconditions, coût, droits, version, comportement en échec, tests | registre | tests publiés ; retrait si ses « vérifié » sont contredits par les faits |
| **Preuve** | objet prouvé ; vérificateur ; trace (données, empreinte, date) ; portée | outil, donnée, fait | reproductibilité de la trace ; la portée dit ce qui est établi |
| **Verdict** | état souhaité ; mesure observée ; date ; règle de score | juge (code) | code testé ; publication au registre (intégrité et antériorité, pas exactitude) |
| **Fiche d'expérience** | cas, arbre, chemins, décisions, verdicts, inconnus, couverture, coût | boucle | empreinte (intégrité et antériorité seulement) |

Règles de la grammaire :
1. Un champ `propose` n'entre jamais dans une **décision d'exécution**. Il peut orienter une recherche (quels outils appeler, quels nœuds ancrer) : c'est la différence entre une proposition qui guide et une assertion qui autorise.
2. Un champ `contredit` est retiré, et sa contradiction est conservée (mémoire négative).
3. Le vérificateur d'un champ appartient à une **classe différente** du producteur (code, donnée, fait, humain nommé) et à une provenance différente. Un second modèle de langage ne vérifie rien : il propose.
4. Les **coupes minimales** sont calculées par code sur le sous-arbre des nœuds et liens `verifie`. Un `inconnu` sur une coupe minimale est **structurant** ; il interdit l'exécution, sauf si une action de mesure autorisée peut le lever.
5. Toute contrainte dure a trois statuts distincts : la source (lue ou non), l'énoncé (vérifié ou non), l'applicabilité (vérifiée ou non).
6. Un nœud proposé par un seul générateur porte la mention « couverture faible » ; un but dont tous les obstacles sont à couverture faible ne peut pas conduire à une exécution irréversible.
7. La **base de confiance** (outils, données, humains) est déclarée au registre avant l'exécution. Elle n'est pas vérifiée par la boucle ; elle est jugée par les faits.

---

## 4. Le processus : une machine à états

La v0 décrivait huit étapes en ligne. La critique a montré que l'ordre était faux (on chiffrait avant d'avoir les chemins) et que la réalité impose des retours. La boucle est donc une **machine à états** : chaque état a une entrée, un producteur, un vérificateur, une sortie, et des transitions, dont une vers ABSTENTION.

```
S0 Réception ─→ S1 État souhaité ─→ S2 Arbre ─→ S3 Ancrage ─→ S4 Chemins et mesures
                      │ (inconnu)        ↑            │ (contredit, 2 fois au plus)
                      ↓                  └────────────┘
                   ESCALADE              ↑
S9 Mémoire ←─ S8 Vérification ←─ S7 Exécution ←─ S6 Contrôle ←─ S5 Filtre et choix
     │              │ (contredit → S4 ou S2)   │ (préconditions avant chaque action)  │ (faisable vide → S2 ; inconnu structurant → ABST)
     └──→ verdict différé (faits)       mandat refusé → ABST
Depuis tout état : → ABSTENTION (motif) ; → ESCALADE (décision humaine). Transitions évaluées dans l'ordre écrit.
```

| État | Entrée | Producteur | Vérificateur | Sortie | Transitions, dans l'ordre |
|---|---|---|---|---|---|
| **S0 Réception** | demande en langage naturel | modèle : fiche de cas | schéma (présence) ; décideur (fidélité) | cas complet | ESCALADE si champ obligatoire manquant ou fidélité refusée ; sinon S1 |
| **S1 État souhaité** | cas | modèle : critère, seuil, date | registre (existence du vérificateur) ; décideur (acceptation) | état souhaité `verifie` | ESCALADE si `inconnu` ou refusé ; sinon S2 |
| **S2 Arbre** | état souhaité | **générateurs multiples et indépendants** (boîte noire : pas de critique, saturation, axes de couverture) ; outils : lecture des sources | aucun (tout est `propose`) ; code : fusion des dépôts, doublons, couverture par nœud | arbre proposé, avec couverture | S3 |
| **S3 Ancrage** | arbre proposé | outils, données, précédents, lecteurs humains | statut par champ ; code : cohérence des liens ; code : coupes minimales sur le sous-arbre vérifié | arbre ancré, liste des inconnus (structurants ou non), couverture | S2 si un nœud est `contredit` (deux fois au plus, puis ABSTENTION) ; sinon S4 |
| **S4 Chemins et mesures** | arbre ancré | modèle : actions proposées, dont des **mesures** qui lèvent un inconnu ; registre : contrats | jonction : tout prérequis couvert par un fait `verifie` ou par l'effet **anticipé** d'une action du chemin ; une action de mesure peut échouer, son effet est anticipé comme les autres | chemins candidats avec coût, durée, réversibilité, inconnus restants | S3 si une action révèle une précondition non ancrée ; ABSTENTION si aucun chemin ; sinon S5 |
| **S5 Filtre et choix** | chemins candidats | code : contraintes dures `verifie` ; code : Pareto ou seuil ; décideur : préférences | une contrainte `inconnu` bloque le chemin ; un inconnu structurant non couvert par une mesure du chemin bloque le chemin | chemin retenu, ou front de Pareto soumis au décideur | S2 si l'ensemble faisable est vide (deux fois au plus) ; ABSTENTION si tous les chemins sont bloqués par un inconnu structurant ; ESCALADE si plusieurs chemins non dominés sans préférences ; sinon S6 |
| **S6 Contrôle avant action** | chemin retenu | code : droits, mandat, réversibilité, budget, règle 6 | mandat du décideur pour toute action irréversible | autorisation | ABSTENTION si mandat refusé ou budget épuisé ; sinon S7 |
| **S7 Exécution** | autorisation | outils sous contrat ; **avant chaque action** : préconditions revérifiées ; **après chaque action** : effets observés, clé d'idempotence enregistrée | contrat (sorties conformes) ; comparaison effet anticipé / observé | résultats avec provenance | S4 si un effet anticipé n'est pas observé (les actions exécutées ne sont jamais rejouées) ; ABSTENTION si un outil échoue hors de son contrat ; sinon S8 |
| **S8 Vérification** | résultats | justesse : recalcul par un code indépendant de l'outil exécutant ; forme : test d'exécutabilité ; fond : vérificateur de l'état souhaité, ou prévision enregistrée ; coût : compteur | quatre statuts | livrable avec ses quatre statuts | S4 si justesse ou forme `contredit` ; S2 si fond `contredit` ; sinon S9 |
| **S9 Mémoire** | livrable | boucle : fiche d'expérience | empreinte (intégrité) | fiche ; verdict différé si le fond attend les faits | fin ; S2 quand un verdict révèle un obstacle absent ; retrait d'un vérificateur contredit par les faits |

Règles transversales :
- **Budget.** Chaque état consomme un budget (appels, temps, argent) fixé en S0. L'épuisement mène à ABSTENTION avec l'état atteint.
- **Journal.** Chaque transition est journalisée (état, objets produits, statuts, coût, horodatage). Le journal est la trace que l'auditeur relit.
- **Reprise.** Une action exécutée porte une clé d'idempotence : un retour vers S4 ne la rejoue pas ; un effet partiel est un fait observé, pas un effet anticipé.
- **Code figé.** Tout code qui vérifie (S3, S5, S6, S8) est écrit, testé et publié avant l'exécution ; il n'est jamais généré pendant la boucle.
- **Rien n'est exécuté sur un champ `propose`.** La règle 1 de la grammaire s'applique à chaque transition vers S7.

### 4.1 Exemple déroulé : le taux de service

Cas pédagogique, sans donnée d'entreprise.

- **S0.** Demande : « notre taux de service est à 94 %, il faut remonter à 98 % d'ici fin de trimestre, sans recruter ». Fiche : décideur = directeur des opérations ; horizon = 10 semaines ; mandat = réorganisation interne, pas d'investissement ; réversibilité maximale = réversible en une semaine.
- **S1.** Critère : lignes livrées complètes à date sur lignes commandées, seuil 98 %, mesuré par le système de commandes. Vérificateur : le rapport hebdomadaire existe → `verifie`.
- **S2.** Arbre proposé par le modèle. Obstacles (OU) : prévision fausse ; ordonnancement non respecté ; panne ; prestataire logistique en retard ; production non conforme. Contraintes dures proposées : durée du travail (source : Code du travail, lu) ; nettoyage entre séries (source : plan de maîtrise sanitaire de l'usine, à lire).
- **S2, suite.** Deux générateurs supplémentaires (un autre modèle, un angle « ce qui a déjà échoué ailleurs ») ajoutent un obstacle : rupture d'un composant d'emballage. Le tour suivant n'apporte aucune famille nouvelle : saturation. Les cinq premiers obstacles sont proposés par les trois générateurs ; le sixième par un seul (couverture faible).
- **S3.** Ancrage. Les retards du prestataire : `verifie` par les données de livraison (12 % des lignes en retard sont dues au prestataire). Les pannes : `verifie` par le journal de maintenance (3 % des lignes). La prévision fausse : existence `verifie` (des écarts sont constatés), estimation `inconnu`, car l'écart n'est pas historisé. L'applicabilité de la contrainte « nettoyage » : `inconnu` tant que le plan de maîtrise n'est pas lu. L'emballage : `inconnu`. Coupes minimales, calculées par code sur le sous-arbre vérifié : l'inconnu sur la prévision est structurant pour imputer les 6 points manquants ; il ne l'est pas pour agir sur le prestataire et les pannes.
- **S4.** Chemins : (a) renégocier les créneaux du prestataire (précondition : le contrat le permet, à vérifier ; effet anticipé : +2 points, provenance : données) ; (b) maintenance préventive sur la ligne la plus pannarde (effet anticipé +1 point) ; (c) **mesurer** l'erreur de prévision pendant trois semaines (effet anticipé : lever l'inconnu, qui peut échouer si la mesure est inconclusive). Jonction : (a) + (b) + (c) couvrent les prérequis d'un gain anticipé de 3 points et d'une décision informée sur le reste.
- **S5.** Contraintes : (a) et (b) ne touchent pas à la durée du travail ; la contrainte « nettoyage » reste `inconnu` mais ne concerne aucun des chemins retenus. L'inconnu structurant (prévision) est couvert par la mesure (c) : le chemin n'est pas bloqué. Critères : coût, délai. (a) et (b) ne sont pas dominés.
- **S6.** Actions réversibles, dans le mandat → autorisation.
- **S7.** Exécution : avant chaque action, ses préconditions sont revérifiées (le contrat du prestataire est lu : il permet la renégociation) ; courrier au prestataire, plan de maintenance, mise en place de la mesure ; chaque action reçoit sa clé d'idempotence.
- **S8.** Justesse : les +2 et +1 points sont recalculés par un code indépendant sur les mêmes données. Forme : le plan est exécutable. Fond : **prévision enregistrée** : « taux de service ≥ 97 % à la semaine 10, probabilité 0,6 ». Coût : 11 appels, 40 minutes.
- **S9.** Fiche d'expérience avec l'inconnu « erreur de prévision » et le verdict différé. À la semaine 10, le fait tranche. Si le taux est à 95 %, l'arbre est incomplet : retour à S2 avec l'obstacle manquant.

Ce que l'exemple montre : la boucle ne promet pas 98 %. Elle promet de dire ce qu'elle sait (3 points vérifiés), ce qu'elle ne sait pas (la prévision), et comment le savoir (mesurer). C'est la différence avec un modèle seul, qui aurait répondu « améliorez la prévision ».

---

## 5. Protocole de test (préenregistré)

### 5.1 Hypothèse

**H1 (primaire).** Sur des cas nouveaux, à enveloppe de calcul égale, la boucle B produit des décisions dont le coût réalisé est inférieur à celui du témoin T1 (mêmes outils, usage libre), sans augmenter les violations, et avec des abstentions justifiées.

**Témoins :**
- **T1**, le modèle avec les mêmes outils que B, appelés librement, sans la machine à états ni les statuts d'ancrage, sous le **même plafond d'appels et de jetons par cas** ;
- **T0**, le modèle seul, sans outil : comparaison secondaire, publiée sans valeur de verdict.

La comparaison B contre T1 isole la valeur de la structure ; T1 contre T0 isole la valeur des outils.

**Ce que ce palier teste, et seulement cela.** La discipline d'ancrage : respecter les dates, n'avancer que des preuves tracées, s'abstenir quand la question ne se pose pas. La décision est binaire et le domaine la pré-structure : la construction d'un arbre complexe n'est pas testée ici (palier 1 bis, section 6).

### 5.2 Palier 1 : le domaine du juge du réel

**Pourquoi ce domaine.** La vérité vient des faits observés (défaillance ou non à 548 jours), pas d'un jugement. Les outils existent (ratios, BODACC, R2, seuils de P6). Le coût réalisé d'une décision est défini par le protocole v1.7.1 (P6).

**Cas.** Un cas est un couple (SIREN, t0 = 30/09/2020) de la seule **origine 2020** de l'espace de développement, avec la question : « couvrir ou conserver le risque de cette contrepartie, sous le scénario s ». Les six scénarios primaires de P6 sont tirés au hasard par cas.

**Pourquoi l'origine 2020 seule.** L'outil « R2 à t0 » doit n'avoir vu aucune issue du cas. Le seul modèle R2 qui respecte la règle de séparation de P4 pour une origine du développement est celui du pli 548 jours **2018 vers 2020** : ajusté sur l'origine 2018, dont les issues se closent avant le 30/09/2020. C'est ce modèle, figé (empreinte publiée), qui sert d'outil.

**Pseudonymisation.** Le modèle de langage ne voit **ni SIREN ni raison sociale**. Il reçoit un identifiant de cas opaque ; les outils reçoivent cet identifiant et le résolvent côté serveur ; leurs sorties sont expurgées des noms, adresses et identifiants. Motif : le modèle peut avoir mémorisé le sort de sociétés françaises de 2018 à 2022 ; la pseudonymisation réduit ce risque sans le supprimer (une reconnaissance par les seuls ratios est jugée improbable, et c'est une hypothèse déclarée).

**Tirage.** N = 300 cas, stratifiés : 150 défaillants à 548 jours, 150 non défaillants, tirés au hasard avec une graine publiée au registre avant le tirage ; un SIREN n'apparaît qu'une fois. Les poids de redressement (part réelle des défaillants dans l'origine 2020) sont appliqués aux mesures. **Pièges** : 30 cas supplémentaires de sociétés en liquidation judiciaire à t0 (exclues de P1). Une société en liquidation n'est pas assurable et la question est sans objet : la seule réponse correcte est l'abstention.

**Information fournie aux trois systèmes.** L'identifiant de cas, la date t0, le scénario. T1 et B ont accès aux mêmes outils : ratios à une date, annonces BODACC à une date, R2 (pli 2018 vers 2020) à t0, seuils de P6, état Sirene à une date. Chaque outil refuse toute date postérieure à t0, ne sert que des données dont la **date de publication** est antérieure à t0 (règle P2 du protocole), et journalise ses appels avec un identifiant de preuve.

**Sortie structurée obligatoire.** Chaque système rend : une décision (couvrir, conserver, abstention) ; la liste des identifiants de preuves utilisés ; une justification qui ne peut citer que ces identifiants. Le texte libre n'est pas évalué.

**Garde du scellé.** Aucune donnée des origines 2022 et 2023 n'est lue.

### 5.3 Mesures

| Mesure | Définition | Système |
|---|---|---|
| **M1, coût réalisé** | Coût de P6 de la décision prise (couvrir : π T + (1 − q) y LGD ; conserver : y LGD ; abstention sur un cas éligible : coût de « conserver », **convention déclarée** ; en secondaire, coût de la meilleure des deux décisions constantes), moyenné avec les poids de redressement | tous |
| **M2, violations** | Nombre de cas où le système (a) cite un identifiant de preuve absent du journal des outils, (b) rend une décision autre que l'abstention sur un cas piège, (c) rend une sortie non conforme au format. Pour T0, qui n'a aucun identifiant admissible, toute justification factuelle compte en (a) : c'est assumé, T0 mesure ce que vaut le modèle sans preuve | tous |
| **M3, abstentions** | Abstentions justifiées (cas piège) et injustifiées (cas éligible) | tous |
| **M4, coût de calcul** | Appels d'outils, appels de modèle, jetons, secondes, euros, sous le plafond commun | tous |

Le vérificateur des quatre mesures est **du code écrit et testé avant l'exécution** : M1 par le calcul de P6 sur l'issue observée ; M2 par comparaison des identifiants au journal ; M3 par la liste des pièges ; M4 par les compteurs.

### 5.4 Verdict

- **Statistique primaire.** Δ = M1(T1) − M1(B), différence appariée par cas, poids de redressement.
- **Inférence.** Bootstrap par cas, stratifié (défaillants, non défaillants), 2 000 réplications, graine publiée, intervalle percentile à 95 %. Hypothèse déclarée : indépendance des cas (les liens de groupe entre sociétés ne sont pas traités).
- **Succès** : borne inférieure de Δ au-dessus de 0 **et** M2(B) ≤ M2(T1) **et** M2(B) ≤ 2 % des cas **et** abstentions injustifiées de B ≤ 5 % des cas éligibles.
- **Échec** : borne supérieure de Δ au-dessous de 0, **ou** M2(B) > M2(T1), **ou** abstentions injustifiées de B > 5 %.
- **Indécis** : sinon.
- **Secondaire, publié sans verdict** : T1 contre T0 ; M4 pour les trois ; décomposition de M1 par scénario ; M1 sous la convention alternative d'abstention.

**Ce qu'un succès établirait, et seulement cela** : sur ce domaine, avec ces outils, à enveloppe égale, la structure de la boucle améliore la décision par rapport à un usage libre des mêmes outils. Il n'établirait rien sur d'autres domaines, ni sur la construction d'arbres.

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

- **Palier 1 bis : les décisions réelles du décideur.** Les problèmes traités au quotidien par Rémi (l'artefact « chemin critique » en tient le registre : actions ouvertes, sources, échéances, décisions, points bloqués faute de source) deviennent des cas. Pour chacun, la boucle produit l'état souhaité, l'arbre des obstacles généré par plusieurs générateurs, les contraintes sourcées, les chemins et les inconnus. La vérité vient de deux endroits : les faits vérifiables par outil (dates, pièces, textes) et le **verdict différé** (la décision prise, puis ce qui s'est passé). Ce palier teste la construction d'arbre, que le palier 1 ne teste pas. Ses difficultés, à régler dans son protocole : le décideur est à la fois juge et partie (parade : la prévision de la boucle est enregistrée avant sa décision) ; la confidentialité (parade : seuls les modèles à rétention nulle et le siège Claude pro traitent les données, et les témoins T0 et T1 tournent sur ces mêmes modèles) ; l'absence de vérité unique (parade : mesures de violations et d'inconnus, acceptation par le décideur, issue observée).
- **Palier 2.** Un domaine opérationnel avec simulateur vérifiable (files d'attente, ordonnancement) : la vérité vient du simulateur, et l'écart simulateur-terrain est déclaré.
- **Palier 3.** Deux domaines reliés par une structure explicite : le transfert est mesuré contre l'absence de transfert.
- **Palier 4.** Essais opérationnels autorisés et observables.

Chaque palier a son propre protocole, écrit et critiqué avant exécution. Rien de cette note ne préjuge de leur résultat.

---

## 7. Ce qui n'est pas revendiqué

- Aucune garantie que la boucle trouve « le bon chemin ». Elle garantit de distinguer ce qui est vérifié de ce qui ne l'est pas, et de s'abstenir sur le second.
- Aucune autonomie hors mandat : toute action irréversible exige une décision humaine.
- Aucun transfert entre domaines avant le palier 3.
- Aucune complétude de l'arbre des obstacles : la boucle contrôle ce qui est représenté, pas ce qui devait l'être. Les générateurs multiples réduisent les omissions, les faits les révèlent, et c'est précisément le rôle du verdict différé.
- Aucune clôture de la confiance : les vérificateurs reposent sur une base déclarée (outils testés, données à empreintes, humains nommés), jugée par les faits et non par la boucle.
- Aucune supériorité économique générale : le verdict du palier 1 vaut pour son domaine et ses outils.

---

## 8. Ce que l'exécution devra livrer

Pour que l'exécution sur le serveur ne soit que de la mise en œuvre, voici les livrables, dans l'ordre :

1. **Schémas** des objets de la grammaire (section 3), en JSON, avec les statuts d'ancrage.
2. **Registre des outils**, avec leurs contrats, leurs tests, et la version datée de chaque outil (refus de toute date postérieure à t0 ; données servies selon leur date de publication ; journal des appels avec identifiants de preuves ; pseudonymisation côté serveur).
3. **Machine à états** (section 4) : un état = une fonction qui prend les objets d'entrée, appelle le producteur, appelle le vérificateur, journalise, et renvoie la transition.
4. **Témoins** T0 et T1 : prompts figés ; plafond d'appels et de jetons commun à T1 et B ; format de sortie structuré commun.
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

## Annexe C. Corrections de la critique du texte v1 (matrice `boucle-matrice-v1.md`)

| N° | Point | Où il est corrigé |
|---|---|---|
| F1 | la structure de l'arbre décidait sans vérificateur | 2.1, 2.2, grammaire (liens, coupes par code, règles 4, 6), S2, S3 |
| F2 | mémorisation du sort des sociétés | 5.2, pseudonymisation |
| F3 | R2 avait vu les issues des cas | 5.2, origine 2020 et modèle du pli 2018 vers 2020 |
| F4 | M2 infaisable sur du texte libre | 5.2 sortie structurée, 5.3 |
| F5 | enveloppe de calcul inégale | 5.1 |
| F6 | verdict désaligné | 5.1, 5.4 |
| F7 | indépendance mal définie | règle 3 |
| F8 | contrôles mal typés | grammaire, colonne « contrôle et portée » |
| F9 | statut composite | grammaire, statut par champ |
| F10 | ordre S3 / S4, retours non bornés, transitions manquantes | section 4 |
| F11 | effets anticipés pris pour des faits | grammaire (Action), S7 |
| F12 | vérificateurs non supervisés | 2.1, règle 7, S9 |
