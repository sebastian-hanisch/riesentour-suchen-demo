"""Savings (Clarke und Wright, 1964), parallele Fassung mit Formparameter λ (aus savings-gegen-split-demo, Stück 4 der Linie, kopiert, umbenannt und gekürzt auf das, was dieses Stück braucht: der Maßstab
„Savings λ = 1“ und „bestes von 9 λ“ aus den Bändern der Stücke 4 und 5).

Ersparnis eines Paares (i, j): s(i, j) = d(0,i) + d(0,j) - lam * d(i,j) (mu = nu = 0). Jeder Kunde fährt zuerst allein; die Paare mit s > 0 werden in absteigender Ersparnis abgearbeitet (Gleichstand: kleineres i, dann
kleineres j); ein Paar legt zwei Routen zusammen, wenn i und j in verschiedenen Routen stehen, beide am Rand ihrer Route und die Last in ein Fahrzeug passt; Routen dürfen dabei umgedreht werden."""

from dataclasses import dataclass

import numpy as np

from rsk_scenario import Instance, distance_matrix

MERGED, SAME_ROUTE, NO_END, CAPACITY = "merged", "same", "no_end", "capacity"          # Ausgänge eines Paares


@dataclass(frozen=True)
class Params:
    lam: float = 1.0
    mu: float = 0.0
    nu: float = 0.0


STANDARD = Params()


# ----------------------------------------------------------------------------------------------------------------------------------------- Ersparnisse

def pair_arrays(inst: Instance, params: Params = STANDARD):
    """Alle Paare i < j (Kundennummern ab 1) als Arrays (i, j, s) in der Reihenfolge von numpy.triu_indices; s kann auch negativ sein."""
    D = distance_matrix(inst)
    q = np.array(inst.demand, dtype=float)
    iu, ju = np.triu_indices(inst.n, 1)
    d0 = D[0][1:]
    s = d0[iu] + d0[ju] - params.lam * D[iu + 1, ju + 1] + params.mu * np.abs(d0[iu] - d0[ju]) + params.nu * (q[iu] + q[ju]) / q.mean()
    return iu + 1, ju + 1, s


def _sorted_pairs(i, j, s):
    order = np.lexsort((j, i, -s))
    return [(float(s[k]), int(i[k]), int(j[k])) for k in order if s[k] > 0]


def savings_list(inst: Instance, params: Params = STANDARD) -> list[tuple[float, int, int]]:
    """Alle Paare i < j mit s(i, j) > 0, absteigend nach Ersparnis, Gleichstand: kleinere Nummern zuerst."""
    return _sorted_pairs(*pair_arrays(inst, params))


# ----------------------------------------------------------------------------------------------------------------------------------------- parallel

def _merge(inst: Instance, routes, where, load, i: int, j: int) -> str:
    """Ein Paar abarbeiten (verändert routes, where und load); Rückgabe: der Ausgang."""
    ri, rj = where[i], where[j]
    if ri == rj:
        return SAME_ROUTE
    a, b = routes[ri], routes[rj]
    if not ((a[0] == i or a[-1] == i) and (b[0] == j or b[-1] == j)):
        return NO_END
    if load[ri] + load[rj] > inst.capacity:
        return CAPACITY
    if a[-1] == i and b[0] == j:
        new = a + b
    elif a[0] == i and b[-1] == j:
        new = b + a
    elif a[0] == i and b[0] == j:
        new = a[::-1] + b
    else:
        new = a + b[::-1]
    routes[ri] = new
    load[ri] += load[rj]
    del routes[rj], load[rj]
    for c in new:
        where[c] = ri
    return MERGED


def _start(inst: Instance):
    routes = {i: [i] for i in range(1, inst.n + 1)}
    return routes, {i: i for i in routes}, {i: inst.demand[i - 1] for i in routes}


def run_pairs(inst: Instance, pairs) -> tuple[tuple[int, ...], ...]:
    """Die Paare in dieser Reihenfolge abarbeiten (ohne Spur); Ergebnis: die Routen."""
    routes, where, load = _start(inst)
    for _, i, j in pairs:
        _merge(inst, routes, where, load, i, j)
    return tuple(tuple(r) for r in routes.values())


def savings_routes(inst: Instance, params: Params = STANDARD, pairs=None) -> tuple[tuple[int, ...], ...]:
    """Dieselben Routen wie `savings(...).routes`, ohne Spur (schneller, für Mehrfachläufe)."""
    return run_pairs(inst, pairs if pairs is not None else savings_list(inst, params))


# ----------------------------------------------------------------------------------------------------------------------------------------- sequentiell


# ----------------------------------------------------------------------------------------------------------------------------------------- Mehrfachläufe

LAMS = tuple(round(0.4 + 0.2 * k, 1) for k in range(9))          # die neun λ-Werte von „bestes von 9 λ“: 0,4 bis 2,0
