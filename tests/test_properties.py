"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Operatoren, Kodierungen, Umnummerieren, Budget, Verbesserung durch die Lokalsuche."""

import random

import pytest

import rsk_algorithm as A
import rsk_constants as C
import rsk_search as G
from rsk_scenario import Instance, make_instance

ABS = 1e-6


@pytest.mark.parametrize("seed", range(10))
def test_order_crossover_gives_a_permutation_with_the_kept_segment(seed):
    rng = random.Random(seed)
    n = rng.randint(3, 15)
    p1, p2 = list(range(1, n + 1)), list(range(1, n + 1))
    rng.shuffle(p1)
    rng.shuffle(p2)
    assert sorted(G.ox(rng, p1, p2)) == list(range(1, n + 1))
    fixed = G.ox(rng, p1, p2, (1, n - 1))
    assert fixed[1:n] == p1[1:n] and sorted(fixed) == list(range(1, n + 1))        # das Teilstück von p1 bleibt
    assert G.ox(rng, p1, p1, (0, 0)) == p1                                          # gleiche Eltern, gleiches Kind


@pytest.mark.parametrize("seed", range(10))
def test_route_crossover_covers_every_customer_exactly_once(seed):
    P = G.Prob(make_instance(20, seed % 3, seed % 2, 3, seed, 90))
    rng = random.Random(seed)
    order_a, order_b = list(range(1, 21)), list(range(1, 21))
    rng.shuffle(order_a)
    rng.shuffle(order_b)
    a, b = G.split(P, order_a)[1], G.split(P, order_b)[1]
    child = G.route_crossover(rng, a, b)
    assert sorted(c for r in child for c in r) == list(range(1, 21)) and all(r for r in child) and G.is_valid_plan(P, child)


def test_the_sequence_encoding_reaches_every_plan(hand):
    """Dominanz: die zusammengesetzten Routen eines zulässigen Plans sind eine Folge, deren Split nicht länger ist als der Plan."""
    P = G.Prob(hand)
    plan = [[1, 2], [3, 4], [5, 6]]
    cost, _ = G.split(P, [c for r in plan for c in r])
    assert cost <= G.plan_len(P, plan) + ABS


@pytest.mark.parametrize("kind", C.KINDS)
def test_relabelling_the_customers_does_not_change_the_optimum_and_no_run_goes_below_it(kind):
    inst = make_instance(8, 1, 0, 3, 5, 90)
    n = inst.n
    perm = list(range(1, n + 1))
    perm = perm[3:] + perm[:3][::-1]
    xy = [inst.xy[0]] + [None] * n
    dem = [0] * n
    for old in range(1, n + 1):
        xy[perm[old - 1]] = inst.xy[old]
        dem[perm[old - 1] - 1] = inst.demand[old - 1]
    other = Instance(tuple(xy), tuple(dem), inst.capacity)
    assert A.exact_cvrp(other).cost == pytest.approx(A.exact_cvrp(inst).cost, abs=ABS)
    for i in (inst, other):
        assert G.run(G.Prob(i), kind, 300, 1).cost >= A.exact_cvrp(i).cost - ABS


def test_a_larger_budget_is_never_worse_and_shares_the_first_children():
    P = G.Prob(make_instance(12, 2, 1, 3, 2, 90))
    for kind in C.ALL_KINDS:
        small, big = G.run(P, kind, 250, 2), G.run(P, kind, 1000, 2)
        assert big.cost <= small.cost + ABS and dict(big.trace)[250] == small.cost         # gleicher Seed: die ersten 250 Kinder sind dieselben


def test_local_search_improves_random_plans():
    P = G.Prob(make_instance(25, 1, 0, 3, 1, 90))
    rng = random.Random(1)
    gains = 0
    for _ in range(5):
        order = list(range(1, 26))
        rng.shuffle(order)
        start = G.next_fit(P, order)
        gains += G.plan_len(P, start) - G.plan_len(P, G.local_search(P, start))
    assert gains > 0


def test_baldwin_and_lamarck_use_the_same_evaluation():
    P = G.Prob(make_instance(12, 1, 1, 3, 6, 90))
    sl, sb = G.run(P, "SL", 300, 6), G.run(P, "SB", 300, 6)
    for r in (sl, sb):
        assert G.is_valid_plan(P, [list(x) for x in r.routes]) and G.plan_len(P, [list(x) for x in r.routes]) == pytest.approx(r.cost, abs=ABS)
    assert sl.trace[0][0] == sb.trace[0][0] == 250
