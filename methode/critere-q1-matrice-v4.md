# Critère de jugement de la question 1 : matrice des critiques du texte de l'amendement v1.7 (projet)

Critiques à l'aveugle du texte (P5 bis, P6, P6 ter, P7), reçues le 20/10/2026 :
- ChatGPT (gpt-6-astra), 15:31 UTC ;
- Gemini (gemini-4-argon), 15:31 UTC.

Mistral n'a pas été sollicité dans ce tour, après quatre échecs dans la session (perte de connexion, dépassements du délai de 230 s). C'est déclaré.

Ce tour ne relève plus aucune objection de fond sur la décision, la perte ou le seuil. L'algèbre est vérifiée par les deux critiques. Le lien avec Schervish est démontré par chacune, par deux écritures équivalentes. Les points bloquants portent sur **l'exécution sans interprétation**.

## 1. Points bloquants retenus (vérifiés), avec correction

| N° | Point | Relevé par | Correction dans le texte |
|---|---|---|---|
| X1 | **États non exclusifs dans P6 ter.** Un plan arrêté peut être suivi d'une résolution avec liquidation : des risques concurrents absorbants ne peuvent pas représenter ces deux issues à la fois | ChatGPT, Gemini (convergence) | **Modèle multi-états** : observation → plan ; observation → liquidation ; plan → liquidation. Liquidation absorbante. Estimateur d'Aalen-Johansen des **probabilités d'occupation des états à τ** : P_L, P_plan, P_obs. Liquidation → LGD 0,95 ; en plan → 0,269 ; en observation → masse ouverte |
| X2 | **« Plan de sauvegarde » dans la continuation** : après une défaillance au sens de P3, un plan est un plan de redressement | Gemini | Exact : continuation = plan de redressement arrêté hors cession |
| X3 | **Dates, unité et support** : jugement ou publication ? procédures comptées deux fois ? support à 1 095 jours ? | ChatGPT | Unité : la procédure (SIREN, date du jugement de défaillance), dédupliquée. Temps : dates de jugement ; une annonce n'est lue que si elle a paru avant le 30/09/2022. Règle de support : si moins de 300 procédures (plancher P9) restent observées à τ, τ est ramené au plus grand délai qui l'atteint |
| X4 | **Fuite dans les plis de P7** : R2 « ajusté sur tout l'espace d'apprentissage » utiliserait 2019 et 2020 pour le pli 2018 vers 2019 | Gemini, ChatGPT (convergence) | Dans chaque pli, R2, le témoin et l'assemblage sont réajustés sur l'apprentissage du pli seul. La validation croisée interne de γ utilise le η du R2 du pli : cette contamination interne est déclarée, et elle est sans effet sur l'évaluation hors pli |
| X5 | **Évaluation d'un candidat seul en P7 non définie** | Gemini, ChatGPT | Chaque candidat est évalué seul : assemblage avec x = ce candidat, même procédure (λ par validation croisée interne). L'assemblage final reprend tous les admis, réajusté une fois |
| X6 | **Optimisation sous-spécifiée** : normalisation de la pénalité, départage, convergence, séparation sur a et b non pénalisés, échelle du seuil de 50 | ChatGPT | Pénalité (λ / 2) ‖γ‖² ajoutée à la log-vraisemblance **moyenne** (implémentation : C = 1 / (λ n)) ; égalité de score → le plus grand λ ; non-convergence = limite d'itérations atteinte (2 000) ; seuil de 50 sur γ, mécanismes réduits ; si a ou b ne convergent pas, arrêt et amendement mécanique déclaré |
| X7 | **Rééchantillonnage incomplet** | ChatGPT | Tirage de 88 grappes environ (leur nombre observé) avec remise ; multiplicité = poids. Δ calculé par origine sur les cas tirés de cette origine, puis moyenne 1/2-1/2. NAF manquante = grappe propre. Une réplication sans cas d'une des origines est retirée. Graine publiée |
| X8 | **Pondération par le total de bilan non exécutable** | Gemini | Total du dernier bilan connu à t0 (P2, P2 quater). Absent ou ≤ 0 : cas exclu de la variante pondérée, et ce nombre est publié |

## 2. Points non bloquants retenus

- **Base contractuelle de q** (ChatGPT ; bloquant selon lui). La fiche 604 parle d'une part « du montant de la créance », alors que la formule suppose une part de la perte nette. **Correction** : convention déclarée. L'assureur indemnise une part q de la perte nette (créance diminuée des recouvrements), les recouvrements étant partagés au prorata. Classé non bloquant, car la convention est écrite et le choix ne dépend d'aucune donnée.
- **Projection de puissance fausse** (Gemini, ChatGPT). Avec un nombre fixe de grappes, l'erreur-type ne décroît pas en 1/√N. **Correction** : la projection est supprimée. On publie la demi-largeur observée sur le pli de développement, avec le même bootstrap, sans projection et à titre indicatif.
- **Formulation de l'approximation de la prime** (les deux). **Correction** : le modèle est écrit. Si la prime cesse à la défaillance, survenue à la fraction f de l'horizon, le seuil exact vaut π T / (q LGD + (1 − f) π T) ; l'écart relatif est (1 − f) p_t ≤ p_t. Gemini qualifie la borne de « fausse », puis la redémontre : c'est contradictoire dans sa critique, mais la demande de modèle explicite est juste.
- **L_min** (Gemini). **Correction** : L_min est l'encours total, toutes contreparties notées confondues, à partir duquel le gain couvre c. Il est publié par scénario et pour la moyenne de la grille.
- **Standardisation des mécanismes** (Gemini) : sur la table des cas à t0 de l'apprentissage, pas sur la table personne-période.
- **Bootstrap percentile et grappes déséquilibrées** (les deux) : la couverture n'est pas garantie à effectif fini. C'est une hypothèse déclarée, déjà inscrite dans la portée.
- **La symétrie n'établit pas que le gain vient du mécanisme économique invoqué** (ChatGPT) : c'est exact, et c'est conforme à la règle 2 (la performance n'est pas une inférence causale). Rien n'est à changer.
- **Le prorata de la masse ouverte est une imputation, et les bornes ne sont pas des intervalles de confiance** (ChatGPT) : exact, ajouté au texte.

## 3. Règle d'arrêt des tours

Les tours v0 à v3 ont porté sur le fond. Ils ont produit sept erreurs (E1 à E7), cinq corrections (B1 à B5), une dégénérescence et une décision respécifiée. Le tour sur le texte n'a soulevé que des points d'exécution, tous corrigés par écrit. Le dernier contrôle se fait sur deux plans :
- un tour de vérification ciblé : les corrections X1 à X8 répondent-elles aux points soulevés ?
- les tests unitaires du code qui exécutera P5 bis, P6 et P6 ter : un tiers exécute sans interpréter si le code est écrit à partir du texte et que ses tests passent.
