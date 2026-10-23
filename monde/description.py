"""Description d'un monde : tableau structuré et texte, générés d'une même source
(spécification v3, §2.2 et §3.1, §3.6).

Le tableau est ce que reçoivent les références en code ; le texte, ce que reçoivent les
systèmes à modèle. Les deux sont produits par les mêmes fonctions à partir de la partie
publique ; aucun champ latent n'y figure. L'ordre de présentation et le lexique sont tirés par
monde.
"""

OPS_TEXTE = {">=": "au moins", "<=": "au plus", "==": "exactement"}
PROV_TEXTE = {"recent": "relevé daté récent", "ancien": "rapport daté ancien",
              "memo": "mémo non daté"}
TYPES_SOURCES = {"releve": "relevé de mesure directe", "rapport": "rapport d'exploitation",
                 "note": "note de maintenance", "journal": "journal de production"}


def tableau(monde):
    lex = monde.lexique
    ordre_v = [monde.variables[i] for i in monde.ordre["variables"]]
    variables = [{"nom": lex[v], "domaine": list(monde.domaines[v]),
                  "valeur_initiale": monde.affiche[v], "provenance": monde.provenances[v]}
                 for v in ordre_v]
    temoins = [{"nom": lex[w], "domaine": list(monde.domaines[w]), "valeur_nominale": n,
                "role": "témoin, sans effet sur l'objectif"} for w, n in monde.temoins.items()]
    actions = []
    for a in sorted(monde.actions, key=lambda a: (lex[a.cible], a.nom)):
        verbe = a.nom.split(":")[0]
        actions.append({"nom": f"{verbe} {lex[a.cible]}" if ":" in a.nom else f"{verbe} {lex[a.cible]}",
                        "effet": "verrouille la variable" if a.verrou else f"{a.delta:+d} sur {lex[a.cible]}",
                        "effets_bord": [f"{d:+d} sur {lex[v]}" for v, d in a.effets_bord],
                        "cout": a.cout, "reversible": a.reversible,
                        "inverse": _nom_action(monde, a.inverse) if a.inverse else None})
    voies = []
    for i in monde.ordre["voies"]:
        voies.append([{"variable": lex[c.var], "op": c.op, "seuil": c.seuil}
                      for c in monde.voies[i]])
    sources = [{"nom": lex[monde.sources[i]], "type": TYPES_SOURCES[monde.sources[i]]}
               for i in monde.ordre["sources"]]
    return {"variables": variables, "temoins": temoins, "actions": actions, "voies": voies,
            "budget": monde.budget, "echeance": monde.echeance, "V": monde.V,
            "valeur_z": monde.valeur_z, "bruit_mesure": monde.q, "bruit_essai": monde.qe,
            "couts_outils": dict(monde.couts_outils), "sources": sources}


def _nom_action(monde, nom):
    verbe, _, var = nom.partition(":")
    return f"{verbe} {monde.lexique[var]}" if var else verbe


def texte(monde):
    t = tableau(monde)
    l = []
    l.append(f"Objectif : satisfaire toutes les conditions d'au moins une voie au moment où vous "
             f"arrêtez, avant la période {t['echeance']}, avec un budget de {t['budget']}. "
             f"Atteindre l'objectif vaut {t['V']:g} ; chaque unité de Z obtenue vaut {t['valeur_z']:g}.")
    l.append("Variables (valeur initiale, provenance) :")
    for v in t["variables"]:
        l.append(f"- {v['nom']}, de {v['domaine'][0]} à {v['domaine'][1]} : {v['valeur_initiale']} "
                 f"({PROV_TEXTE[v['provenance']]})")
    for w in t["temoins"]:
        l.append(f"- {w['nom']}, de {w['domaine'][0]} à {w['domaine'][1]} : valeur nominale "
                 f"{w['valeur_nominale']} ({w['role']})")
    l.append("Voies (toutes les conditions d'une voie doivent tenir) :")
    for i, voie in enumerate(t["voies"], 1):
        conds = " ; ".join(f"{c['variable']} {OPS_TEXTE[c['op']]} {c['seuil']}" for c in voie)
        l.append(f"- voie {i} : {conds}")
    l.append("Actions (coût, effet, réversibilité) :")
    for a in t["actions"]:
        bord = f", effet de bord {', '.join(a['effets_bord'])}" if a["effets_bord"] else ""
        rev = f"réversible par « {a['inverse']} »" if a["reversible"] else "irréversible"
        l.append(f"- {a['nom']} : coût {a['cout']}, {a['effet']}{bord}, {rev}")
    o = t["couts_outils"]
    l.append(f"Outils : mesurer une variable ou l'objectif (atteint ou non) (coût {o['mesurer']}, juste avec la "
             f"probabilité {t['bruit_mesure']:g}, sinon valeur tirée uniformément dans le domaine, qui "
             f"peut retomber sur la vraie) ; essayer une action à petite échelle sans changer "
             f"l'état (coût {o['essayer']}, sens de variation de chaque variable : le vrai avec la "
             f"probabilité {t['bruit_essai']:g}, sinon un sens tiré uniformément) ; lire une source (coût "
             f"{o['lire']}) ; attendre (coût {o['attendre']}) ; arrêter. Une commande par période.")
    l.append("Sources : " + " ; ".join(f"{s['nom']} ({s['type']})" for s in t["sources"]) + ".")
    l.append("Avertissement : cette description peut être incomplète et contenir une affirmation "
             "fausse ; des sources peuvent se contredire.")
    return "\n".join(l)
