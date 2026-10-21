# La boucle de supervision

## Cadre théorique et protocole de test pour une IA qui décide avec des outils

Note de cadrage, 21 octobre 2026. Rédigée par Claude pour Rémi Cabrit. Ce document se suffit à lui-même : il expose le problème, les idées reçues qu'il faut abandonner, le cadre théorique avec ses sources, la grammaire des objets, le processus sous forme de machine à états, un exemple déroulé, puis le protocole de test préenregistré. Après lui, l'exécution n'est plus que de la mise en œuvre.

Convention de lecture. Les références marquées **[vérifié]** ont été retrouvées dans un catalogue bibliographique ou sur Légifrance pendant la rédaction. Celles marquées **[de mémoire]** sont des classiques cités de mémoire, à vérifier avant le gel. Les chiffres cités proviennent d'exécutions enregistrées, et sont datés.

---

## 0. Résumé

**Le problème.** Un modèle de langage produit des solutions plausibles. Il ne peut pas, seul, garantir qu'une solution est faisable, légale, chiffrée et vraie. Lui brancher des outils ne suffit pas : il faut une discipline qui impose le chemin, les preuves et le droit de s'abstenir.

**La proposition.** Une **boucle de supervision** qui sépare deux rôles. Le modèle de langage **propose** : états souhaités, obstacles, hypothèses, chemins, candidats. Des **vérificateurs** indépendants du modèle **tranchent** : données, calculs, textes lus, faits observés. Tout ce qu'aucun vérificateur ne peut trancher est marqué **inconnu**. Un inconnu sur le chemin critique interdit l'exécution : la boucle répond « je ne sais pas, je n'exécute pas ».

**Ce qui la rend capable d'apprendre.** Trois mécanismes : la **rétroaction** (quand les faits s'écartent de la prévision enregistrée, l'écart est attribué aux nœuds observables là où une règle d'agrégation a été déclarée d'avance, et la part inexpliquée, le résidu, mesure ce que l'arbre ne contenait pas) ; l'**analyse** (un obstacle observé sur assez de cas devient un précédent chiffré, qui sert d'estimation initiale au cas suivant dans son domaine de validité) ; l'**autonomie** (à l'intérieur d'un mandat, un ordonnanceur choisit lui-même la mesure suivante par une priorité calculée, et enchaîne les cycles).

**Ce qu'elle ne promet pas.** Elle ne garantit pas le bon chemin. Elle contrôle ce qui est représenté, pas ce qui devait l'être : un obstacle que personne n'a proposé n'existe pour aucun vérificateur. Elle réduit ce risque (générateurs multiples, test de résidu) et le détecte après coup (verdict des faits). Elle ne le supprime pas.

**La preuve.** La boucle n'est adoptée que si elle bat, sur des cas nouveaux et préenregistrés, un témoin qui dispose des mêmes outils sans la discipline. Le protocole du premier palier (section 7) fixe les cas, les mesures, le verdict et le budget avant la première exécution.

---

## 1. Pourquoi ce document

Trois observations, tirées d'un projet voisin de prévision de défaillances d'entreprises françaises conduit en octobre 2026, motivent ce cadre.

1. **Les IA proposent, les faits tranchent, et les deux divergent.** Sur 35 variables candidates proposées à l'aveugle par trois modèles de langage, 17 ont été admises par les données. Plusieurs variables jugées plausibles par leurs auteurs se sont révélées nuisibles, l'une d'elles dégradant la prévision de 27 % sur une période de test. Aucune discussion entre modèles n'aurait pu le voir ; seuls les faits l'ont fait.
2. **Une erreur silencieuse peut traverser toute une chaîne.** Une série statistique a été lue vide pendant deux évaluations complètes, sans qu'aucun contrôle ne s'en aperçoive, parce que le reste de la chaîne restait cohérent. Le défaut n'a été vu que parce que trois variables sont sorties exactement nulles. Leçon : la cohérence interne ne protège de rien ; seul un vérificateur à chaque étape protège.
3. **Définir un succès coûte cher.** Dire ce qu'est une « bonne » prévision sur un seul domaine a demandé une décision explicite du décideur, des sources, plusieurs corrections d'algèbre et quatre tours de critique indépendante. C'est le coût réel de l'ancrage, et il faut l'attendre pour chaque nouveau domaine.

Le point de départ du décideur est le suivant : partir de l'état souhaité, chercher ce qui l'empêche, juger une solution sur plusieurs plans (opérationnel, financier, juridique, qualité), la valider sur plusieurs aspects (fond, forme, justesse, coût). L'exemple fil rouge de ce document est un taux de service insuffisant.

---

## 2. Cinq idées reçues à abandonner

Chacune de ces idées est naturelle. Chacune conduit à une méthode qui a l'air de marcher.

### 2.1 « Une IA bien outillée trouvera la solution »

Non. Un modèle de langage produit ce qui est plausible, pas ce qui est vrai. Lui donner des outils augmente ce qu'il peut faire, pas ce qu'il peut garantir. Ce qu'il faut n'est pas plus d'outils, mais une séparation des rôles : proposer d'un côté, vérifier de l'autre. Les cadres dits « LLM-Modulo » (Kambhampati et al., 2024 [vérifié]) formalisent cette séparation : le modèle génère des candidats, des vérificateurs externes les acceptent ou les rejettent, et la boucle itère.

### 2.2 « Formaliser le problème élimine l'erreur du modèle »

Non. Si c'est le modèle qui remplit la structure formelle (l'arbre, les probabilités, les contraintes), l'erreur n'est pas éliminée, elle est déplacée vers le modèle du problème, et la forme mathématique la rend plus convaincante. C'est le problème de l'**ancrage**. La structure est aussi suspecte que le contenu : qui a dit que ces obstacles étaient les bons, et qu'ils étaient tous là ?

### 2.3 « Régler un gros problème, c'est enchaîner des questions binaires bien détaillées et exhaustives »

Vrai sur un point, faux sur trois.

**Le point vrai.** Un problème devient traitable et auditable quand il est décomposé en questions qui peuvent recevoir un verdict de quelqu'un d'autre que celui qui les a posées. C'est ce que fait l'ingénierie des systèmes depuis des décennies.

**Premier point faux : l'exhaustivité n'est pas garantie pour un problème ouvert.** Un même problème admet plusieurs décompositions, et choisir la décomposition est déjà une décision, prise avant toute vérification. Pour un domaine clos (une grammaire finie, un jeu de règles), l'exhaustivité existe et se prouve par code. Pour un problème ouvert, énumérer tout ce qui pourrait empêcher un but n'a pas de terme : c'est le problème de la qualification, posé en intelligence artificielle par McCarthy (1980 [vérifié] : on ne peut pas lister toutes les conditions qui qualifient le succès d'une action), et c'est la raison d'être de la rationalité limitée (Simon, 1955 [vérifié]). Ce qu'on peut obtenir à la place :
- la **saturation** : on arrête de générer quand un tour supplémentaire n'apporte plus de famille nouvelle ;
- la **couverture** : des axes déclarés d'avance, et chaque case vide l'est pour une raison écrite ;
- le **test de résidu** : si la prévision annonçait un gain de 3 points, que 1 point est observé, et que les obstacles vérifiés se sont comportés comme prévu, les 2 points d'écart mesurent ce que l'arbre ne contient pas. L'exhaustivité ne se constate pas sur une liste ; son défaut se mesure, après coup, sur l'écart inexpliqué.

**Deuxième point faux : les sous-questions ne sont pas indépendantes.** Résoudre chaque question localement ne compose pas en solution globale si les questions interagissent. L'économie du bien-être en a un résultat précis, le théorème du second rang (Lipsey et Lancaster, 1956 [vérifié]) : quand une condition de l'optimum ne peut pas être remplie, pousser les autres à leur valeur « parfaite » n'est en général plus optimal. Ce théorème vaut sous ses hypothèses économiques ; la boucle en retient, par analogie déclarée, une leçon structurelle : on n'a pas le droit de **supposer** que les étapes sont indépendantes. Une bonne décomposition est celle où les interactions sont faibles ou explicitement déclarées (systèmes « presque décomposables » : Simon, 1962 [de mémoire]). Concrètement, chaque lien entre deux branches est un objet à part entière, avec sa règle d'agrégation et son statut de vérification.

**Troisième point faux : ce n'est pas une succession, c'est une politique.** Beaucoup de sous-questions ne sont pas binaires (combien de stock, quelle priorité), et surtout l'information arrive en cours de route. Le bon chemin n'est pas une liste d'actions fixée d'avance ; c'est un arbre de décisions conditionnelles où « mesurer » est souvent la meilleure action suivante. C'est le cadre des décisions sous observation partielle (Kaelbling, Littman et Cassandra, 1998 [vérifié]). Et toutes les questions n'ont pas le même poids : on mesure d'abord ce dont la réponse change le plus la décision, à coût égal (valeur de l'information : Howard, 1966 [de mémoire]).

### 2.4 « Si la prévision était parfaite, le problème serait réglé »

Seulement si tout le reste l'est aussi. « Prévision parfaite » n'est qu'un élément d'un ensemble de conditions qui, ensemble, suffisent ; seule, elle n'est ni nécessaire (du stock ou de la flexibilité atteignent le même taux de service) ni suffisante (l'ordonnancement, les pannes, le prestataire). C'est la condition INUS de Mackie (1965 [vérifié]) : élément insuffisant mais nécessaire d'une condition non nécessaire mais suffisante. La bonne question n'est donc pas « comment rendre la prévision parfaite », mais « quel ensemble de conditions atteignables suffit, et à quel coût ».

### 2.5 « Une contrainte lue dans sa source est applicable »

Non. Un texte connaît des exceptions, des dérogations, des interprétations : le droit a une texture ouverte (Hart [de mémoire]). Exemple vérifié : le Code du travail limite la durée quotidienne de travail d'un salarié à dix heures (art. L. 3121-18 [vérifié], sauf dérogations) et la durée hebdomadaire à quarante-huit heures (art. L. 3121-20 [vérifié]). Ces articles limitent le travail d'un salarié, pas le fonctionnement d'une usine : une organisation en équipes successives n'est pas exclue par eux, et le travail de nuit relève d'autres textes. Formuler la contrainte « l'usine ne peut pas tourner 24 heures sur 24 » au lieu de « un salarié ne peut pas dépasser 10 heures par jour » élimine à tort une solution valable. **La formulation d'une contrainte fait partie du problème, et c'est une proposition à vérifier.**

---

## 3. Cadre théorique

Chaque sous-section donne l'idée, sa source, et ce qu'elle impose à la boucle.

### 3.1 L'ancrage : proposer n'est pas établir

**Idée.** Tout ce que produit le modèle a le statut de proposition tant qu'un vérificateur extérieur ne l'a pas confronté à quelque chose : une donnée, un calcul, un texte, un fait. La question n'est jamais « le raisonnement est-il cohérent ? » mais « chaque élément a-t-il été confronté à l'extérieur ? ».

**Source.** Kambhampati et al., 2024 [vérifié], pour la séparation générateur / vérificateurs.

**Ce que cela impose.** Chaque champ structurant d'un objet porte un **statut d'ancrage** : *proposé*, *vérifié* (par qui, avec quelle trace, pour quelle assertion), *contredit*, *inconnu*. Seuls les champs vérifiés servent à décider. Le vérificateur appartient à une classe différente du producteur (code, donnée, fait, humain nommé) ; un second modèle de langage ne vérifie rien, il propose. Une empreinte prouve l'intégrité, pas la vérité ; un schéma prouve la présence des champs, pas leur exactitude : chaque contrôle dit ce qu'il établit.

**Ce que cela ne règle pas.** La structure (quels obstacles, quels liens) est aussi proposée. Les liens reçoivent un statut et se vérifient par des tests de cohérence ; une omission, elle, n'a pas de statut. Deux parades partielles : des générateurs multiples et indépendants (3.2), et le test de résidu (3.9). Enfin, un vérificateur n'est fiable que par une **base de confiance déclarée** : outils testés, données à empreintes, humains nommés. Cette base n'est pas vérifiée par la boucle ; elle est jugée par les faits : un vérificateur dont les « vérifié » sont contredits par les issues est retiré du registre.

### 3.2 Buts et obstacles

**Idée.** Un but se décompose en sous-buts (liens ET : tous nécessaires ; OU : l'un suffit). Pour chaque but, on cherche les **obstacles** (ce qui l'empêche) et, pour chaque obstacle, les **parades**.

**Sources.** Ingénierie des exigences orientée buts : Dardenne, van Lamsweerde et Fickas, 1993 [vérifié] (méthode KAOS) ; analyse des obstacles : van Lamsweerde et Letier, 2000 [vérifié]. Même structure dans les arbres de défaillances de la sûreté de fonctionnement [de mémoire], où les **coupes minimales** sont les plus petits ensembles de causes qui suffisent à produire l'échec, et dans l'arbre des prérequis de Goldratt [de mémoire].

**Ce que cela impose.** L'arbre est l'objet central. Sa génération suit les règles d'une boîte noire : plusieurs générateurs qui ne voient pas les dépôts des autres (modèles différents, angles différents), aucune critique pendant la génération, arrêt à saturation, axes de couverture déclarés d'avance, et aucune branche tuée sauf sur contrainte dure vérifiée. Un nœud proposé par un seul générateur porte la mention « couverture faible ». Les liens ET / OU sont des objets avec leur statut : un parent OU n'est vérifié que si une branche vérifiée suffit **et** que cette suffisance est elle-même vérifiée. Les coupes minimales sont calculées par du code, sur le sous-arbre des nœuds et liens vérifiés, jamais sur l'arbre proposé.

**Exemple.** But : « taux de service ≥ 98 % sur le trimestre ». Obstacles (OU) : prévision fausse ; ordonnancement non respecté ; panne de ligne ; prestataire logistique en retard ; production non conforme ; rupture d'un composant d'emballage. Une parade par obstacle, et chaque parade a ses propres obstacles.

### 3.3 Actions, états et croyances

**Idée.** Une action se décrit par ses **préconditions** et ses **effets** (Fikes et Nilsson, 1971 [vérifié], formalisme STRIPS). Un chemin est une suite d'actions dont chaque précondition est soit un fait vérifié, soit l'effet d'une action précédente. Quand l'état n'est pas connu, ce qu'on manipule est une croyance, révisée à chaque observation ; la meilleure action suivante peut être une **mesure** (Kaelbling, Littman et Cassandra, 1998 [vérifié]).

**Ce que cela impose.** Les actions portent un contrat : préconditions, effets, coût, durée, réversibilité, droits. La **jonction** entre la recherche en avant (depuis l'état présent) et en arrière (depuis l'état souhaité) a une définition précise : elle est atteinte quand tout prérequis du but est couvert par un fait vérifié ou par l'effet **anticipé** d'une action du chemin. Un effet anticipé n'est pas un fait : il reste anticipé jusqu'à observation après exécution, et les préconditions se revérifient avant chaque action, pas seulement avant la première.

### 3.4 Conditions conjointes et second rang

Voir 2.3 et 2.4. **Ce que cela impose.** L'état attendu de chaque étape ne se fixe pas en isolant l'étape. La boucle doit soit traiter les étapes ensemble dans un modèle formel quand il existe (programmation par contraintes, optimisation stochastique ou robuste), soit déclarer qu'elles sont traitées séparément avec une hypothèse d'indépendance écrite et testable, soit marquer l'interaction comme inconnue. Les trois sont permis ; le silence ne l'est pas.

### 3.5 Contraintes dures et critères

**Idée.** Deux natures de critères ne se mélangent pas. Les **contraintes dures** décident de la faisabilité (droit, sécurité des aliments, sécurité des personnes, qualité) : une solution qui en viole une est éliminée, quel que soit son coût. Les **critères** départagent les solutions faisables (coût, délai, robustesse) : on garde celles qu'aucune autre ne bat sur tous les critères (front de Pareto), puis on tranche par des préférences explicites (analyse multicritère : Keeney et Raiffa, 1976 ; Roy, méthodes ELECTRE [de mémoire]). Pour une décision courante, une solution « satisfaisante » qui dépasse un seuil suffit (Simon, 1955 [vérifié]) ; le front de Pareto est réservé aux décisions lourdes.

**Ce que cela impose.** Une contrainte dure a trois statuts distincts : la **source** (lue par un outil, avec date), l'**énoncé formel**, l'**applicabilité**. Les deux derniers sont proposés par le modèle et vérifiés par une règle enregistrée, un lecteur humain nommé ou du code, jamais par un autre modèle de langage. Une contrainte dont l'applicabilité est inconnue bloque les chemins qu'elle concerne. Quand l'ensemble des solutions faisables est vide, la boucle ne classe pas : elle remonte à l'arbre ou s'abstient.

### 3.6 Chiffrage et incertitude

**Idée.** Un obstacle sans probabilité ni impact est une liste, pas un modèle. Mais exiger un chiffre pour tout fabrique de la précision là où elle n'existe pas.

**Ce que cela impose.** Chaque obstacle porte une estimation typée : une probabilité avec sa provenance, un intervalle, un ensemble de scénarios, ou **inconnu**. Un inconnu sur une coupe minimale est structurant : il bloque l'exécution, sauf si une mesure autorisée peut le lever. Les obstacles peuvent être corrélés ; une corrélation inconnue est elle-même un inconnu à publier.

### 3.7 Vérification, validation, coût

**Idée.** Le génie logiciel distingue (Boehm, 1984 [vérifié]) la **vérification** (construit-on la chose correctement : justesse du calcul, forme exécutable) et la **validation** (construit-on la bonne chose : le but atteint est-il le but voulu). Le **coût** s'ajoute, mesuré sur le cycle complet.

**Ce que cela impose.** Quatre vérificateurs distincts : justesse par un recalcul indépendant (code, pas modèle) ; forme par un test d'exécutabilité ; fond par le critère de l'état souhaité quand il est observable, sinon par une **prévision enregistrée** dont le verdict viendra des faits, avec une règle de score propre (une observation isolée ne valide pas une probabilité, il faut une série) ; coût par la boucle elle-même.

### 3.8 Actions irréversibles et abstention

**Idée.** Vérifier après l'exécution ne protège pas d'une action dommageable. Il faut trois moments : avant l'action (préconditions, droits, mandat), pendant (surveillance), après (résultat).

**Ce que cela impose.** Chaque action porte un attribut de réversibilité. Une action irréversible exige un mandat explicite du décideur. La boucle dispose d'un état terminal **ABSTENTION**, avec motif, atteignable depuis tout état. Une abstention justifiée est un résultat correct, et elle est mesurée comme telle.

### 3.9 Rétroaction : le test de résidu

**Idée.** Quand les faits arrivent, ils ne disent pas seulement « la prévision était juste ou fausse ». Si la grandeur visée se décompose par une règle connue (un taux de service est un total moins des parts de lignes manquées, chacune imputable à une cause), on peut **attribuer** l'écart entre la prévision enregistrée et l'observation aux nœuds observables : le prestataire a-t-il livré ? la panne a-t-elle eu lieu ? La part de l'écart qu'aucun nœud n'explique est le **résidu**. Un résidu élevé signifie que l'arbre ne contenait pas le vrai obstacle.

**Ce que cela suppose, et qui doit être écrit.** L'attribution n'est possible que si une **règle d'agrégation** du nœud parent (comment les contributions des enfants se combinent) a été déclarée **avant** l'exécution, comme champ du lien, avec son statut. Sans cette règle, il n'y a pas d'attribution nodale : la boucle publie un écart inexpliqué, et c'est tout. Les contributions sont publiées nœud par nœud et pas seulement en somme, parce qu'un résidu nul peut cacher deux erreurs qui se compensent. Une observation unique contredit une assertion déterministe (une existence, une applicabilité, un effet anticipé) ; elle ne contredit pas une estimation probabiliste, qui se score sur une série (3.7).

**Ce que cela impose.** Un état d'analyse d'écart après chaque verdict. Les nœuds dont l'assertion déterministe est contredite passent au statut *contredit* (mémoire négative). Le résidu est publié, par rapport à la prévision enregistrée, jamais par rapport à la cible. S'il dépasse un seuil fixé d'avance dans le cas, une nouvelle génération d'obstacles est déclenchée, avec le résidu comme consigne (« qu'est-ce qui, en dehors de ces nœuds, explique l'écart ? »). C'est le seul mécanisme qui corrige la structure, et non seulement le contenu ; c'est aussi un mécanisme de rationalisation après coup si on le laisse se noter lui-même. D'où trois garde-fous : les obstacles ainsi générés restent `propose` et passent par l'ancrage comme les autres ; leur estimation ne se valide que sur des observations futures, jamais sur le cas qui les a fait naître ; le score de l'arbre initial est conservé tel quel. Le nombre de tours de génération déclenchés par résidu est borné dans le mandat, et le budget n'est jamais réinitialisé.

### 3.10 Analyse : la mémoire comme base de précédents

**Idée.** Un obstacle observé sur assez de cas, avec sa fréquence et ses conditions, est un précédent. Le cas suivant qui rencontre le même obstacle dans des conditions comparables part de cette estimation, au lieu de partir du modèle de langage.

**Ce que cela impose.** Les fiches d'expérience sont indexées par obstacle et par conditions. Une estimation tirée d'un précédent a trois champs, chacun avec son statut : la **provenance** (vérifiée par la fiche et sa trace) ; le **calcul** (vérifié par code : une fréquence sur n cas, n au-dessus d'un minimum fixé d'avance, avec dénominateur et intervalle ; une réalisation isolée est une observation, pas une estimation) ; l'**applicabilité** (vérifiée seulement par un prédicat évaluable par code sur les conditions déclarées de la fiche, par exemple le secteur et la taille ; si c'est le modèle qui juge la comparabilité, l'applicabilité est `propose`, donc l'estimation ne sert pas à décider). Hors du domaine de validité, l'estimation est inconnue. Le transfert d'un précédent à un cas nouveau reste une hypothèse de stabilité du mécanisme, déclarée comme telle. La mémoire négative (ce qui a été contredit, et où) vaut autant que la mémoire positive. Ce qui est conservé sans limite : les conclusions, leurs statuts, leurs conditions de validité, les empreintes. Ce qui peut être effacé selon les règles applicables : les données brutes.

### 3.11 Autonomie : l'ordonnanceur sous mandat

**Idée.** L'autonomie n'est pas l'absence d'humain ; c'est la capacité de choisir soi-même l'essai suivant à l'intérieur d'un périmètre fixé. Le mandat définit les actions permises, le budget, la réversibilité maximale, le nombre de cycles. À l'intérieur, un **ordonnanceur** choisit la prochaine mesure : celle qui lève l'inconnu qui bloque le plus de chemins, ou qui pèse le plus sur le résidu, au moindre coût. Hors mandat, la boucle prépare une proposition et demande.

**Pourquoi une priorité et non une valeur d'information.** La valeur d'information attendue (Howard, 1966 [de mémoire]) exige une distribution de probabilité sur l'inconnu et une utilité des décisions. Par définition, un inconnu n'a pas de probabilité vérifiée ; si le modèle la fournit, c'est un `propose`, et la règle 1 lui interdit de décider d'une expérience réelle. L'ordonnanceur calcule donc, par code et sur le seul arbre ancré, une **priorité topologique** : nombre de chemins bloqués que la mesure débloque, poids de l'inconnu sur le résidu publié, divisés par le coût lu dans le contrat de l'outil. C'est une heuristique, nommée comme telle ; la valeur d'information reste l'horizon vers lequel elle tend quand des précédents vérifiés fournissent des fréquences.

**Sources.** Exploration autonome avec objectifs auto-générés (Forestier et al., 2022 [de mémoire]) ; planification et apprentissage intégrés (Sutton, 1990 [de mémoire]). Ces travaux fournissent les mécanismes ; leur transposition à des problèmes d'entreprise est une hypothèse d'ingénierie à tester.

**Ce que cela impose.** Un état d'ordonnancement qui reçoit les inconnus de l'arbre ancré, les chemins bloqués, le résidu s'il existe, le budget restant et le mandat, et renvoie la prochaine mesure autorisée ou un arrêt (saturation : aucune mesure autorisée ne lève plus d'inconnu structurant à un coût admissible). Il choisit d'abord parmi les mesures autorisées ; il n'escalade que si aucune mesure autorisée ne lève un inconnu structurant et qu'une mesure hors mandat le ferait. La mesure retenue n'est pas exécutée par l'ordonnanceur : elle entre dans un chemin, passe le filtre et le contrôle avant action comme toute action. La continuité est une reprise sur événement ou échéance, pas une consommation permanente.

### 3.12 Évaluer la méthode elle-même

**Idée.** Une méthode n'est pas adoptée parce qu'elle est cohérente ou parce que plusieurs IA l'approuvent. Elle est adoptée si elle fait mieux que des témoins, sur des cas qu'elle n'a pas vus, selon des mesures et un verdict fixés avant l'exécution.

**Ce que cela impose.** La section 7.

---

## 4. Grammaire commune

Tous les objets manipulés par la boucle appartiennent à l'une des classes suivantes. Chaque objet porte un identifiant, une date, un auteur (modèle, outil ou humain). Chaque **champ structurant** porte un statut d'ancrage : `propose`, `verifie(par, trace, portee)`, `contredit(par, trace)`, `inconnu`. La colonne « contrôle et portée » dit quelle assertion le contrôle établit.

| Classe | Champs | Producteur | Contrôle et portée |
|---|---|---|---|
| **Cas** | objet de la décision, décideur, horizon, budget, mandat (actions permises, réversibilité maximale), seuil de résidu | humain (demande) ; modèle (mise en forme) | schéma : présence des champs ; décideur : fidélité de la mise en forme |
| **État souhaité** | critère mesurable, seuil, date, vérificateur nommé | modèle | registre : existence du vérificateur ; décideur : acceptation ; sinon escalade |
| **But** | énoncé ; liens avec les sous-buts (ET / OU), chacun avec son statut ; règle d'agrégation (comment les contributions des enfants se combinent, déclarée avant exécution, ou `inconnu`) ; couverture (nombre de générateurs) | générateurs multiples | feuilles : ancrage ; liens : test de cohérence par code ; agrégation : déclaration explicite ; couverture : code |
| **Obstacle** | énoncé ; but visé ; existence ; estimation typée ; impact ; contribution observée à l'écart (après verdict) | modèle (énoncé) ; outil, donnée ou précédent (existence, estimation) | chaque champ a son statut ; la contribution observée vient du vérificateur du fond |
| **Parade** | actions ; obstacle visé | modèle | voir Action |
| **Contrainte dure** | source lue (référence, texte, date, outil) ; énoncé formel ; applicabilité | outil (lecture) ; modèle (énoncé, applicabilité) | source : outil (intégrité, date) ; énoncé et applicabilité : règle enregistrée, humain nommé ou code ; jamais un modèle de langage |
| **Critère** | grandeur, unité, sens, poids ou seuil | décideur (préférences) ; modèle (proposition) | déclaration explicite du décideur |
| **Action** | préconditions ; effets anticipés ; effets observés ; coût ; durée ; réversibilité ; droits ; clé d'idempotence | modèle (proposition) ; registre (contrat) | préconditions revérifiées avant chaque exécution ; effets observés après ; coût et droits par le contrat |
| **Mesure** | action dont l'effet est de lever un inconnu ; inconnu visé ; priorité (chemins débloqués, poids sur le résidu, coût) ; coût | modèle (proposition) ; ordonnanceur (priorité, par code) | comme une action ; l'effet « inconnu levé » est anticipé jusqu'à résultat |
| **Outil** | contrat : entrées, sorties, unités, préconditions, coût, droits, version, comportement en échec, tests | registre | tests publiés ; retrait si ses « vérifié » sont contredits par les faits |
| **Preuve** | objet prouvé ; vérificateur ; trace ; portée | outil, donnée, fait | reproductibilité de la trace |
| **Verdict** | état souhaité ; mesure observée ; date ; règle de score ; attribution par nœud ; résidu | juge (code) | code testé ; publication au registre (intégrité et antériorité) |
| **Précédent** | obstacle ; conditions de validité (prédicats évaluables par code) ; fréquence observée, effectif n, intervalle ; fiches d'origine | boucle (après verdicts) | provenance : trace vers les fiches ; calcul : code, n au-dessus du minimum fixé ; applicabilité : prédicat par code |
| **Fiche d'expérience** | cas, arbre, chemins, décisions, verdicts, inconnus, couverture, résidu, coût | boucle | empreinte (intégrité et antériorité) |

Règles :
1. Un champ `propose` n'entre jamais dans une **décision d'exécution**. Il peut orienter une recherche (quels outils appeler, quels nœuds ancrer) : une proposition guide, une assertion vérifiée autorise.
2. Un champ `contredit` est retiré de la décision, et sa contradiction est conservée.
3. Le vérificateur d'un champ appartient à une classe différente du producteur (code, donnée, fait, humain nommé) et à une provenance différente. Un second modèle de langage ne vérifie rien.
4. Les coupes minimales sont calculées par code sur le sous-arbre vérifié. Un `inconnu` sur une coupe minimale est structurant : il interdit l'exécution, sauf si une mesure autorisée peut le lever.
5. Une contrainte dure a trois statuts distincts : source, énoncé, applicabilité.
6. Un nœud proposé par un seul générateur porte « couverture faible » ; un but dont tous les obstacles sont à couverture faible ne conduit à aucune exécution irréversible.
7. La base de confiance (outils, données, humains) est déclarée au registre avant l'exécution ; elle est jugée par les faits, pas par la boucle.
8. Un résidu supérieur au seuil du cas déclenche une nouvelle génération d'obstacles, avec le résidu comme consigne. Les obstacles ainsi générés restent `propose` jusqu'à ancrage ; leur estimation ne se valide que sur des observations futures ; le score de l'arbre initial est conservé. Le nombre de ces tours est borné par le mandat.
9. Une estimation tirée d'un précédent n'est vérifiée que si sa provenance, son calcul (fréquence sur n cas, n au-dessus du minimum fixé) et son applicabilité (prédicat évalué par code) le sont chacun ; hors du domaine de validité, elle est inconnue.
10. L'attribution d'un écart à un nœud exige une règle d'agrégation déclarée avant l'exécution ; sans elle, l'écart est publié inexpliqué.

---

## 5. Le processus : une machine à états

Un état a une entrée, un producteur, un vérificateur, une sortie, et des transitions évaluées dans l'ordre écrit. Deux états terminaux sont atteignables depuis partout : **ABSTENTION** (avec motif) et **ESCALADE** (décision humaine demandée). Deux boucles s'emboîtent : la **boucle d'enquête**, avant la décision (S2 à S6, avec l'ordonnanceur S11 entre l'ancrage et les chemins), et la **boucle de verdict**, après les faits (S9, S10). Les numéros nomment les états ; ils ne donnent pas l'ordre du flux.

```
S0 Réception → S1 État souhaité → S2 Arbre (boîte noire) → S3 Ancrage → S11 Ordonnanceur → S4 Chemins et mesures
                     │ inconnu              ↑                   │ contredit (2 fois au plus)      │ saturation : S4 sans mesure nouvelle
                     ↓                      └───────────────────┘                                  │ hors mandat seul utile : ESCALADE
                  ESCALADE                  ↑
S9 Mémoire ← S8 Vérification ← S7 Exécution ← S6 Contrôle ← S5 Filtre et choix
     │ (attente des faits)   │ contredit → S4 ou S2   │ préconditions avant chaque action   │ faisable vide → S2
     ↓                                                  mandat refusé → ABSTENTION           │ inconnu structurant sans mesure → ABSTENTION
S10 Analyse d'écart → résidu > seuil → S2 (consigne : le résidu, dans la borne du mandat)
                    → inconnus restants et mandat ouvert → S3 (ré-ancrage) → S11
                    → sinon fin
```

| État | Entrée | Producteur | Vérificateur | Sortie | Transitions, dans l'ordre |
|---|---|---|---|---|---|
| **S0 Réception** | demande en langage naturel | modèle : fiche de cas | schéma ; décideur (fidélité) | cas, avec mandat, budget, seuil de résidu | ESCALADE si champ manquant ou fidélité refusée ; sinon S1 |
| **S1 État souhaité** | cas | modèle : critère, seuil, date | registre (existence du vérificateur) ; décideur (acceptation) | état souhaité vérifié | ESCALADE si inconnu ou refusé ; sinon S2 |
| **S2 Arbre** | état souhaité ; consigne éventuelle (résidu) | générateurs multiples et indépendants ; outils : lecture des sources | code : fusion des dépôts, doublons, couverture par nœud ; aucun jugement de fond | arbre proposé, avec couverture | S3 |
| **S3 Ancrage** | arbre proposé | outils, données, précédents (3.10), lecteurs humains | statut par champ ; code : cohérence des liens, coupes minimales sur le sous-arbre vérifié | arbre ancré ; inconnus (structurants ou non) ; couverture | S2 si un nœud est contredit (deux fois au plus, puis ABSTENTION) ; S11 s'il reste des inconnus ; sinon S4 |
| **S4 Chemins et mesures** | arbre ancré ; mesures retenues par S11 | modèle : actions et mesures ; registre : contrats | jonction (3.3) ; chaque effet est anticipé | chemins candidats avec coût, durée, réversibilité, inconnus restants | S3 si une action révèle une précondition non ancrée ; ABSTENTION si aucun chemin ; sinon S5 |
| **S5 Filtre et choix** | chemins candidats | code : contraintes dures vérifiées ; code : Pareto ou seuil ; décideur : préférences | une contrainte inconnue bloque le chemin ; un inconnu structurant non couvert par une mesure du chemin bloque le chemin | chemin retenu, ou front de Pareto soumis | S2 si l'ensemble faisable est vide (deux fois au plus) ; ABSTENTION si tous les chemins sont bloqués ; ESCALADE si plusieurs chemins non dominés sans préférences ; sinon S6 |
| **S6 Contrôle avant action** | chemin retenu | code : droits, mandat, réversibilité, budget, règle 6 | mandat du décideur pour toute action irréversible | autorisation | ABSTENTION si mandat refusé ou budget épuisé ; sinon S7 |
| **S7 Exécution** | autorisation | outils sous contrat ; préconditions revérifiées avant chaque action ; effets observés après ; clé d'idempotence | contrat ; comparaison anticipé / observé | résultats avec provenance | S4 si un effet anticipé n'est pas observé (rien n'est rejoué) ; ABSTENTION si un outil échoue hors contrat ; sinon S8 |
| **S8 Vérification** | résultats | justesse : code indépendant de l'outil exécutant ; forme : test ; fond : vérificateur de l'état souhaité, ou prévision enregistrée ; coût : compteur | quatre statuts | livrable avec ses quatre statuts | S4 si justesse ou forme contredite ; S2 si fond contredit ; sinon S9 |
| **S9 Mémoire** | livrable | boucle : fiche d'expérience | empreinte | fiche ; verdict différé si le fond attend les faits | S10 quand les faits arrivent ; fin si le fond était observable en S8 et qu'aucun inconnu ne subsiste |
| **S10 Analyse d'écart** | verdict ; arbre ancré avec règles d'agrégation ; observations par nœud | code : écart entre prévision enregistrée et observation ; attribution aux nœuds observables là où une règle d'agrégation est déclarée ; contributions par nœud ; résidu | règle de score ; données d'observation | assertions déterministes contredites marquées ; estimations scorées (série) ; observations versées aux précédents ; résidu publié ; vérificateur retiré seulement sur série contredite | S2 avec consigne si résidu > seuil et borne du mandat non atteinte ; S3 s'il reste des inconnus et que le mandat est ouvert ; sinon fin |
| **S11 Ordonnanceur** | arbre ancré, inconnus, chemins bloqués, résidu s'il existe, budget restant, mandat | code : priorité topologique par mesure (chemins débloqués, poids sur le résidu, divisés par le coût du contrat) | mandat ; budget | mesures retenues, ou aucune | S4 avec les mesures retenues ; S4 sans mesure nouvelle si saturation (aucune mesure autorisée ne lève un inconnu structurant à coût admissible) ; ESCALADE seulement si aucune mesure autorisée ne lève un inconnu structurant et qu'une mesure hors mandat le ferait ; ABSTENTION si budget épuisé |

Règles transversales :
- **Budget.** Fixé en S0 ; chaque état consomme ; l'épuisement mène à ABSTENTION avec l'état atteint.
- **Journal.** Chaque transition est journalisée (état, objets, statuts, coût, horodatage). C'est la trace que l'auditeur relit.
- **Reprise.** Une action exécutée porte une clé d'idempotence ; un retour vers S4 ne la rejoue pas ; un effet partiel est un fait observé.
- **Code figé.** Tout code qui vérifie ou ordonnance (S3, S5, S6, S8, S10, S11) est écrit, testé et publié avant l'exécution ; il n'est jamais généré pendant la boucle.
- **Bornes globales.** Les retours S3 → S2, S5 → S2 et S10 → S2 se comptent chacun ; le mandat fixe le nombre de cycles ; aucun retour ne réinitialise le budget.
- **Rien n'est exécuté sur un champ proposé.** La règle 1 s'applique à chaque transition vers S7.

---

## 6. Exemple déroulé : le taux de service

Cas pédagogique, sans donnée d'entreprise.

**S0.** Demande : « notre taux de service est à 94 %, il faut remonter à 98 % d'ici fin de trimestre, sans recruter ». Fiche : décideur = directeur des opérations ; horizon = 10 semaines ; mandat = réorganisation interne, mesures internes, pas d'investissement, actions réversibles en une semaine, trois cycles au plus ; budget = 40 appels de modèle, 2 heures ; seuil de résidu = 1 point de taux de service.

**S1.** Critère : lignes livrées complètes à date sur lignes commandées, seuil 98 %, mesuré par le système de commandes. Le rapport hebdomadaire existe : vérifié. Le décideur l'accepte. L'écart à combler est de 4 points. Règle d'agrégation déclarée : le taux de service vaut 100 % moins la somme des parts de lignes manquées, chaque ligne manquée étant imputée à une cause unique par le système de commandes ; les contributions des obstacles s'additionnent donc par construction.

**S2.** Trois générateurs indépendants (deux modèles, un angle « ce qui a déjà échoué ailleurs »). Obstacles proposés : prévision fausse ; ordonnancement non respecté ; panne de ligne ; prestataire logistique en retard ; production non conforme ; rupture d'un composant d'emballage. Les cinq premiers viennent des trois générateurs ; le sixième d'un seul (couverture faible). Le tour suivant n'apporte aucune famille nouvelle : saturation. Contraintes dures proposées : durée du travail (source : Code du travail, lu) ; nettoyage entre séries (source : plan de maîtrise sanitaire, à lire).

**S3.** Retards du prestataire : existence et estimation vérifiées par les données de livraison (12 % des lignes en retard lui sont imputables). Pannes : vérifiées par le journal de maintenance (3 %). Prévision fausse : existence vérifiée (des écarts sont constatés), estimation inconnue (l'écart n'est pas historisé). Nettoyage : applicabilité inconnue tant que le plan n'est pas lu. Emballage : inconnu. Coupes minimales, calculées par code sur le sous-arbre vérifié : l'inconnu sur la prévision est structurant pour combler les 4 points ; il ne l'est pas pour agir sur le prestataire et les pannes.

**S11.** Inconnus : erreur de prévision (bloque le chemin qui comble le quatrième point), nettoyage (ne bloque aucun chemin envisagé), emballage (couverture faible, aucun chemin). Priorité calculée par code : la mesure de l'erreur de prévision débloque un chemin pour un coût faible (lecture de l'historique pendant trois semaines) ; elle est retenue. Lire le plan de maîtrise sanitaire ne débloque rien pour l'instant : non retenu.

**S4.** Chemins : (a) renégocier les créneaux du prestataire (précondition : le contrat le permet, à vérifier ; effet anticipé +2 points, provenance : données) ; (b) maintenance préventive sur la ligne la plus pannarde (effet anticipé +1 point) ; (c) la **mesure** retenue en S11 : historiser l'erreur de prévision pendant trois semaines (effet anticipé : lever l'inconnu ; peut échouer si la mesure est inconclusive). Jonction : (a) + (b) couvrent un gain anticipé de 3 points ; le quatrième point dépend de l'inconnu que (c) doit lever.

**S5.** (a) et (b) ne touchent pas à la durée du travail ; la contrainte « nettoyage » reste inconnue mais ne concerne aucun chemin retenu. L'inconnu structurant est couvert par la mesure (c). Critères : coût, délai ; (a) et (b) ne sont pas dominés.

**S6.** Actions réversibles, dans le mandat : autorisation.

**S7.** Avant (a), le contrat du prestataire est lu : la renégociation est permise. Courrier, plan de maintenance, mise en place de la mesure. Clés d'idempotence enregistrées.

**S8.** Justesse : les +2 et +1 points recalculés par un code indépendant sur les mêmes données. Forme : le plan est exécutable. Fond : **prévision enregistrée** : « taux de service ≥ 97 % à la semaine 10, probabilité 0,6 ». Coût : 11 appels, 40 minutes.

**S9.** Fiche avec l'inconnu « erreur de prévision » et le verdict différé.

**S10, à la semaine 10.** Observé : 95 %, soit +1 point ; la prévision enregistrée annonçait +3 : écart de 2 points. Attribution, possible parce que la règle d'agrégation a été déclarée en S1 : les lignes manquées imputables au prestataire ont reculé de 2 points, comme anticipé (l'effet anticipé de (a) est observé, contribution à l'écart : 0) ; les lignes manquées pour panne ont reculé de 1 point, comme anticipé (contribution : 0) ; la mesure (c) est concluante (erreur moyenne de prévision de 11 %, l'inconnu est levé ; une observation est versée, qui ne devient un précédent qu'avec d'autres cas). Les deux nœuds vérifiés ont tenu ; aucun n'explique l'écart. Résidu : 2 points, au-dessus du seuil de 1. Premier retour à S2 (sur trois permis) avec la consigne : « 2 points d'écart ne sont expliqués par aucun obstacle vérifié ». Le nouveau tour de génération fait apparaître un obstacle absent du premier arbre : des commandes modifiées après le gel de l'ordonnancement. Cet obstacle est `propose` ; son existence est vérifiée en S3 (le système de commandes garde l'historique des modifications), son estimation est inconnue, et elle ne sera validée que par les observations des semaines suivantes, pas par l'écart qui l'a fait naître.

**S11, second cycle.** Sous mandat, l'ordonnanceur retient la mesure autorisée qui débloque le plus de chemins au moindre coût : historiser les modifications de commandes pendant deux semaines. Elle entre dans un chemin (S4), passe le filtre (S5) et le contrôle avant action (S6), qui l'autorise sans nouvelle demande au décideur parce qu'elle est dans le mandat. Si la seule mesure utile était hors mandat (un investissement), S11 escaladerait avec une proposition et s'arrêterait là.

Ce que l'exemple montre : la boucle ne promet pas 98 %. Elle promet de dire ce qu'elle sait (3 points vérifiés), ce qu'elle ne sait pas (la prévision, puis les commandes modifiées), comment le savoir (mesurer), et de corriger son propre arbre quand les faits montrent qu'il était incomplet, sans se créditer de cette correction avant que les faits suivants l'aient confirmée. C'est la différence avec un modèle seul, qui aurait répondu « améliorez la prévision ».

---

## 7. Protocole de test, palier 1 (préenregistré)

### 7.1 Hypothèse et témoins

**H1 (primaire).** Sur des cas nouveaux, à enveloppe de calcul égale, la boucle B produit des décisions dont le coût réalisé est inférieur à celui du témoin T1, sans augmenter les violations, et avec des abstentions justifiées.

- **T1** : le même modèle de langage, avec les mêmes outils que B, appelés librement, sans la machine à états ni les statuts d'ancrage, sous le **même plafond d'appels et de jetons par cas**.
- **T0** : le même modèle sans outil. Comparaison secondaire, publiée sans valeur de verdict.

B contre T1 isole la valeur de la discipline ; T1 contre T0 isole la valeur des outils.

**Ce que ce palier teste, et seulement cela.** La discipline d'ancrage : respecter les dates, n'avancer que des preuves tracées, s'abstenir quand la question ne se pose pas. La décision y est binaire et le domaine la pré-structure ; la construction d'arbre, la rétroaction et l'autonomie ne sont pas testées ici (section 8).

### 7.2 Domaine et cas

**Domaine.** La prévision de défaillance d'entreprises françaises, selon un protocole public préenregistré (dépôt `bet-proof-memory`, protocole v1.7.1). La vérité vient des faits : défaillance ou non dans les 548 jours suivant une date d'origine. Les outils existent. Le coût réalisé d'une décision y est défini : un fournisseur choisit de couvrir le risque d'une contrepartie par une assurance-crédit (prime π du chiffre d'affaires, part indemnisée q) ou de le conserver (perte LGD en cas de défaillance) ; la décision optimale est de couvrir si la probabilité de défaillance dépasse πT / (q LGD), T étant la rotation de l'encours sur l'horizon.

**Cas.** Un couple (SIREN, t0 = 30/09/2020), tiré dans la seule **origine 2020**, avec la question « couvrir ou conserver, sous le scénario s », s étant tiré parmi six scénarios préenregistrés (délai de paiement 30, 45, 60 jours ; part indemnisée 70 %, 90 % ; prime 0,1 %).

**Pourquoi l'origine 2020 seule.** L'outil de prévision mis à disposition ne doit avoir vu aucune issue du cas. Le seul modèle qui le garantit pour une origine disponible est celui ajusté sur l'origine 2018, dont les issues se closent avant le 30/09/2020. C'est ce modèle, figé et à empreinte publiée, qui sert d'outil.

**Pseudonymisation.** Le modèle de langage ne voit **ni SIREN ni raison sociale**. Il reçoit un identifiant de cas opaque ; les outils le résolvent côté serveur ; leurs sorties sont expurgées des noms, adresses et identifiants. Motif : le modèle peut avoir mémorisé, lors de son entraînement, le sort de sociétés françaises de 2018 à 2022. La pseudonymisation réduit ce risque sans le supprimer (une reconnaissance par les seuls ratios est jugée improbable ; c'est une hypothèse déclarée).

**Tirage.** 300 cas stratifiés (150 défaillants à 548 jours, 150 non défaillants), graine publiée avant le tirage, un SIREN par cas ; poids de redressement (part réelle des défaillants dans l'origine 2020) appliqués aux mesures. **Pièges** : 30 cas de sociétés déjà en liquidation judiciaire à t0 ; une telle société n'est pas assurable, la question est sans objet, la seule réponse correcte est l'abstention.

**Information fournie.** L'identifiant de cas, t0, le scénario. Outils identiques pour T1 et B : ratios à une date ; annonces du BODACC à une date ; prévision du modèle figé à t0 ; seuils de décision ; état administratif à une date. Chaque outil refuse toute date postérieure à t0, ne sert que des données publiées avant t0, et journalise ses appels avec un identifiant de preuve.

**Sortie structurée obligatoire.** Décision (couvrir, conserver, abstention) ; liste des identifiants de preuves utilisés ; justification limitée à ces identifiants. Le texte libre n'est pas évalué.

### 7.3 Mesures

| Mesure | Définition |
|---|---|
| **M1, coût réalisé** | Coût de la décision sur l'issue observée (couvrir : πT + (1 − q) y LGD ; conserver : y LGD ; abstention sur un cas éligible : coût de « conserver », convention déclarée ; en secondaire, coût de la meilleure des deux décisions constantes), moyenné avec les poids de redressement |
| **M2, violations** | Cas où le système (a) cite un identifiant de preuve absent du journal des outils, (b) rend une décision autre que l'abstention sur un piège, (c) rend une sortie non conforme au format. Pour T0, sans identifiant admissible, toute justification factuelle compte en (a) : assumé, T0 mesure ce que vaut le modèle sans preuve |
| **M3, abstentions** | Justifiées (pièges) et injustifiées (cas éligibles) |
| **M4, coût de calcul** | Appels d'outils et de modèle, jetons, secondes, euros, sous le plafond commun |

Le vérificateur des quatre mesures est du **code écrit et testé avant l'exécution**.

### 7.4 Verdict

- **Statistique primaire.** Δ = M1(T1) − M1(B), différence appariée par cas, poids de redressement.
- **Inférence.** Bootstrap par cas, stratifié, 2 000 réplications, graine publiée, intervalle percentile à 95 %. Hypothèse déclarée : indépendance des cas (les liens de groupe entre sociétés ne sont pas traités).
- **Succès** : borne inférieure de Δ au-dessus de 0, **et** M2(B) ≤ M2(T1), **et** M2(B) ≤ 2 % des cas, **et** abstentions injustifiées de B ≤ 5 % des cas éligibles.
- **Échec** : borne supérieure de Δ au-dessous de 0, **ou** M2(B) > M2(T1), **ou** abstentions injustifiées de B > 5 %.
- **Indécis** : sinon.
- **Secondaire, sans valeur de verdict** : T1 contre T0 ; M4 ; M1 par scénario ; M1 sous la convention alternative d'abstention.

Un succès n'établirait que ceci : sur ce domaine, avec ces outils, à enveloppe égale, la discipline améliore la décision par rapport à un usage libre des mêmes outils.

### 7.5 Reproductibilité, budget, arrêts, calendrier

- Même modèle de langage pour T0, T1 et B ; épinglé à une version quand le fournisseur le permet, sinon date consignée et absence d'épinglage déclarée ; température fixée ; prompts figés, empreintes publiées avant exécution ; journal complet conservé.
- **Pilote** : 50 cas (25 / 25) et 10 pièges, hors verdict, pour mesurer le coût réel par système. Estimation avant pilote : T0 un appel par cas, T1 environ trois, B environ six ; environ 3 300 appels pour 330 cas. Le coût en euros sera mesuré au pilote et soumis à validation avant le tirage principal.
- **Arrêts** : un outil a servi une date postérieure à t0 (correction avant reprise) ; coût du pilote supérieur au budget validé.
- **Calendrier des publications** : cette note (empreinte) ; code de la boucle, des témoins, des outils datés et des vérificateurs (empreintes, tests au vert) ; prompts figés ; graine et liste du pilote ; résultats du pilote et coût ; graine et liste des 330 cas, avant toute exécution ; résultats et verdict.

---

## 8. Palier 1 bis : les décisions réelles du décideur

**Objet.** Exercer ce que le palier 1 n'exerce pas : la construction d'arbre, la rétroaction, l'autonomie sous mandat. **Statut : étude prospective de faisabilité**, pas une validation d'efficacité. Avec un seul décideur, dont la décision dépend de ce que la boucle lui montre, aucune revendication causale n'est possible ; ce palier établit que la boucle tourne sur des cas réels, ce qu'elle coûte, et la fréquence de ses violations, inconnus et résidus.

**Cas.** Les problèmes traités au quotidien par le décideur, tels que son registre d'actions ouvertes les tient (actions, sources, échéances, points bloqués faute de source, décisions à prendre). Les cas admissibles, les horizons de verdict et le traitement des issues manquantes sont fixés avant le premier cas. Pour chacun, la boucle produit l'état souhaité, l'arbre généré par plusieurs générateurs, les contraintes sourcées, les chemins, les inconnus, et une prévision enregistrée.

**Vérité.** Deux sources : les faits vérifiables par outil (dates, pièces, textes) et le **verdict différé** (ce qui s'est passé à l'horizon fixé), mesuré de préférence sur des événements que l'action du décideur ne commande pas. Le test de résidu s'applique à chaque verdict là où une règle d'agrégation existe.

**Contamination et parades, à écrire dans son protocole :**
- le décideur est juge et partie, et la sortie de la boucle influence sa décision, donc l'issue. L'empreinte avant décision empêche de réécrire la prévision ; elle n'empêche pas cette influence. Parade : **cas scellés**. Sur une moitié des cas tirée au sort, la boucle tourne, sa sortie est enregistrée et scellée, et le décideur ne la voit qu'après l'issue. La comparaison scellés / montrés mesure l'influence ; elle ne mesure pas l'efficacité ;
- l'acceptation par le décideur est une mesure d'adoption, pas de vérité : publiée en secondaire ;
- confidentialité : seuls des modèles à rétention nulle et le siège professionnel du décideur traitent les données ; les témoins tournent sur ces mêmes modèles ;
- pas de vérité unique : les mesures primaires sont les violations, les inconnus, le résidu, le coût, puis l'issue observée à l'horizon.

**Ordre.** Le palier 1 passe avant, parce que la discipline d'ancrage s'y mesure sans contestation possible et qu'il coûte peu.

---

## 9. Paliers suivants (non préenregistrés ici)

- **Palier 2.** Un domaine opérationnel avec simulateur vérifiable (files d'attente, ordonnancement) : la vérité vient du simulateur, et l'écart simulateur-terrain est déclaré.
- **Palier 3.** Deux domaines reliés par une structure explicite : le transfert est mesuré contre l'absence de transfert.
- **Palier 4.** Essais opérationnels autorisés et observables.

Chaque palier a son protocole, écrit et critiqué avant exécution.

---

## 10. Ce qui n'est pas revendiqué

- Aucune garantie de trouver le bon chemin. La boucle distingue ce qui est vérifié de ce qui ne l'est pas, et s'abstient sur le second.
- Aucune exhaustivité de l'arbre. La boucle contrôle ce qui est représenté, pas ce qui devait l'être ; les générateurs multiples réduisent les omissions, le résidu les mesure après coup et seulement là où une règle d'agrégation existe, les faits les révèlent.
- Aucune efficacité établie par le palier 1 bis : avec un seul décideur dont la décision dépend de la sortie de la boucle, ce palier mesure la faisabilité, le coût et la discipline, pas un effet causal.
- Aucune clôture de la confiance. Les vérificateurs reposent sur une base déclarée, jugée par les faits.
- Aucune autonomie hors mandat. Toute action irréversible exige une décision humaine.
- Aucun transfert entre domaines avant le palier 3.
- Aucune supériorité économique générale : le verdict d'un palier vaut pour son domaine et ses outils.

---

## 11. Ce que l'exécution devra livrer

1. **Schémas** des objets de la grammaire (section 4), en JSON, avec les statuts par champ, les règles d'agrégation des liens et les trois champs d'une estimation héritée d'un précédent.
2. **Registre des outils** : contrats, tests, versions datées ; refus de toute date postérieure à t0 ; données servies selon leur date de publication ; journal avec identifiants de preuves ; pseudonymisation côté serveur.
3. **Machine à états** (section 5) : un état = une fonction qui prend les objets d'entrée, appelle le producteur, appelle le vérificateur, journalise, renvoie la transition ; S10 et S11 compris.
4. **Générateurs** de S2 : au moins deux modèles distincts, isolés, avec fusion et couverture par code.
5. **Témoins** T0 et T1 : prompts figés ; plafond commun ; format de sortie structuré commun.
6. **Vérificateurs des mesures** M1 à M4 : code déterministe, tests unitaires sur cas construits à la main (un piège, une preuve hors journal, une sortie non conforme).
7. **Tirage** des cas, avec graine.
8. **Rapport** : journal, mesures, bootstrap, verdict, empreintes.

Chaque livrable est testé et son empreinte publiée avant d'être utilisé.

---

## Annexe. Références

**Vérifiées pendant la rédaction (catalogue OpenAlex ou Légifrance) :**
- Boehm, B. W. (1984). Verifying and Validating Software Requirements and Design Specifications. *IEEE Software*. DOI 10.1109/ms.1984.233702.
- Dardenne, A., van Lamsweerde, A. et Fickas, S. (1993). Goal-directed requirements acquisition. *Science of Computer Programming*. DOI 10.1016/0167-6423(93)90021-g.
- Fikes, R. E. et Nilsson, N. J. (1971). STRIPS: A new approach to the application of theorem proving to problem solving. *Artificial Intelligence*. DOI 10.1016/0004-3702(71)90010-5.
- Kaelbling, L. P., Littman, M. L. et Cassandra, A. R. (1998). Planning and acting in partially observable stochastic domains. *Artificial Intelligence*. DOI 10.1016/s0004-3702(98)00023-x.
- Kambhampati, S. et al. (2024). LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks. arXiv 2402.01817.
- Lipsey, R. G. et Lancaster, K. (1956). The General Theory of Second Best. *Review of Economic Studies*. DOI 10.2307/2296233.
- Mackie, J. L. (1965). Causes and Conditions. *American Philosophical Quarterly*.
- McCarthy, J. (1980). Circumscription, a form of non-monotonic reasoning. *Artificial Intelligence*. DOI 10.1016/0004-3702(80)90011-9. (La référence est vérifiée ; l'attribution du problème de la qualification à cet article est de mémoire.)
- Simon, H. A. (1955). A Behavioral Model of Rational Choice. *Quarterly Journal of Economics*. DOI 10.2307/1884852.
- van Lamsweerde, A. et Letier, E. (2000). Handling obstacles in goal-oriented requirements engineering. *IEEE Transactions on Software Engineering*. DOI 10.1109/32.879820.
- Code du travail, art. L. 3121-18 et L. 3121-20 (Légifrance, lus le 21/10/2026).

**De mémoire, à vérifier avant le gel :**
- Simon, H. A. (1962). The Architecture of Complexity. *Proceedings of the American Philosophical Society*.
- Keeney, R. L. et Raiffa, H. (1976). Decisions with Multiple Objectives.
- Roy, B., méthodes ELECTRE.
- Hart, H. L. A. (1961). The Concept of Law, sur la texture ouverte du droit.
- Goldratt, E. M., arbre des prérequis (processus de réflexion de la théorie des contraintes).
- Howard, R. A. (1966). Information Value Theory. *IEEE Transactions on Systems Science and Cybernetics*.
- Arbres de défaillances, norme CEI 61025.
- Forestier, S. et al. (2022). Intrinsically Motivated Goal Exploration Processes. *JMLR*.
- Sutton, R. S. (1990). Integrated Architectures for Learning, Planning, and Reacting (architecture Dyna).
