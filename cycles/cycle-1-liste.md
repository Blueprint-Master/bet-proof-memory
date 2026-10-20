# Cycle 1 : liste figée des candidats (étape 3)

Figée le 20/10/2026, avant toute évaluation. Définitions : `cycle-1-propositions-brutes.md`, avec les précisions d'exécution de `cycle-1-verification.md`. Code de calcul : `mecanismes/cycle1.py` ; code d'évaluation : `evaluation/cycle.py` (empreintes au registre).

**35 candidats :**
- C1 à C12 ;
- G1 à G13 ;
- M1 à M8 ;
- M11 et M12.

M9 et M10 sont rejetés (motifs dans la vérification).

**Règle mécanique pour les données à confirmer.** Elle ne demande aucune décision :
- C9 et M4 ne sont calculables que si l'instantané des conciliations contient des annonces. Sinon, leurs colonnes sont entièrement manquantes : ils sont « non calculables » sur chaque pli et ne sont pas admis. G10 est alors calculé sur les seules procédures closes.
- G13 suit la même règle pour les séries Banque de France toutes branches par taille.

**Admission (P7).** Le candidat est évalué seul. Il est admis si, sur chacun des trois plis, il réduit la perte de P6 par rapport au témoin (estimation ponctuelle) et que l'assemblage n'est pas réduit au témoin. Tous les résultats sont publiés, admis ou non.
