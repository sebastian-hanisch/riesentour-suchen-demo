"""Orakel (unabhängiger Rechenweg): der Split gegen die Aufzählung aller Zerlegungen, die Dominanz (Minimum über alle Folgen gleich dem exakten Optimum), jede Fassung liefert vollständige, kapazitätsgerechte Pläne
mit gemessener Länge gleich der Bewertung, Lokalsuche nie schlechter und idempotent, Läufe bitgleich bei gleichem Seed."""

import itertools
import math
import random

import pytest

import rsk_algorithm as A
import rsk_constants as C
import rsk_search as G
from rsk_scenario import make_instance

ABS = 1e-6


def oracle_len(inst, route):
    xy = inst.xy
    pts = [xy[0]] + [xy[c] for c in route] + [xy[0]]
    return sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))


def oracle_split(inst, order):
    """Alle Zerlegungen der Folge in aufeinanderfolgende Routen mit eigener Länge und Lastprüfung."""
    n = len(order)
    best = math.inf
    for mask in range(1 << (n - 1)):
        cuts = [0] + [i + 1 for i in range(n - 1) if mask >> i & 1] + [n]
        parts = [order[a:b] for a, b in zip(cuts, cuts[1:])]
        if all(sum(inst.demand[c - 1] for c in r) <= inst.capacity for r in parts):
            best = min(best, sum(oracle_len(inst, r) for r in parts))
    return best


@pytest.mark.parametrize("seed", range(6))
def test_split_equals_the_enumeration_of_all_compositions(seed):
    inst = make_instance(8, seed % 3, seed % 2, 3, seed, 90)
    P = G.Prob(inst)
    rng = random.Random(seed)
    for _ in range(8):
        order = list(range(1, 9))
        rng.shuffle(order)
        cost, routes = G.split(P, order)
        assert cost == pytest.approx(oracle_split(inst, order), abs=ABS)
        assert [c for r in routes for c in r] == order and G.is_valid_plan(P, routes) and sum(oracle_len(inst, r) for r in routes) == pytest.approx(cost, abs=ABS)


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_dominance_minimum_over_all_orders_is_the_exact_optimum(seed):
    inst = make_instance(7, 1, seed % 2, 3, seed, 90)
    P = G.Prob(inst)
    best = min(G.split(P, p)[0] for p in itertools.permutations(range(1, 8)))
    assert best == pytest.approx(A.exact_cvrp(inst).cost, abs=ABS)


@pytest.mark.parametrize("kind", C.ALL_KINDS)
@pytest.mark.parametrize("n,seed", [(8, 0), (12, 1), (25, 2)])
def test_every_kind_gives_a_valid_plan_of_the_stated_cost(kind, n, seed):
    inst = make_instance(n, seed % 3, seed % 2, 3, seed, 90)
    P = G.Prob(inst)
    res = G.run(P, kind, 300, seed)
    routes = [list(r) for r in res.routes]
    assert G.is_valid_plan(P, routes) and sum(oracle_len(inst, r) for r in routes) == pytest.approx(res.cost, abs=ABS)
    if n <= 12:
        assert res.cost >= A.exact_cvrp(inst).cost - ABS                      # kein Plan unter dem Optimum


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_every_kind_finds_the_optimum_of_the_hand_instance(kind, hand):
    P = G.Prob(hand)
    best = min(G.run(P, kind, 1500, seed).cost for seed in range(4))
    assert best == pytest.approx(A.exact_cvrp(hand).cost, abs=ABS)


@pytest.mark.parametrize("seed", range(5))
def test_local_search_is_never_worse_valid_and_idempotent(seed):
    inst = make_instance(25, seed % 3, seed % 2, 3, seed, 90)
    P = G.Prob(inst)
    rng = random.Random(seed)
    order = list(range(1, 26))
    rng.shuffle(order)
    start = G.next_fit(P, order)
    trace: list = []
    out = G.local_search(P, start, trace=trace)
    assert G.is_valid_plan(P, out) and G.plan_len(P, out) <= G.plan_len(P, start) + ABS
    costs = [G.plan_len(P, start)] + [t["cost"] for t in trace]
    assert all(b < a - 1e-10 for a, b in zip(costs, costs[1:])) and costs[-1] == pytest.approx(G.plan_len(P, out), abs=ABS)       # jeder Zug verbessert, die Kosten der Spur stimmen
    assert all(G.is_valid_plan(P, [list(r) for r in t["routes"]]) and G.plan_len(P, [list(r) for r in t["routes"]]) == pytest.approx(t["cost"], abs=ABS) for t in trace)
    again: list = []
    assert G.plan_len(P, G.local_search(P, out, trace=again)) == pytest.approx(G.plan_len(P, out), abs=ABS) and not again


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_runs_are_bit_identical_for_the_same_seed_and_differ_for_another(kind):
    P = G.Prob(make_instance(12, 1, 0, 3, 4, 90))
    a, b, c = G.run(P, kind, 400, 7), G.run(P, kind, 400, 7), G.run(P, kind, 400, 8)
    assert a.cost == b.cost and a.routes == b.routes and a.trace == b.trace
    assert a.trace != c.trace or a.routes != c.routes                        # mit Lokalsuche enden kleine Instanzen oft im selben Optimum, aber auf anderem Weg


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_the_trace_is_monotone_and_ends_at_the_budget(kind):
    P = G.Prob(make_instance(12, 2, 1, 3, 3, 90))
    res = G.run(P, kind, 1200, 3)
    costs = [c for _, c in res.trace]
    assert [k for k, _ in res.trace] == [250, 500, 1000, 1200] and all(b <= a + 1e-12 for a, b in zip(costs, costs[1:]))
    assert res.cost <= costs[-1] + ABS and G.cost_at(res, 500) == costs[1] and G.cost_at(res, 123) is None
