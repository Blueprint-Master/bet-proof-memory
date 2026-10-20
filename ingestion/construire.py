"""Phase 5, étape 2 : construction des cas de l'espace de développement (protocole Q1 v1.5).

Lit les instantanés de l'étape 1 (dossier de données) et écrit :
  cas-dev.parquet           un cas par couple (SIREN, origine), origines 2008 à 2020,
                            avec les variables de l'annexe A et l'issue (P3)
  construction-<date>.json  décomptes par origine : couverture, exclusions par motif,
                            issues ; empreintes des entrées et de la sortie

Règles appliquées, par article du protocole :
  P1    forme juridique (historique Sirene valide à t0), création antérieure à t0,
        aucune radiation parue avant t0, au moins un bilan connu à t0, et pas de
        défaillance en cours (v1.0.2, protocole v1.6) : sont exclues les sociétés en
        observation de redressement, en liquidation, ou dont l'ouverture n'est pas
        identifiable ; sont incluses, avec un indicateur, celles en observation de
        sauvegarde et celles en exécution d'un plan (sauvegarde, redressement).
        Un jugement d'ouverture daté avant t0 mais paru après t0 écarte le cas
        (compté à part) : il était inéligible en réalité, sans qu'on le sache.
  P2    bilan connu à t0 : avis de dépôt des comptes paru avant t0, retrouvé par
        (SIREN, date de clôture) ; le plus récent fait foi.
  P2 bis  clôtures antérieures au 01/01/2000, postérieures à l'extraction ou à
        la parution : exclues, comptées par motif.
  P2 ter  compte de résultat disponible si `marge_ebe` est renseigné ; sinon
        variables du groupe 2 neutralisées à 0 et indicateur à 1.
  P2 quater  comptes sociaux (C préféré à S) ; consolidés (K) écartés ; total de
        bilan = EE (C) ou 180 (S).
  P3    issue = premier jugement d'entrée en redressement ou en liquidation judiciaire
        (ouverture, conversion d'une sauvegarde, résolution d'un plan) daté dans
        ]t0, t0 + 548 jours] ; sauvegarde, radiation sans procédure, dissolution et
        fusion rapportées à part.
  R1    composantes du Z'' d'Altman approché, lues dans la liasse (v1.0.2).
  P4    couverture : origine retenue si les sociétés de P1 ayant un bilan connu
        à t0 sont au moins 346 859 ; origines 2008 à 2020 seulement (la 2021
        est le tampon, les suivantes relèvent du scellé ou du prospectif).

Aucune origine postérieure au 30/09/2020 n'est construite ici, et les annonces de
procédure lues sont celles de l'étape 1, toutes parues avant le 30/09/2022.
"""

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
from extraire import DOSSIER_DEFAUT, GARDE_SCELLE, sha256_fichier  # noqa: E402
from p0_sources import forme_p1, journal  # noqa: E402

HORIZON_JOURS = 548
SEUIL_COUVERTURE = 346_859
ORIGINES_DEV = tuple(range(2008, 2021))
CLOTURE_MIN = dt.date(2000, 1, 1)
GROUPE1 = ("ratio_de_liquidite", "taux_d_endettement", "autonomie_financiere", "ratio_de_vetuste")
GROUPE2 = ("marge_ebe", "caf_sur_ca", "poids_bfr_exploitation_sur_ca", "couverture_des_interets",
           "capacite_de_remboursement")
MOTIF_CONFID = re.compile(r"confid", re.I)
MOTIF_CLOTURE = re.compile(r'"?dateCloture"?\s*:\s*"(\d{4}-\d{2}-\d{2})"')
MOTIF_SIREN = re.compile(r"(\d{9})")

# Secteur Banque de France (DIREN) à partir de la division NAF (2 chiffres).
SECTEURS_BDF = ((1, 3, "AZ"), (5, 39, "BE"), (41, 43, "FZ"), (45, 47, "G"), (49, 53, "H"), (55, 56, "I"),
                (58, 63, "JZ"), (64, 66, "KZ"), (68, 68, "LZ"), (69, 82, "MN"), (84, 99, "PS"))


# --- Lecture des instantanés -------------------------------------------------

def _lire(dossier: str, motif: str, colonnes=None):
    import pyarrow as pa
    import pyarrow.parquet as pq

    chemins = sorted(glob.glob(os.path.join(dossier, motif)))
    if not chemins:
        raise RuntimeError(f"aucun instantané {motif} dans {dossier}")
    tables = [pq.read_table(c, columns=colonnes) for c in chemins]
    return pa.concat_tables(tables, promote_options="default"), chemins


def _date(v):
    if v is None:
        return None
    if isinstance(v, dt.date):
        return v
    s = str(v)[:10]
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def _siren(v):
    if v is None:
        return None
    m = MOTIF_SIREN.search(str(v).replace(" ", ""))
    return m.group(1) if m else None


COLONNES_RATIOS = ("siren", "date_cloture_exercice", "type_bilan", "confidentiality",
                   "chiffre_d_affaires", "resultat_net") + GROUPE1 + GROUPE2


class Ratios:
    """Colonnes des ratios en mémoire compacte : chaînes en listes, montants en numpy (NaN = absent)."""

    def __init__(self, table):
        import numpy as np

        self.siren = table.column("siren").to_pylist()
        self.cloture = table.column("date_cloture_exercice").to_pylist()
        self.type = table.column("type_bilan").to_pylist()
        self.conf = table.column("confidentiality").to_pylist()
        self.num = {c: np.asarray(table.column(c).to_numpy(zero_copy_only=False), dtype="float64")
                    for c in COLONNES_RATIOS[4:]}

    def valeur(self, c, i):
        v = self.num[c][i]
        return None if v != v else float(v)


def _num(table, nom):
    import numpy as np

    if nom not in table.column_names:
        return np.full(table.num_rows, np.nan)
    return np.asarray(table.column(nom).to_numpy(zero_copy_only=False), dtype="float64")


def composantes_liasse(sf) -> dict:
    """{(siren, clôture, type): (total de bilan, (X1, X2, X3, X4))} : Z'' d'Altman approché (v1.0.2).

    X1 = (actif circulant − dettes non financières) / total ; dettes non financières =
    total des dettes − dettes financières (approximation des dettes à court terme).
    X2 = (réserves + report à nouveau) / total. X3 = résultat d'exploitation / total.
    X4 = capitaux propres / total des dettes. Total = total du passif.
    Complet (C) : CJ-CK, EC, DS+DT+DU+DV, DD à DH, GG, DL, EE.
    Simplifié (S) : 096, 176, 156, 126+130+132+134, 270, 142, 180.
    Une composante dont un terme essentiel manque est absente (None) ; les postes
    d'une somme absents de la liasse valent zéro.
    """
    import numpy as np

    g = lambda n: _num(sf, n)  # noqa: E731
    z = lambda a: np.nan_to_num(a, nan=0.0)  # noqa: E731
    typ = np.asarray(sf.column("type_bilan").to_pylist(), dtype=object)
    est_c = typ == "C"
    total = np.where(est_c, g("EE"), g("180"))
    ac = np.where(est_c, g("CJ-CK"), g("096"))
    dettes = np.where(est_c, g("EC"), g("176"))
    dettes_fin = np.where(est_c, z(g("DS")) + z(g("DT")) + z(g("DU")) + z(g("DV")), z(g("156")))
    reserves = np.where(est_c, z(g("DD")) + z(g("DE")) + z(g("DF")) + z(g("DG")) + z(g("DH")),
                        z(g("126")) + z(g("130")) + z(g("132")) + z(g("134")))
    rex = np.where(est_c, g("GG"), g("270"))
    cp = np.where(est_c, g("DL"), g("142"))
    with np.errstate(divide="ignore", invalid="ignore"):
        tot_ok = np.where(total > 0, total, np.nan)
        x1 = (ac - (dettes - dettes_fin)) / tot_ok
        x2 = reserves / tot_ok
        x3 = rex / tot_ok
        x4 = cp / np.where(dettes > 0, dettes, np.nan)
    v = lambda a, k: None if a[k] != a[k] or abs(a[k]) == np.inf else float(a[k])  # noqa: E731
    out = {}
    sirens = sf.column("siren").to_pylist()
    clotures = sf.column("date_cloture_exercice").to_pylist()
    for k in range(sf.num_rows):
        if typ[k] not in ("C", "S") or not sirens[k]:
            continue
        out[(str(sirens[k]).zfill(9), str(clotures[k])[:10], typ[k])] = (
            v(total, k), (v(x1, k), v(x2, k), v(x3, k), v(x4, k)))
    return out


def bilans_dates(dossier: str, aujourdhui: dt.date) -> tuple:
    """Bilans sociaux datés par leur avis de dépôt : {siren: [(cloture, parution, indice, total), ...]}."""
    table, chemins = _lire(dossier, "ratios-*.parquet", list(COLONNES_RATIOS))
    R = Ratios(table)
    del table
    journal(f"{len(R.siren)} lignes de ratios")
    dpc, c2 = _lire(dossier, "bodacc-dpc.parquet", ["dateparution", "registre", "depot"])
    avis = {}
    for r, p, d in zip(dpc.column("registre").to_pylist(), dpc.column("dateparution").to_pylist(),
                       dpc.column("depot").to_pylist()):
        s, m, p = _siren(r), MOTIF_CLOTURE.search(d or ""), _date(p)
        if s and m and p:
            k = (s, m.group(1))
            if k not in avis or p < avis[k]:
                avis[k] = p
    del dpc
    journal(f"{len(avis)} couples (SIREN, clôture) avec avis de dépôt")
    sf, c3 = _lire(dossier, "sf-totaux.parquet")
    totaux = composantes_liasse(sf)
    del sf
    motifs = {"consolides": 0, "doublon_type": 0, "sans_avis": 0, "cloture_avant_2000": 0,
              "cloture_future": 0, "cloture_apres_parution": 0, "sans_siren": 0}
    retenus = {}
    for i in range(len(R.siren)):
        s, c = _siren(R.siren[i]), _date(R.cloture[i])
        if not s or not c:
            motifs["sans_siren"] += 1
            continue
        t = R.type[i]
        if t not in ("C", "S"):
            motifs["consolides"] += 1
            continue
        k = (s, c.isoformat())
        if k in retenus:
            motifs["doublon_type"] += 1
            if not (t == "C" and R.type[retenus[k]] == "S"):
                continue
        retenus[k] = i
    par_siren = {}
    for (s, c_iso), i in retenus.items():
        c = dt.date.fromisoformat(c_iso)
        p = avis.get((s, c_iso))
        if p is None:
            motifs["sans_avis"] += 1
        elif c < CLOTURE_MIN:
            motifs["cloture_avant_2000"] += 1
        elif c > aujourdhui:
            motifs["cloture_future"] += 1
        elif c > p:
            motifs["cloture_apres_parution"] += 1
        else:
            tot, zc = totaux.get((s, c_iso, R.type[i]), (None, (None, None, None, None)))
            par_siren.setdefault(s, []).append((c, p, (i, zc), tot))
    for v in par_siren.values():
        v.sort(key=lambda x: x[0])
    return R, par_siren, motifs, chemins + c2 + c3


def sirene(dossier: str) -> tuple[dict, dict, list]:
    h, c1 = _lire(dossier, "sirene-historique.parquet")
    periodes = {}
    for s, d, f, cj, naf, nom in zip(*(h.column(n).to_pylist() for n in (
            "siren", "dateDebut", "dateFin", "categorieJuridiqueUniteLegale",
            "activitePrincipaleUniteLegale", "nomenclatureActivitePrincipaleUniteLegale"))):
        periodes.setdefault(str(s).zfill(9), []).append((_date(d), _date(f), cj, naf, nom))
    u, c2 = _lire(dossier, "sirene-creation.parquet")
    creation = {str(s).zfill(9): _date(d) for s, d in zip(u.column("siren").to_pylist(),
                                                          u.column("dateCreationUniteLegale").to_pylist())}
    return periodes, creation, c1 + c2


def periode_a(periodes: list, t0: dt.date):
    for d, f, cj, naf, nom in periodes:
        if (d is None or d <= t0) and (f is None or t0 <= f):
            return cj, naf, nom
    return None


# Natures de jugement (v1.0.1, d'après la répartition observée le 20/10/2026 sur l'espace
# de développement). OUVRANTS : la procédure est en cours après ce jugement (P1).
# ISSUES : le jugement est une défaillance au sens de P3 (entrée en redressement ou en
# liquidation judiciaire d'une société qui n'y était pas).
OUVRANTS = {"OUV-LJ", "OUV-RJ", "OUV-SAUV", "OUV-INDET", "CONV-SAUV-LJ", "CONV-SAUV-RJ",
            "RESOL-LJ", "REOUV"}
# État de la société après chaque nature (v1.0.2). Seuls RJ, LJ et INDET excluent :
# la société a déjà défailli (ou on ne peut pas le savoir), la question ne se pose pas.
# En observation de sauvegarde ou en plan, elle fonctionne : la question se pose.
ETAT_APRES = {"OUV-RJ": "RJ", "CONV-SAUV-RJ": "RJ", "OUV-LJ": "LJ", "CONV-SAUV-LJ": "LJ", "RESOL-LJ": "LJ",
              "REOUV": "LJ", "OUV-SAUV": "SAUV", "OUV-INDET": "INDET", "PLAN": "PLAN", "CLOT": None}
ETATS_EXCLUANTS = {"RJ", "LJ", "INDET"}
NATURES_EXCLUANTES = {n for n, e in ETAT_APRES.items() if e in ETATS_EXCLUANTS}
ISSUES = {"OUV-LJ", "OUV-RJ", "CONV-SAUV-LJ", "CONV-SAUV-RJ", "RESOL-LJ"}


def reparer(texte: str) -> str:
    """Répare le texte UTF-8 lu comme Latin-1 (« clÃ´ture »), constaté dans le BODACC."""
    if "Ã" in texte:
        try:
            return texte.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return texte
    return texte


def classer_jugement(jugement) -> tuple:
    """(nature, date) d'une annonce de procédure.

    OUV-LJ, OUV-RJ, OUV-SAUV : jugements d'ouverture ; OUV-INDET : ouverture dont la
    procédure n'est nommée ni dans la nature ni dans le complément ; CONV-SAUV-LJ et
    CONV-SAUV-RJ : conversion d'une sauvegarde ; RESOL-LJ : résolution d'un plan et
    liquidation ; REOUV : reprise d'une liquidation clôturée ; PLAN : plan de sauvegarde,
    de redressement ou de continuation arrêté ou modifié (pas de cession) ; CLOT : clôture
    ou fin de la procédure ; ANNULE ; AUTRE (conversions de redressement en liquidation,
    états des créances, sanctions personnelles...).
    """
    j = jugement
    if isinstance(j, str):
        try:
            j = json.loads(j)
        except ValueError:
            j = {"nature": j}
    j = j or {}
    if str(j.get("type", "")).lower() == "annule":
        return "ANNULE", None
    nature = reparer(f"{j.get('famille', '')} {j.get('nature', '')}").lower()
    complement = reparer(str(j.get("complementJugement") or "")).lower()
    date = _date(j.get("date"))
    if "clôture" in nature or "cloture" in nature or "mettant fin à la procédure" in nature:
        return "CLOT", date
    if "reprise de la procédure de liquidation" in nature:
        return "REOUV", date
    if "résolution du plan" in nature and "liquidation" in nature:
        return "RESOL-LJ", date
    if any(k in nature for k in ("plan de redressement", "plan de sauvegarde", "plan de continuation")) \
            and "cession" not in nature:
        return "PLAN", date
    if "conversion" in nature and "sauvegarde" in nature:
        if "liquidation" in nature:
            return "CONV-SAUV-LJ", date
        if "redressement" in nature:
            return "CONV-SAUV-RJ", date
    if "ouverture" in nature:
        for texte in (nature, complement):
            if "sauvegarde" in texte:
                return "OUV-SAUV", date
            if "liquidation" in texte:
                return "OUV-LJ", date
            if "redressement" in texte:
                return "OUV-RJ", date
        return "OUV-INDET", date
    return "AUTRE", date


def procedures(dossier: str) -> tuple[dict, dict, list]:
    evenements, chemins, natures, exemples = {}, [], {}, []
    for motif in ("bodacc-collective.parquet", "bodacc-pcl.parquet"):
        try:
            t, c = _lire(dossier, motif, ["dateparution", "registre", "jugement"])
        except RuntimeError:
            continue
        chemins += c
        for r, p, j in zip(t.column("registre").to_pylist(), t.column("dateparution").to_pylist(),
                           t.column("jugement").to_pylist()):
            s, p = _siren(r), _date(p)
            if not s or not p:
                continue
            if p >= GARDE_SCELLE:
                raise RuntimeError("annonce postérieure à la garde du scellé dans les instantanés")
            n, d = classer_jugement(j)
            natures[n] = natures.get(n, 0) + 1
            if n == "OUV-INDET" and len(exemples) < 15:
                try:
                    jj = json.loads(j) if isinstance(j, str) else (j or {})
                except ValueError:
                    jj = {}
                exemples.append(reparer(str(jj.get("complementJugement") or ""))[:200])
            if n not in ("ANNULE", "AUTRE"):
                evenements.setdefault(s, []).append((p, d or p, n))
    if not chemins:
        raise RuntimeError("aucun instantané de procédures collectives")
    for v in evenements.values():
        v.sort()
    rad, c = _lire(dossier, "bodacc-radiation.parquet", ["dateparution", "registre"])
    radiations = {}
    for r, p in zip(rad.column("registre").to_pylist(), rad.column("dateparution").to_pylist()):
        s, p = _siren(r), _date(p)
        if s and p:
            if p >= GARDE_SCELLE:
                raise RuntimeError("radiation postérieure à la garde du scellé dans les instantanés")
            radiations[s] = min(p, radiations.get(s, p))
    return evenements, {"radiations": radiations, "natures": natures, "exemples_ouv_indet": exemples}, chemins + c


def modifications(dossier: str) -> tuple[dict, list]:
    """Dissolutions et fusions (événements concurrents de P3), datées par leur parution."""
    t, c = _lire(dossier, "bodacc-modification-evenements.parquet")
    ev = {}
    for r, p, e in zip(t.column("registre").to_pylist(), t.column("dateparution").to_pylist(),
                       t.column("evenement").to_pylist()):
        s, p = _siren(r), _date(p)
        if s and p:
            if p >= GARDE_SCELLE:
                raise RuntimeError("modification postérieure à la garde du scellé dans les instantanés")
            ev.setdefault(s, []).append((p, e))
    for v in ev.values():
        v.sort()
    return ev, c


def bdf(dossier: str) -> tuple[dict, list]:
    try:
        t, c = _lire(dossier, "bdf-diren.parquet")
    except RuntimeError:
        return {}, []
    series = {}
    for k, per, v in zip(t.column("series_key").to_pylist(), t.column("time_period").to_pylist(),
                         t.column("obs_value").to_pylist()):
        if v is not None:
            series.setdefault(k, {})[per[:7]] = v
    return series, c


def secteur_bdf(naf2):
    try:
        n = int(naf2)
    except (TypeError, ValueError):
        return None
    for a, b, code in SECTEURS_BDF:
        if a <= n <= b:
            return code
    return None


def taille_bdf(total, ca):
    if total is None:
        return "TT"
    if total <= 2e6 and (ca is None or ca <= 2e6):
        return "MI"
    if total <= 43e6:
        return "PM"
    return "IG"


def intensite(series: dict, secteur, taille, t0: dt.date):
    """Valeur au mois t0 − 3 mois divisée par la moyenne des 60 mois précédents."""
    def mois(m):
        a, r = divmod(t0.year * 12 + t0.month - 1 - m, 12)
        return f"{a:04d}-{r + 1:02d}"
    for cle in (f"DIREN.M.FR.DE.UL.DF.03.N.{secteur}.{taille}", f"DIREN.M.FR.DE.UL.DF.03.N.{secteur}.TT",
                f"DIREN.M.FR.DE.UL.DF.03.N.ZZ.{taille}", "DIREN.M.FR.DE.UL.DF.03.N.ZZ.TT"):
        s = series.get(cle)
        if not s or mois(3) not in s:
            continue
        passe = [s[mois(3 + i)] for i in range(1, 61) if mois(3 + i) in s]
        if len(passe) == 60 and sum(passe) > 0:
            return s[mois(3)] / (sum(passe) / 60), cle
    return None, None


# --- Construction ------------------------------------------------------------

def _log(x):
    return math.log(max(x, 1.0)) if x is not None else None


INSTANTANES_REQUIS = ("ratios-*.parquet", "bodacc-dpc.parquet", "bodacc-collective.parquet",
                      "bodacc-radiation.parquet", "bodacc-modification-evenements.parquet",
                      "sirene-historique.parquet", "sirene-creation.parquet", "sf-totaux.parquet",
                      "bdf-diren.parquet")


def verifier_instantanes(dossier: str) -> dict:
    """Refuse de construire si un instantané manque ou ne correspond pas à son dernier manifeste.

    Une empreinte différente signale une extraction en cours (fichier en réécriture) ou un
    fichier modifié hors outil (v1.0.3, après un lancement prématuré le 20/10/2026)."""
    attendus = {}
    for m in sorted(glob.glob(os.path.join(dossier, "manifeste-*.json"))):  # le plus récent l'emporte
        with open(m, encoding="utf-8") as f:
            for e in json.load(f).get("fichiers", []):
                attendus[e["fichier"]] = (e["sha256"], os.path.basename(m))
    controle = {}
    for motif in INSTANTANES_REQUIS:
        chemins = sorted(glob.glob(os.path.join(dossier, motif)))
        if not chemins:
            raise RuntimeError(f"instantané manquant : {motif} (extraction non faite ou en cours)")
        for c in chemins:
            nom = os.path.basename(c)
            if nom not in attendus:
                raise RuntimeError(f"{nom} sans manifeste : extraction en cours ou interrompue")
            if sha256_fichier(c) != attendus[nom][0]:
                raise RuntimeError(f"{nom} ne correspond pas à {attendus[nom][1]} : extraction en cours ou "
                                   f"fichier modifié")
            controle[nom] = attendus[nom][1]
    return controle


def construire(dossier: str, sortie, origines=ORIGINES_DEV, seuil=SEUIL_COUVERTURE, aujourdhui=None):
    aujourdhui = aujourdhui or dt.date.today()
    if any(dt.date(a, 9, 30) + dt.timedelta(days=HORIZON_JOURS) >= GARDE_SCELLE for a in origines):
        raise ValueError("origine dont la fenêtre d'issue atteint le scellé : refusée")
    journal("bilans datés")
    R, bilans, motifs_bilans, e1 = bilans_dates(dossier, aujourdhui)
    journal("Sirene")
    periodes, creation, e2 = sirene(dossier)
    journal("procédures et radiations")
    evts, info, e3 = procedures(dossier)
    series, e4 = bdf(dossier)
    modifs, e5 = modifications(dossier)
    radiations = info["radiations"]
    rapport, total_lignes = {}, 0
    for a in origines:
        t0 = dt.date(a, 9, 30)
        fin = t0 + dt.timedelta(days=HORIZON_JOURS)
        m = {"bilan_connu": 0, "forme_hors_p1": 0, "sans_periode_sirene": 0, "non_cree": 0,
             "radiee": 0, "procedure_en_cours": 0, "ouverture_anterieure_publiee_apres_t0": 0,
             "eligibles": 0, "defaillances": 0,
             "sauvegardes": 0, "ouvertures_indeterminees": 0, "radiations_sans_procedure": 0}
        cas = []
        for s, liste in bilans.items():
            connus = [x for x in liste if x[1] < t0]
            if not connus:
                continue
            m["bilan_connu"] += 1
            c, p, b, total = connus[-1]
            per = periode_a(periodes.get(s, []), t0)
            if per is None:
                m["sans_periode_sirene"] += 1
                continue
            cj, naf, nom = per
            if not forme_p1(cj):
                m["forme_hors_p1"] += 1
                continue
            cr = creation.get(s)
            if cr is not None and cr > t0:
                m["non_cree"] += 1
                continue
            if s in radiations and radiations[s] < t0:
                m["radiee"] += 1
                continue
            etat = None
            for pe, _dj, n in evts.get(s, []):
                if pe >= t0:
                    break
                if n in ETAT_APRES:
                    # Un plan ne s'arrête que sur une procédure de sauvegarde ou de redressement.
                    if n == "PLAN" and etat not in ("RJ", "SAUV", "PLAN"):
                        continue
                    etat = ETAT_APRES[n]
            if etat in ETATS_EXCLUANTS:
                m["procedure_en_cours"] += 1
                m[f"exclus_etat_{etat}"] = m.get(f"exclus_etat_{etat}", 0) + 1
                continue
            # P1 vise un jugement d'ouverture ANTÉRIEUR à t0. Un jugement daté avant t0 mais
            # paru après t0 rend le cas inéligible en réalité, sans qu'on puisse le savoir à t0 :
            # le cas est écarté et compté, plutôt qu'étiqueté « sans défaillance ».
            if any(n in NATURES_EXCLUANTES and dj <= t0 <= pe for pe, dj, n in evts.get(s, [])):
                m["ouverture_anterieure_publiee_apres_t0"] += 1
                continue
            m["eligibles"] += 1
            issue, date_issue, sauv, indet = 0, None, 0, 0
            for _pe, dj, n in evts.get(s, []):
                if t0 < dj <= fin:
                    if n in ISSUES and not issue:
                        issue, date_issue = 1, dj
                    elif n == "OUV-SAUV":
                        sauv = 1
                    elif n == "OUV-INDET":
                        indet = 1
            rad = int(not issue and s in radiations and t0 <= radiations[s] <= fin)
            conc = next((ev for d_ev, ev in modifs.get(s, []) if t0 < d_ev <= fin), None) if not issue else None
            m["en_plan"] = m.get("en_plan", 0) + int(etat == "PLAN")
            m["en_observation_sauvegarde"] = m.get("en_observation_sauvegarde", 0) + int(etat == "SAUV")
            if conc:
                m[f"concurrent_{conc}"] = m.get(f"concurrent_{conc}", 0) + 1
            m["defaillances"] += issue
            m["sauvegardes"] += sauv
            m["ouvertures_indeterminees"] += int(indet and not issue)
            m["radiations_sans_procedure"] += rad
            cas.append((s, c, p, b, total, cj, naf, nom, cr, issue, date_issue, sauv, rad, etat, conc))
        m["couverture"] = m["eligibles"]
        m["retenue"] = m["eligibles"] >= seuil
        rapport[str(a)] = m
        journal(f"origine {a} : {m['eligibles']} cas, retenue={m['retenue']}")
        lignes = []
        for s, c, p, (i, zc), total, cj, naf, nom, cr, issue, date_issue, sauv, rad, etat, conc in cas:
            v = lambda col: R.valeur(col, i)  # noqa: E731
            cr_dispo = v("marge_ebe") is not None
            ca = v("chiffre_d_affaires") if cr_dispo else None
            naf2 = naf[:2] if naf and nom == "NAFRev2" else None
            sect, taille = secteur_bdf(naf2), taille_bdf(total, ca)
            inten, cle = intensite(series, sect, taille, t0) if sect else (None, None)
            rapport[str(a)]["intensite_absente"] = rapport[str(a)].get("intensite_absente", 0) + int(inten is None)
            conf = R.conf[i] or ""
            l = {"siren": s, "origine": a, "t0": t0, "cloture": c, "parution_avis": p,
                 "type_bilan": R.type[i], "confidentialite": conf,
                 "confidentiel": int(bool(MOTIF_CONFID.search(conf))),
                 "categorie_juridique": str(cj), "naf2": naf2 or "hors_NAFRev2",
                 "age_ans": round((t0 - cr).days / 365.25, 2) if cr else None,
                 "retard_depot_jours": (p - c).days,
                 "log_total_bilan": _log(total), "total_bilan_absent": int(total is None),
                 "cr_indisponible": int(not cr_dispo),
                 "capitaux_propres_negatifs": int((v("autonomie_financiere") or 0) < 0),
                 "vetuste_absente": int(v("ratio_de_vetuste") is None),
                 "intensite_sectorielle": inten, "serie_bdf": cle, "secteur_bdf": sect, "taille_bdf": taille,
                 "origine_retenue": int(rapport[str(a)]["retenue"]),
                 "issue": issue, "date_issue": date_issue, "sauvegarde": sauv, "radiation_sans_procedure": rad,
                 "en_plan": int(etat == "PLAN"), "en_observation_sauvegarde": int(etat == "SAUV"),
                 "evenement_concurrent": conc,
                 "altman_x1": zc[0], "altman_x2": zc[1], "altman_x3": zc[2], "altman_x4": zc[3]}
            for col in GROUPE1:
                l[col] = v(col)
            for col in GROUPE2:
                l[col] = v(col) if cr_dispo else 0.0
            l["log_chiffre_affaires"] = _log(ca) if cr_dispo else 0.0
            rn = v("resultat_net")
            l["resultat_net_sur_total_bilan"] = rn / total if cr_dispo and total and rn is not None else 0.0
            lignes.append(l)
        absente = rapport[str(a)].get("intensite_absente", 0)
        if rapport[str(a)]["retenue"] and lignes and absente == len(lignes):
            # v1.0.4 : l'intensité sectorielle (annexe A, groupe 4) ne peut pas manquer partout.
            raise RuntimeError(f"origine {a} : intensité sectorielle absente pour tous les cas (séries DIREN illisibles)")
        sortie.ecrire(lignes)
        total_lignes += len(lignes)
    return total_lignes, {"origines": rapport, "bilans_exclus": motifs_bilans, "natures_jugements": info["natures"],
                    "exemples_ouvertures_indeterminees": info["exemples_ouv_indet"],
                    "seuil_couverture": seuil, "horizon_jours": HORIZON_JOURS,
                    "entrees": sorted(set(e1 + e2 + e3 + e4 + e5))}


def schema_cas():
    import pyarrow as pa

    f, i, st, d = pa.float64(), pa.int64(), pa.string(), pa.date32()
    champs = [("siren", st), ("origine", i), ("t0", d), ("cloture", d), ("parution_avis", d),
              ("type_bilan", st), ("confidentialite", st), ("confidentiel", i), ("categorie_juridique", st),
              ("naf2", st), ("age_ans", f), ("retard_depot_jours", i), ("log_total_bilan", f),
              ("total_bilan_absent", i), ("cr_indisponible", i), ("capitaux_propres_negatifs", i),
              ("vetuste_absente", i), ("intensite_sectorielle", f), ("serie_bdf", st), ("secteur_bdf", st),
              ("taille_bdf", st), ("origine_retenue", i), ("issue", i), ("date_issue", d), ("sauvegarde", i),
              ("radiation_sans_procedure", i), ("en_plan", i), ("en_observation_sauvegarde", i),
              ("evenement_concurrent", st), ("altman_x1", f), ("altman_x2", f), ("altman_x3", f), ("altman_x4", f)]
    champs += [(c, f) for c in GROUPE1 + GROUPE2] + [("log_chiffre_affaires", f),
                                                     ("resultat_net_sur_total_bilan", f)]
    return pa.schema(champs)


class Sortie:
    def __init__(self, chemin: str):
        import pyarrow.parquet as pq

        self.chemin, self.schema = chemin, schema_cas()
        self.ecrivain = pq.ParquetWriter(chemin, self.schema)

    def ecrire(self, lignes: list) -> None:
        import pyarrow as pa

        if lignes:
            self.ecrivain.write_table(pa.Table.from_pylist(lignes, schema=self.schema))

    def fermer(self) -> None:
        self.ecrivain.close()


def ecrire_rapport(dossier: str, sortie: "Sortie", lignes: int, rapport: dict) -> tuple[str, str]:
    rapport = dict(rapport)
    rapport["entrees"] = {os.path.basename(c): sha256_fichier(c) for c in rapport["entrees"]}
    rapport["sortie"] = {"fichier": os.path.basename(sortie.chemin), "lignes": lignes,
                         "sha256": sha256_fichier(sortie.chemin)}
    rapport["construit_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"
    chemin = os.path.join(dossier, f"construction-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    return chemin, hashlib.sha256(texte.encode()).hexdigest()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dossier", default=DOSSIER_DEFAUT)
    a = p.parse_args(argv)
    journal("vérification des instantanés")
    manifestes = verifier_instantanes(a.dossier)
    sortie = Sortie(os.path.join(a.dossier, "cas-dev.parquet"))
    lignes, rapport = construire(a.dossier, sortie)
    rapport["manifestes"] = manifestes
    sortie.fermer()
    chemin, h = ecrire_rapport(a.dossier, sortie, lignes, rapport)
    print("origine;bilan_connu;eligibles;retenue;defaillances;sauvegardes;ouvertures_indeterminees;"
          "radiations_sans_procedure;procedure_en_cours", file=sys.stderr)
    for o, m in rapport["origines"].items():
        print(f"{o};{m['bilan_connu']};{m['eligibles']};{m['retenue']};{m['defaillances']};"
              f"{m['sauvegardes']};{m['ouvertures_indeterminees']};{m['radiations_sans_procedure']};"
              f"{m['procedure_en_cours']}", file=sys.stderr)
    print(f"natures des jugements : {rapport['natures_jugements']}", file=sys.stderr)
    for o, m in rapport["origines"].items():
        print(f"{o} : " + json.dumps({k: v for k, v in m.items() if k.startswith(("exclus_", "en_", "concurrent_"))},
                                     ensure_ascii=False), file=sys.stderr)
    for e in rapport["exemples_ouvertures_indeterminees"]:
        print(f"  ouverture indéterminée : {e}", file=sys.stderr)
    print(f"\nRapport : {chemin}\nSHA-256 : {h}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
