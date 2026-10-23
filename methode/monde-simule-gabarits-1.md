# Monde simulé : gabarits de perturbations par un tiers, et leur critique

*23/10/2026. Étape prévue par la v2 (§2, dernier point) : un modèle du comité rédige les gabarits à partir de la seule spécification du générateur, sans rien sur la boucle ; un second les critique ; le concepteur les traduit en code. Ce document consigne les deux réponses, ce que le concepteur en retient et ce qu'il n'en retient pas. Il ne modifie pas la v2 : les changements retenus iront dans une v3.*

## 1. Déroulé

| Appel | Modèle | Contenu envoyé | Statut | Jetons (entrée / sortie) |
|---|---|---|---|---|
| 1 | gemini-4-argon | Spécification du générateur seule ; consigne : quatre familles, gabarits par facteur, équilibre prudent et rapide, contrôles, pièges | Tronquée au milieu de la section C | 1 111 / 4 000 |
| 2 | gemini-4-argon | Rappel du cadre, résumé de sa propre réponse, demande de la fin de C, de D et de E | Complète | 958 / 2 885 |
| 3 | gpt-6-astra | Spécification et résumé fidèle des appels 1 et 2, sans le nom de l'auteur ni rien sur la boucle ; critique demandée | Complète | 3 184 / 2 207 |

Aucun appel à Grok (écarté pour coût, décision du 19/10) ni à Mistral (modèle des systèmes testés). Trois appels dans le cycle ; les deux modèles sont des alias flottants, non épinglés. Les réponses brutes sont conservées hors dépôt, dans le bloc-notes de la session.

**Erreur du concepteur, déclarée.** La consigne de l'appel 3 décrit l'abstention par « U = − coût déjà dépensé », formule de la v1. La v2 dit autre chose : l'abstention conserve la valeur de Z déjà acquise. L'objection B4 du relecteur porte en partie sur cette formule périmée ; seule sa partie valable sous la v2 est retenue (§3, B4).

## 2. Proposition de l'auteur (gemini-4-argon), en bref

- **Quatre familles** : F1 flux et capacités (débordement au-delà de la capacité) ; F2 réglages et seuils (effet de bord d'un réglage sur un autre) ; F3 ressources partagées (activer une unité consomme un stock commun) ; F4 séquencement et délais (prérequis qui échoue sans signal). Pour chacune : variables, trois voies, actions avec coût, délai et réversibilité, voie évidente selon la description.
- **Gabarits par facteur** pour chaque famille : obstacle caché sur la voie évidente (canal de mesure et note de maintenance ancienne et vague) ; affirmation fausse dans un tableau daté, contredite par une archive plus récente qui confirme aussi trois éléments vrais ; occasion sur Z par une action secondaire découvrable par lecture ou par effet collatéral d'un essai ; prudence coûteuse (mémo non daté mais vrai ; marge d'échéance de 0 à 2 périodes) ; mondes impossibles appariés à un jumeau qui ne diffère que par un paramètre latent.
- **Équilibre** : biais signalés par l'auteur lui-même (F4 vers la rapidité, F2 vers le tâtonnement, F3 vers la paralysie) ; critère proposé : la politique bayésienne domine, et une politique rapide et une politique prudente écrites en code font jeu égal sur 1 000 mondes de développement par famille.
- **Contrôles** : texte et tableau issus d'un même arbre, avec un opérateur de mutation explicite ; faisabilité à information parfaite ; égalité stricte des descriptions des jumeaux à t = 0 ; calibrage des rapports de vraisemblance ; énumération de l'espace d'hypothèses.
- **Pièges** : position fixe de la voie évidente, noms révélateurs, paramètres visibles corrélés aux facteurs, fuites de surface du texte, bruit pur de loi différente du signal ; parades par permutation, lexique renouvelé, tirage indépendant, gabarit textuel rigide, même loi marginale.

## 3. Critique (gpt-6-astra) et vérifications du concepteur

### Bloquantes

| N° | Objection | Vérification | Retenu |
|---|---|---|---|
| B1 | Un produit de 4 à 6 variables binaires ou ternaires va de 16 à 729 hypothèses ; la borne de 64 n'est tenue que si l'on s'y astreint, et les effets de bord, délais et fiabilités inconnus doivent y figurer s'ils changent les prévisions | Arithmétique exacte (2⁴ = 16, 3⁶ = 729) | Oui : table exhaustive des hypothèses par famille, avec loi a priori, transitions et observations ; loi renormalisée après tout rejet, et c'est cette loi finale que connaît R_Bayes |
| B2 | Le calibrage du facteur 1 confond confiance a posteriori et performance de détection ; la formule du contrôle D4 de l'auteur donne 2/3, pas 0,80 ; les précisions de mesure proposées (0,75 et 0,60) donnent une exactitude de 75 % après deux mesures et de 64,8 % après quatre | Recalculé par code : rapports requis pour 0,80 depuis 0,50 = 4, 2, 1,414 pour 1, 2, 4 mesures (la section B de l'auteur est juste, son D4 est décalé d'un rang) ; exactitude par décision majoritaire 0,750 et 0,648 ; probabilité a posteriori après mesures toutes concordantes 0,90 et 0,835 | Oui : « détectable à 80 % en k mesures » est défini comme l'exactitude de la décision bayésienne après k mesures, sous la loi a priori réelle du facteur, calculée par énumération de toutes les suites d'observations. La loi a priori d'un monde impossible est de l'ordre de 10 %, pas 50 % |
| B3 | La dynamique ne garantit pas la structure : en F1, une somme de flux peut dépasser la cible sans voie satisfaite ; en F2, un « cycle » d'effets de bord heurte l'absence de rétroaction ; en F3, convertir un stock en un autre ne reconstitue pas le premier | Vérifié sur le texte de la proposition | Oui : graphe causal admissible par famille ; équivalence entre « Y atteint la cible » et « une voie au moins est satisfaite » vérifiée par énumération à la génération ; bilans matière explicites en F3 ; « trois actions par condition » = trois types d'action |
| B4 | Z et l'abstention mal articulés ; une action sur Z qui consomme une période peut nuire à Y | La première partie vient de la formule périmée de la consigne (§1) ; la seconde est juste sous la v2 (une action par période) | En partie : l'occasion sur Z est toujours en concurrence avec Y pour le temps, et cela est voulu ; la règle d'atteinte (constatée à la période où Y franchit la cible, ou à l'échéance) sera fixée en v3 |

### Majeures

| N° | Objection | Retenu |
|---|---|---|
| M1 | Découvrabilité non démontrée : un essai « divisé par deux » ne révèle pas un verrou temporel ; une note vague n'identifie rien ; une source plus récente n'est pas forcément vraie ; une découverte en 2 à 4 mesures peut arriver trop tard | Oui : pour chaque outil, coût, durée, issues possibles et vraisemblances ; pour chaque facteur, trois contrôles séparés par code : identifiable, accessible avant l'échéance, utile à la décision (valeur de l'information positive pour R_Bayes) |
| M2 | Égaliser une politique rapide et une politique prudente caricaturales ne prouve aucune neutralité ; le croisement exigeant une marge de 4 périodes ne couvre pas le gabarit 4b (marge de 0 à 2) ; ajouter une accélération coûteuse change le problème | Oui : critère de l'auteur remplacé par un panel de politiques en code (rapide, prudente, inspection ciblée, essai opportuniste, arrêt adaptatif) ; le critère devient la diversité des politiques gagnantes selon les cases du plan croisé, publiée case par case, pas l'égalité des moyennes |
| M3 | Fuites résiduelles : vieux tableau contre archive récente, « Annexe_Z », « sous-système 1 », nombre de confirmations, signature temporelle du bruit ; le rejet de mondes peut recréer des corrélations | Oui : provenance contrebalancée (la source récente a tort dans une part fixée des mondes, ce qui recoupe le cas 4a) ; audit des corrélations après rejet ; formulations et lexique séparés entre mondes de développement et de confirmation ; jumeaux d'une même paire toujours dans le même espace |
| M4 | Verdict en fraction de G fragile si G est petit ; numérateur non défini | Oui : la v2 exprime déjà ΔU en fraction de G ; s'y ajoutent un plancher de G fixé sur les mondes de développement, sous lequel le verdict n'est pas interprété, et la publication des utilités brutes. Il est rappelé que R_Bayes connaît les fréquences des facteurs, que les systèmes testés ignorent |

### Mineures

- m1 : identifiants de famille et de variable confondus (F1) ; « Ajuster(P4, 2) » contredit le pas de ± 1. Retenu : signatures typées.
- m2 : « non-dégénérescence de la première action » indéfinie, et rejeter les mondes à première action évidente biaiserait l'échantillon. Retenu : contrôle supprimé ; la part de ces mondes est seulement publiée.

## 4. Ce que le concepteur retient de la proposition de l'auteur

- Les quatre familles et leurs mécaniques, comme **premier jet** : toutes les valeurs numériques (coûts, délais, seuils, stocks) seront fixées par règle sur les mondes de développement, pas reprises telles quelles.
- La génération du texte et du tableau à partir d'un même arbre, avec un opérateur de mutation explicite (D1).
- L'égalité stricte des descriptions des jumeaux à t = 0 (D3).
- Les cinq pièges de surface (E1 à E5) et leurs parades.
- **Non retenus** : le contrôle D4 (arithmétique fausse), le critère d'équilibre par égalité de deux heuristiques, le contrôle de non-dégénérescence.

## 5. Ce qui manque pour coder sans arbitraire (liste du relecteur, reprise comme liste de contrôle de la v3)

États initiaux, budgets, V et valeur de Z ; seuils stricts ou inclusifs ; loi conjointe des facteurs ; effets exacts, saturations et conversions ; consommations et remboursements ; sens opérationnel de « réversible » ; calendrier des délais et chevauchements ; conséquences des échecs ; bruit et dépendances ; catalogue et navigation des documents ; nombre maximal d'affirmations fausses ; règles de fin ; définition de R_naïf ; calcul et précision de R_Bayes ; critères statistiques et loi après rejet.

## 6. Suite

1. **v3 de la spécification** : intégrer §3 et §5 ; ne contient encore aucun résultat.
2. **Moteur exhaustif minimal d'abord** (première recommandation du relecteur) : une famille, une table d'hypothèses énumérée, transitions, observations, U ; texte généré ensuite. Coût de modèle nul.
3. **Certification par case** du plan croisé, par énumération : structure, faisabilité, détection, valeur de l'information, traitement de Z ; puis panel de politiques en code. Les quatre familles ne passent au mini-pilote de T1c qu'une fois certifiées.
