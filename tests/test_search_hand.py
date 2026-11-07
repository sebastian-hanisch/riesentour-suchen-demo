"""Handwerte der Suche an der Handinstanz und einem Quadrat: Split der Eltern, Ordnungskreuzung, Routenkreuzung, Lokalsuche (2-opt), Füllen bis voll, Prüfer."""

import math

import pytest

import rsk_search as G
from conftest import OPTIMUM


class FixedRng:
    """Zufall, der immer die ersten Elemente nimmt (für die Handrechnung der Routenkreuzung)."""

    def sample(self, population, k):
        return list(population)[:k]

    def random(self):
        return 0.0

    def randrange(self, n):
        return 0


def test_split_of_the_hand_example_parents_and_child(hand):
    P = G.Prob(hand)
    ca, ra = G.split(P, (3, 5, 2, 6, 4, 1))
    cb, rb = G.split(P, (1, 6, 4, 3, 5, 2))
    cc, rc = G.split(P, (1, 4, 2, 6, 3, 5))
    assert ca == pytest.approx(48.7306, abs=5e-5) and ra == [[3, 5, 2, 6], [4, 1]]
    assert cb == pytest.approx(58.8797, abs=5e-5) and rb == [[1], [6, 4, 3], [5, 2]]
    assert cc == pytest.approx(OPTIMUM, abs=1e-9) and cc == pytest.approx(44.3623, abs=5e-5) and rc == [[1, 4], [2, 6, 3, 5]]


def test_order_crossover_by_hand():
    # p1 = (1 2 3 4 5), p2 = (5 4 3 2 1), Schnitt Plätze 2 bis 3 (0-basiert 1 bis 2): Teilstück (2 3) bleibt, der Rest in der Reihenfolge von p2 ohne 2 und 3: 5, 4, 1
    assert G.ox(None, [1, 2, 3, 4, 5], [5, 4, 3, 2, 1], (1, 2)) == [5, 2, 3, 4, 1]
    # das Handbeispiel: A = (3 5 2 6 4 1), B = (1 6 4 3 5 2), Schnitt Plätze 3 bis 4 (0-basiert 2 bis 3): Teilstück (2 6), Rest aus B ohne 2 und 6: 1, 4, 3, 5
    assert G.ox(None, [3, 5, 2, 6, 4, 1], [1, 6, 4, 3, 5, 2], (2, 3)) == [1, 4, 2, 6, 3, 5]
    assert G.ox(None, [1, 2, 3], [3, 2, 1], (0, 2)) == [1, 2, 3] and G.ox(None, [1, 2, 3], [3, 2, 1], (1, 1)) == [3, 2, 1]


def test_route_crossover_by_hand():
    child = G.route_crossover(FixedRng(), [[1, 2], [3, 4], [5]], [[5, 1], [3], [2, 4]])
    assert child == [[1, 2], [5], [3], [4]]                       # k = 1: die Route (1 2) von A; von B bleiben (5), (3), (4); (5 1) verliert die 1, (2 4) verliert die 2


def test_local_search_removes_the_crossing_by_hand(square):
    P = G.Prob(square)
    before = G.plan_len(P, [[1, 3, 2, 4]])
    assert before == pytest.approx(6 * math.sqrt(2) + 2) and before == pytest.approx(10.4853, abs=5e-5)
    trace: list = []
    out = G.local_search(P, [[1, 3, 2, 4]], trace=trace)
    assert G.plan_len(P, out) == pytest.approx(6 + 2 * math.sqrt(2)) and G.plan_len(P, out) == pytest.approx(8.8284, abs=5e-5)
    # Die Durchmusterung beginnt bei Platz 1: path = (0 1 3 2 4 0), i = 1, j = 3 (Stück 1 3 2): Kanten (0,1) und (2,4) werden durch (0,2) und (1,4) ersetzt, Gewinn (sqrt2 + 2 sqrt2) - (sqrt2 + 2) = 2 sqrt2 - 2 = 0,8284;
    # die Route heißt danach (2 3 1 4) mit Länge 4 sqrt2 + 4 = 9,6569; ein zweiter 2-opt-Zug führt zum Quadrat.
    first = trace[0]
    assert first["kind"] == "2-opt" and first["customers"] == (1, 2)
    assert first["gain"] == pytest.approx(2 * math.sqrt(2) - 2) and first["gain"] == pytest.approx(0.8284, abs=5e-5)
    assert first["routes"] == ((2, 3, 1, 4),) and first["cost"] == pytest.approx(4 * math.sqrt(2) + 4) and first["cost"] == pytest.approx(9.6569, abs=5e-5)
    assert len(trace) == 2 and trace[1]["kind"] == "2-opt" and trace[1]["gain"] == pytest.approx(4 * math.sqrt(2) - 4 - (2 * math.sqrt(2) - 2) + 0.0, abs=1e-9)
    assert all(s["gain"] > 0 for s in trace) and trace[-1]["cost"] == pytest.approx(G.plan_len(P, out))


def test_local_search_relocate_by_hand(hand):
    """Kunde 5 (-1,-1) liegt nahe am Depot; allein in einer Route kostet er 2 sqrt2 = 2,8284, in (2 6 3) eingefügt nach 3 weniger (Umweg unter 2,83): die Lokalsuche verschiebt ihn."""
    P = G.Prob(hand)
    out = G.local_search(P, [[1, 4], [2, 6, 3], [5]])
    assert sorted(c for r in out for c in r) == [1, 2, 3, 4, 5, 6] and len(out) == 2
    assert G.plan_len(P, out) == pytest.approx(OPTIMUM, abs=1e-9)


def test_next_fit_and_validity_check(hand):
    P = G.Prob(hand)
    assert G.next_fit(P, (1, 2, 3, 4, 5, 6)) == [[1, 2, 3], [4, 5, 6]]          # Last 3, 5, 7 | 4, 6, 7 (Kapazität 7)
    assert G.is_valid_plan(P, [[1, 4], [2, 6, 3, 5]]) and not G.is_valid_plan(P, [[1, 4], [2, 6, 3]]) and not G.is_valid_plan(P, [[1, 2, 3, 4], [5, 6]]) and not G.is_valid_plan(P, [[1, 4], [2, 6, 3, 5, 5]])
    assert G.route_len(P, []) == 0.0 and G.plan_len(P, [[1, 4], [2, 6, 3, 5]]) == pytest.approx(OPTIMUM, abs=1e-9)


def test_mutation_helpers_keep_every_customer(hand):
    import random
    P = G.Prob(hand)
    rng = random.Random(5)
    for _ in range(50):
        assert sorted(G.mutate_seq(rng, [1, 2, 3, 4, 5, 6])) == [1, 2, 3, 4, 5, 6]
        routes = G.mutate_routes(P, rng, [[1, 4], [2, 6, 3, 5]])
        assert G.is_valid_plan(P, routes)
