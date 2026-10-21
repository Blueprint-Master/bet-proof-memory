# Boucle de supervision : audit de provenance temporelle du modèle de prévision dédié

Palier 1, outil de prévision servi à B, T1 et D pour les cas du 30/09/2020. Spécification : `methode/boucle-de-supervision.md` (note gelée le 21/10/2026), section 7.2. Code audité : `evaluation/modele_dedie.py` et ses dépendances. Rédigé le 22/10/2026, avant l'exécution sur les données.

**Question posée.** Pour chaque maillon de la chaîne qui produit la prévision d'un cas au 30/09/2020, quelle est la date de l'information la plus récente qu'il utilise ? Toute information postérieure à t0 est une fuite. Une fuite est soit éliminée, soit contrôlée à l'exécution, soit déclarée avec son sens et son ampleur probables.

**Légende des statuts.**
- **Par construction** : le code ne peut pas lire l'information interdite. La preuve est la ligne de code citée.
- **Contrôlé** : un contrôle automatique vérifie la propriété sur les données réelles à chaque exécution. Un échec arrête le calcul.
- **Résiduel** : une information postérieure à t0 peut entrer. La fuite est déclarée, et elle ne peut pas être éliminée sans changer le protocole.

## 1. Maillons

| N° | Maillon | Information utilisée | Date maximale | Statut | Preuve |
|---|---|---|---|---|---|
| A1 | Origine d'apprentissage | cas de l'origine 2018 seulement | 30/09/2018 | Contrôlé | contrôle « apprentissage limité à l'origine 2018 » ; `modele_dedie.py`, masque `origine == 2018` |
| A2 | Étiquettes d'apprentissage | jugements d'ouverture dans ]t0, t0 + 548 j] | 31/03/2020 | Contrôlé | contrôles « fenêtre d'issue close avant t0 cible » et « issues d'apprentissage toutes antérieures à t0 cible » |
| A3 | Bilans des cas (apprentissage et cible) | bilan le plus récent dont l'avis de dépôt est paru avant t0 (P2) | veille de t0 | Contrôlé | contrôles « avis de dépôt antérieurs à t0 » ; `construire.py`, règle P2 (`x[1] < t0`) |
| A4 | Variables de l'annexe A, hors intensité | dérivées des bilans de A3, de l'âge et du retard de dépôt | veille de t0 | Par construction | `construire.py`, calcul ligne par ligne à partir du bilan retenu |
| A5 | Intensité sectorielle (variable de R2) | séries de défaillances de la Banque de France, mois t0 − 3 et 60 mois antérieurs | juin 2020 pour la cible | **Résiduel** | voir R1 |
| A6 | Candidats du premier cycle | annonces et avis parus avant t0, bilans connus à t0, périodes Sirene débutant avant t0, séries de la Banque de France jusqu'à t0 − 3 mois | veille de t0 | Par construction, sauf R1 et R2 | `mecanismes/cycle1.py` : `connus` (`b[1] < t0`), `depots_connus` (`p < t0`), `dans` (`debut <= d < t0`), `changements_sirene` (`debut <= b[0] < t0`) |
| A7 | Pénalité de R2 | validation croisée en 5 parts par SIREN, interne à 2018 | 31/03/2020 | Par construction | `rf.R2(HORIZON).ajuster(app, y_app)`, sur l'apprentissage 2018 seul |
| A8 | Témoin recalibré | ajusté sur l'apprentissage du pli | 31/03/2020 | Par construction | `cr.Temoin().ajuster` sur les cas hors pli |
| A9 | Admission des candidats | 5 plis par division NAF, 20 répartitions, tous internes à 2018 | 31/03/2020 | Par construction | `repartition`, `preparer` et `evaluer_candidat_plis` ne reçoivent que l'apprentissage 2018 |
| A10 | Modèle final | R2, témoin et assemblage ajustés sur toute l'origine 2018 | 31/03/2020 | Par construction | bloc « modèle final sur toute l'origine 2018 » |
| A11 | Prévisions de la cible | variables des cas 2020 à t0, modèle de A10 | veille du 30/09/2020 | Par construction, sauf R1 et R2 | aucune issue de 2020 n'est lue ; contrôle « cible limitée à l'origine 2020 » |
| A12 | Seuils de décision et coût de P6 | LGD estimée sur des annonces parues jusqu'au 30/09/2022 ; prime et part indemnisée tirées de la fiche 604 de la Banque de France (2021) | 30/09/2022 | **Résiduel** (paramètre du scénario) | voir R3 |
| A13 | Population des cas | exclusion des sociétés dont l'ouverture est datée avant t0 mais publiée après | jusqu'au 30/09/2022 | **Résiduel** (sélection des cas) | voir R4 |
| A14 | Spécification de R2 et des règles | annexe A, grille de pénalité, contrôle de séparation, choix de garder l'intensité | décidée en octobre 2026 | **Résiduel** (conception) | voir R5 |
| A15 | Liste des 35 candidats | proposée par des modèles de langage en octobre 2026 | octobre 2026 | **Résiduel** (conception) | voir R6 |

## 2. Fuites résiduelles déclarées

**R1. Millésime des séries de la Banque de France (A5, A6).** Les séries ont été extraites en 2026. Leurs valeurs sont celles d'aujourd'hui, après révisions, et non celles qui étaient publiées au 30/09/2020. De plus, je ne sais pas si la valeur de juin 2020 était déjà publiée à cette date.
- **Sens probable :** léger avantage pour toute variable qui utilise ces séries (l'intensité sectorielle et les candidats construits sur la Banque de France). B, T1 et D reçoivent la même prévision, donc aucun système n'est favorisé.
- **Ampleur :** inconnue. On peut la mesurer en réajustant R2 sans l'intensité, ce qui est prévu comme contrôle secondaire.

**R2. Historique Sirene extrait en 2026 (A6).** Les périodes de l'historique peuvent avoir été corrigées après coup, par exemple un changement de code NAF saisi avec une date d'effet antérieure.
- **Sens probable :** faible, et sans effet sur la comparaison entre systèmes. Sont concernés les candidats qui comptent des changements de NAF ou de catégorie juridique.

**R3. LGD et paramètres du scénario (A12).** Ce sont des paramètres de la décision, pas de l'information sur le cas. Ils sont fournis à l'identique à B, T1 et D (note, section 7.2). Le verdict est aussi publié sous une LGD de 0,70.

**R4. Sélection de la population (A13).** Une société dont l'ouverture de procédure est datée avant t0 mais publiée après t0 est écartée : elle était en réalité inéligible, mais on ne pouvait pas le savoir à t0.
- Cette règle utilise une information postérieure à t0 pour choisir les cas, et non pour les prévoir. Elle s'applique à l'apprentissage comme à la cible.
- Pour le palier 1, les pièges sont tirés à part (section 7.2 de la note) : cette exclusion ne les touche pas.

**R5. Spécification arrêtée après avoir vu des résultats sur 2020 (A14).** Plusieurs révisions du protocole (pénalité nulle ajoutée à la grille, contrôle de séparation, maintien de l'intensité sectorielle) ont été décidées en octobre 2026. Ces décisions ont été prises après lecture d'évaluations dont certains plis testaient l'origine 2020.
- C'est une fuite de conception : le modèle n'a pas vu les issues de 2020, mais ses concepteurs, si.
- **Atténuation :** aucune de ces décisions n'a été prise pour améliorer la performance sur 2020. L'intensité sectorielle a été gardée alors qu'elle dégradait les plis testant 2020.
- **Ampleur :** non mesurable.

**R6. Liste des candidats proposée en 2026 (A15).** Les modèles qui ont proposé les 35 candidats connaissent l'histoire économique de 2020 à 2022.
- **Contrôle fait le 22/10/2026 :** aucune définition de candidat ne mentionne un événement postérieur à 2018. Recherche faite sur « covid », « PGE », « prêt garanti », « confinement », « pandémie » et « 2020 » dans `cycles/cycle-1-liste.md` et `cycles/cycle-1-propositions-brutes.md` : aucun résultat.
- **Garde-fou :** l'admission se fait sur 2018 seulement, donc un candidat inspiré par 2020 n'entre que s'il prédisait déjà en 2018.

## 3. Ce que l'audit ne couvre pas

Cet audit couvre uniquement l'outil de prévision. Les autres outils du palier 1 seront audités au moment de leur construction, avec la même grille :
- les ratios à une date ;
- les annonces codées ;
- l'état administratif ;
- les seuils.

## 4. Exécution

Sur bpm-prod, depuis le dossier du dépôt :

```bash
git pull
python3 -m unittest discover -s tests
python3 evaluation/modele_dedie.py --lgd ~/bpm-donnees/lgd-20261020-165221.json --processus 2 --chrono
```

Le mode `--chrono` ajuste R2 et prépare une répartition, puis évalue un candidat. Il affiche ensuite la durée estimée du calcul complet. Le calcul complet n'est lancé qu'après validation de cette durée, puisque le serveur porte aussi la production :

```bash
nohup python3 evaluation/modele_dedie.py --lgd ~/bpm-donnees/lgd-20261020-165221.json --processus 2 > ~/bpm-donnees/modele-dedie.log 2>&1 &
```

Le rapport `modele-dedie-<date>.json` et le fichier `prevision-dediee-2020-<date>.parquet` sont inscrits au registre avec leurs empreintes. Un contrôle de provenance en échec arrête le calcul, avec le code de sortie 2.
