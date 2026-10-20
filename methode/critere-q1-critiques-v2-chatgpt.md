# Thèse v2 : critique de ChatGPT (gpt-6-astra), reçue le 20/10/2026 à 14:59 UTC

Statut : critique à l'aveugle. Celles de Gemini et de Mistral n'ont pas pu être obtenues : la connexion au serveur s'est perdue, et un appel a dépassé le délai. Elles seront demandées avec le même texte, sans leur montrer celle-ci.

## Points bloquants signalés (non encore vérifiés par Claude)

- **B1. Convention de la marge.** Le résultat m − LGD n'est cohérent que si L est la valeur facturée et m la marge rapportée au chiffre d'affaires. Il faut fixer cette convention.
- **B2. LGD pondérée par l'issue finale.** L'estimateur doit traiter les procédures non closes ; « censure déclarée » ne suffit pas.
- **B3. Seuils extrêmes.** p_t ≥ 1 quand LGD ≤ m : il faut un support de R dans [0, 1] et une règle pour les décisions constantes.
- **B4. Annualisation du seuil de rentabilité.** g porte sur 548 jours et c est annuel : L_min = c × (548 / 365) / g, sous la convention d'un encours constant.
- **B5. Probabilité utilisée.** p doit être la probabilité cumulée à 548 jours, et non le hasard d'un intervalle.

## Points non bloquants

- **Algèbre de p_t.** Vérifiée juste sous les gains stipulés.
- **Portée de S0.** S0 devient un verdict de performance décisionnelle locale, pas de signal général.
- **Grappes NAF.** Le bootstrap par grappes NAF n'est pas automatiquement valide : la méthode d'intervalle doit être préspécifiée.
- **Proxy et assurance.**
  - Le total de bilan est un proxy de l'exposition.
  - La prime d'assurance-crédit rémunère un transfert de risque, pas une information.
- **Désaccord S0 / S+.** Il est rendu explicite (succès primaire = S0, pertinence sans verdict binaire), mais non résolu par consensus.
