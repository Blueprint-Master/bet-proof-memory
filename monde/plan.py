"""Planification à information parfaite (R∞) et évaluation de plans en boucle ouverte.

Sous une hypothèse h, le monde est déterministe : la valeur optimale de la suite se calcule par
programmation dynamique sur (état, période, budget restant). Seules les actions `agir` et
l'arrêt sont utiles à information parfaite (mesurer, lire, essayer ne rapportent rien quand on
connaît le monde ; attendre non plus, les délais valant une période dans cette famille).
"""

from modele import appliquer, valeur_terminale


class Planificateur:
    """Programmation dynamique mémorisée pour un monde et une hypothèse."""

    def __init__(self, monde, h):
        self.monde = monde
        self.h = h
        self.memo = {}
        self.trans = {}
        self.agir = [(a.nom, a.cout) for a in monde.actions]
        self.cout_max = max(c for _, c in self.agir)
        self.term = {}

    def valeur(self, etat, t, reste):
        """Valeur optimale de la suite (gains futurs, coûts futurs déduits) et première action
        (None = arrêter)."""
        m = self.monde
        reste = min(reste, self.cout_max * (m.echeance - t))  # budget non contraignant : clé réduite
        cle = (etat, t, reste)
        if cle in self.memo:
            return self.memo[cle]
        vt = self.term.get(etat)
        if vt is None:
            vt = self.term[etat] = valeur_terminale(m, etat)
        meilleur = (vt, None)
        if t < m.echeance:
            for nom, cout in self.agir:
                if cout > reste:
                    continue
                cle_t = (etat, nom)
                suivant = self.trans.get(cle_t)
                if suivant is None:
                    suivant = self.trans[cle_t] = appliquer(m, self.h, etat, nom)[0]
                if suivant == etat:
                    continue
                v = -cout + self.valeur(suivant, t + 1, reste - cout)[0]
                if v > meilleur[0] + 1e-12:
                    meilleur = (v, nom)
        self.memo[cle] = meilleur
        return meilleur

    def plan(self, etat, t, reste):
        """Suite d'actions optimale en boucle ouverte (déterministe sous h)."""
        actions = []
        while True:
            _, a = self.valeur(etat, t, reste)
            if a is None:
                return actions
            actions.append(a)
            reste -= self.monde.action(a).cout
            etat, _ = appliquer(self.monde, self.h, etat, a)
            t += 1


def evaluer_plan(monde, h, etat, t, reste, actions):
    """Valeur (gains futurs moins coûts futurs) d'un plan exécuté tel quel sous h ; une action
    hors budget ou au-delà de l'échéance est sautée (elle serait refusée)."""
    cout = 0
    for nom in actions:
        a = monde.action(nom)
        if t >= monde.echeance or a.cout > reste:
            break
        etat, _ = appliquer(monde, h, etat, nom)
        cout += a.cout
        reste -= a.cout
        t += 1
    return valeur_terminale(monde, etat) - cout
