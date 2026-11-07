"""Verdikte sind reine Funktionen: jede Zahl im Text stammt aus der Rechnung, Art und Wortlaut folgen den Schwellen."""

import pytest

import rsk_constants as C
import rsk_evaluation as ev
import rsk_search as G

HAND = ev.Settings()                                         # Voreinstellung: Handinstanz
SMALL = ev.Settings(12, 1, 1, 3, 90, 300001)


def test_formats():
    assert ev.de(3.14159) == "3,14" and ev.pct(12.345) == "12,3 %" and ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(2.5) == "+2,5 %" and ev.signed_pct(-2.5) == "−2,5 %"
    assert ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz"
    assert ev.gap_percent(10.0, 10.0) == 0.0 and ev.gap_percent(9.0, 10.0) == pytest.approx(-10.0) and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0) and ev.gap_percent(1.0, 0.0) == 0.0


def test_cross_verdict_for_the_hand_example():
    view = ev.crossover_view(HAND, 31, 873, (2, 3))
    kind, text = ev.verdict_cross(view)
    assert kind == "success" and text.startswith("Das Kind ist besser als beide Eltern.")
    assert "Eltern A kostet 48,73 (2 Routen), Eltern B 58,88 (3 Routen); das Kind kostet 44,36 (2 Routen)" in text and "Von 21 Schnitten liefern 1 ein Kind, das beide Eltern schlägt, 6 eines" in text


def test_cross_verdict_levels():
    view = ev.crossover_view(HAND, 31, 873, (0, 0))
    kind, text = ev.verdict_cross(view)
    assert kind in ("info", "warning", "success") and f"Von {view['cuts']['total']} Schnitten" in text
    worse = {**view, "child": {**view["child"], "cost": max(view["a"]["cost"], view["b"]["cost"]) + 1.0}}
    assert ev.verdict_cross(worse)[0] == "warning" and ev.verdict_cross(worse)[1].startswith("Das Kind ist schlechter")
    equal = {**view, "child": {**view["child"], "cost": min(view["a"]["cost"], view["b"]["cost"])}}
    assert ev.verdict_cross(equal)[0] == "info" and ev.verdict_cross(equal)[1].startswith("Das Kind ist so gut wie der bessere Elter")


def test_runs_verdict_exact_and_best_known():
    a = ev.analyse(SMALL)
    res = {k: ev.run_kind(SMALL, k, 300 if C.HAS_LS[k] else 400, None) for k in C.KINDS}
    kind, text = ev.verdict_runs(a, res)
    assert kind == "info" and "exaktes Optimum, 650,67" in text and "Am besten:" in text and "keine Untergrenze" not in text
    big = ev.Settings(14, 1, 0, 3, 90, 5)
    ab = ev.analyse(big)
    resb = {k: ev.run_kind(big, k, 100, None) for k in C.KINDS}
    assert "keine Untergrenze" in ev.verdict_runs(ab, resb)[1] and ab.exact is None
    ref, label = ev.reference(ab, resb)
    assert ref == min([v[0] for v in ab.baselines.values()] + [r.cost for r in resb.values()]) and "beste Lösung dieser Seite" in label


def test_ls_verdict():
    info = ev.ls_steps(HAND, "random")
    kind, text = ev.verdict_ls(info)
    assert kind == "success" and "5 Züge (Tauschen 2, Verschieben 3)" in text and "62,60 auf 44,36" in text and "der Ausgangsplan war 41,1 % länger" in text and "von 3 auf 2" in text
    none = ev.ls_steps(HAND, "es")                            # Einfügen nach Split trifft hier das Optimum: kein Zug
    assert not none["steps"] and ev.verdict_ls(none)[0] == "info" and "keinen verbessernden Zug" in ev.verdict_ls(none)[1]


def test_lamarck_verdict_levels():
    P = G.Prob(ev.build_instance(HAND))
    sl = G.run(P, "SL", 50, 0)
    better = G.Result(sl.cost + 1.0, sl.routes, sl.trace, 0.0, 0.0, 50)
    assert ev.verdict_lamarck({"SL": sl, "SB": better})[0] == "success"
    assert ev.verdict_lamarck({"SL": sl, "SB": sl})[0] == "info"
    assert ev.verdict_lamarck({"SL": better, "SB": sl})[0] == "warning"


def test_band_verdict():
    assert ev.verdict_bands({})[0] == "warning"
    kind, text = ev.verdict_bands(ev.band_stats(ev.band_rows(100)))
    assert kind == "success" and "100 Kunden, 8 Instanzen" in text and "Referenz (PyVRP)" in text and "Mit Lokalsuche Folge gegen Routen billiger / gleich / teurer: 8 / 0 / 0" in text
    assert "Die Referenz ist keine bewiesene Untergrenze" in text and "Ein Lauf je Instanz" in text
    kind, text = ev.verdict_bands(ev.band_stats(ev.band_rows(12)))
    assert kind == "info" and "Optimum" in text and "bewiesene Untergrenze" not in text
