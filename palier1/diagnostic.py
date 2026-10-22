"""Palier 1 de la boucle de supervision : diagnostic des écarts à D, sans issue ni poids.

Pour chaque cas où T1 ou B s'écarte de D, ou commet une violation, affiche le type de cas, le
scénario, les décisions des quatre systèmes, les violations, les appels d'outils de T1, la fin
de trace de B et le début de la justification. N'affiche jamais l'issue ni le poids : ce
diagnostic peut être lu avant la décision sur le tirage principal sans rien révéler de plus que
les mesures agrégées. Affiche aussi la consommation par système.
"""

import argparse
import json
import sys

import verificateurs as vf

SYSTEMES = ["D", "T0", "T1", "B"]


def main(argv=None) -> int:
    pa = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    pa.add_argument("--cas", required=True)
    pa.add_argument("--executions", required=True)
    pa.add_argument("--lgd", type=float, required=True)
    a = pa.parse_args(argv)
    with open(a.cas, encoding="utf-8") as f:
        cas = json.load(f)
    with open(a.executions, encoding="utf-8") as f:
        exe = [json.loads(l) for l in f if l.strip()]
    par = {(e["systeme"], e["cas"]): e for e in exe}
    fs = vf.fiches(cas, exe, a.lgd, SYSTEMES)
    print("CONSOMMATION")
    for s in SYSTEMES:
        es = [e for e in exe if e["systeme"] == s]
        som = lambda k: sum((e["cout"].get(k) or 0) for e in es)  # noqa: E731
        print(f"  {s} : {len(es)} exécutions, {som('appels_modele')} appels, entrée {som('jetons_entree')}, "
              f"sortie {som('jetons_sortie')} (raisonnement {som('jetons_raisonnement')}), "
              f"tronquées {som('reponses_tronquees')}, {round(som('secondes'))} s, "
              f"modèles {sorted({m for e in es for m in e['cout'].get('modeles_servis', [])})}")
    print("ÉCARTS ET VIOLATIONS (T1, B)")
    n = 0
    for k in sorted(cas):
        d = {s: fs[s][k]["decision"] for s in SYSTEMES}
        viol = {s: [t for t, v in fs[s][k]["violations"].items() if v] for s in ("T1", "B")}
        if d["T1"] == d["D"] and d["B"] == d["D"] and not viol["T1"] and not viol["B"]:
            continue
        n += 1
        t1, b = par.get(("T1", k), {}), par.get(("B", k), {})
        just = ""
        try:
            just = json.loads(t1.get("sortie") or "")["justification"][:240]
        except (ValueError, TypeError, KeyError):
            just = repr((t1.get("sortie") or "")[:240])
        print(f"- {k} [{cas[k]['type']}, {cas[k]['scenario']}] D={d['D']} T0={d['T0']} T1={d['T1']} B={d['B']}"
              f" | violations T1 {viol['T1']} B {viol['B']}")
        print(f"    T1 outils : {[(j['outil'], j.get('date'), j.get('args'), j['statut']) for j in t1.get('journal', [])]}")
        print(f"    T1 justification : {just}")
        print(f"    B trace : {[(x['etat'], x.get('verdict') or x.get('motif')) for x in b.get('trace', [])][-4:]}"
              f" ; bloqués {len(b.get('bloques', []))}")
    print(f"{n} cas listés sur {len(cas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
