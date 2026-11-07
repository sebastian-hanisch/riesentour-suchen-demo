"""Die fünf Experimente der App per AppTest: Kreuzung, Läufe, Lokalsuche Zug für Zug, Lamarck gegen Baldwin, Bänder; dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import rsk_constants as C
import rsk_evaluation as ev
from rsk_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SETTING_KEYS = {"n": "n_slider", "family": "family_select", "depot": "depot_select", "routes": "routes_slider", "fill": "fill_slider", "seed": "seed_input"}
HAND = "Ein Kind besser als beide Eltern (Handinstanz)"


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.error])


def test_the_hand_preset_shows_the_hand_example():
    text = _texts(_app(HAND))
    assert "Das Kind ist besser als beide Eltern." in text and "Von 21 Schnitten liefern 1 ein Kind" in text and "exaktes Optimum, 44,36" in text


def test_parent_seeds_and_the_cut_can_be_changed():
    at = _app(HAND)
    at.number_input(key="parent_a").set_value(5).run()
    assert not at.exception
    at.number_input(key="parent_b").set_value(6).run()
    assert not at.exception and "Schnitten" in _texts(at)
    at.slider(key="cut_6").set_value((1, 6)).run()
    assert not at.exception


def test_budgets_and_mutation_sliders_rerun_the_search():
    at = _app()
    at.slider(key="budget_plain").set_value(500).run()
    assert not at.exception
    at.slider(key="budget_ls").set_value(100).run()
    assert not at.exception
    at.slider(key="mut_plain").set_value(0.5).run()
    at.slider(key="mut_ls").set_value(0.0).run()
    assert not at.exception and "Abstand zur Referenz" in _texts(at)


def test_every_start_plan_of_the_local_search_works_and_steps_can_be_chosen():
    at = _app("Die Konstruktion liegt 15 % daneben (n = 12, exakt)")
    for start in ("random", "es", "sav"):
        at.radio(key="ls_start").set_value(start).run()
        assert not at.exception, start
    at.radio(key="ls_start").set_value("random").run()
    slider = next(s for s in at.slider if s.key and s.key.startswith("ls_step_random_"))
    slider.set_value(0).run()
    assert not at.exception


def test_instance_controls_and_every_family():
    at = _app()
    for family in range(len(C.FAMILIES)):
        at.selectbox(key="family_select").set_value(family).run()
        assert not at.exception, family
    at.selectbox(key="family_select").set_value(1).run()
    at.slider(key="n_slider").set_value(14).run()
    assert not at.exception and "beste Lösung dieser Seite" in " ".join([m.value for m in at.markdown] + [c.value for c in at.caption] + [m.value for m in at.metric])


def test_band_selection_for_every_size():
    at = _app()
    for n in C.BAND_SIZES:
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception, n
        assert f"{n} Kunden, " in _texts(at)


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        a = ev.analyse(s)
        results = {k: ev.run_kind(s, k, 100, None) for k in C.KINDS}
        data = build_pdf(s, a, results)
        assert data[:5] == b"%PDF-" and len(data) > 1500
