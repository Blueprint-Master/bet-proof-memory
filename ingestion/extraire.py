"""Phase 5, étape 1 : extraction des sources brutes en instantanés figés.

Chaque sous-commande lit une source publique et écrit un instantané parquet
dans le dossier de données (hors du dépôt), avec un manifeste : fichiers,
effectifs, empreintes SHA-256, source, requête, date d'extraction. L'empreinte
du manifeste est publiée au registre avant toute construction de cas (P10).

Sous-commandes :
  ratios   tous les champs des ratios BCE/INPI, clôtures 2014 à l'année en cours
  sf       bilans détaillés (Signaux Faibles) : clés et totaux de bilan seuls
           (EE, 180, CO-1A, 110-112), lus dans la liasse
  sirene   historique des unités légales et date de création, restreints aux
           SIREN présents dans les ratios
  bodacc   avis de dépôt des comptes (toutes dates) ; procédures collectives,
           conciliations et radiations PARUES AVANT LE 30/09/2022 seulement

GARDE DU SCELLÉ (P4, P10). Toute annonce de procédure parue à partir du
30/09/2022 (première origine du scellé) serait une issue du scellé ou une
information sur elle. Elle n'est pas lue avant l'ouverture du scellé : la date
est inscrite en dur, et aucun paramètre ne permet de la dépasser. Une annonce
parue avant cette date est antérieure à toute origine du scellé.

Minimisation : aucun champ nominatif n'est extrait du BODACC (ni personnes, ni
adresses) ; les SIREN et les dates suffisent au protocole.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "..", "p0"))
from p0_faisabilite import SOURCE_SF_PARQUET, _get_json  # noqa: E402
from p0_jointure import BODACC, RATIOS, flux_csv  # noqa: E402
from p0_sources import SIRENE_UL, SIRENE_UL_HISTO, FichierAvecReprise, avec_reprise, journal  # noqa: E402

DOSSIER_DEFAUT = os.path.expanduser("~/bpm-donnees")
GARDE_SCELLE = dt.date(2022, 9, 30)  # première origine du scellé : rien de daté à partir de ce jour
PREMIERE_CLOTURE = 2014
# Procédures collectives : code « collective » observé, « pcl » selon le schéma de la DILA ;
# les deux sont lus (v1.0.1, constaté dans le connecteur registre_annonces).
FAMILLES_PROCEDURES = ("collective", "pcl", "conciliation", "radiation")
FAMILLES_TOUTES = ("dpc",) + FAMILLES_PROCEDURES
FAMILLES_OBLIGATOIRES = {"dpc", "radiation"}  # plus : collective et pcl ne peuvent être vides ensemble
BDF_EXPORT = "https://webstat.banque-france.fr/export/csv/fr/catalogue/diren"
BDF_PREFIXE = "DIREN.M.FR.DE.UL.DF.03.N."
CHAMPS_BODACC = ("id", "publicationavis", "familleavis", "familleavis_lib", "dateparution",
                 "numeroannonce", "registre", "tribunal", "jugement", "depot", "radiationaurcs")
CLES_LIASSE = ("EE", "180", "CO-1A", "110-112")
LOT = 200_000


# --- Écriture des instantanés ----------------------------------------------

def sha256_fichier(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


class Ecrivain:
    """Écrit des lignes (dict) en parquet par lots ; colonnes fixées à l'avance."""

    def __init__(self, chemin: str, colonnes: dict):
        import pyarrow as pa

        self.chemin, self.colonnes, self.lignes = chemin, colonnes, 0
        self.schema = pa.schema([(n, t) for n, t in colonnes.items()])
        self.tampon = {n: [] for n in colonnes}
        self.ecrivain = None

    def ajouter(self, ligne: dict) -> None:
        for n in self.colonnes:
            self.tampon[n].append(ligne.get(n))
        self.lignes += 1
        if len(self.tampon[next(iter(self.colonnes))]) >= LOT:
            self._vider()

    def _vider(self) -> None:
        import pyarrow as pa
        import pyarrow.parquet as pq

        if not self.tampon[next(iter(self.colonnes))]:
            return
        table = pa.table({n: pa.array(v, type=self.schema.field(n).type) for n, v in self.tampon.items()},
                         schema=self.schema)
        if self.ecrivain is None:
            self.ecrivain = pq.ParquetWriter(self.chemin, self.schema)
        self.ecrivain.write_table(table)
        self.tampon = {n: [] for n in self.colonnes}

    def fermer(self) -> dict:
        import pyarrow.parquet as pq

        self._vider()
        if self.ecrivain is None:  # aucun enregistrement : fichier vide mais valide
            pq.write_table(self.schema.empty_table(), self.chemin)
        else:
            self.ecrivain.close()
        return {"fichier": os.path.basename(self.chemin), "lignes": self.lignes,
                "sha256": sha256_fichier(self.chemin)}


def ecrire_manifeste(dossier: str, source: str, fichiers: list, details: dict) -> tuple[str, str]:
    m = {"source": source, "extrait_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
         "garde_scelle": GARDE_SCELLE.isoformat(), "fichiers": fichiers, **details}
    texte = json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    chemin = os.path.join(dossier, f"manifeste-{source}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    return chemin, hashlib.sha256(texte.encode()).hexdigest()


def _nombre(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _pa():
    import pyarrow as pa
    return pa


# --- Ratios -------------------------------------------------------------------

def extraire_ratios(dossier: str, annees, ouvrir=urllib.request.urlopen) -> tuple:
    pa = _pa()
    champs = [f["name"] for f in avec_reprise(_get_json, RATIOS, ouvrir).get("fields", [])]
    texte = {"siren", "date_cloture_exercice", "confidentiality", "type_bilan"}
    colonnes = {c: (pa.string() if c in texte or not champs else pa.float64()) for c in champs}
    fichiers = []
    for a in annees:
        journal(f"ratios, clôtures {a}")
        where = f"date_cloture_exercice >= date'{a}-01-01' and date_cloture_exercice < date'{a + 1}-01-01'"

        def une_annee():
            e = Ecrivain(os.path.join(dossier, f"ratios-{a}.parquet"), colonnes)
            for ligne in flux_csv(RATIOS, "*", where, ouvrir):
                e.ajouter({c: (ligne.get(c) if c in texte else _nombre(ligne.get(c))) for c in colonnes})
            return e.fermer()

        fichiers.append(avec_reprise(une_annee))
    return fichiers, {"url": RATIOS, "annees": list(annees), "champs": champs}


# --- BODACC -------------------------------------------------------------------

def where_bodacc(famille: str) -> str:
    if famille == "dpc":
        return 'familleavis="dpc"'
    # Garde du scellé, inscrite dans la requête même.
    return f'familleavis="{famille}" and dateparution < date\'{GARDE_SCELLE.isoformat()}\''


def extraire_bodacc(dossier: str, ouvrir=urllib.request.urlopen, familles=FAMILLES_TOUTES) -> tuple:
    pa = _pa()
    presents = {f["name"] for f in avec_reprise(_get_json, BODACC, ouvrir).get("fields", [])}
    champs = [c for c in CHAMPS_BODACC if c in presents]
    manquants = [c for c in CHAMPS_BODACC if c not in presents]
    colonnes = {c: pa.string() for c in champs}
    fichiers, effectifs = [], {}
    inconnues = [f for f in familles if f not in FAMILLES_TOUTES]
    if inconnues:
        raise ValueError(f"familles inconnues : {inconnues}")
    for famille in familles:
        journal(f"BODACC, famille {famille}")
        select = ",".join(c for c in champs if famille == "dpc" or c != "depot")
        cols = {c: t for c, t in colonnes.items() if c in select.split(",")}

        def une_famille():
            e = Ecrivain(os.path.join(dossier, f"bodacc-{famille}.parquet"), cols)
            for ligne in flux_csv(BODACC, select, where_bodacc(famille), ouvrir):
                d = (ligne.get("dateparution") or "")[:10]
                if famille != "dpc" and (not d or d >= GARDE_SCELLE.isoformat()):
                    raise RuntimeError(f"garde du scellé violée par la source : parution {d!r}")
                e.ajouter(ligne)
            return e.fermer()

        f = avec_reprise(une_famille)
        if f["lignes"] == 0 and famille in FAMILLES_OBLIGATOIRES:
            raise RuntimeError(f"famille {famille!r} vide : code de famille à vérifier")
        if f["lignes"] == 0:
            journal(f"famille {famille!r} vide : rapportée, non bloquante")
        fichiers.append(f)
        effectifs[famille] = f["lignes"]
    if {"collective", "pcl"} <= set(familles) and effectifs["collective"] + effectifs["pcl"] == 0:
        raise RuntimeError("aucune procédure collective sous « collective » ni « pcl »")
    return fichiers, {"url": BODACC, "champs": champs, "champs_absents": manquants,
                      "requetes": {f: where_bodacc(f) for f in familles}, "effectifs": effectifs}


# --- Sirene ---------------------------------------------------------------------

def sirens_des_ratios(dossier: str) -> "object":
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    morceaux = []
    for nom in sorted(os.listdir(dossier)):
        if nom.startswith("ratios-") and nom.endswith(".parquet"):
            morceaux.append(pq.read_table(os.path.join(dossier, nom), columns=["siren"]).column("siren"))
    if not morceaux:
        raise RuntimeError("extraire d'abord les ratios")
    return pc.unique(pa.chunked_array([c for m in morceaux for c in m.chunks]))


def _filtrer_parquet(url: str, colonnes: list, sirens, sortie: str) -> dict:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    absentes = [c for c in colonnes if c not in pf.schema_arrow.names]
    if absentes:
        raise RuntimeError(f"colonnes absentes {absentes}")
    ecrivain, lignes = None, 0
    for batch in pf.iter_batches(columns=colonnes, batch_size=500_000):
        col = pc.cast(batch.column("siren"), pa.string())
        b = batch.filter(pc.is_in(col, value_set=pc.cast(sirens, pa.string())))
        if b.num_rows:
            t = pa.Table.from_batches([b])
            if ecrivain is None:
                ecrivain = pq.ParquetWriter(sortie, t.schema)
            ecrivain.write_table(t)
            lignes += b.num_rows
    if ecrivain is None:
        raise RuntimeError(f"aucune ligne retenue dans {url}")
    ecrivain.close()
    return {"fichier": os.path.basename(sortie), "lignes": lignes, "sha256": sha256_fichier(sortie),
            "octets_lus": f.octets_lus}


def extraire_sirene(dossier: str, url_ul=SIRENE_UL, url_histo=SIRENE_UL_HISTO) -> tuple:
    sirens = sirens_des_ratios(dossier)
    journal(f"Sirene, {len(sirens)} SIREN ; historique")
    h = _filtrer_parquet(url_histo, ["siren", "dateDebut", "dateFin", "categorieJuridiqueUniteLegale",
                                     "activitePrincipaleUniteLegale",
                                     "nomenclatureActivitePrincipaleUniteLegale"],
                         sirens, os.path.join(dossier, "sirene-historique.parquet"))
    journal("Sirene, dates de création")
    u = _filtrer_parquet(url_ul, ["siren", "dateCreationUniteLegale"], sirens,
                         os.path.join(dossier, "sirene-creation.parquet"))
    return [h, u], {"urls": [url_histo, url_ul], "sirens": len(sirens)}


# --- Bilans détaillés (Signaux Faibles) ---------------------------------------------

def extraire_sf(dossier: str, url=SOURCE_SF_PARQUET) -> tuple:
    """Clés et totaux de bilan seuls ; la liasse est filtrée en vectoriel, clé par clé."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    sortie = os.path.join(dossier, "sf-totaux.parquet")
    schema = pa.schema([("siren", pa.string()), ("date_cloture_exercice", pa.date32()),
                        ("type_bilan", pa.string()), ("confidentiality", pa.string())]
                       + [(k, pa.float64()) for k in CLES_LIASSE])
    ecrivain, lignes = pq.ParquetWriter(sortie, schema), 0
    for g in range(pf.metadata.num_row_groups):
        if g % 20 == 0:
            journal(f"bilans détaillés, groupe {g + 1}/{pf.metadata.num_row_groups}")
        t = avec_reprise(pf.read_row_group, g,
                         columns=["siren", "date_cloture_exercice", "type_bilan", "confidentiality", "liasse"])
        liasse = t.column("liasse").combine_chunks()
        # Indice de ligne de chaque entrée de la liasse, par les décalages (offsets) ;
        # list_parent_indices n'accepte pas le type map dans toutes les versions.
        import numpy as np

        off = liasse.offsets.to_numpy(zero_copy_only=False)
        parents = pa.array(np.repeat(np.arange(len(off) - 1), np.diff(off)))
        debut, fin = int(off[0]), int(off[-1])
        cles, valeurs = liasse.keys.slice(debut, fin - debut), liasse.items.slice(debut, fin - debut)
        colonnes = {}
        for k in CLES_LIASSE:
            masque = pc.equal(cles, k)
            idx = pc.filter(parents, masque).to_numpy(zero_copy_only=False)
            val = pc.filter(valeurs, masque).to_numpy(zero_copy_only=False)
            col = [None] * t.num_rows
            for i, v in zip(idx, val):
                col[int(i)] = float(v)
            colonnes[k] = pa.array(col, type=pa.float64())
        sortie_t = pa.table({
            "siren": pc.cast(t.column("siren"), pa.string()),
            "date_cloture_exercice": pc.cast(t.column("date_cloture_exercice"), pa.date32()),
            "type_bilan": pc.cast(t.column("type_bilan"), pa.string()),
            "confidentiality": pc.cast(t.column("confidentiality"), pa.string()),
            **colonnes}, schema=schema)
        ecrivain.write_table(sortie_t)
        lignes += t.num_rows
    ecrivain.close()
    return ([{"fichier": os.path.basename(sortie), "lignes": lignes, "sha256": sha256_fichier(sortie),
              "octets_lus": f.octets_lus}], {"url": url, "cles_liasse": list(CLES_LIASSE)})


# --- Banque de France (défaillances, export public du jeu DIREN) ----------------

def extraire_bdf(dossier: str, ouvrir=urllib.request.urlopen, url=BDF_EXPORT) -> tuple:
    """Séries nationales « cumul 12 mois, brut », par secteur et taille ; date de mise à jour gardée."""
    import csv
    import gzip
    import io

    pa = _pa()
    cols = {"series_key": pa.string(), "time_period": pa.string(), "obs_value": pa.float64(),
            "updated_at": pa.string(), "OBS_STATUS": pa.string()}

    def lire():
        req = urllib.request.Request(url, headers={"User-Agent": "bet-proof-memory-ingestion/1.0"})
        r = io.BufferedReader(ouvrir(req, timeout=600))
        if r.peek(2)[:2] == b"\x1f\x8b":
            r = gzip.GzipFile(fileobj=r)
        texte = io.TextIOWrapper(r, encoding="utf-8-sig", newline="")
        echantillon = texte.readline()
        sep = ";" if echantillon.count(";") > echantillon.count(",") else ","
        lecteur = csv.DictReader(io.StringIO(echantillon), delimiter=sep)
        entetes = lecteur.fieldnames
        e = Ecrivain(os.path.join(dossier, "bdf-diren.parquet"), cols)
        for ligne in csv.DictReader(texte, fieldnames=entetes, delimiter=sep):
            if (ligne.get("series_key") or "").startswith(BDF_PREFIXE):
                e.ajouter({**ligne, "obs_value": _nombre(ligne.get("obs_value"))})
        return e.fermer(), entetes

    f, entetes = avec_reprise(lire)
    if f["lignes"] == 0:
        raise RuntimeError(f"aucune série {BDF_PREFIXE}* dans l'export ; colonnes : {entetes}")
    return [f], {"url": url, "prefixe": BDF_PREFIXE, "colonnes_source": entetes}


# --- Ligne de commande ------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("source", choices=["ratios", "bodacc", "sirene", "sf", "bdf"])
    p.add_argument("--familles", default=",".join(FAMILLES_TOUTES), help="BODACC seulement")
    p.add_argument("--dossier", default=DOSSIER_DEFAUT)
    a = p.parse_args(argv)
    os.makedirs(a.dossier, exist_ok=True)
    if a.source == "ratios":
        fichiers, details = extraire_ratios(a.dossier, range(PREMIERE_CLOTURE, dt.date.today().year + 1))
    elif a.source == "bodacc":
        fichiers, details = extraire_bodacc(a.dossier, familles=tuple(x for x in a.familles.split(",") if x))
    elif a.source == "sirene":
        fichiers, details = extraire_sirene(a.dossier)
    elif a.source == "bdf":
        fichiers, details = extraire_bdf(a.dossier)
    else:
        fichiers, details = extraire_sf(a.dossier)
    nom = a.source if a.source != "bodacc" or a.familles == ",".join(FAMILLES_TOUTES) else "bodacc-" + a.familles.replace(",", "-")
    chemin, h = ecrire_manifeste(a.dossier, nom, fichiers, details)
    for f in fichiers:
        print(f"{f['fichier']} : {f['lignes']} lignes", file=sys.stderr)
    print(f"\nManifeste : {chemin}\nSHA-256 : {h}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
