# Bet, Proof, Memory

Un protocole ouvert pour confronter les prévisions, humaines et artificielles, aux issues documentées. Nom d'usage en français : le juge du réel.

La boucle tient en trois mots :
- **Bet** : une prévision est une probabilité figée avant le verdict, un pari au sens où de Finetti définissait la probabilité ;
- **Proof** : le verdict vient des issues documentées selon une procédure nommée, jamais d'un avis ;
- **Memory** : rien n'est supprimé ; ce qui a tenu et ce qui a échoué restent en registre, datés et attribués.

Ce dépôt tient deux rôles :
1. **Registre public horodaté** (`registre/`) : l'empreinte SHA-256 de chaque document de protocole, de chaque liste de candidats et de chaque instantané de données est publiée ici, par commit daté, AVANT tout accès aux issues concernées. Toute modification après coup devient détectable.
2. **Outils du protocole** : chaque outil sert une règle du protocole, et aucun autre.

## Contenu

| Chemin | Rôle |
|---|---|
| `protocole/q1-v1.5.md` | Protocole de la question 1 (défaillance à 548 jours), version en vigueur |
| `protocole/q1-v1.4.md`, `q1-v1.3.md`, `q1-v1.2.md`, `q1-v1.1.md` | Versions précédentes, conservées ; chaque amendement est motivé dans le journal de la version suivante |
| `registre/empreintes.md` | Empreintes datées des documents et des rapports |
| `p0/p0_faisabilite.py` | P0 : schémas et métadonnées des sources |
| `p0/p0_jointure.py` | P0 (v1.2) : part des bilans qui retrouvent leur avis de dépôt au BODACC, par année de clôture |
| `p0/p0_remplissage.py` | P0 (v1.2) : remplissage de chaque champ des ratios par niveau de confidentialité (comptages seuls) |
| `p0/p0_sources.py` | P0 (v1.3) : couverture de Sirene et des bilans détaillés de Signaux Faibles |
| `p0/p0_structure.py` | P0 (v1.4) : noms des clés de la liasse par type de bilan, nombre de bilans par année de clôture |
| `ingestion/extraire.py` | Phase 5, étape 1 : instantanés figés des sources (ratios, BODACC sous garde du scellé, Sirene, totaux de bilan), avec manifeste et empreintes |
| `ingestion/construire.py` | Phase 5, étape 2 : cas de l'espace de développement (origines 2008 à 2020), variables de l'annexe A, issues, couverture par origine |
| `tests/` | Tests, sans accès réseau extérieur |

## Exécuter P0

Sur une machine qui a accès à data.gouv.fr, data.economie.gouv.fr et opendatasoft.com, depuis le dossier personnel (jamais depuis le dossier d'une autre application) :

```bash
cd ~
git clone https://github.com/Blueprint-Master/bet-proof-memory.git && cd bet-proof-memory
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 p0/p0_faisabilite.py
python3 p0/p0_jointure.py
```

Le script lit le pied du parquet des bilans détaillés par requêtes HTTP Range (quelques centaines de kilo-octets sur 2,6 Go), puis les métadonnées des API Opendatasoft. Il n'interroge aucune issue. Il écrit un rapport JSON daté et affiche son empreinte SHA-256, à reporter dans `registre/empreintes.md`.

`p0_jointure.py` ne lit que des clés : (SIREN, date de clôture, confidentialité) côté bilans, (SIREN, date de clôture, date de parution) côté avis de dépôt des comptes du BODACC (famille `dpc`). Aucun montant, aucune annonce de procédure collective.

## Ce que ce dépôt ne contient pas

Aucune donnée, aucune issue, aucun résultat avant sa publication prévue par le protocole.
