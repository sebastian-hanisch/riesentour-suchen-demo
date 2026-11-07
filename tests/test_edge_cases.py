"""Randfälle: n = 1, 2, 3, Population größer als die Zahl der Folgen, Kinderzahl 0, Kapazität für alle, Nachfrage gleich Kapazität."""

import pytest

import rsk_constants as C
import rsk_search as G
from rsk_scenario import Instance


def _inst(xy, demand, cap):
    return Instance(tuple(xy), tuple(demand), cap)


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_one_customer(kind):
    P = G.Prob(_inst(((0.0, 0.0), (3.0, 4.0)), (2,), 5))
    res = G.run(P, kind, 20, 0)
    assert res.routes == ((1,),) and res.cost == pytest.approx(10.0)


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_two_and_three_customers_with_a_population_larger_than_the_number_of_orders(kind):
    for xy, dem in ((((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)), (1, 1)), (((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)), (1, 1, 1))):
        P = G.Prob(_inst(xy, dem, 10))
        res = G.run(P, kind, 50, 1)                                        # 2 oder 6 Folgen, Population 30: die Anfangspopulation enthält Duplikate statt endlos zu suchen
        assert G.is_valid_plan(P, [list(r) for r in res.routes]) and len(res.routes) == 1


@pytest.mark.parametrize("kind", C.ALL_KINDS)
def test_zero_children_returns_the_best_of_the_initial_population(kind):
    P = G.Prob(_inst(((0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (5.0, 5.0)), (1, 1, 1), 2))
    res = G.run(P, kind, 0, 3)
    assert res.children == 0 and res.trace == ((0, res.cost),) and G.is_valid_plan(P, [list(r) for r in res.routes])


def test_capacity_for_everyone_and_demand_equal_to_capacity():
    xy = ((0.0, 0.0), (5.0, 0.0), (0.0, 5.0), (-5.0, 0.0), (0.0, -5.0))
    big = G.Prob(_inst(xy, (1, 1, 1, 1), 100))
    assert all(len(G.run(big, k, 200, 1).routes) == 1 for k in C.KINDS)
    tight = G.Prob(_inst(xy, (4, 4, 4, 4), 4))
    for k in C.ALL_KINDS:
        assert sorted(G.run(tight, k, 100, 1).routes) == [(1,), (2,), (3,), (4,)]


def test_split_with_a_single_feasible_decomposition():
    P = G.Prob(_inst(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (3, 3, 3), 3))
    cost, routes = G.split(P, [1, 2, 3])
    assert routes == [[1], [2], [3]] and cost == pytest.approx(2 + 4 + 6)


def test_one_route_for_everyone_reaches_the_square():
    """Quadrat um das Depot, eine Route für alle: die kürzeste Rundreise ist das Quadrat, 6 + 2 sqrt2."""
    sq = _inst(((0.0, 0.0), (1.0, 1.0), (1.0, -1.0), (-1.0, -1.0), (-1.0, 1.0)), (1, 1, 1, 1), 10)
    assert G.run(G.Prob(sq), "SL", 100, 0).cost == pytest.approx(6 + 2 * 2 ** 0.5)
