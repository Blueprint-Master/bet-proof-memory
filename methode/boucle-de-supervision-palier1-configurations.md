# Boucle de supervision, palier 1 : configurations de T0, T1 et B

*Rédigé le 22/10/2026, avant tout appel de modèle. Le choix du modèle et le budget restent à valider ; les configurations sont figées à leur empreinte, sauf le nom du modèle, qui sera publié avant le pilote.*

Code : `palier1/systemes.py` (T0, T1, machine de B), `palier1/modeles.py` (adaptateurs), `palier1/executer.py` (exécution et reprise) ; tests : `tests/test_palier1_systemes.py` (18 tests, modèle factice scripté).

## 1. Choix de configuration

| N° | Point | Choix | Motif |
|---|---|---|---|
| C1 | Protocole d'échange | Texte JSON commun : une réponse qui porte la clé `appels` demande des outils ; toute autre réponse est la sortie. Pas d'appel de fonction propre à un fournisseur | Identique pour T1 et B, indépendant du fournisseur |
| C2 | Information | Identifiant opaque, t0, scénario ; T1 et B ont les cinq outils ; T0 n'en a aucun | Section 7.2 |
| C3 | Prompt système | Le même mot pour mot pour T1 et B (contexte, trois règles métier de `regles.py`, description des outils, format de sortie) ; T0 sans la description des outils. Égalité vérifiée par un test | « Mêmes règles, mêmes informations, même format » |
| C4 | Règle (e) | Les prompts ne disent pas quelles preuves sont « nécessaires » : la note ne range pas cette exigence parmi les règles métier. Un T1 qui décide sans lire l'état à t0 commet (e) | Ne pas ajouter de règle que la note n'a pas listée |
| C5 | Plafond commun | T1 et B : 6 appels de modèle et 40 000 jetons (entrée et sortie) par cas ; T0 : 1 appel. Sortie limitée à 1 500 jetons par appel ; température 0 ; version épinglée par son nom exact | Estimation : T1 2 à 3 appels, B 2 appels plus 2 retours au plus |
| C6 | T1 | Boucle libre : chaque demande d'outil passe par le registre et son journal, refus compris ; plafond atteint sans sortie : sortie nulle (I2) | Usage libre du même modèle |
| C7 | B, états | S0, S1, S2 fixés par les règles (l'arbre n'est pas testé à ce palier, section 7.1) ; S3 : le modèle propose ses appels, la machine bloque avant l'outil toute demande hors mandat (outil inconnu, date absente, mal formée ou postérieure à t0) ; S11 : pour chaque champ structurant inconnu (éligibilité, p, p_t), la machine lance l'appel canonique ; ABSTENTION si un champ reste inconnu ; S4, S5, S8 : le modèle propose la sortie, la machine contrôle le format, la contrainte dure et la règle du seuil ; en cas de contradiction, retour avec son motif, deux fois au plus, puis ABSTENTION | Section 5, réduite à ce que le palier exerce |
| C8 | B, sortie | Composée par le code : la décision proposée et vérifiée, les preuves des champs vérifiés, la justification du modèle. La machine ne substitue jamais sa propre décision à celle du modèle | Règle 1 : rien n'est exécuté sur un champ proposé ; la machine vérifie, elle ne décide pas |
| C9 | Exécution | Cas triés par identifiant opaque ; pour chaque cas, D, T0, T1, B ; une ligne par exécution, écrite dès la fin ; reprise sans rejouer ; arrêt avant le plafond total d'appels ; du fichier des cas, seul le scénario est lu | Clé d'idempotence ; l'issue ne peut pas fuiter vers un système |
| C10 | Adaptateurs | Interface compatible OpenAI (Mistral, OpenAI, xAI, Gemini) et interface Anthropic ; messages consécutifs d'un même rôle fusionnés ; reprises sur 429 et 5xx ; clé dans une variable d'environnement | Aucune dépendance ajoutée ; aucune clé dans le dépôt |

## 2. Conséquence à connaître avant de lancer : ce que le verdict mesurera

Par construction (C7, C8), B ne peut rendre que la décision de D ou l'abstention. Les violations (a), (c), (d) et (e) lui sont impossibles ; sur un piège avant t0, l'abstention lui est imposée par la contrainte dure. Il ne lui reste que deux façons de perdre : s'abstenir à tort (désaccord persistant du modèle après deux retours, sur un cas éligible ou un piège après t0), et consommer plus d'appels.

La note l'annonçait pour (d) et (e) (section 7.1, « ce qui est acquis par construction ») ; le code l'étend à (a) et (c), puisque la sortie de B est composée par la machine. Le verdict compare donc, en substance, **la dérive libre de T1 par rapport à D** avec **le taux d'abstention que la discipline coûte à B**. Deux lectures en découlent :

- si le modèle suit bien les règles en usage libre, T1 ≈ D, Δ ≈ 0, et le verdict est indécis : la discipline n'apporte rien sur une tâche que le modèle sait déjà faire ;
- si T1 dérive (preuve manquante, lecture après t0, seuil mal appliqué, abstention de confort), Δ est positif tant que les abstentions de B restent sous 5 %.

C'est exactement la portée revendiquée par la note (« un modèle sous discipline s'écarte moins du code et viole moins de règles que le même modèle en usage libre »). Ce n'est pas une preuve que la boucle décide mieux qu'un code, et elle ne sera pas présentée comme telle.

## 3. Volume estimé

Mesuré sur un dossier de taille réelle avec le modèle factice (caractères des messages envoyés), converti à raison d'environ 3,2 caractères par jeton pour un texte français mêlé de JSON :

| Système | Appels par cas | Jetons d'entrée par cas | Jetons de sortie par cas |
|---|---|---|---|
| T0 | 1 | environ 300 | environ 200 |
| T1 | 2 (5 outils lus) | environ 1 700 | environ 400 |
| B | 2 (sans retour) à 4 | environ 1 700 à 4 300 | environ 400 à 800 |

Soit environ 4 000 jetons d'entrée et 1 000 de sortie par cas sans retour. Avec une marge de 3 pour les comportements réels (plus de tours, justifications longues) : **pilote (60 cas) ≤ 0,75 M d'entrée et 0,2 M de sortie ; principal (340 cas) ≤ 4,2 M d'entrée et 1 M de sortie**. Le coût réel sera mesuré au pilote (M4), et le budget du principal soumis à validation.

## 4. Modèle retenu (22/10/2026, avant le pilote)

- **Modèle : `mistral-large-4-0`**, par l'interface `https://api.mistral.ai/v1/chat/completions`, température 0, sortie limitée à 1 500 jetons. Parmi les identifiants listés sur le compte le 22/10/2026 (`mistral-large-2512`, `mistral-large-4`, `mistral-large-4-0`, `mistral-large-latest`), c'est le plus précis ; les alias `mistral-large-4` et `mistral-large-latest` peuvent changer de cible et sont écartés. Mistral ne garantit pas par écrit qu'un identifiant versionné reste figé : le nom du modèle effectivement servi est relevé à chaque appel (`modeles_servis` dans chaque exécution), et tout changement en cours de route sera publié.
- **Clé** : celle du serveur Blueprint (`~/blueprint-mcp-server/.env`), chargée dans la session d'exécution seulement, jamais écrite ailleurs.
- **Budget du pilote** : plafond total de 600 appels de modèle (60 cas : T0 1 appel, T1 et B 6 au plus chacun, soit 780 au pire ; l'exécution s'arrête avant 600 et reprend sur décision). Estimation haute du coût : environ 2 $ au tarif indicatif, à confirmer sur la console Mistral.
- **Essai à blanc** : les 10 premiers appels servent de contrôle de bout en bout. Sans anomalie, ils sont conservés dans le pilote ; s'ils révèlent un défaut du code, le fichier d'exécutions est supprimé, le défaut corrigé et publié, et le pilote relancé en entier.

## 5. Constat du premier essai (22/10/2026) et ajustements

Le premier appel a été refusé par l'interface (erreur 400, sans facturation). Deux faits établis par une requête minimale :

- `mistral-large-4-0` exige `top_p = 1` avec une température 0 (échantillonnage glouton) : le paramètre est ajouté. La configuration reste déterministe au sens du fournisseur.
- **`mistral-large-4-0` est un modèle à raisonnement** : sa réponse contient des blocs « thinking » suivis d'un bloc « text », et les jetons de raisonnement sont facturés comme jetons de sortie (71 sur 75 dans l'essai). Seul le bloc « text » est lu comme réponse ; le raisonnement n'est ni renvoyé au modèle dans les tours suivants ni conservé. Le nombre de jetons de raisonnement et les réponses tronquées sont relevés par exécution. La limite de sortie par appel passe de 1 500 à 4 000 jetons pour ne pas tronquer le raisonnement ; le plafond de 40 000 jetons par cas est inchangé et commun à T1 et B.

Conséquence sur le coût : la sortie, plus chère, sera plus volumineuse que prévu. Le plafond total de 600 appels du pilote borne la dépense ; le coût réel sera mesuré et publié avant le principal.

## 6. Essai à blanc (22/10/2026) et graine d'analyse du pilote

Essai de 10 appels : 5 exécutions sur deux cas, toutes conformes ; aucune requête bloquée, aucune réponse tronquée ; modèle servi : `mistral-large-4-0` à chaque appel. Arrêt correct avant le plafond (le cas suivant de T1 pouvait demander 6 appels). Aucun défaut de code : l'essai est conservé dans le pilote. Le raisonnement domine la consommation : 1 150 à 2 216 jetons de raisonnement par appel, soit environ 5 000 jetons de sortie et 3 000 d'entrée par cas pour les trois systèmes.

**Graine de l'analyse du pilote (permutation, BCa) : 816420796**, tirée le 22/10/2026 avant la fin du pilote.
