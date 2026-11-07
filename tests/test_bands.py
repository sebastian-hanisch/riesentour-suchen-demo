"""Vorberechnete Bänder (rsk_bands.json): Aufbau, Vollständigkeit, Stimmigkeit der Zeilen und frische Nachrechnung einzelner Läufe (Stichprobe, bitgleich)."""

import json
from pathlib import Path

import pytest

import rsk_algorithm as A
import rsk_constants as C
import rsk_evaluation as ev
import rsk_search as G
from rsk_scenario import make_instance

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / C.BAND_FILE).read_text(encoding="utf-8"))
ROWS = DATA["rows"]
PER_SIZE = {n: len(C.BAND_CELLS) * C.BAND_PER_CELL[n] for n in C.BAND_SIZES}


def test_every_size_is_there_with_the_right_number_of_instances_and_runs():
    for n in C.BAND_SIZES:
        rows = ev.band_rows(n)
        assert len(rows) == PER_SIZE[n] and {(r["family"], r["depot"]) for r in rows} == set(C.BAND_CELLS)
        assert all(set(r["runs"]) == set(C.ALL_KINDS) for r in rows)
    assert len(ROWS) == sum(PER_SIZE.values()) == 60


def test_runs_have_the_budget_and_a_monotone_trace_ending_there():
    for r in ROWS:
        for kind, run in r["runs"].items():
            budget = ev.budget_of(r["n"], kind)
            ks = [k for k, _ in run["trace"]]
            assert run["children"] == budget and ks[-1] == budget and ks == sorted(ks) and set(ks) <= set(C.CHECKPOINTS) | {budget}, (r["n"], kind)
            costs = [c for _, c in run["trace"]]
            assert all(b <= a + 1e-9 for a, b in zip(costs, costs[1:])) and run["cost"] <= costs[-1] + 1e-6 and run["cost"] > 0


def test_references_and_baselines_are_sane():
    for r in ROWS:
        assert r["ref"] > 0 and r["es"] >= r["ref"] - 1e-6 and r["sav"] >= r["ref"] - 1e-6 and r["best9"] >= r["ref"] - 1e-6 and r["best9"] <= r["sav"] + 1e-9
        if r["n"] <= C.EXACT_MAX:
            assert all(run["cost"] >= r["ref"] - 1e-6 for run in r["runs"].values())                       # das exakte Optimum ist eine Untergrenze


def test_exact_references_equal_a_fresh_exact_run():
    for r in ev.band_rows(12)[::6]:
        inst = make_instance(12, r["family"], r["depot"], C.BAND_ROUTES, r["seed"], C.BAND_FILL)
        assert A.exact_cvrp(inst).cost == pytest.approx(r["ref"], abs=1e-6)


@pytest.mark.parametrize("pick", [(12, "S"), (12, "SL"), (12, "RL"), (25, "R"), (25, "SL"), (25, "SB"), (50, "SL")])
def test_a_fresh_run_equals_the_stored_run(pick):
    n, kind = pick
    r = ev.band_rows(n)[3 if n == 12 else 1]
    P = G.Prob(make_instance(n, r["family"], r["depot"], C.BAND_ROUTES, r["seed"], C.BAND_FILL))
    stored = r["runs"][kind]
    budget = stored["children"] if C.HAS_LS[kind] or n == 12 else 2000          # die einfachen Fassungen: nur die ersten 2000 Kinder nachgerechnet (die Spur ist dieselbe)
    fresh = G.run(P, kind, budget, r["seed"])
    assert [list(t) for t in fresh.trace if t[0] in (250, 500, 1000, 2000)] == [t for t in stored["trace"] if t[0] in (250, 500, 1000, 2000) and t[0] <= budget]
    if budget == stored["children"]:
        assert fresh.cost == pytest.approx(stored["cost"], abs=1e-9)


def test_band_stats_counts_and_ordering():
    stats = ev.band_stats(ev.band_rows(25))
    assert stats["count"] == 16 and set(stats["final"]) == set(C.ALL_KINDS)
    assert all(v["min"] <= v["median"] <= v["max"] for v in stats["final"].values())
    assert all(sum(p[k] for k in ("cheaper", "equal", "more")) == 16 for p in stats["paired"].values() if p)
    assert ev.band_stats([]) == {} and ev.band_rows(7) == []
    assert ev.run_at(ev.band_rows(25)[0], "S", 1000) is not None and ev.run_at(ev.band_rows(25)[0], "SL", 4000) is None
