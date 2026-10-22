"""Palier 1 de la boucle de supervision : registre des outils datés, pseudonymisés et journalisés.

Spécification : methode/boucle-de-supervision.md (note gelée le 21/10/2026), section 7.2.

Les mêmes outils sont servis à B, T1 et T0 (T0 n'en reçoit aucun) ; la référence D les appelle
aussi. Chaque outil :
  - ne lit que les dossiers produits par palier1/extraire_cas.py, qui ne contiennent que
    l'information parue avant t0 et aucun identifiant ;
  - refuse toute date postérieure à t0, et toute date mal formée ;
  - journalise chaque appel, refus compris, avec un identifiant de preuve déterministe
    (« P » suivi de 12 caractères du SHA-256 de l'appel et de sa réponse) : une même
    question rend la même preuve, ce qui permet au vérificateur de M2 de contrôler qu'un
    identifiant cité figure bien au journal.

Outils :
  ratios(cas, date)       bilan le plus récent dont l'avis de dépôt est paru avant la date :
                          clôture, type, ratios, ordre de grandeur du total, retard de dépôt
  annonces(cas, date)     annonces parues avant la date, en codes : dépôt des comptes,
                          procédure (nature classée), radiation, dissolution, fusion
  etat(cas, date)         état administratif à la date : catégorie juridique, NAF, âge,
                          radiation, procédure en cours (RJ, LJ, SAUV, PLAN, INDET ou aucune)
  prevision(cas, date)    probabilité de défaillance à 548 jours du modèle dédié, au seul t0
  seuils(scenario)        seuil de décision p_t = pi T / (q LGD) du scénario S1 à S6
"""

import datetime as dt
import hashlib
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "ingestion"))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
from construire import ETAT_APRES  # noqa: E402

HORIZON = 548
PI = 0.001
SCENARIOS = {f"S{i + 1}": {"D": d, "q": q} for i, (d, q) in
             enumerate((d, q) for d in (30, 45, 60) for q in (0.7, 0.9))}
OUTILS = ("ratios", "annonces", "etat", "prevision", "seuils")


def canonique(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Registre:
    def __init__(self, dossiers: dict, lgd: float, journal: str = None):
        if not dossiers:
            raise ValueError("aucun dossier")
        t0s = {v["t0"] for v in dossiers.values()}
        if len(t0s) != 1:
            raise ValueError("un seul t0 par registre")
        self.t0 = dt.date.fromisoformat(t0s.pop())
        self.dossiers, self.lgd, self.chemin_journal = dossiers, lgd, journal
        self.journal = []

    # --- appel central ----------------------------------------------------------------
    def appeler(self, outil: str, cas: str = None, date: str = None, **args) -> dict:
        requete = {"outil": outil, "cas": cas, "date": date, "args": args}
        try:
            if outil not in OUTILS:
                raise Refus("outil inconnu")
            if outil == "seuils":
                donnees = self._seuils(**args)
            else:
                if cas not in self.dossiers:
                    raise Refus("cas inconnu")
                d = self._date(date)
                donnees = getattr(self, "_" + outil)(self.dossiers[cas], d)
            reponse = {"statut": "ok", "donnees": donnees}
        except Refus as e:
            reponse = {"statut": "refus", "motif": str(e)}
        except TypeError:
            reponse = {"statut": "refus", "motif": "arguments invalides"}
        preuve = "P" + hashlib.sha256(canonique({"requete": requete, "reponse": reponse}).encode()).hexdigest()[:12]
        reponse["preuve"] = preuve
        entree = {"n": len(self.journal) + 1, **requete, "statut": reponse["statut"],
                  "motif": reponse.get("motif"), "preuve": preuve}
        self.journal.append(entree)
        if self.chemin_journal:
            with open(self.chemin_journal, "a", encoding="utf-8") as f:
                f.write(canonique(entree) + "\n")
        return reponse

    def preuves(self, statut: str = "ok") -> set:
        return {e["preuve"] for e in self.journal if e["statut"] == statut}

    def _date(self, date) -> dt.date:
        if not isinstance(date, str):
            raise Refus("date absente")
        try:
            d = dt.date.fromisoformat(date)
        except ValueError:
            raise Refus("date mal formée") from None
        if d > self.t0:
            raise Refus("date postérieure à t0")
        return d

    # --- outils -------------------------------------------------------------------------
    @staticmethod
    def _ratios(x: dict, d: dt.date) -> dict:
        connus = [b for b in x["bilans"] if dt.date.fromisoformat(b["parution"]) < d]
        if not connus:
            return {"bilan": None}
        b = max(connus, key=lambda b: b["cloture"])
        retard = (dt.date.fromisoformat(b["parution"]) - dt.date.fromisoformat(b["cloture"])).days
        return {"bilan": {"cloture": b["cloture"], "type": b["type"], "confidentiel": b["confidentiel"],
                          "ordre_total_bilan": b["ordre_total_bilan"], "retard_depot_jours": retard,
                          "ratios": b["ratios"]}, "bilans_connus": len(connus)}

    @staticmethod
    def _annonces(x: dict, d: dt.date) -> dict:
        avant = lambda p: dt.date.fromisoformat(p) < d  # noqa: E731
        a = [{"type": "DEPOT_COMPTES", "parution": v["parution"], "cloture": v["cloture"]}
             for v in x["depots"] if avant(v["parution"])]
        a += [{"type": "PROCEDURE", "parution": v["parution"], "nature": v["nature"]}
              for v in x["procedures"] if avant(v["parution"])]
        a += [{"type": v["evenement"].upper(), "parution": v["parution"]}
              for v in x["modifications"] if avant(v["parution"])]
        if x["radiation"] and avant(x["radiation"]):
            a.append({"type": "RADIATION", "parution": x["radiation"]})
        return {"annonces": sorted(a, key=lambda v: (v["parution"], v["type"]))}

    @staticmethod
    def _etat(x: dict, d: dt.date) -> dict:
        per = None
        for p in x["sirene"]:
            deb = dt.date.fromisoformat(p["debut"]) if p["debut"] else None
            fin = dt.date.fromisoformat(p["fin"]) if p["fin"] else None
            if (deb is None or deb <= d) and (fin is None or d <= fin):
                per = p
        etat = None
        for v in sorted(x["procedures"], key=lambda v: v["parution"]):
            if dt.date.fromisoformat(v["parution"]) < d and v["nature"] in ETAT_APRES:
                etat = ETAT_APRES[v["nature"]]
        cr = dt.date.fromisoformat(x["creation"]) if x["creation"] else None
        return {"categorie_juridique": per["categorie_juridique"] if per else None,
                "naf": per["naf"] if per else None,
                "age_ans": round((d - cr).days / 365.25, 1) if cr and cr <= d else None,
                "radiee": bool(x["radiation"] and dt.date.fromisoformat(x["radiation"]) < d),
                "procedure_en_cours": etat}

    def _prevision(self, x: dict, d: dt.date) -> dict:
        if d != self.t0:
            raise Refus("prévision disponible au seul t0")
        if "prevision" not in x:
            raise Refus("prévision absente pour ce cas")
        return {"p_defaillance_548j": round(x["prevision"]["p"], 6), "modele": x["prevision"]["fichier"]}

    def _seuils(self, scenario: str = None) -> dict:
        if scenario not in SCENARIOS:
            raise Refus("scénario inconnu")
        s = SCENARIOS[scenario]
        T = HORIZON / s["D"]
        return {"scenario": scenario, "pi": PI, "D": s["D"], "q": s["q"], "lgd": self.lgd, "T": round(T, 6),
                "p_t": round(PI * T / (s["q"] * self.lgd), 8)}


class Refus(Exception):
    pass


def charger(chemin_dossiers: str, lgd: float, journal: str = None) -> Registre:
    with open(chemin_dossiers, encoding="utf-8") as f:
        return Registre(json.load(f), lgd, journal)


if __name__ == "__main__":
    print(__doc__)
