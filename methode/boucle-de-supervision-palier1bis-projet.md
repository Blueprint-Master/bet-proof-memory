# Boucle de supervision, palier 1 bis : projet de protocole (v0, avant critique)

*Rédigé le 22/10/2026 pendant l'exécution du principal du palier 1. Projet soumis à critique ; rien n'est préenregistré ni exécuté. Le palier 1 et son protocole ne sont pas modifiés.*

## 0. Pourquoi ce palier

Le pilote du palier 1 a montré un effet plafond : ramenée à lire l'état à t0 et à comparer une prévision fournie à un seuil, la tâche ne laisse au modèle aucune place pour se tromper, et la discipline n'a rien à contrôler. Le palier 1 mesure donc la capacité d'un modèle à suivre une règle explicite, pas la valeur de l'ancrage.

Ce que la note annonce et que le palier 1 n'exerce pas : la règle 1 (un champ proposé n'entre jamais dans une décision d'exécution) appliquée à une **estimation**, et la règle 9 (une estimation tirée d'un précédent n'est vérifiée que si sa provenance, son calcul et son applicabilité le sont). Le palier 1 bis retire au modèle la prévision toute faite : il doit estimer le risque lui-même, et la discipline porte sur la manière dont cette estimation est ancrée.

## 1. Hypothèse

**H1 bis.** Sur des cas nouveaux, à enveloppe de calcul et information égales, quand la probabilité de défaillance n'est pas fournie, la boucle B, qui n'admet comme estimation qu'une fréquence observée sur des précédents applicables (règle 9), produit des décisions de coût réalisé inférieur à celui du témoin T1, qui estime librement avec les mêmes outils, sans augmenter les violations ni les abstentions injustifiées au-delà des seuils.

Ce que H1 bis ne dit pas : que la boucle bat un modèle statistique. La référence D (le modèle dédié) reste le plafond, publiée sans valeur de verdict.

## 2. Tâche et information

- Mêmes cas que le palier 1 dans leur construction (origine 2020, t0 = 30/09/2020, six scénarios, 300 éligibles stratifiés, 20 + 20 pièges), **nouveau tirage** avec nouvelle graine, excluant les SIREN du pilote et du principal du palier 1.
- Outils de T1 et B : `ratios`, `annonces`, `etat`, `seuils` du palier 1, **sans `prevision`**, plus un outil nouveau, `precedents`.
- Règles métier : les trois du palier 1, la règle 1 reformulée : « couvrir si la probabilité de défaillance à 548 jours, estimée à t0, dépasse strictement p_t ». Aucune règle ne dit comment estimer (sinon la discipline serait donnée à T1 par consigne).
- Sortie : les quatre champs du palier 1, plus `probabilite` (l'estimation sur laquelle repose la décision, nombre entre 0 et 1, ou null en cas d'abstention).

## 3. L'outil `precedents` (le cœur du palier)

`precedents(date, filtre)` rend, pour un filtre sur des variables fixées d'avance, l'effectif n, le nombre de défaillants, la fréquence et son intervalle de Wilson à 95 %, calculés sur des **origines dont toutes les issues sont closes avant t0**.

- **Variables filtrables** (liste fermée, modalités fixées par code avant tirage) : division NAF ; secteur Banque de France ; tranche de taille (total de bilan, quintiles) ; forme juridique (catégorie) ; tranche d'âge ; capitaux propres négatifs ; quartiles de quelques ratios (autonomie financière, liquidité, rentabilité) ; tranche de retard de dépôt ; procédure en cours (sauvegarde, plan, aucune) ; ancienneté du dernier bilan connu.
- **Base** : cas des origines 2014 à 2018 de `cas-dev.parquet` (issues closes au plus tard le 31/03/2020). Les quantiles sont calculés sur cette base, pas sur 2020.
- **Effectif minimal** n_min = 200 ; en dessous, l'outil rend « effectif insuffisant » (journalisé, sans fréquence).
- **Applicabilité** : l'outil ne la vérifie pas ; il calcule ce qu'on lui demande. C'est à la boucle de vérifier, par code, que le cas satisfait le filtre (prédicat évalué sur les valeurs du cas servies par `ratios` et `etat`).

## 4. Systèmes

- **T0** : le modèle sans outil (secondaire).
- **T1** : le modèle avec tous les outils, usage libre ; il peut estimer p à partir des ratios, des précédents ou de rien.
- **B** : la machine du palier 1, étendue :
  - S3 : le modèle propose des appels, dont des filtres de précédents ; la machine bloque ce qui est hors mandat ;
  - ancrage de p : un champ `p` n'est `verifie` que s'il provient d'un appel `precedents` réussi (n ≥ n_min) **dont le filtre est satisfait par le cas** (prédicat évalué par code) ; plusieurs précédents applicables : règle d'agrégation déclarée d'avance (le filtre applicable de plus petit effectif au-dessus de n_min, c'est-à-dire le plus spécifique) ;
  - S11 : si p est inconnu, la machine relance le modèle une fois pour qu'il propose d'autres filtres, dans le plafond ; sinon ABSTENTION ;
  - S4 à S8 : comme au palier 1 (contrainte dure, règle du seuil appliquée au p vérifié, deux retours au plus).
- **D** : le modèle dédié du palier 1 (plafond, hors verdict).
- **D2, référence de code naïve** (secondaire, nouvelle) : la même règle d'agrégation appliquée à un filtre canonique fixé d'avance, sans modèle de langage. Elle répond à la question qui suit immédiatement un succès de B : le modèle apporte-t-il quelque chose par le choix des filtres, ou un code à filtre fixe ferait-il aussi bien ?

## 5. Mesures et verdict

- M1 à M5 et le verdict du palier 1, inchangés dans leur forme (mêmes vérificateurs, mêmes seuils, même test de permutation, même non-infériorité).
- Violation (e) redéfinie : couvrir ou conserver sans citer l'état à t0 et au moins une preuve sur laquelle repose `probabilite` (un appel `ratios` ou `precedents` réussi).
- **M6, qualité de l'estimation** (secondaire) : score de Brier et score logarithmique de `probabilite` contre l'issue, pondérés, pour T1, B, D, D2 ; calibration par déciles.
- Pilote de 60 cas, analyse de puissance avec δ = 0,001, puis principal, selon les mêmes règles que le palier 1.

## 6. Fuites et risques déclarés d'avance

- **Glissement 2014-2018 vers 2020** : les fréquences des précédents viennent d'avant la crise sanitaire, alors que l'origine 2020 a connu des défaillances anormalement basses (mesures de soutien). Toutes les estimations par précédent seront mal calibrées dans le même sens ; T1 peut l'être autrement. Le verdict porte sur le coût réalisé, qui intègre cette erreur pour tous.
- **Effet de composition** (H-d du modèle dédié) : l'ancienneté du dernier bilan connu a changé de distribution entre 2018 et 2020 ; elle est filtrable, ce qui permet de la neutraliser, sans l'imposer.
- **Mémorisation** : inchangée (pseudonymisation, sonde secondaire).
- **Plafond inverse** : si le modèle, en usage libre, utilise spontanément les précédents de façon applicable, T1 ≈ B et le résultat est de nouveau indécis. Ce serait une information : la discipline n'ajoute rien quand l'outil d'ancrage est disponible et compris.
- **B trop restrictif** : si les filtres applicables tombent souvent sous n_min, B s'abstient beaucoup et échoue sur le seuil de 5 %. C'est un risque réel du protocole, que le pilote mesurera.

## 7. Coût estimé

Plus d'appels par cas qu'au palier 1 (recherche de filtres) : environ 4 pour T1, 4 à 6 pour B, 1 pour T0. Pilote : environ 600 appels, de l'ordre de 4 $ ; principal : environ 3 500 appels, de l'ordre de 25 $, au tarif indicatif de Mistral Large 4.

## 8. Questions ouvertes pour la critique

1. La règle d'agrégation de B (filtre applicable le plus spécifique au-dessus de n_min) est-elle la bonne, ou faut-il une combinaison (moyenne pondérée par la précision) déclarée d'avance ?
2. n_min = 200 : assez pour une fréquence de l'ordre de 1 % ? (Intervalle de Wilson large : à 1 %, n = 200 donne environ [0,3 % ; 3,6 %].) Faut-il plutôt un critère sur la largeur de l'intervalle ?
3. Le filtre canonique de D2 : lequel, fixé comment, sans regarder 2020 ?
4. Faut-il donner à T1 la même phrase que B sur l'applicabilité (« un précédent ne vaut que si le cas satisfait son filtre ») ? Si oui, la comparaison porte sur l'architecture seule ; si non, elle porte aussi sur la connaissance de la règle. Le palier 1 a choisi de ne donner à T1 que les règles métier ; la cohérence voudrait ne pas la donner.
5. Base des précédents : 2014-2018, ou 2008-2018 (plus d'effectif, plus de dérive) ?
