"""Palier 1 de la boucle de supervision : configurations des systèmes T0, T1 et B.

Spécification : methode/boucle-de-supervision.md, sections 5 et 7.1 ; choix C1 à C12 :
methode/boucle-de-supervision-palier1-configurations.md.

Les trois systèmes utilisent le même modèle (interface `Modele`), les mêmes règles métier
(regles.REGLES_METIER), le même format de sortie, et, pour T1 et B, les mêmes outils sous le
même protocole d'appel et le même plafond par cas. Ne varient, entre T1 et B, que la machine à
états, les statuts d'ancrage, le blocage sur inconnu et les contrôles avant action.

Protocole d'échange, identique pour T1 et B : chaque réponse du modèle est un objet JSON seul ;
s'il porte la clé « appels », c'est une liste de demandes d'outils
({"outil": ..., "date": ...} ou {"outil": "seuils", "scenario": ...}) ; sinon c'est la sortie.

  T0  un appel, sans outil ; la réponse est la sortie.
  T1  boucle libre : le modèle appelle les outils comme il veut (chaque appel passe par le
      registre et son journal, refus compris) jusqu'à rendre une sortie, sous le plafond.
  B   machine à états propre au palier 1 (S0, S1, S2 fixés par les règles ; S3 ancrage ;
      S11 ordonnanceur ; S4-S5 proposition et filtre ; S8 vérification ; ABSTENTION) :
      le modèle propose, le code vérifie ; la sortie est composée par le code à partir de
      la seule proposition vérifiée.
"""

import datetime as dt
import json
import time

import outils as ou
import regles as rg

PLAFOND = {"appels_modele": 6, "jetons": 40_000}
RETOURS_MAX = 2
CHAMPS_STRUCTURANTS = ("eligibilite", "p", "p_t")

DESCRIPTION_OUTILS = """Outils (chacun refuse toute date postérieure à t0 ; chaque appel est journalisé et rend un identifiant de preuve « preuve ») :
- ratios(date) : bilan le plus récent dont l'avis de dépôt est paru avant la date (clôture, type, ratios, ordre de grandeur du total de bilan, retard de dépôt).
- annonces(date) : annonces légales parues avant la date, en codes (dépôt des comptes, procédure et sa nature, radiation, dissolution, fusion).
- etat(date) : état administratif à la date (catégorie juridique, NAF, âge, radiation, procédure en cours : RJ, LJ, SAUV, PLAN, INDET ou aucune).
- prevision(date) : probabilité de défaillance à 548 jours du modèle de prévision ; servie au seul t0.
- seuils(scenario) : seuil de décision p_t du scénario.
Pour appeler des outils, réponds uniquement par un objet JSON de la forme
{"appels": [{"outil": "etat", "date": "AAAA-MM-JJ"}, {"outil": "seuils", "scenario": "S1"}]}."""

FORMAT_SORTIE = """Sortie finale : réponds uniquement par un objet JSON, sans texte ni balise autour, aux quatre champs exacts
{"cas": "<identifiant du cas>", "decision": "couvrir" | "conserver" | "abstention", "preuves": ["<identifiants de preuve utilisés>"], "justification": "<au plus 2000 caractères, limitée aux faits des preuves citées>"}."""

CONTEXTE = """Tu conseilles un fournisseur qui doit décider, pour une contrepartie, de couvrir le risque de défaillance par une assurance-crédit ou de le conserver.
Règles métier :
{regles}"""


def systeme_commun(avec_outils: bool) -> str:
    parts = [CONTEXTE.format(regles=rg.REGLES_METIER)]
    if avec_outils:
        parts.append(DESCRIPTION_OUTILS)
    parts.append(FORMAT_SORTIE)
    return "\n\n".join(parts)


def message_cas(cas: str, t0: str, scenario: str) -> str:
    return f"Cas : {cas}. Date de décision t0 : {t0}. Scénario : {scenario}. Question : couvrir ou conserver ?"


# --- modèle ------------------------------------------------------------------------------------
class Modele:
    """Interface : appeler(messages) -> {"texte", "jetons_entree", "jetons_sortie"}.
    messages : [{"role": "system" | "user" | "assistant", "content": str}] ; température fixée
    par l'adaptateur. Les adaptateurs réels sont dans palier1/modeles.py."""

    nom = "abstrait"

    def appeler(self, messages: list) -> dict:
        raise NotImplementedError


class Compteur:
    """Plafond commun par cas : appels de modèle et jetons (entrée + sortie)."""

    def __init__(self, modele: Modele, plafond: dict):
        self.modele, self.plafond = modele, plafond
        self.appels = self.entree = self.sortie = 0

    def disponible(self) -> bool:
        return self.appels < self.plafond["appels_modele"] and self.entree + self.sortie < self.plafond["jetons"]

    def appeler(self, messages: list) -> str:
        r = self.modele.appeler(messages)
        self.appels += 1
        self.entree += int(r.get("jetons_entree", 0))
        self.sortie += int(r.get("jetons_sortie", 0))
        return r["texte"]

    def cout(self, journal_outils: list, debut: float) -> dict:
        return {"appels_outils": len(journal_outils), "appels_modele": self.appels, "jetons_entree": self.entree,
                "jetons_sortie": self.sortie, "secondes": round(time.perf_counter() - debut, 3), "euros": 0.0}


def lire_json(texte):
    try:
        x = json.loads(texte) if isinstance(texte, str) else None
    except (json.JSONDecodeError, RecursionError):
        return None
    return x if isinstance(x, dict) else None


def resultat_pour_modele(demande: dict, reponse: dict) -> dict:
    return {"demande": demande, **reponse}


# --- T0 ------------------------------------------------------------------------------------------
def executer_T0(modele: Modele, cas: str, t0: str, scenario: str) -> dict:
    debut, c = time.perf_counter(), Compteur(modele, {"appels_modele": 1, "jetons": PLAFOND["jetons"]})
    texte = c.appeler([{"role": "system", "content": systeme_commun(False)},
                       {"role": "user", "content": message_cas(cas, t0, scenario)}])
    return {"systeme": "T0", "cas": cas, "sortie": texte, "journal": [], "trace": [], "cout": c.cout([], debut)}


# --- T1 ------------------------------------------------------------------------------------------
def _appeler_outil(reg: ou.Registre, cas: str, d: dict) -> dict:
    if not isinstance(d, dict):
        return reg.appeler("?", cas, None)
    args = {k: v for k, v in d.items() if k not in ("outil", "date")}
    if d.get("outil") == "seuils":
        return reg.appeler("seuils", **args)
    return reg.appeler(str(d.get("outil")), cas, d.get("date"), **args)


def executer_T1(modele: Modele, dossiers: dict, lgd: float, cas: str, scenario: str,
                plafond: dict = PLAFOND) -> dict:
    debut, c = time.perf_counter(), Compteur(modele, plafond)
    reg = ou.Registre(dossiers, lgd)
    t0 = reg.t0.isoformat()
    messages = [{"role": "system", "content": systeme_commun(True)},
                {"role": "user", "content": message_cas(cas, t0, scenario)}]
    sortie = None
    while c.disponible():
        texte = c.appeler(messages)
        x = lire_json(texte)
        if x is not None and "appels" in x and isinstance(x["appels"], list):
            res = [resultat_pour_modele(d, _appeler_outil(reg, cas, d)) for d in x["appels"]]
            messages += [{"role": "assistant", "content": texte},
                         {"role": "user", "content": json.dumps({"resultats": res}, ensure_ascii=False)}]
            continue
        sortie = texte
        break
    return {"systeme": "T1", "cas": cas, "sortie": sortie, "journal": list(reg.journal), "trace": [],
            "cout": c.cout(reg.journal, debut)}


# --- B -------------------------------------------------------------------------------------------
class Machine:
    """Machine à états de B pour le palier 1. Chaque transition est tracée (état, statuts, motif)."""

    def __init__(self, modele: Modele, dossiers: dict, lgd: float, cas: str, scenario: str, plafond: dict):
        self.c = Compteur(modele, plafond)
        self.reg = ou.Registre(dossiers, lgd)
        self.cas, self.scenario, self.t0 = cas, scenario, self.reg.t0.isoformat()
        self.trace, self.resultats, self.bloques = [], [], []
        self.champs = {k: {"statut": "inconnu"} for k in CHAMPS_STRUCTURANTS}
        self.messages = [{"role": "system", "content": systeme_commun(True)},
                         {"role": "user", "content": message_cas(cas, self.t0, scenario)}]

    def tracer(self, etat: str, **x):
        self.trace.append({"etat": etat, **x})

    # S3 et S11 : exécuter une demande d'outil, après contrôle du mandat par le code
    def executer_demande(self, d: dict, origine: str):
        if not isinstance(d, dict) or d.get("outil") not in ou.OUTILS:
            self.bloques.append({"demande": d, "motif": "outil hors mandat"})
            return
        if d["outil"] != "seuils":
            date = d.get("date")
            try:
                ok_date = isinstance(date, str) and dt.date.fromisoformat(date) <= self.reg.t0
            except ValueError:
                ok_date = False
            if not ok_date:
                # blocage par la machine, avant l'outil : rien n'est demandé à l'outil
                self.bloques.append({"demande": d, "motif": "date hors mandat (absente, mal formée ou après t0)"})
                return
        r = _appeler_outil(self.reg, self.cas, d)
        self.resultats.append(resultat_pour_modele(d, r))
        self.ancrer(d, r, origine)

    def ancrer(self, d: dict, r: dict, origine: str):
        if r["statut"] != "ok":
            return
        o = d["outil"]
        if o == "etat" and d.get("date") == self.t0:
            el = rg.eligible(r["donnees"])
            self.champs["eligibilite"] = {"statut": "verifie", "valeur": el, "preuve": r["preuve"], "par": origine}
        elif o == "prevision" and d.get("date") == self.t0:
            self.champs["p"] = {"statut": "verifie", "valeur": r["donnees"]["p_defaillance_548j"],
                                "preuve": r["preuve"], "par": origine}
        elif o == "seuils" and d.get("scenario") == self.scenario:
            self.champs["p_t"] = {"statut": "verifie", "valeur": r["donnees"]["p_t"], "preuve": r["preuve"],
                                  "par": origine}

    def demande_canonique(self, champ: str) -> dict:
        return {"eligibilite": {"outil": "etat", "date": self.t0}, "p": {"outil": "prevision", "date": self.t0},
                "p_t": {"outil": "seuils", "scenario": self.scenario}}[champ]

    def statuts(self) -> dict:
        return {k: v["statut"] for k, v in self.champs.items()}

    def fin(self, decision: str, preuves: list, justification: str, debut: float) -> dict:
        self.tracer("FIN", decision=decision)
        return {"systeme": "B", "cas": self.cas, "sortie": rg.sortie(self.cas, decision, preuves, justification),
                "journal": list(self.reg.journal), "trace": self.trace, "bloques": self.bloques,
                "cout": self.c.cout(self.reg.journal, debut)}

    def abstention(self, motif: str, debut: float) -> dict:
        self.tracer("ABSTENTION", motif=motif, statuts=self.statuts())
        preuves = [v["preuve"] for v in self.champs.values() if v["statut"] == "verifie"]
        return self.fin("abstention", preuves, f"abstention de la machine : {motif}", debut)

    def executer(self) -> dict:
        debut = time.perf_counter()
        self.tracer("S0", mandat="lecture des outils à des dates au plus t0", plafond=self.c.plafond)
        self.tracer("S1", etat_souhaite="décision conforme aux règles métier, preuves tracées")
        self.tracer("S2", arbre="éligibilité ET (p, p_t) ; contrainte dure : inéligibilité en liquidation")
        # S3 : le modèle propose les appels ; la machine filtre et exécute
        if not self.c.disponible():
            return self.abstention("budget épuisé avant l'ancrage", debut)
        texte = self.c.appeler(self.messages + [{"role": "user", "content":
                                                 "Étape d'enquête : propose les appels d'outils nécessaires. "
                                                 "Réponds uniquement par {\"appels\": [...]}."}])
        x = lire_json(texte)
        for d in (x.get("appels") if x and isinstance(x.get("appels"), list) else []):
            self.executer_demande(d, "S3")
        self.tracer("S3", statuts=self.statuts(), bloques=len(self.bloques), proposition_lisible=x is not None)
        # S11 : un inconnu structurant a une mesure autorisée (l'appel canonique) ; la machine la lance
        for k in CHAMPS_STRUCTURANTS:
            if self.champs[k]["statut"] == "inconnu":
                if k != "eligibilite" and self.champs["eligibilite"].get("valeur") is False:
                    continue  # inutile : la contrainte dure suffit
                self.executer_demande(self.demande_canonique(k), "S11")
        self.tracer("S11", statuts=self.statuts())
        if self.champs["eligibilite"]["statut"] != "verifie":
            return self.abstention("éligibilité inconnue à t0", debut)
        eligible = self.champs["eligibilite"]["valeur"]
        if eligible and any(self.champs[k]["statut"] != "verifie" for k in ("p", "p_t")):
            return self.abstention("prévision ou seuil inconnu à t0", debut)
        attendue = "abstention" if not eligible else rg.decision_seuil(self.champs["p"]["valeur"],
                                                                       self.champs["p_t"]["valeur"])
        # S4-S5-S8 : le modèle propose la décision ; la machine filtre et vérifie
        faits = {k: {c: v[c] for c in ("statut", "valeur", "preuve") if c in v} for k, v in self.champs.items()}
        consigne = ("Faits vérifiés (statut, valeur, preuve) : " + json.dumps(faits, ensure_ascii=False)
                    + "\nRésultats d'outils : " + json.dumps(self.resultats, ensure_ascii=False)
                    + "\nÉtape de décision : rends la sortie finale.")
        conv = self.messages + [{"role": "user", "content": consigne}]
        for tour in range(RETOURS_MAX + 1):
            if not self.c.disponible():
                return self.abstention("budget épuisé avant décision vérifiée", debut)
            texte = self.c.appeler(conv)
            s, motif = rg.controler_sortie(texte, self.cas)
            if s is None:
                contradiction = f"sortie non conforme ({motif})"
            elif not eligible and s["decision"] != "abstention":
                contradiction = "contrainte dure : société en liquidation judiciaire à t0, seule l'abstention est admise"
            elif s["decision"] != attendue:
                contradiction = (f"décision {s['decision']} contredite par les faits vérifiés et la règle métier "
                                 f"(p = {self.champs['p'].get('valeur')}, p_t = {self.champs['p_t'].get('valeur')})")
            else:
                self.tracer("S8", tour=tour, verdict="verifie")
                preuves = [v["preuve"] for v in self.champs.values() if v["statut"] == "verifie"]
                return self.fin(s["decision"], preuves, s["justification"], debut)
            self.tracer("S8", tour=tour, verdict="contredit", motif=contradiction)
            conv = conv + [{"role": "assistant", "content": texte if isinstance(texte, str) else ""},
                           {"role": "user", "content": f"Contredit par la vérification : {contradiction}. "
                                                       "Rends une nouvelle sortie finale."}]
        return self.abstention("proposition contredite après deux retours", debut)


def executer_B(modele: Modele, dossiers: dict, lgd: float, cas: str, scenario: str,
               plafond: dict = PLAFOND) -> dict:
    return Machine(modele, dossiers, lgd, cas, scenario, plafond).executer()
