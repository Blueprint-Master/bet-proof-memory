# Monde simulé : spécification v2 (après comité, avant gabarits)

*23/10/2026. Intègre les 21 objections du premier tour de critique (`monde-simule-matrice-1.md`), l'avis du comité sur la v1 (`monde-simule-comite-1.md`) et les décisions de Rémi Cabrit du même jour : conduite par étapes, enveloppe de 200 à 500 $, dépense étalée sur deux à trois mois. Non préenregistré : le préenregistrement viendra après les gabarits et le développement du générateur.*

## 0. Objet

Tester, dans un monde où l'objectif est connu et le chemin ne l'est pas, si l'architecture de la boucle de supervision (couche C) améliore les décisions d'un modèle de langage **à consignes égales**. L'étape 2 ajoutera, sur le même générateur, la décomposition (couche A), l'exploration dosée (couche B) et l'apprentissage entre mondes. Genèse et intentions : base de connaissance, fiche 2317.

## 1. Étape 1 : question, hypothèse, verdict

- **Question.** À description, outils, budget et consignes identiques, la boucle obtient-elle une meilleure utilité que le même modèle en usage libre ?
- **Utilité, unique et préenregistrée.** U = V × atteinte + valeur de Z obtenue − coût dépensé dans le monde. V et la valeur unitaire de Z sont fixés par règle sur les mondes de développement (§6), connus de tous les systèmes.
- **Échelle.** Les écarts sont exprimés en fraction de G = E[U(R_Bayes)] − E[U(R_naïf)], **fixé numériquement sur les mondes de développement** avant la confirmation ; ΔU est aussi publié en unités brutes. Si G est trop faible en développement, on s'arrête avant la confirmation.
- **Hypothèse primaire.** ΔU = E[U(C)] − E[U(T1c)] ; gain minimal d'intérêt 0,10 G ; marge d'équivalence ± 0,05 G.
- **Inférence.** Différences appariées par monde (mêmes mondes, mêmes aléas pour tous) ; test de permutation et intervalle BCa **par grappes de gabarit**, puisque les mondes d'un même gabarit ne sont pas indépendants.
- **Verdict.** **Succès** si la borne basse de l'intervalle dépasse 0,05 G et l'estimation atteint 0,10 G ; **effet positif détecté** (publié, pas un succès) si la borne basse dépasse 0 sans remplir la condition précédente ; **équivalence** si l'intervalle tient dans ± 0,05 G ; **échec** si ΔU est significativement négatif ; indécis sinon. Les contrastes secondaires sont corrigés par la méthode de Holm.

## 2. Le générateur

- **Espace fini.** Chaque monde est tiré dans une famille de gabarits ; dans un monde, la structure réelle appartient à un ensemble fini et petit d'hypothèses (de l'ordre de 16 à 64). La résolution exacte de R_Bayes est d'abord vérifiée sur de petits mondes ; si elle reste intraitable à la taille retenue, une politique bayésienne approchée est publiée comme borne basse et R∞ comme borne haute, et le gaspillage n'est calculé que là où la valeur de l'information est exacte.
- **Structure.** Y atteint la cible si l'une des voies (4 au plus) est satisfaite ; une voie est un ensemble minimal de conditions de succès (4 au plus) ; chaque condition se satisfait par des actions (3 au plus) ayant coût, délai, réversibilité. Trois ingrédients d'interaction : effets de bord négatifs (une action satisfait une condition et en défait une autre), seuils sur variables discrétisées, ressources partagées entre voies. Pas de boucles de rétroaction en v1 (limite de portée déclarée).
- **Temps et coût.** Échéance de 12 à 20 périodes ; **une action par période** ; `mesurer` coûte peu mais consomme la période ; observations discrètes. Le budget du monde (primaire) est distinct du budget de calcul (appels de modèle), avec un plafond commun fixé au pilote ; au plafond, la dernière décision est tenue pour finale ; consommation complète publiée, performance sous plafond et efficience séparées.
- **Bruit.** Tiré de façon déterministe à partir de (monde, période, action, occurrence) : tous les systèmes voient les mêmes aléas, et une mesure répétée n'est pas une copie de la précédente.
- **Description fournie.** Texte et tableau des variables, actions, coûts. Elle peut être incomplète et contenir une affirmation fausse ; **tous les systèmes en sont informés** de la même façon (sans les fréquences).
- **Une seule source pour le texte et la structure.** Chaque passage de description ou de documentation est généré avec son équivalent structuré. Les systèmes à modèle reçoivent le texte ; les références en code reçoivent l'équivalent structuré **des mêmes observations, au même coût et au même moment**, jamais l'état caché. Un contrôle automatique vérifie la cohérence de chaque paire.
- **Plan croisé des perturbations**, chaque facteur présent ou absent, équilibré entre mondes :
  - obstacle caché sur la voie la plus évidente, difficulté réglée par le nombre de mesures dont un détecteur bayésien a besoin pour le voir à 80 % (2 ou 4) ; second canal possible par un passage de `lire` ;
  - affirmation fausse de provenance vérifiable ;
  - occasion sur Z (levier caché, valeur connue) ;
  - **cas où la prudence coûte** : affirmation de provenance douteuse mais vraie ; échéance serrée où vérifier fait manquer la cible. Leur proportion est fixée avant tout essai ; en secondaire obligatoire, U est publiée par case et hors de ces cas, avec une analyse de sensibilité aux proportions ;
  - anomalies de pur bruit dans tous les mondes, pour que poursuivre chaque anomalie ait un coût et que les fausses alertes se mesurent.
- **Mondes impossibles** : environ 10 %, chacun apparié à un monde faisable quasi identique ; l'abstention y est la bonne réponse. Toute fin de monde, abstention comprise, est évaluée par la même fonction U : une abstention ne rapporte pas V, conserve la valeur de Z déjà acquise et arrête la dépense ; s'abstenir tôt dans un monde impossible est donc la meilleure conduite, et s'abstenir dans un monde faisable coûte V.
- **Domaine.** Fond abstrait, noms neutres, unités cohérentes, rôles décrits. En secondaire, un sous-ensemble des mêmes mondes est habillé en domaine concret, apparié, pour mesurer ce que le modèle tire de ses connaissances générales. Jamais mêlés dans le verdict.
- **Gabarits de perturbations écrits par un tiers.** Un modèle du comité, dans un appel qui ne contient que la spécification du générateur (sans rien sur la boucle), rédige les gabarits d'obstacles, d'affirmations fausses et de cas où la prudence coûte ; un second les critique ; le concepteur les traduit en code, chaque monde passant le contrôle de cohérence.

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

Même modèle épinglé pour T1c, C et T1 ; même description ; même budget ; même plafond de calcul ; **aucune mémoire entre mondes** à l'étape 1, pour aucun système. **C construit son arbre à partir du même texte et du même tableau que T1c** ; rien de structuré n'est donné à C seul. Les références lisent l'équivalent structuré des mêmes observations.

## 4. Adaptation déclarée de la boucle gelée (erratum de transposition)

- **Générateurs multiples (S2 de la note).** Un seul modèle à l'étape 1, pour garder l'égalité avec T1c ; la génération multiple relève de la couche A, testée à l'étape 2. Écart déclaré.
- **Mandat.** Toutes les actions du monde, réversibles ou non, sont dans le mandat, dans la limite du budget : le contrôle avant action vérifie budget, préconditions et statuts, pas une autorisation humaine.
- **Vérificateur humain.** Aucun ; les vérificateurs sont le code du monde (mesures, essais) et les passages de documentation avec leur provenance.
- **Ordonnanceur (S11).** Priorité topologique de la note, calculée sur l'arbre ancré de C ; l'ablation R_boucle-code en mesure l'apport propre.
- **Sens de « vérifié » sous bruit (ajout).** Une observation authentifiée (mesure, essai, passage de provenance établie) est vérifiée *en tant qu'observation*, pas en tant que vérité. Une proposition sur l'état du monde passe au statut vérifié quand sa croyance a posteriori, calculée sous le bruit déclaré, dépasse un seuil préenregistré ; elle passe à contredit sous le seuil symétrique. Aucun vérificateur n'accède à l'état caché (audit du code).
- **Invalidation temporelle (ajout).** Chaque statut vérifié porte ses dépendances (variables, période) ; toute action qui touche une dépendance le ramène à inconnu. La note gelée raisonnait sur des faits statiques : écart déclaré.

## 5. Mesures

| Mesure | Définition | Statut |
|---|---|---|
| U | §1 | **Primaire** |
| Gaspillage | Part du coût dépensée en mesures et essais dont la valeur de l'information attendue, calculée sous la loi du générateur au vu des seules observations du système à ce moment (reconstituées par le journal), était inférieure au coût | Secondaire (QA) |
| Conditions identifiées | Question latérale posée après coup sur une copie de la trace arrêtée à 25, 50 et 75 % du budget, hors budget de l'agent ; rappel et précision contre l'ensemble des voies réellement valides, partie décrite et partie cachée séparées | Secondaire (QC) |
| Découverte | Déclaration structurée (variable, sens de l'effet) avant d'en tirer parti ; utile si faite avant tout engagement irréversible sur la voie bloquée ; fausses alertes sur les anomalies de bruit | Secondaire (QB, préparation de l'étape 2) |
| Abstentions | Justes (mondes impossibles) et injustes, avec leur coût préenregistré | Secondaire |
| Violations | Événements du monde : action fondée sur l'affirmation fausse sans l'avoir vérifiée, dépassement de budget ; publiées par type, avec ce qui est acquis par construction | Secondaire |
| Calcul | Appels, jetons d'entrée et de sortie, secondes, dollars | Contrôle |

Résultats publiés par case du plan croisé ; les cases trop peu fournies sont déclarées exploratoires.

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
