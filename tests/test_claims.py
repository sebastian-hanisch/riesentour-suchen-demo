"""Jede Zahl der README und der Preset-Hilfen wird aus den Bändern beziehungsweise der Rechnung nachgerechnet und muss im Text stehen (DEMO-PLAYBOOK §1b)."""

from functools import lru_cache
from pathlib import Path

import pytest

import rsk_constants as C
import rsk_evaluation as ev
import rsk_search as G

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def stat(n):
    return ev.band_stats(ev.band_rows(n))


def fmt(x, digits=1):
    return ev.de(x, digits)


def med_final(n, kind):
    return round(stat(n)["final"][kind]["median"], 1)


def med_at(n, kind, k):
    return round(stat(n)["at"][kind][k]["median"], 1)


def triple(n, key):
    p = stat(n)["paired"][key]
    return (p["cheaper"], p["equal"], p["more"])


def text3(t):
    return f"{t[0]} / {t[1]} / {t[2]}"


def test_the_table_of_final_gaps():
    expected = {12: (2.5, 1.3, 0.6, 0.0, 0.0, 0.0, 0.0), 25: (4.0, 2.9, 1.5, 1.2, 5.3, 0.0, 0.0), 50: (8.4, 6.9, 4.0, 24.0, 11.6, 0.0, 0.1), 100: (11.5, 8.4, 5.9, 97.5, 27.6, 1.7, 7.4)}
    for n, (es, sav, b9, s, r, sl, rl) in expected.items():
        st_ = stat(n)
        assert [round(st_["baselines"][k]["median"], 1) for k in ("es", "sav", "best9")] == [es, sav, b9]
        assert [med_final(n, k) for k in ("S", "R", "SL", "RL")] == [s, r, sl, rl]
        row = f"| {fmt(es)} / {fmt(sav)} / {fmt(b9)} | {fmt(s)} | {fmt(r)} | {fmt(sl)} | {fmt(rl)} |"
        assert row in README, row
    assert [stat(n)["count"] for n in C.BAND_SIZES] == [20, 16, 16, 8]


def test_with_local_search_the_sequence_is_ahead_or_level():
    assert [triple(n, "SL_RL_final") for n in C.BAND_SIZES] == [(0, 20, 0), (1, 15, 0), (9, 7, 0), (8, 0, 0)]
    assert [triple(n, "SL_RL_1000") for n in (25, 50, 100)] == [(2, 14, 0), (9, 6, 1), (8, 0, 0)]
    for text in ("n = 12: 0 / 20 / 0; n = 25: 1 / 15 / 0; n = 50: **9 / 7 / 0**; n = 100: **8 / 0 / 0** (1,7 gegen 7,4 %)", "n = 25: 2 / 14 / 0, n = 50: 9 / 6 / 1, n = 100: 8 / 0 / 0"):
        assert text in README, text


def test_without_local_search_it_tips_with_size_and_time():
    assert [triple(n, "S_R_1000") for n in C.BAND_SIZES] == [(6, 4, 10), (1, 0, 15), (1, 0, 15), (0, 0, 8)]
    assert [triple(n, "S_R_final") for n in C.BAND_SIZES] == [(9, 11, 0), (12, 0, 4), (3, 0, 13), (0, 0, 8)]
    assert (med_at(50, "S", 1000), med_at(50, "R", 1000)) == (104.5, 60.2) and (med_final(25, "S"), med_final(25, "R")) == (1.2, 5.3) and (med_final(50, "S"), med_final(50, "R")) == (24.0, 11.6) and (med_final(100, "S"), med_final(100, "R")) == (97.5, 27.6)
    assert med_at(25, "R", 8000) == med_at(25, "R", 16000) == 5.3
    for text in ("n = 12: 6 / 4 / 10, n = 25: **1 / 0 / 15**, n = 50: 1 / 0 / 15, n = 100: 0 / 0 / 8 (n = 50: 104,5 gegen 60,2 %)", "n = 12: 9 / 11 / 0, n = 25: **12 / 0 / 4** (1,2 gegen 5,3 %), n = 50: 3 / 0 / 13 (24,0 gegen 11,6 %), n = 100: 0 / 0 / 8 (97,5 gegen 27,6 %)", "5,3 % nach 8 000 und 16 000 Kindern"):
        assert text in README, text


def test_local_search_decides():
    assert [triple(n, "SL_S_1000") for n in C.BAND_SIZES] == [(13, 7, 0), (16, 0, 0), (16, 0, 0), (8, 0, 0)] and [triple(n, "RL_R_1000") for n in C.BAND_SIZES] == [(9, 11, 0), (16, 0, 0), (16, 0, 0), (8, 0, 0)]
    assert [med_at(25, k, 250) for k in ("SL", "RL", "S", "R")] == [0.0, 0.0, 50.8, 48.2] and [med_at(50, k, 250) for k in ("SL", "RL", "S", "R")] == [0.1, 0.8, 152.0, 150.2]
    for text in ("Folge: n = 12: 13 / 7 / 0, n = 25: 16 / 0 / 0, n = 50: 16 / 0 / 0, n = 100: 8 / 0 / 0; Routen: 9 / 11 / 0, 16 / 0 / 0, 16 / 0 / 0, 8 / 0 / 0", "bei n = 50 bei 0,1 % (Folge) und 0,8 % (Routen)", "50,8 / 48,2 % (n = 25) und 152,0 / 150,2 % (n = 50)"):
        assert text in README, text


def test_lamarck_against_baldwin():
    assert [triple(n, "SL_SB_final") for n in C.BAND_SIZES] == [(0, 20, 0), (1, 15, 0), (14, 2, 0), (7, 0, 1)]
    assert (med_final(50, "SL"), med_final(50, "SB")) == (0.0, 1.1) and (med_final(100, "SL"), med_final(100, "SB")) == (1.7, 4.4)
    for text in ("n = 12: 0 / 20 / 0; n = 25: 1 / 15 / 0; n = 50: **14 / 2 / 0** (0,0 gegen 1,1 %); n = 100: **7 / 0 / 1** (1,7 gegen 4,4 %)",):
        assert text in README, text


def test_runs_under_the_reference():
    assert [(stat(n)["under"]["SL"], stat(n)["under"]["RL"], stat(n)["under"]["SB"]) for n in (25, 50, 100)] == [(6, 6, 6), (6, 4, 2), (1, 0, 0)] and stat(25)["under"]["S"] == 1
    for text in ("n = 25: 6 / 6 / 6 von 16; n = 50: 6 / 4 / 2 von 16; n = 100: 1 / 0 / 0 von 8", "die Folge ohne Lokalsuche in 1 von 16 (n = 25)"):
        assert text in README, text


def test_the_hand_example():
    inst = ev.hand_instance()
    P = G.Prob(inst)
    view = ev.crossover_view(ev.Settings(), *C.PARENT_SEEDS, (2, 3))
    assert view["a"]["order"] == C.HAND_PARENTS[0] and view["b"]["order"] == C.HAND_PARENTS[1] and view["child"]["order"] == (1, 4, 2, 6, 3, 5)
    assert (round(view["a"]["cost"], 4), round(view["b"]["cost"], 4), round(view["child"]["cost"], 4)) == (48.7306, 58.8797, 44.3623) and view["child"]["routes"] == ((1, 4), (2, 6, 3, 5))
    opt = G.split(P, view["child"]["order"])[0]
    assert (ev.gap_percent(view["a"]["cost"], opt), ev.gap_percent(view["b"]["cost"], opt)) == (pytest.approx(9.8, abs=0.05), pytest.approx(32.7, abs=0.05))
    assert view["cuts"] == {"total": 21, "better": 1, "equal": 6}
    for text in ("48,7306", "58,8797", "44,3623", "(3 5 2 6 4 1)", "(1 6 4 3 5 2)", "(1 4 2 6 3 5)", "9,8 und 32,7 %", "Von den 21 möglichen Schnitten liefert nur dieser ein Kind, das beide Eltern schlägt, 6 liefern"):
        assert text in README, text


# --- Presets -----------------------------------------------------------------------------------------------------------------------------

def _live(name):
    p = C.PRESETS[name]
    s = ev.Settings(p["n"], p["family"], p["depot"], p["routes"], p["fill"], p["seed"])
    a = ev.analyse(s)
    res = {k: ev.run_kind(s, k, C.LIVE_BUDGET_LS[2] if C.HAS_LS[k] else C.LIVE_BUDGET_PLAIN[2], None) for k in C.ALL_KINDS}
    ref, _ = ev.reference(a, {k: v for k, v in res.items() if k in C.KINDS})
    return a, res, ref


def _gap(res, ref, k):
    return round(ev.gap_percent(res[k].cost, ref), 1)


def test_hand_preset():
    name = "Ein Kind besser als beide Eltern (Handinstanz)"
    view = ev.crossover_view(ev.Settings(), *C.PARENT_SEEDS, (2, 3))
    h = C.PRESET_HELP[name]
    for text in ("48,73", "58,88", "44,36", "(3 5 2 6 4 1)", "(1 6 4 3 5 2)", "(1 4 2 6 3 5)", "21 Schnitten"):
        assert text in h, text
    assert (round(view["a"]["cost"], 2), round(view["b"]["cost"], 2), round(view["child"]["cost"], 2)) == (48.73, 58.88, 44.36)


def test_local_search_preset():
    name = "Die Lokalsuche entscheidet (n = 25)"
    a, res, ref = _live(name)
    assert round(ref, 2) == 496.75 and (_gap(res, ref, "S"), _gap(res, ref, "R"), _gap(res, ref, "SL"), _gap(res, ref, "RL")) == (26.7, 10.2, 0.0, 0.0) and round(ev.gap_percent(a.baselines["es"][0], ref), 1) == 2.3
    for text in ("26,7 %", "10,2 %", "496,75", "0,0 %", "2,3 %", "2000 Kindern ohne und 500 mit"):
        assert text in C.PRESET_HELP[name], text


def test_either_or_preset():
    name = "Folge oder Routen: je nach Instanz (n = 25)"
    a, res, ref = _live(name)
    assert round(ref, 2) == 531.43 and (_gap(res, ref, "S"), _gap(res, ref, "R"), _gap(res, ref, "SL"), _gap(res, ref, "RL")) == (10.1, 23.7, 0.0, 0.0) and (len(res["S"].routes), len(res["R"].routes)) == (3, 5)
    for text in ("10,1 %", "3 Routen", "23,7 %", "5 Routen", "531,43", "0,0 %"):
        assert text in C.PRESET_HELP[name], text


def test_construction_preset():
    name = "Die Konstruktion liegt 15 % daneben (n = 12, exakt)"
    a, res, ref = _live(name)
    assert round(a.exact.cost, 2) == 650.67 and round(a.baselines["es"][0], 2) == 749.98 and round(a.baselines["sav"][0], 2) == 701.75 and round(ev.gap_percent(a.baselines["es"][0], ref), 1) == 15.3
    assert all(abs(r.cost - a.exact.cost) < 1e-6 for r in res.values())
    for text in ("650,67", "749,98", "15,3 %", "701,75", "2000 und 500 Kindern"):
        assert text in C.PRESET_HELP[name], text


def test_lamarck_preset():
    name = "Rückschreiben zählt (n = 25)"
    a, res, ref = _live(name)
    assert round(ref, 2) == 495.23 and round(res["SL"].cost, 2) == 495.23 and round(res["SB"].cost, 2) == 495.73 and _gap(res, ref, "SB") == 0.1 and (_gap(res, ref, "S"), _gap(res, ref, "R")) == (9.5, 5.4)
    for text in ("495,23", "495,73", "0,1 %", "9,5 %", "5,4 %"):
        assert text in C.PRESET_HELP[name], text
