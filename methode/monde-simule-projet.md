# Monde simulé : tester ensemble les trois couches (projet v0, avant critique)

*Rédigé le 23/10/2026 sur décision de Rémi Cabrit. Projet soumis à critique ; rien n'est préenregistré ni construit. Remplace le projet de palier sur les précédents actuariels, abandonné le 22/10/2026 (`boucle-de-supervision-palier1-2-comite-1.md`).*

## 0. D'où vient ce projet

L'intention de départ compte trois volets (base de connaissance, fiche 2317) : **utiliser les bons outils au bon moment**, **apprendre à trouver le chemin critique vers un objectif** (l'ensemble minimal de conditions dont dépend son atteinte, et l'ordre pour les lever), **faire place à la sérendipité**. Le 20/10/2026, ces volets ont reçu une architecture en trois couches : A exploitation (choisir les outils qu'exige le besoin), B exploration (sérendipité, budget fixe, ordonnanceur externe), C validation (provenance, épreuve du réel). La boucle de supervision développe la couche C.

Le palier 1 a testé la couche C seule, sur une tâche dont le chemin est donné d'avance : son pilote montre que le modèle suit déjà la règle (T1 = B = D sur 60 cas). Il fallait un terrain où l'objectif est connu et le chemin ne l'est pas, où le vrai chemin critique existe et se constate, où les outils coûtent, et où des mécanismes ne sont décrits nulle part. Ce terrain est un monde simulé, que la note de la boucle prévoyait au palier 2.

## 1. Questions

- **QA, bon outil au bon moment.** À budget égal, quel système dépense le moins en mesures qui ne changent aucune décision ?
- **QC, chemin critique.** Quel système identifie le plus tôt et le plus exactement l'ensemble minimal de conditions qui conditionne l'objectif, et l'atteint ?
- **QL, apprendre.** Le coût baisse-t-il d'un monde au suivant quand les mondes partagent des mécanismes ?
- **QB, sérendipité.** Quel système découvre à temps ce que la description du monde ne contient pas, et le convertit en valeur, sans se perdre en fausses pistes ?

## 2. Le générateur de mondes

Un monde est tiré par code, avec une graine, selon des règles fixées avant tout essai.

- **Objectif.** Amener une variable de sortie Y au-dessus d'une cible avant l'échéance H (en périodes), sous un budget de coût. Une variable secondaire Z (par exemple un coût d'exploitation) existe aussi, hors objectif déclaré.
- **Structure cachée.** Y n'atteint la cible que si l'une des **voies** est satisfaite ; une voie est une conjonction de conditions sur des variables d'état (forme « OU de ET », qui rend explicites les conditions conjointes et les coupes minimales). Chaque condition se satisfait par des actions, chacune avec un coût, un délai et un caractère réversible ou non. Le **vrai chemin critique** est la voie réalisable la moins coûteuse dans le délai ; il est calculé par code, puisque le monde est connu de son générateur.
- **Description fournie à l'agent.** Un texte décrit le monde : objectif, variables, actions, coûts. Elle est **volontairement incomplète** (certaines conditions n'y figurent pas) et peut contenir **une affirmation fausse** dont la provenance est vérifiable (piège pour la couche C).
- **Outils.**

  | Outil | Effet | Coût, délai |
  |---|---|---|
  | `mesurer(variable)` | Rend la valeur courante, avec un bruit déclaré | faible, immédiat |
  | `lire(source)` | Rend un passage de documentation, avec sa provenance et sa date | faible |
  | `essayer(action)` | Essai réversible à petite échelle : rend l'effet observé, bruité | moyen, une période |
  | `agir(action)` | Action réelle, parfois irréversible | élevé, délai propre |
  | `attendre` | Laisse passer une période | coût du temps |

- **Surprises plantées.**
  - **Obstacle caché** : une condition absente de la description, sur la voie la plus évidente. Elle la fait échouer, et elle laisse un signal faible (une mesure qui ne se comporte pas comme le modèle déclaré le prévoit).
  - **Occasion hors objectif** : un levier qui améliore fortement Z, visible seulement à qui explore hors du chemin vers Y.
  - **Mondes témoins** : au moins 20 % des mondes n'ont aucune surprise, pour que l'exploration ait un coût réel et qu'un système ne soit pas récompensé de chercher partout.
- **Familles.** Les mondes sont tirés dans des familles qui partagent des gabarits de mécanismes (par exemple un même type d'obstacle caché). On peut ainsi mesurer l'apprentissage d'un monde au suivant, et le transfert entre familles.
- **Domaine.** Abstrait (noms de variables neutres) ou concret (atelier, chaîne logistique, projet) : question ouverte (§7).

## 3. Systèmes comparés

Même modèle de langage, mêmes outils, même description, même budget et même plafond d'appels.

| Système | Couches | Description |
|---|---|---|
| T1 | aucune | Le modèle libre avec les outils |
| C | C | La boucle de supervision : statuts, ancrage, blocage sur inconnu, contrôle avant action |
| AC | A + C | Décomposition explicite de l'objectif en conditions, puis la boucle |
| ABC | A + B + C | AC plus un budget d'exploration fixe, dosé par un bandit externe au modèle, trois suggestions au plus, double score pertinence et inattendu ; les observations hors arbre sont des objets de statut « proposé » |
| R0, plancher | code | Politique aléatoire sous le même budget |
| R1, référence en code | code | Heuristique de valeur de l'information appliquée à la seule description fournie |
| R∞, plafond | code | Politique optimale qui connaît la structure réelle (oracle) |

Principe tiré du 20/10 : le modèle de langage n'explore pas seul de façon fiable (Krishnamurthy et al. 2024). L'exploration de ABC est donc pilotée hors du modèle ; le modèle propose les pistes, le bandit décide lesquelles financer.

## 4. Mesures

| Mesure | Définition | Question |
|---|---|---|
| Atteinte | Y au-dessus de la cible à l'échéance (oui, non), et date | QC |
| Coût total | Somme des coûts dépensés | toutes |
| Gaspillage | Part du coût dépensée en mesures et essais qui n'ont changé aucune décision ultérieure, comparée à R∞ | QA |
| Chemin identifié | Rappel et précision de l'ensemble de conditions déclaré par le système avant d'agir, contre la vraie coupe minimale | QC |
| Pente d'apprentissage | Baisse du coût total sur une suite de mondes d'une même famille | QL |
| Découverte | Part des surprises découvertes avant l'échéance ; part converties (l'obstacle levé, l'occasion exploitée) ; fausses pistes coûteuses | QB |
| Violations | Action fondée sur un champ seulement proposé, usage de l'affirmation fausse sans vérification, dépassement de budget | C |

Toutes les mesures sont calculées par code, puisque la vérité du monde est connue.

## 5. Validité

- **Calibrer la difficulté avant tout appel de modèle.** Leçon directe du palier 1 : on fait d'abord tourner R0, R1 et R∞ seuls sur des mondes de développement. La tâche n'est retenue que si l'écart R0 à R∞ est large et si R1 se place entre les deux, assez loin de R∞ pour laisser au modèle la place de faire mieux ou moins bien. Sinon on règle le générateur, sur les seuls mondes de développement.
- **Trois espaces de mondes séparés** (fiche 2167) : développement (réglage du générateur et des systèmes), confirmation scellée (graine publiée, consultée une seule fois), et nouvelles familles jamais vues pour le transfert.
- **Pas de mondes faits pour la boucle.** Les règles du générateur sont écrites avant que les systèmes existent, et les mondes témoins en garantissent le contrepoids.
- **Limite de portée déclarée.** Un succès dira que la méthode fonctionne quand le monde a cette structure ; il ne dira pas qu'elle fonctionne sur le terrain. Le passage au réel est une étape distincte.

## 6. Coût

Un monde demande plusieurs tours (ordre de 10 à 30 appels de modèle selon le système). Au tarif mesuré au palier 1 (environ 2 000 jetons de sortie par appel, raisonnement compris), 100 mondes pour quatre systèmes à modèle représentent de l'ordre de 8 000 appels, soit environ 70 à 100 $ au tarif indicatif. La calibration par les références en code ne coûte rien. Le pilote sera chiffré et soumis à validation avant le principal.

## 7. Questions ouvertes pour la critique

1. **Domaine abstrait ou concret ?** Concret : résultats lisibles, mais le modèle peut s'appuyer sur ses connaissances générales plutôt que sur la méthode. Abstrait : plus propre, moins parlant.
2. **La forme « OU de ET » est-elle assez riche ?** Elle rend le chemin critique calculable, mais ignore les effets continus et les rétroactions.
3. **Comment rendre l'obstacle caché découvrable sans le rendre évident ?** Force du signal, bruit des mesures.
4. **Comment définir la conversion d'une occasion** sans la récompenser au point que l'exploration systématique devienne la meilleure stratégie ?
5. **Faut-il un bras « T1 avec consignes »** (les principes de la boucle donnés en texte au modèle libre) pour séparer architecture et consigne, comme le comité l'a demandé ?
6. **Taille** : combien de mondes et de familles, à fixer par simulation avec les références en code.
