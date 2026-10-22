# Palier 1.2 : avis du petit comité (22/10/2026, 22 h 45)

*Dossier autoportant identique soumis à trois modèles (gemini-4-argon, gpt-6-astra, grok-4.7 ; alias non épinglés). Mistral exclu : c'est le modèle testé. Les réponses sont des avis non vérifiés de tiers ; ci-dessous, chaque argument est jugé sur sa vérifiabilité, pas sur le nombre de modèles qui le portent. Dossier envoyé : copie conservée hors dépôt (bloc-notes de session), contenu résumé en §1.*

## 1. Question posée

Après l'effet plafond du palier 1 et les 18 objections au projet v0 : la voie « estimation par précédents actuariels » est-elle le bon prochain test de la boucle, ou faut-il reposer la question ? Corrections envisagées, connaissance du futur par le modèle (K5), critère de réfutation, défauts non vus.

## 2. Arguments retenus

| Argument | Porté par | Jugement |
|---|---|---|
| Corrigé honnêtement (engagement à l'aveugle, rétrécissement, seuil en événements), B converge vers D2 : le modèle ne fait plus que proposer un filtre que le code neutralise ; on mesure un estimateur codé, pas la boucle | les trois | **Retenu** : conséquence logique des corrections ; le pressentiment était dans K3, il devient décisif |
| K5 n'est pas corrigeable proprement sur des issues 2020 réelles : une sonde n'établit ni l'ignorance ni l'influence ; le coût réalisé 2020 récompense celui qui « sait » la baisse | les trois | **Retenu** pour toute tâche où le modèle estime p ; sans objet quand p est fourni (palier 1) |
| Le prochain test doit porter sur une tâche où le code peut trancher le **statut** d'un champ (provenance, date, contradiction, applicabilité) sans pouvoir calculer la décision à la place du modèle : pièges de provenance, sources contradictoires à priorité spécifiée, précédents proches mais inapplicables, inconnus insolubles exigeant l'abstention | les trois (formes diverses) | **Retenu comme direction**, avec la réserve d'OpenAI : ne pas fabriquer exclusivement des pièges favorables à B ; prévoir cas propres, perturbations isolées et combinaisons |
| Règle 9 et seuil : un franchissement de p_t n'est « vérifié » que si l'intervalle de l'estimation ne contient pas p_t ; sinon inconnu | Gemini | **Retenu** comme raffinement de la règle 9, à porter dans tout palier où p est estimé |
| Préenregistrer un gain minimal, un coût de l'abstention comme politique opérationnelle, une marge d'équivalence B contre la référence en code | OpenAI, Grok | **Retenu** (le coût de l'abstention existe déjà en M1 : pire des deux décisions) |
| Un seul régime macroéconomique (2020) : les cas ne sont pas échangeables vis-à-vis du choc commun ; la conclusion vaut « sous ce régime » | Grok | **Retenu** comme limite de portée, à déclarer aussi pour le palier 1 |
| Réidentification par profil sectoriel et ratios, distincte de K5 | Grok | **Déjà déclaré** (R8, quasi-identifiants) ; la **sonde de mémorisation** préenregistrée au palier 1 (§7.2) n'a pas encore été exécutée : à faire |
| Horizon de vérité (548 jours) et exposition réelle selon le délai de paiement | OpenAI | **Connu** : coût conventionnel fixé par le protocole du juge du réel (P6) ; à rappeler comme convention dans le rapport |

## 3. Arguments écartés ou corrigés

- **« 2 à 4 défaillances sur l'échantillon, puissance quasi nulle »** (Gemini) : faux. Le tirage est stratifié (150 défaillants sur 300) ; la difficulté réelle est l'effectif utile pondéré (environ 153), déjà déclarée.
- **« Chaque dossier évalué sous six scénarios, erreurs corrélées »** (Gemini) : faux. Chaque cas reçoit un seul scénario tiré.
- **« Au 30/09/2020 l'effet des mesures de soutien était inconnu »** (Gemini) : discutable ; la baisse des ouvertures de procédures était déjà visible au premier semestre 2020. Non utilisé.
- Les « il est établi » de Gemini sont souvent des jugements ; lus comme tels.

## 4. Conclusion de la consultation

La voie « précédents actuariels sur 2020 » n'est pas le bon prochain test : corrigée, elle mesure un estimateur codé ; non corrigée, elle mesure le bruit, la recherche de filtre et la connaissance du futur. Le prochain test doit placer le modèle là où le code peut vérifier sans pouvoir décider : statut des informations (provenance, date, contradiction, applicabilité), avec la prévision fournie comme au palier 1. Le projet v0 et sa matrice restent au dépôt comme trace ; ils ne seront pas préenregistrés.
