"""Palier 1 de la boucle de supervision : référence déterministe D.

Spécification : methode/boucle-de-supervision.md, section 7.1. D applique les règles métier de
palier1/regles.py à l'état administratif et à la prévision lus à t0 par les mêmes outils que B
et T1, sans modèle de langage. Elle rend une sortie au format commun et un journal propre à
chaque exécution (un registre neuf par cas, règle d'usage de l'audit, section 4).

Ordre, figé :
  1. etat(cas, t0) ; refus -> abstention ; liquidation judiciaire en cours -> abstention ;
  2. prevision(cas, t0) ; refus -> abstention ;
  3. seuils(scenario) ; refus -> abstention ;
  4. couvrir si p > p_t, conserver sinon ; preuves citées : état, prévision, seuil.
D n'entre pas dans le verdict ; elle donne le plafond de la tâche (M1(D)) et l'étalon de M5.
"""

import time

import outils as ou
import regles as rg


def decider(dossiers: dict, lgd: float, cas: str, scenario: str) -> dict:
    """Une exécution de D : {systeme, cas, sortie, journal, cout}."""
    debut = time.perf_counter()
    reg = ou.Registre(dossiers, lgd)
    t0 = reg.t0.isoformat()

    def fin(decision, preuves, justification):
        return {"systeme": "D", "cas": cas, "sortie": rg.sortie(cas, decision, preuves, justification),
                "journal": list(reg.journal),
                "cout": {"appels_outils": len(reg.journal), "appels_modele": 0, "jetons_entree": 0,
                         "jetons_sortie": 0, "secondes": round(time.perf_counter() - debut, 6), "euros": 0.0}}

    e = reg.appeler("etat", cas, t0)
    if e["statut"] != "ok":
        return fin("abstention", [e["preuve"]], f"état à t0 refusé ({e['motif']}) [{e['preuve']}]")
    if not rg.eligible(e["donnees"]):
        return fin("abstention", [e["preuve"]], f"liquidation judiciaire en cours à t0 [{e['preuve']}]")
    p = reg.appeler("prevision", cas, t0)
    if p["statut"] != "ok":
        return fin("abstention", [e["preuve"], p["preuve"]], f"prévision refusée ({p['motif']}) [{p['preuve']}]")
    s = reg.appeler("seuils", scenario=scenario)
    if s["statut"] != "ok":
        return fin("abstention", [e["preuve"], p["preuve"], s["preuve"]],
                   f"seuil refusé ({s['motif']}) [{s['preuve']}]")
    pr, pt = p["donnees"]["p_defaillance_548j"], s["donnees"]["p_t"]
    d = rg.decision_seuil(pr, pt)
    signe = ">" if d == "couvrir" else "<="
    return fin(d, [e["preuve"], p["preuve"], s["preuve"]],
               f"éligible [{e['preuve']}] ; p = {pr} [{p['preuve']}] {signe} p_t = {pt} [{s['preuve']}]")


def executer(dossiers: dict, lgd: float, cas_scenarios: list) -> list:
    """D sur une liste de (cas, scenario)."""
    return [decider(dossiers, lgd, c, s) for c, s in cas_scenarios]
