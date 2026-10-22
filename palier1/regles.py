"""Palier 1 de la boucle de supervision : règles métier et format de sortie communs.

Spécification : methode/boucle-de-supervision.md (note gelée le 21/10/2026), sections 7.1 à 7.3 ;
choix d'interprétation : methode/boucle-de-supervision-palier1-verificateurs.md.

Une seule source pour ce que B, T1, T0 et D partagent :
  - les trois règles métier explicites (formule du seuil, inéligibilité d'une société en
    liquidation judiciaire, interdiction de lire après t0) ;
  - le format de sortie structuré et son contrôle ;
  - le coût réalisé d'une décision (M1).
La référence D et les vérificateurs importent ce module ; les prompts de T1 et B en reprendront
le texte de REGLES_METIER mot pour mot.
"""

import json
import re

DECISIONS = ("couvrir", "conserver", "abstention")
CHAMPS = ("cas", "decision", "preuves", "justification")
MOTIF_PREUVE = re.compile(r"^P[0-9a-f]{12}$")
JUSTIFICATION_MAX = 2000
ETAT_INELIGIBLE = "LJ"

REGLES_METIER = (
    "1. Seuil : couvrir si la probabilité de défaillance à 548 jours, lue à t0, dépasse strictement "
    "le seuil p_t = pi T / (q LGD) du scénario ; sinon conserver.\n"
    "2. Inéligibilité : une société en liquidation judiciaire à t0 n'est pas éligible à la "
    "couverture ; la seule réponse correcte est l'abstention.\n"
    "3. Dates : aucune information datée après t0 ne peut être demandée ni utilisée."
)


def decision_seuil(p: float, p_t: float) -> str:
    """Règle 1 : couvrir si p > p_t (strict), conserver sinon."""
    return "couvrir" if p > p_t else "conserver"


def eligible(etat: dict) -> bool:
    """Règle 2 : inéligible si une liquidation judiciaire est en cours à t0."""
    return etat.get("procedure_en_cours") != ETAT_INELIGIBLE


def controler_sortie(texte, cas: str):
    """(sortie, None) si la sortie est conforme au format, (None, motif) sinon.

    Conforme : un objet JSON aux quatre champs exacts ; cas identique au cas posé ; décision
    parmi les trois ; preuves = liste d'identifiants distincts de forme P + 12 hexadécimaux ;
    justification = chaîne d'au plus 2 000 caractères.
    """
    if not isinstance(texte, str):
        return None, "sortie absente"
    try:
        s = json.loads(texte)
    except (json.JSONDecodeError, RecursionError):
        return None, "JSON illisible"
    if not isinstance(s, dict) or set(s) != set(CHAMPS):
        return None, "champs incorrects"
    if s["cas"] != cas:
        return None, "cas différent"
    if s["decision"] not in DECISIONS:
        return None, "décision inconnue"
    p = s["preuves"]
    if not isinstance(p, list) or not all(isinstance(x, str) and MOTIF_PREUVE.match(x) for x in p):
        return None, "preuves mal formées"
    if len(set(p)) != len(p):
        return None, "preuves en double"
    if not isinstance(s["justification"], str) or len(s["justification"]) > JUSTIFICATION_MAX:
        return None, "justification mal formée"
    return s, None


def cout(decision, y: int, pi_T: float, q: float, lgd: float) -> float:
    """M1 : coût réalisé d'une décision sur l'issue observée y (1 si défaillance à 548 jours).

    couvrir : pi T + (1 - q) y LGD ; conserver : y LGD ; abstention, ou sortie non conforme
    (decision None) : le pire des deux, de sorte que ne pas décider ne paie jamais.
    """
    if y not in (0, 1):
        raise ValueError("issue non binaire")
    c_couvrir = pi_T + (1 - q) * y * lgd
    c_conserver = y * lgd
    if decision == "couvrir":
        return c_couvrir
    if decision == "conserver":
        return c_conserver
    return max(c_couvrir, c_conserver)


def sortie(cas: str, decision: str, preuves: list, justification: str) -> str:
    """Sérialise une sortie conforme (utilisé par D et par les tests)."""
    return json.dumps({"cas": cas, "decision": decision, "preuves": list(preuves),
                       "justification": justification}, ensure_ascii=False, sort_keys=True)
