#!/usr/bin/env python3
"""
P0, porte de faisabilité des données (protocole Q1 v1, juge du réel).

RÈGLE DE P0 : ne lire que des MÉTADONNÉES. Schémas, nombres de lignes,
taux de remplissage, plages de dates. Jamais une issue (aucun comptage de
procédures collectives), jamais la distribution d'une variable explicative.

Trois sources :
  A. Bilans détaillés Signaux Faibles (parquet, 2,6 Go) : seul le PIED du
     fichier est lu, par requêtes HTTP Range. Il contient le schéma, le nombre
     de lignes et, par groupe de lignes, les statistiques de chaque colonne
     (nombre de nulls, minimum, maximum). Aucune donnée n'est téléchargée.
  B. Ratios BCE/INPI (API Opendatasoft de data.economie.gouv.fr) : liste des
     champs, effectif, plages et remplissage des champs de type date.
  C. BODACC annonces commerciales (API Opendatasoft de la DILA) : liste des
     champs et plage des dates de parution, tous types d'annonces confondus.

Verdict (P0 et P12 du protocole, amendement v1.1 du 19/10/2026) : part des
bilans portant une date de dépôt.
  >= 90 %  : analyse principale limitée aux dépôts datés.
  50-90 %  : analyse principale limitée aux dépôts datés, biais de sélection
             déclaré dans chaque résultat (une date imputée ne sert jamais
             qu'en sensibilité, P2).
  < 50 %   : arrêt.
  aucune   : aucune date de dépôt identifiée, arrêt (P2 n'aurait plus
             d'analyse principale possible).

Dépendances : Python 3.10+, pyarrow. Aucun autre accès réseau que les trois
sources ci-dessus. Sortie : rapport JSON sur la sortie standard et dans un
fichier daté, avec son empreinte SHA-256 à publier dans le registre.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request

SOURCE_SF_PARQUET = (
    "https://static.data.gouv.fr/resources/"
    "donnees-financieres-detaillees-des-entreprises-format-parquet/"
    "20260210-082327/export-detail-bilan.parquet"
)
SOURCE_RATIOS_ODS = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/ratios_inpi_bce"
SOURCE_BODACC_ODS = "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales"

SEUIL_PRINCIPAL = 0.90
SEUIL_ARRET = 0.50
DELAI_HTTP_S = 60
AGENT = "juge-du-reel-p0/1.0"

# Une date de dépôt ou de publication des comptes, sous les graphies probables.
MOTIF_DEPOT = re.compile(r"(d[eé]p[oô]t|depos|publi|transmission|reception|r[eé]ception)", re.I)
MOTIF_DATE = re.compile(r"date|dt_|_dt$|jour", re.I)


# --- Lecture HTTP Range : un fichier distant vu comme un fichier local -------

class FichierHttpRange(io.RawIOBase):
    """Fichier distant en lecture seule, chaque read() devient une requête Range.

    Sert à lire le pied d'un parquet sans le télécharger. Compte les octets lus,
    pour prouver dans le rapport que seules quelques centaines de kilo-octets
    ont transité.
    """

    def __init__(self, url: str, ouvrir=urllib.request.urlopen):
        super().__init__()
        self.url = url
        self._ouvrir = ouvrir
        self.pos = 0
        self.octets_lus = 0
        self.requetes = 0
        requete = urllib.request.Request(url, method="HEAD", headers={"User-Agent": AGENT})
        with self._ouvrir(requete, timeout=DELAI_HTTP_S) as r:
            taille = r.headers.get("Content-Length")
            if taille is None:
                raise RuntimeError("taille du fichier distant inconnue (pas de Content-Length)")
            self.taille = int(taille)
            if r.headers.get("Accept-Ranges", "").lower() != "bytes":
                raise RuntimeError("le serveur n'annonce pas les requêtes Range (Accept-Ranges: bytes)")

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.taille + offset
        else:
            raise ValueError(f"whence invalide : {whence}")
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if self.pos >= self.taille:
            return b""
        fin = self.taille - 1 if n is None or n < 0 else min(self.taille, self.pos + n) - 1
        requete = urllib.request.Request(
            self.url, headers={"Range": f"bytes={self.pos}-{fin}", "User-Agent": AGENT}
        )
        with self._ouvrir(requete, timeout=DELAI_HTTP_S) as r:
            if getattr(r, "status", 206) != 206:
                raise RuntimeError(f"réponse {getattr(r, 'status', '?')} au lieu de 206 : le serveur ignore Range")
            donnees = r.read()
        self.requetes += 1
        self.octets_lus += len(donnees)
        self.pos += len(donnees)
        return donnees

    def readinto(self, b) -> int:
        donnees = self.read(len(b))
        b[: len(donnees)] = donnees
        return len(donnees)


def _valeur_json(v):
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except UnicodeDecodeError:
            return v.hex()
    return str(v)


def metadonnees_parquet(fichier) -> dict:
    """Schéma, effectif et statistiques de colonnes, lus dans le pied seul."""
    import pyarrow.parquet as pq

    meta = pq.ParquetFile(fichier).metadata
    schema = meta.schema.to_arrow_schema()
    colonnes = {}
    for i, champ in enumerate(schema):
        nulls, minimum, maximum, stats_completes = 0, None, None, True
        for g in range(meta.num_row_groups):
            col = meta.row_group(g).column(i)
            s = col.statistics
            if s is None or not s.has_null_count:
                stats_completes = False
                continue
            nulls += s.null_count
            if s.has_min_max:
                minimum = s.min if minimum is None else min(minimum, s.min)
                maximum = s.max if maximum is None else max(maximum, s.max)
        colonnes[champ.name] = {
            "type": str(champ.type),
            "nulls": nulls if stats_completes else None,
            "remplissage": (1 - nulls / meta.num_rows) if stats_completes and meta.num_rows else None,
            "min": _valeur_json(minimum),
            "max": _valeur_json(maximum),
        }
    return {"lignes": meta.num_rows, "groupes_de_lignes": meta.num_row_groups, "colonnes": colonnes}


# --- API Opendatasoft : métadonnées et agrégats seulement -----------------

def _decompresser(corps: bytes, encodage: str | None) -> bytes:
    """Rend le corps en clair. Certains serveurs compressent en gzip même sans
    Accept-Encoding (constaté le 19/10/2026 sur bpm-prod) : on se fie à
    l'en-tête ET à la signature gzip (1f 8b), pas à la seule politesse du serveur."""
    if (encodage or "").lower() == "gzip" or corps[:2] == b"\x1f\x8b":
        return gzip.decompress(corps)
    return corps


def _get_json(url: str, ouvrir=urllib.request.urlopen) -> dict:
    requete = urllib.request.Request(
        url, headers={"User-Agent": AGENT, "Accept": "application/json", "Accept-Encoding": "gzip"}
    )
    with ouvrir(requete, timeout=DELAI_HTTP_S) as r:
        entetes = getattr(r, "headers", None)
        encodage = entetes.get("Content-Encoding") if entetes is not None else None
        return json.loads(_decompresser(r.read(), encodage).decode("utf-8"))


def _agregat(base: str, select: str, where: str | None, ouvrir) -> dict:
    params = {"select": select, "limit": "1"}
    if where:
        params["where"] = where
    rep = _get_json(f"{base}/records?{urllib.parse.urlencode(params)}", ouvrir)
    resultats = rep.get("results") or []
    return resultats[0] if resultats else {}


def metadonnees_ods(base: str, ouvrir=urllib.request.urlopen, remplissage_dates: bool = True) -> dict:
    """Champs, effectif, et pour chaque champ date : plage et remplissage."""
    meta = _get_json(base, ouvrir)
    champs = [{"nom": f.get("name"), "type": f.get("type"), "libelle": f.get("label")} for f in meta.get("fields", [])]
    total = _agregat(base, "count(*) as n", None, ouvrir).get("n")
    dates = {}
    for f in champs:
        if f["type"] not in ("date", "datetime"):
            continue
        nom = f["nom"]
        plage = _agregat(base, f"min({nom}) as min, max({nom}) as max", None, ouvrir)
        entree = {"min": plage.get("min"), "max": plage.get("max")}
        if remplissage_dates:
            n = _agregat(base, "count(*) as n", f"{nom} is not null", ouvrir).get("n")
            entree["non_nuls"] = n
            entree["remplissage"] = (n / total) if total and n is not None else None
        dates[nom] = entree
    return {"effectif": total, "champs": champs, "dates": dates}


# --- Verdict -------------------------------------------------------------

def champs_depot(noms_et_libelles: dict[str, str]) -> list[str]:
    """Champs qui ressemblent à une date de dépôt ou de publication des comptes."""
    return sorted(
        nom for nom, libelle in noms_et_libelles.items()
        if MOTIF_DEPOT.search(nom or "") or MOTIF_DEPOT.search(libelle or "")
    )


def verdict(remplissage_depot: float | None) -> dict:
    """Verdict de P0 selon le protocole Q1 v1.1. Aucun cas n'est laissé à l'interprétation."""
    if remplissage_depot is None:
        return {
            "code": "arret-sans-date",
            "regle": "aucune date de dépôt identifiée : l'analyse principale de P2 est impossible, "
                     "une date imputée ne servant qu'en sensibilité ; arrêt (P12, v1.1)",
        }
    if remplissage_depot >= SEUIL_PRINCIPAL:
        return {"code": "principal-dates", "regle": f"remplissage {remplissage_depot:.1%} >= 90 % : analyse principale limitée aux dépôts datés"}
    if remplissage_depot < SEUIL_ARRET:
        return {"code": "arret", "regle": f"remplissage {remplissage_depot:.1%} < 50 % : arrêt (P12)"}
    return {
        "code": "principal-dates-biais-declare",
        "regle": f"remplissage {remplissage_depot:.1%} entre 50 et 90 % : analyse principale limitée aux dépôts datés, "
                 "biais de sélection déclaré dans chaque résultat (v1.1)",
    }


# --- Exécution -------------------------------------------------------------

def executer(sources: list[str]) -> dict:
    rapport = {
        "objet": "P0, porte de faisabilité, protocole Q1 v1 du juge du réel",
        "regle": "métadonnées seules ; aucune issue lue ; aucune distribution de variable lue",
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": {},
    }
    candidats_depot = {}

    if "sf" in sources:
        try:
            f = FichierHttpRange(SOURCE_SF_PARQUET)
            m = metadonnees_parquet(f)
            m["url"] = SOURCE_SF_PARQUET
            m["octets_lus"] = f.octets_lus
            m["requetes_http"] = f.requetes
            m["taille_fichier"] = f.taille
            rapport["sources"]["signaux_faibles_parquet"] = m
            for nom, c in m["colonnes"].items():
                if MOTIF_DEPOT.search(nom) and c["remplissage"] is not None:
                    candidats_depot[f"sf:{nom}"] = c["remplissage"]
        except Exception as e:  # noqa: BLE001 : le rapport doit dire l'échec, pas le masquer
            rapport["sources"]["signaux_faibles_parquet"] = {"url": SOURCE_SF_PARQUET, "echec": repr(e)}

    if "ratios" in sources:
        try:
            m = metadonnees_ods(SOURCE_RATIOS_ODS)
            m["url"] = SOURCE_RATIOS_ODS
            rapport["sources"]["ratios_bce_inpi"] = m
            libelles = {c["nom"]: c["libelle"] for c in m["champs"]}
            for nom in champs_depot(libelles):
                d = m["dates"].get(nom)
                if d and d.get("remplissage") is not None:
                    candidats_depot[f"ratios:{nom}"] = d["remplissage"]
        except Exception as e:  # noqa: BLE001
            rapport["sources"]["ratios_bce_inpi"] = {"url": SOURCE_RATIOS_ODS, "echec": repr(e)}

    if "bodacc" in sources:
        try:
            # Remplissage des dates non calculé : seule la plage de parution importe ici.
            m = metadonnees_ods(SOURCE_BODACC_ODS, remplissage_dates=False)
            m["url"] = SOURCE_BODACC_ODS
            rapport["sources"]["bodacc_annonces_commerciales"] = m
        except Exception as e:  # noqa: BLE001
            rapport["sources"]["bodacc_annonces_commerciales"] = {"url": SOURCE_BODACC_ODS, "echec": repr(e)}

    rapport["candidats_date_de_depot"] = candidats_depot
    meilleur = max(candidats_depot.values()) if candidats_depot else None
    rapport["verdict"] = verdict(meilleur)
    return rapport


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sources", default="sf,ratios,bodacc", help="sous-ensemble de sf,ratios,bodacc")
    p.add_argument("--sortie", default=None, help="chemin du rapport JSON (défaut : p0-rapport-AAAAMMJJ-HHMMSS.json)")
    a = p.parse_args(argv)

    rapport = executer([s.strip() for s in a.sources.split(",") if s.strip()])
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)
    chemin = a.sortie or f"p0-rapport-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + "\n")
    empreinte = hashlib.sha256((texte + "\n").encode("utf-8")).hexdigest()
    print(texte)
    print(f"\nRapport : {chemin}\nSHA-256 : {empreinte}\nVerdict : {rapport['verdict']['code']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
