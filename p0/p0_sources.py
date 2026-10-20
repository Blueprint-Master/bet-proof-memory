"""P0 v1.3, couverture des sources complémentaires pour les bilans de la population.

Questions, pour chaque année de clôture et chaque niveau de confidentialité des
bilans (ratios BCE/INPI) :
1. Sirene, unités légales : le SIREN est-il connu ? Sa catégorie juridique est-elle
   l'une des formes retenues par P1 ? Le code NAF et la date de création sont-ils
   renseignés ?
2. Sirene, historique des unités légales : le SIREN y figure-t-il ? Combien ont
   changé de NAF ou de catégorie juridique depuis 2014 (enjeu point-in-time) ?
3. Bilans détaillés de Signaux Faibles : le couple (SIREN, date de clôture) y
   figure-t-il ? (source candidate du total de bilan, absent des ratios.) Type
   de la colonne « liasse », lu dans le schéma seul.

Métadonnées de disponibilité seules : présence, remplissage, comptages de
changements. Aucun montant, aucune valeur de variable, aucune issue.
Les parquets sont lus colonne par colonne, par requêtes HTTP Range.
"""

import argparse
import http.client
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0_faisabilite import SOURCE_SF_PARQUET, FichierHttpRange  # noqa: E402
from p0_jointure import charger_bilans  # noqa: E402

_SIRENE = "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/"
SIRENE_UL = _SIRENE + "20261001-073325/stock-stockunitelegale-parquet.parquet"
SIRENE_UL_HISTO = _SIRENE + "20261001-073513/stock-stockunitelegalehistorique-parquet.parquet"

ANNEES_DEFAUT = "2019,2022"
ESSAIS = 5
ATTENTE_S = 10


def journal(message: str) -> None:
    """Progression sur la sortie d'erreur, horodatée (v1.0.1)."""
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def avec_reprise(fonction, *args, essais=ESSAIS, attente_s=ATTENTE_S, **kwargs):
    """Rejoue une lecture idempotente après une coupure réseau (v1.0.1).

    Constaté le 20/10/2026 : « Connection reset by peer » en cours d'exécution.
    Les lectures sont idempotentes (Range sur un fichier figé, export CSV
    rejoué en entier), donc rejouer ne change pas le résultat.
    """
    for i in range(1, essais + 1):
        try:
            return fonction(*args, **kwargs)
        except (urllib.error.URLError, http.client.HTTPException, EOFError, OSError) as e:
            if i == essais:
                raise
            journal(f"coupure réseau ({e}), essai {i + 1}/{essais} dans {attente_s * i} s")
            time.sleep(attente_s * i)


class FichierAvecReprise(FichierHttpRange):
    """Chaque requête Range est rejouée en cas de coupure (v1.0.1)."""

    def read(self, n: int = -1) -> bytes:
        pos = self.pos
        def lire():
            self.pos = pos
            return FichierHttpRange.read(self, n)
        return avec_reprise(lire)
DEBUT_CHANGEMENTS = "2014-01-01"
# Formes de P1 (SARL, SA, SAS, SNC), catégories juridiques Insee de niveau III.
# Liste à figer en v1.3 ; ce rapport en mesure la couverture.
PREFIXES_P1 = ("54", "55", "56", "57")
CODES_P1 = {"5202", "5203"}


def forme_p1(cj) -> bool:
    cj = "" if cj is None else str(cj).strip()
    return cj.startswith(PREFIXES_P1) or cj in CODES_P1


def _vrai(v) -> bool:
    return v is True or (isinstance(v, str) and v.strip().lower() in ("true", "1", "o", "oui"))


def _siren(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _colonnes(pf, voulues: list[str]) -> list[str]:
    noms = set(pf.schema_arrow.names)
    manquantes = [c for c in voulues if c not in noms]
    if manquantes:
        raise RuntimeError(f"colonnes absentes {manquantes} ; présentes : {sorted(noms)}")
    return voulues


def _filtrer(batch, cible):
    """Ne garde que les lignes dont le SIREN est dans la cible (filtre vectoriel)."""
    import pyarrow as pa
    import pyarrow.compute as pc

    col = batch.column("siren")
    if pa.types.is_integer(col.type):
        valeurs = pa.array(sorted(cible), type=col.type)
    else:
        valeurs = pa.array([f"{s:09d}" for s in sorted(cible)], type=pa.string())
        col = pc.cast(col, pa.string())
    return batch.filter(pc.is_in(col, value_set=valeurs))


def lire_sirene_ul(url: str, cible: set[int]) -> tuple[dict, dict]:
    import pyarrow.parquet as pq

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    cols = _colonnes(pf, ["siren", "categorieJuridiqueUniteLegale",
                          "activitePrincipaleUniteLegale", "dateCreationUniteLegale"])
    vus = {}
    for batch in pf.iter_batches(columns=cols, batch_size=500_000):
        b = _filtrer(batch, cible).to_pydict()
        for s, cj, naf, cr in zip(b["siren"], b["categorieJuridiqueUniteLegale"],
                                  b["activitePrincipaleUniteLegale"], b["dateCreationUniteLegale"]):
            vus[_siren(s)] = (forme_p1(cj), naf not in (None, ""), cr not in (None, ""))
    return vus, {"lignes": pf.metadata.num_rows, "octets_lus": f.octets_lus, "requetes": f.requetes}


def lire_sirene_histo(url: str, cible: set[int]) -> tuple[dict, dict]:
    import pyarrow.parquet as pq

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    cols = _colonnes(pf, ["siren", "dateDebut", "changementActivitePrincipaleUniteLegale",
                          "changementCategorieJuridiqueUniteLegale"])
    vus = {}
    for batch in pf.iter_batches(columns=cols, batch_size=500_000):
        b = _filtrer(batch, cible).to_pydict()
        for s, debut, ch_naf, ch_cj in zip(b["siren"], b["dateDebut"],
                                           b["changementActivitePrincipaleUniteLegale"],
                                           b["changementCategorieJuridiqueUniteLegale"]):
            s = _siren(s)
            naf, cj = vus.get(s, (False, False))
            recent = debut is not None and str(debut)[:10] >= DEBUT_CHANGEMENTS
            vus[s] = (naf or (recent and _vrai(ch_naf)), cj or (recent and _vrai(ch_cj)))
    return vus, {"lignes": pf.metadata.num_rows, "octets_lus": f.octets_lus, "requetes": f.requetes}


def lire_sf(url: str, cles: dict) -> tuple[set, dict]:
    import pyarrow.parquet as pq

    from p0_jointure import cle

    f = avec_reprise(FichierAvecReprise, url)
    pf = pq.ParquetFile(f)
    cols = _colonnes(pf, ["siren", "date_cloture_exercice"])
    annees = set(cles)
    trouves = set()
    for batch in pf.iter_batches(columns=cols, batch_size=500_000):
        b = batch.to_pydict()
        for s, d in zip(b["siren"], b["date_cloture_exercice"]):
            s = _siren(s)
            if s is None or d is None:
                continue
            if isinstance(d, str):
                try:
                    d = dt.date.fromisoformat(d[:10])
                except ValueError:
                    continue
            if isinstance(d, dt.datetime):
                d = d.date()
            if d.year in annees:
                k = cle(s, d)
                if k in cles[d.year]:
                    trouves.add(k)
    types = {c: str(pf.schema_arrow.field(c).type) for c in pf.schema_arrow.names}
    return trouves, {"lignes": pf.metadata.num_rows, "types": types,
                     "octets_lus": f.octets_lus, "requetes": f.requetes}


def _part(k, n):
    return round(k / n, 4) if n else None


def executer(annees: list[int], ouvrir=urllib.request.urlopen, url_ul=SIRENE_UL,
             url_histo=SIRENE_UL_HISTO, url_sf=SOURCE_SF_PARQUET) -> dict:
    journal("export des clés de bilans (ratios)")
    cles, _ = avec_reprise(charger_bilans, annees, ouvrir)
    cible = {k // 100_000_000 for a in cles for k in cles[a]}
    journal(f"{len(cible)} SIREN ; lecture de Sirene, unités légales")
    ul, meta_ul = lire_sirene_ul(url_ul, cible)
    journal("lecture de l'historique Sirene")
    histo, meta_histo = lire_sirene_histo(url_histo, cible)
    journal("lecture des bilans détaillés de Signaux Faibles")
    sf, meta_sf = lire_sf(url_sf, cles)
    journal("calcul des parts")
    par_annee = {}
    for a in annees:
        groupes = {}
        for k, conf in cles.get(a, {}).items():
            groupes.setdefault(conf, []).append(k)
        res = {}
        for conf, ks in sorted(groupes.items()):
            sirens = {k // 100_000_000 for k in ks}
            n = len(sirens)
            u = [ul[s] for s in sirens if s in ul]
            h = [histo[s] for s in sirens if s in histo]
            res[conf] = {
                "bilans": len(ks),
                "sirens": n,
                "sirene_ul_trouves": _part(len(u), n),
                "forme_p1": _part(sum(x[0] for x in u), n),
                "naf_renseigne": _part(sum(x[1] for x in u), n),
                "creation_renseignee": _part(sum(x[2] for x in u), n),
                "historique_trouves": _part(len(h), n),
                "changement_naf_depuis_2014": _part(sum(x[0] for x in h), n),
                "changement_cj_depuis_2014": _part(sum(x[1] for x in h), n),
                "signaux_faibles_trouves": _part(sum(k in sf for k in ks), len(ks)),
            }
        par_annee[str(a)] = res
    return {
        "objet": "P0 v1.3, couverture de Sirene et des bilans détaillés pour les bilans des ratios",
        "regle": "présence, remplissage et comptages de changements seuls ; aucun montant ; aucune issue",
        "execute_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": {"sirene_ul": {"url": url_ul, **meta_ul},
                    "sirene_ul_historique": {"url": url_histo, **meta_histo},
                    "signaux_faibles": {"url": url_sf, **meta_sf}},
        "par_annee": par_annee,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--annees", default=ANNEES_DEFAUT)
    a = p.parse_args(argv)
    rapport = executer([int(x) for x in a.annees.split(",") if x.strip()])
    texte = json.dumps(rapport, ensure_ascii=False, indent=2, sort_keys=True)
    chemin = f"p0-sources-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + "\n")
    champs = ["bilans", "sirene_ul_trouves", "forme_p1", "naf_renseigne", "creation_renseignee",
              "historique_trouves", "changement_naf_depuis_2014", "changement_cj_depuis_2014",
              "signaux_faibles_trouves"]
    print("annee;confidentialite;" + ";".join(champs), file=sys.stderr)
    for an, groupes in rapport["par_annee"].items():
        for conf, v in groupes.items():
            print(f"{an};{conf};" + ";".join(str(v[c]) for c in champs), file=sys.stderr)
    print("types SF : " + json.dumps(rapport["sources"]["signaux_faibles"]["types"], ensure_ascii=False),
          file=sys.stderr)
    print(f"\nRapport : {chemin}\nSHA-256 : {hashlib.sha256((texte + chr(10)).encode()).hexdigest()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
