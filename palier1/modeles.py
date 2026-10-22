"""Palier 1 de la boucle de supervision : adaptateurs de modèles de langage.

Deux familles d'interface, sans dépendance extérieure (urllib) :
  CompatibleOpenAI  POST {base}/chat/completions (Mistral, OpenAI, xAI, Gemini en mode compatible)
  Anthropic         POST https://api.anthropic.com/v1/messages
La clé est lue dans une variable d'environnement, jamais écrite dans un fichier du dépôt.
Température 0 ; version du modèle épinglée par son nom exact ; nombre maximal de jetons de
sortie fixé. Un appel n'est compté qu'une fois réussi ; les erreurs 429 et 5xx sont reprises
(attente 2, 4, 8, 16, 32 s), puis l'erreur est levée et l'exécution du cas s'arrête.
"""

import json
import os
import time
import urllib.error
import urllib.request

from systemes import Modele

SORTIE_MAX = 1500
REPRISES = (2, 4, 8, 16, 32)


def _post(url: str, entetes: dict, corps: dict, delai: int = 120) -> dict:
    donnees = json.dumps(corps).encode()
    for attente in (*REPRISES, None):
        req = urllib.request.Request(url, data=donnees, headers={"Content-Type": "application/json", **entetes})
        try:
            with urllib.request.urlopen(req, timeout=delai) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if attente is None or not (e.code == 429 or e.code >= 500):
                raise
        except (urllib.error.URLError, TimeoutError):
            if attente is None:
                raise
        time.sleep(attente)
    raise RuntimeError("inatteignable")


def fusionner(messages: list) -> list:
    """Fusionne les messages consécutifs d'un même rôle (certaines interfaces exigent l'alternance)."""
    out = []
    for m in messages:
        if out and out[-1]["role"] == m["role"]:
            out[-1] = {"role": m["role"], "content": out[-1]["content"] + "\n\n" + m["content"]}
        else:
            out.append(dict(m))
    return out


class CompatibleOpenAI(Modele):
    def __init__(self, base: str, modele: str, cle_env: str):
        self.base, self.modele, self.cle_env = base.rstrip("/"), modele, cle_env
        self.nom = f"{modele} via {base}"

    def appeler(self, messages: list) -> dict:
        cle = os.environ[self.cle_env]
        r = _post(f"{self.base}/chat/completions", {"Authorization": f"Bearer {cle}"},
                  {"model": self.modele, "messages": fusionner(messages), "temperature": 0, "max_tokens": SORTIE_MAX})
        u = r.get("usage") or {}
        return {"texte": r["choices"][0]["message"]["content"] or "", "jetons_entree": u.get("prompt_tokens", 0),
                "jetons_sortie": u.get("completion_tokens", 0), "modele_servi": r.get("model")}


class Anthropic(Modele):
    def __init__(self, modele: str, cle_env: str = "ANTHROPIC_API_KEY"):
        self.modele, self.cle_env, self.nom = modele, cle_env, f"{modele} via api.anthropic.com"

    def appeler(self, messages: list) -> dict:
        systeme = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        reste = fusionner([m for m in messages if m["role"] != "system"])
        r = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": os.environ[self.cle_env], "anthropic-version": "2023-06-01"},
                  {"model": self.modele, "system": systeme, "messages": reste, "temperature": 0,
                   "max_tokens": SORTIE_MAX})
        u = r.get("usage") or {}
        texte = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
        return {"texte": texte, "jetons_entree": u.get("input_tokens", 0), "jetons_sortie": u.get("output_tokens", 0),
                "modele_servi": r.get("model")}
