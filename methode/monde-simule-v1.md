# Monde simulé : spécification v1 (avant comité)

*23/10/2026. Intègre les 21 objections du premier tour de critique (`monde-simule-matrice-1.md`) et les décisions de Rémi Cabrit du même jour : conduite par étapes, enveloppe de 200 à 500 $, dépense étalée sur deux à trois mois. Non préenregistré : le préenregistrement viendra après le comité et le développement du générateur.*

## 0. Objet

Tester, dans un monde où l'objectif est connu et le chemin ne l'est pas, si l'architecture de la boucle de supervision (couche C) améliore les décisions d'un modèle de langage **à consignes égales**. L'étape 2 ajoutera, sur le même générateur, la décomposition (couche A), l'exploration dosée (couche B) et l'apprentissage entre mondes. Genèse et intentions : base de connaissance, fiche 2317.

## 1. Étape 1 : question, hypothèse, verdict

- **Question.** À description, outils, budget et consignes identiques, la boucle obtient-elle une meilleure utilité que le même modèle en usage libre ?
- **Utilité, unique et préenregistrée.** U = V × atteinte + valeur de Z obtenue − coût dépensé dans le monde. V et la valeur unitaire de Z sont fixés par règle sur les mondes de développement (§6), connus de tous les systèmes.
- **Échelle.** Les écarts sont exprimés en fraction de l'écart G = E[U(R_Bayes)] − E[U(R_naïf)] mesuré sur les mondes de confirmation par les références en code.
- **Hypothèse primaire.** ΔU = E[U(C)] − E[U(T1c)] ; gain minimal d'intérêt 0,10 G ; marge d'équivalence ± 0,05 G.
- **Inférence.** Test de permutation apparié par monde (mêmes mondes, mêmes aléas pour tous), intervalle BCa, comme au palier 1.
- **Verdict.** Succès si ΔU est significativement positif et que la borne basse de l'intervalle dépasse 0 ; équivalence si l'intervalle tient dans ± 0,05 G ; échec si ΔU est significativement négatif ; indécis sinon. Les contrastes secondaires sont corrigés par la méthode de Holm.

## 2. Le générateur

- **Espace fini.** Chaque monde est tiré dans une famille de gabarits ; dans un monde, la structure réelle appartient à un ensemble fini et petit d'hypothèses (de l'ordre de 16 à 64), ce qui rend calculable la politique de référence R_Bayes. Si le calcul exact se révèle trop lourd en développement, R_Bayes est remplacée par une politique bayésienne à horizon borné, et l'encadrement entre elle et R∞ est publié.
- **Structure.** Y atteint la cible si l'une des voies (4 au plus) est satisfaite ; une voie est un ensemble minimal de conditions de succès (4 au plus) ; chaque condition se satisfait par des actions (3 au plus) ayant coût, délai, réversibilité. Trois ingrédients d'interaction : effets de bord négatifs (une action satisfait une condition et en défait une autre), seuils sur variables continues bruitées, ressources partagées entre voies. Pas de boucles de rétroaction en v1 (limite de portée déclarée).
- **Temps et coût.** Échéance de 4 à 8 périodes ; au plus 3 actions par période ; `mesurer` coûte peu mais consomme une action de la période. Le budget du monde (primaire) est distinct du budget de calcul (appels de modèle), publié comme contrôle d'égalité, avec un plafond commun fixé au pilote assez large pour C.
- **Bruit.** Tiré de façon déterministe à partir du triplet (monde, période, action) : tous les systèmes voient les mêmes aléas.
- **Description fournie.** Texte et tableau des variables, actions, coûts. Elle peut être incomplète et contenir une affirmation fausse ; **tous les systèmes en sont informés** de la même façon (sans les fréquences).
- **Plan croisé des perturbations**, chaque facteur présent ou absent, équilibré entre mondes :
  - obstacle caché sur la voie la plus évidente, difficulté réglée par le nombre de mesures dont un détecteur bayésien a besoin pour le voir à 80 % (2 ou 4) ; second canal possible par un passage de `lire` ;
  - affirmation fausse de provenance vérifiable ;
  - occasion sur Z (levier caché, valeur connue) ;
  - **cas où la prudence coûte** : affirmation de provenance douteuse mais vraie ; échéance serrée où vérifier fait manquer la cible ;
  - anomalies de pur bruit dans tous les mondes, pour que poursuivre chaque anomalie ait un coût et que les fausses alertes se mesurent.
- **Mondes impossibles** : environ 10 %, chacun apparié à un monde faisable quasi identique ; l'abstention y est la bonne réponse. Une abstention vaut U = − coût déjà dépensé : elle ne rapporte jamais V, mais arrête la dépense ; s'abstenir tôt dans un monde impossible est donc la meilleure conduite, et s'abstenir dans un monde faisable coûte V.
- **Domaine.** Fond abstrait, noms neutres, unités cohérentes, rôles décrits. En secondaire, un sous-ensemble des mêmes mondes est habillé en domaine concret, apparié, pour mesurer ce que le modèle tire de ses connaissances générales. Jamais mêlés dans le verdict.
- **Gabarits de perturbations écrits par un tiers.** Un modèle du comité qui n'a pas vu la boucle rédige les gabarits d'obstacles, d'affirmations fausses et de cas où la prudence coûte, à partir de la seule spécification du générateur ; un second les critique.

## 3. Systèmes de l'étape 1

| Système | Rôle | Description |
|---|---|---|
| **T1c** | Témoin principal | Le modèle libre avec les outils, plus les consignes de la boucle données en texte (statuts, vérifier avant d'agir, s'abstenir si un inconnu bloque) |
| **C** | Bras testé | La boucle adaptée (§4) |
| T1 | Secondaire, sous-échantillon | Le modèle libre sans consignes |
| R_naïf | Référence | Suit la voie la moins coûteuse selon la description, sans mesurer |
| R_explore | Référence | Explore systématiquement avant d'agir |
| R_boucle-code | Ablation | Les règles de la boucle exécutées par code sur la description structurée, avec détection d'anomalie : si C gagne, distingue l'apport du modèle de celui du code |
| R_Bayes | Borne atteignable | Connaît la loi de tirage, pas le monde tiré |
| R∞ | Borne de voyant | Connaît le monde tiré |

Même modèle épinglé pour T1c, C et T1 ; même description ; même budget ; même plafond de calcul ; **aucune mémoire entre mondes** à l'étape 1, pour aucun système. L'information décisive des perturbations est placée en texte libre (`lire`), que le code des références ne lit pas.

## 4. Adaptation déclarée de la boucle gelée (erratum de transposition)

- **Générateurs multiples (S2 de la note).** Un seul modèle à l'étape 1, pour garder l'égalité avec T1c ; la génération multiple relève de la couche A, testée à l'étape 2. Écart déclaré.
- **Mandat.** Toutes les actions du monde, réversibles ou non, sont dans le mandat, dans la limite du budget : le contrôle avant action vérifie budget, préconditions et statuts, pas une autorisation humaine.
- **Vérificateur humain.** Aucun ; les vérificateurs sont le code du monde (mesures, essais) et les passages de documentation avec leur provenance.
- **Ordonnanceur (S11).** Priorité topologique de la note, calculée sur l'arbre ancré de C ; l'ablation R_boucle-code en mesure l'apport propre.

## 5. Mesures

| Mesure | Définition | Statut |
|---|---|---|
| U | §1 | **Primaire** |
| Gaspillage | Part du coût dépensée en mesures et essais dont la valeur de l'information attendue, calculée sous la loi du générateur au vu des seules observations du système à ce moment (reconstituées par le journal), était inférieure au coût | Secondaire (QA) |
| Conditions identifiées | Réponse à une question latérale posée à 25, 50 et 75 % du budget, non renvoyée au système ; rappel et précision contre la voie de R_Bayes, partie décrite et partie cachée séparées | Secondaire (QC) |
| Découverte | Déclaration structurée (variable, sens de l'effet) avant d'en tirer parti ; utile si faite avant tout engagement irréversible sur la voie bloquée ; fausses alertes sur les anomalies de bruit | Secondaire (QB, préparation de l'étape 2) |
| Abstentions | Justes (mondes impossibles) et injustes, avec leur coût préenregistré | Secondaire |
| Violations | Événements du monde : action fondée sur l'affirmation fausse sans l'avoir vérifiée, dépassement de budget ; publiées par type, avec ce qui est acquis par construction | Secondaire |
| Calcul | Appels, jetons d'entrée et de sortie, secondes, dollars | Contrôle |

Résultats publiés par case du plan croisé.

## 6. Développement, calibration, validité

1. **Références en code d'abord** (coût nul), sur des mondes de développement : fixer V et la valeur de Z ; critères R_naïf < R_Bayes et R_explore < R_Bayes, avec un écart R_naïf à R_Bayes assez large pour que G ait un sens.
2. **Mini-pilote de T1c** sur 15 à 20 mondes de développement : vérifier que le modèle n'est ni au plancher ni au plafond (leçon du palier 1).
3. **Trois espaces de mondes séparés** : développement (réglages), confirmation (graine dont seule l'empreinte est publiée avant l'exécution, révélée après), familles de transfert figées avant tout développement des systèmes (étape 2).
4. Même nombre d'itérations de développement pour T1c et C.

## 7. Étapes, calendrier et budget (décision du 23/10/2026)

Enveloppe totale de 200 à 500 $, étalée sur deux à trois mois, chaque tranche soumise à validation sur le coût mesuré.

| Période | Contenu | Dépense de modèle |
|---|---|---|
| Mois 1 | Comité sur cette v1 ; gabarits par un tiers ; générateur, références, calibration (code) ; mini-pilote T1c ; pilote T1c et C sur 20 à 30 mondes ; coût réel et variance de ΔU ; taille fixée ; préenregistrement de l'étape 1 | 30 à 80 $ |
| Mois 2 | Confirmation de l'étape 1 (150 à 250 mondes, T1c et C, T1 sur sous-échantillon) ; verdict | 100 à 250 $ |
| Mois 3 | Étape 2 (couches A et B, apprentissage avec un même carnet de mémoire pour tous), seulement si l'étape 1 est interprétable ; protocole propre, préenregistré | le reste de l'enveloppe |

Plafond de dépense par exécution fixé dans le code, arrêt avant dépassement ; aucune tranche lancée sans accord.

## 8. Ce qui n'est pas revendiqué

- Un succès dira que la discipline améliore ce modèle dans des mondes de cette structure, pas sur le terrain, ni que la boucle bat un code.
- Pas d'interaction par rétroaction en v1.
- Référence citée de mémoire : complexité de la planification sous observation partielle (Papadimitriou et Tsitsiklis, 1987) ; aucune décision n'en dépend, le générateur étant restreint.
