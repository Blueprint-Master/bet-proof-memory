# Boucle de supervision, palier 1 : résultats du pilote

*Pilote exécuté le 22/10/2026 de 16 h 57 à 18 h 15 sur bpm-prod ; analyse avec la graine 816420796, publiée avant la fin du pilote. Hors verdict.*

## 1. Résultat

**T1 et B rendent exactement les décisions de D sur les 60 cas** (50 éligibles, 5 pièges avant t0, 5 pièges après t0). Aucune violation pour l'un comme pour l'autre ; aucune abstention injustifiée ; les cinq pièges en liquidation à t0 ont reçu l'abstention, les cinq pièges liquidés après t0 une décision. Δ = 0 sur les 50 cas éligibles.

| Mesure | D | B | T1 | T0 |
|---|---|---|---|---|
| M1, coût réalisé pondéré | 0,00775 | 0,00775 | 0,00775 | 0,01230 |
| M2, cas avec violation | 0 | 0 | 0 | 59 sur 60 (e : 54, b : 5, c : 5) |
| M3, abstentions justifiées / injustifiées | 5 / 0 | 5 / 0 | 5 / 0 | 0 / 1 |
| M5, écart à D | 0 % | 0 % | 0 % | 60 % (48 % pondéré) |
| Appels de modèle | 0 | 120 | 120 | 60 |
| Jetons d'entrée / de sortie | 0 | 86 853 / 108 938 | 81 341 / 90 424 | 15 838 / 146 238 |

Constats de comportement :
- **T1** a appelé exactement trois outils par cas (état, prévision, seuil, tous à t0), jamais les ratios ni les annonces, jamais une date postérieure à t0.
- **B** a fait deux appels de modèle par cas : aucune proposition n'a été contredite par la vérification, aucun retour, aucune abstention de la machine hors pièges.
- **T0**, sans information, s'écarte de D sur 60 % des cas ; l'apport des outils est mesurable en secondaire : M1(T0) − M1(T1) = 0,0046, p = 0,028 (permutation).

## 2. Lecture

C'est la première des deux issues annoncées avant le pilote (configurations, section 2) : sur cette tâche, le modèle en usage libre applique déjà les règles sans dérive. La discipline ne coûte rien (zéro abstention injustifiée) et n'apporte rien de mesurable. **Effet plafond** : la tâche, réduite par construction à lire l'état et comparer deux nombres, ne laisse pas au modèle la place de se tromper.

Ce que le pilote n'établit pas : que la dérive de T1 soit nulle en population. Avec 0 écart sur 60 cas, la borne supérieure à 95 % du taux d'écart est d'environ 5 % (règle de trois : 3 / 60) ; sur 340 cas sans écart, elle descendrait à environ 0,9 %.

## 3. Puissance et coût

- Analyse de puissance : aucune différence entre T1 et B dans aucune strate ; la puissance n'est pas calculable. Règle fixée avant le pilote : le principal ne part à 300 cas qu'avec la validation du décideur, en déclarant que l'effet attendu est peut-être nul.
- Coût mesuré : 300 appels de modèle (essai à blanc compris), 184 032 jetons d'entrée et 345 600 de sortie, soit environ 1,7 $ au tarif indicatif de Mistral Large 4 (1,36 $ et 4,18 $ par million). Extrapolation au principal (340 cas) : environ 10 $ et 6 heures d'exécution.

## 4. Empreintes

Fichier d'exécutions complet 54c6bbc6… ; rapport 0a4e767d… (au registre). Le rapport prématuré 06c3af90… reste déclaré nul.
