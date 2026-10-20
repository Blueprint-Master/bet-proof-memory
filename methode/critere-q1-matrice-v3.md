# Critère de jugement de la question 1 : matrice des critiques (thèse v3)

Critiques à l'aveugle reçues le 20/10/2026 :
- ChatGPT (gpt-6-astra), 15:21 UTC ;
- Gemini (gemini-4-argon), 15:22 UTC.

Mistral a dépassé le délai de 230 s : troisième échec consécutif dans ce cycle, son absence est déclarée. Ces avis ne sont pas vérifiés. Chaque point est confronté au calcul ou à une source, sans moyenne.

## 1. Accords vérifiés

- **Algèbre de p_t = π T / LGD juste**, sous les hypothèses stipulées (les deux critiques ; calcul de Claude).
- **R primaire ≈ [0,96 % ; 6,8 %]** et R de sensibilité ≈ [19,2 % ; 135,8 %] avant retrait des seuils ≥ 1. Calculs recoupés par les deux critiques.
- **Statut des corrections B :**
  - B1 est sans objet : la marge sort de la décision ;
  - B3, B4 et B5 sont correctement intégrés ;
  - B2 reste ouvert (voir 2).

## 2. Points bloquants établis et retenus

| N° | Point | Relevé par | Vérification | Correction |
|---|---|---|---|---|
| C1 | **Quotité garantie ignorée.** Avec une perte résiduelle sous couverture, le seuil change | ChatGPT (forme générale), Gemini (chiffres d'exemple non sourcés, non retenus) | **Source** : Banque de France, fiche 604 (06/2021) : « une franchise de 10 % à 30 % à la charge de l'assuré, soit une indemnisation entre 70 % et 90 % du montant de la créance ». Calcul : couvrir coûte π T + (1 − q) p LGD, conserver coûte p LGD ; on couvre si **p > π T / (q LGD)** | Paramètre q ∈ {0,7 ; 0,9}, sourcé |
| C2 | **B2 non résolu.** À horizon fini, les incidences cumulées d'Aalen-Johansen ne somment pas à 1 ; renormaliser revient à conditionner sur les issues déjà observées | ChatGPT | Exact | Spécifier l'origine (jugement d'ouverture), l'horizon (le plus long observable sous la garde du scellé), la masse des procédures encore ouvertes. Estimation ponctuelle : masse ouverte répartie au prorata. Bornes : masse ouverte entièrement en liquidation, ou entièrement en continuation |
| C3 | **Contradiction entre B2 et R primaire** : B2 produit une LGD ponctuelle, alors que R était bornée par les LGD extrêmes | Gemini | Exact | R n'est plus une enveloppe : voir C4. Les bornes de C2 servent de sensibilité |
| C4 | **La moyenne uniforme sur l'enveloppe ne correspond à aucune distribution des paramètres métier.** Le coût d'erreur à un seuil est proportionnel à LGD | Gemini | Exact au regard de la représentation de Schervish : dans cette décision, la perte élémentaire au seuil p_t a l'échelle q × LGD. La perte espérée sous scénarios est le **mélange des pertes élémentaires pondérées par leur échelle et par le poids des scénarios**. Ce mélange est exactement le coût réalisé moyen, en euros par euro d'encours. Il exige un modèle monétaire explicite (correction E2) : ce modèle existe désormais | S0 et S+ partagent la même perte : le coût réalisé moyen sous la grille de scénarios. Poids déclarés : D et q équiprobables sur leurs valeurs (aucune source ne les pondère) ; LGD ponctuelle |
| C5 | **Définitions manquantes pour reproduire S0 :** échelle du « R2 figé » (logit du hasard ou de la probabilité cumulée), sélection de λ, sociétés présentes dans les deux cohortes au regard des grappes | ChatGPT | Exact | À écrire dans le texte de l'amendement : assemblage au niveau du hasard par intervalle ; λ par validation croisée en 5 parts groupées par SIREN sur le développement, comme R2 ; une société reste dans la grappe de sa division NAF à l'origine 2022 (ou 2023 si elle n'est que dans cette cohorte), et toutes les sociétés d'une grappe sont tirées ensemble pour les deux cohortes |

**R primaire après C1** (π = 0,1 %, q ∈ {0,7 ; 0,9}, D ∈ {30, 45, 60}, LGD aux deux extrêmes, pour mémoire) : de 1,07 % à 9,70 %. Une fois la LGD estimée, il ne reste que six seuils (3 D × 2 q).

## 3. Points non bloquants retenus

- **La prime porte sur le chiffre d'affaires effectivement réalisé**, qui s'arrête à la défaillance (ChatGPT). Compter π T sur tout l'horizon surestime le coût de couverture d'au plus p × π T. Le seuil exact est p_t = π T / (q LGD + f π T), où f ≤ 1 est la fraction d'horizon perdue. L'erreur relative sur p_t est donc au plus p_t lui-même, soit moins de 10 % sur la grille. C'est une approximation déclarée, en faveur de « conserver ».
- **Portée** (ChatGPT) : π = 0,1 % est un scénario préspécifié, pas une valeur représentative du marché. Le succès primaire vaut pour ce décideur, pas comme supériorité économique générale.
- **Le bootstrap NAF suppose une indépendance entre grappes** (ChatGPT). C'est une hypothèse déclarée ; les chocs communs à tous les secteurs ne sont pas couverts. Cette limite est déjà inscrite dans la portée (chemin macroéconomique réalisé).

## 4. Point discuté : π = 0,1 % est-il un choix fait après coup ? (Gemini, bloquant)

**Objection.** Choisir la borne basse ramène « miraculeusement » R autour du taux de base. Ce serait une ingénierie à rebours du critère. De plus, un assureur ne couvre pas un acheteur risqué au tarif plancher (sélection adverse).

**Faits :**
- **Antériorité.** Rémi a donné le chiffre de 1/1000 pour une PME dont les clients sont la grande distribution **avant** la thèse v2, qui le cite. La dégénérescence de la région de la v2 n'a été établie qu'ensuite (matrice v2). Le chiffre précède donc le constat. En revanche, le choix de la forme de décision (O2) a suivi ce constat, ce que la matrice v2 consigne.
- **Sélection adverse.** La fiche 604 établit que la prime est « personnalisée » et que l'assureur rend, acheteur par acheteur, un avis « accepté », « montant maximum » ou « refus ». La décision par acheteur existe donc bien, prise par l'assureur. Elle a la même forme : l'assureur accepte si l'indemnité espérée p q LGD est inférieure à la prime π T. Le seuil est identique. L'objection confirme le modèle au lieu de l'invalider.
- **Gemini parle d'un « taux médian (ex. 0,5 %) »** : ce chiffre n'est pas sourcé, il n'est pas retenu.

**Conclusion.** Le scénario central reste π = 0,1 %, au motif qu'il est la spécification du décideur. π = 2 % est publié sans valeur de verdict. La rétroactivité partielle (forme de décision choisie après le constat) est consignée, pas effacée.

## 5. Ce qui en découle pour l'amendement v1.7

1. **Seuil de décision.** p_t = π T / (q LGD), et p = 1 − ∏(1 − h_k).
2. **Grille de scénarios.** π = 0,1 % ; D ∈ {30, 45, 60} ; q ∈ {0,7 ; 0,9} ; poids égaux. LGD : estimation ponctuelle par Aalen-Johansen, masse ouverte au prorata ; ses bornes servent de sensibilité.
3. **Perte unique.** Coût réalisé moyen, en euros par euro d'encours, moyenné sur la grille. Elle sert au verdict S0 (inférence) et au gain S+ (seuil de rentabilité).
4. **Sensibilités publiées sans valeur de verdict :**
   - π = 2 % ;
   - bornes de la LGD ;
   - R2 non recalibré ;
   - critère de la v1.6 ;
   - décomposition MCB − DSC + UNC.
5. **Définitions de C5** écrites dans le texte.
6. **Le prochain tour de critique porte sur le texte même de l'amendement**, et non sur une thèse v4, pour éviter une boucle de révisions sans fin.
