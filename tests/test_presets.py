"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import rsk_constants as C
import rsk_evaluation as ev
import rsk_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert (preset["fill"] - C.FILL_MIN) % C.FILL_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_constants_are_consistent():
    assert max(C.BAND_SIZES) > C.N_MAX >= C.EXACT_MAX and C.EXACT_MAX in C.BAND_SIZES and set(C.BAND_BUDGET) == set(C.BAND_SIZES) == set(C.BAND_PER_CELL)
    assert set(C.KINDS) | set(C.EXTRA_KINDS) == set(C.ALL_KINDS) and all(k in C.KIND_NAMES and k in C.KIND_COLORS and k in C.HAS_LS for k in C.ALL_KINDS)
    assert all(b[1] <= b[0] for b in C.BAND_BUDGET.values()) and C.CHECKPOINTS == tuple(sorted(C.CHECKPOINTS))
    assert C.LIVE_BUDGET_PLAIN[0] <= C.LIVE_BUDGET_PLAIN[2] <= C.LIVE_BUDGET_PLAIN[1] and C.LIVE_BUDGET_LS[0] <= C.LIVE_BUDGET_LS[2] <= C.LIVE_BUDGET_LS[1]
