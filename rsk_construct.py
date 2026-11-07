"""Erzeuger der Reihenfolgen für den Vergleich (aus riesentouren-erzeugen-demo und split-gegen-fuellen-demo kopiert und umbenannt, ohne `larger_place`).

Gleichstände: bei Kunden die kleinere Nummer, bei Stellen die kleinere Stelle. Eine Stelle p heißt: vor den p-ten Kunden der Folge."""

import rsk_algorithm as A
import rsk_constants as C
from rsk_scenario import Instance, distance_matrix


def insert_split_order(inst: Instance) -> tuple[int, ...]:
    """Einfügen nach Split: Kunden in absteigender Entfernung vom Depot, jeder an der Stelle mit den kleinsten Split-Kosten der Teilfolge."""
    D = distance_matrix(inst)
    sequence = sorted(range(1, inst.n + 1), key=lambda c: (-D[0][c], c))
    order: tuple[int, ...] = ()
    for c in sequence:
        best = None
        for p in range(len(order) + 1):
            trial = order[:p] + (c,) + order[p:]
            cost = A.split(inst, trial).cost
            if best is None or cost < best[0] - C.TIE:
                best = (cost, trial)
        order = best[1]
    return order
