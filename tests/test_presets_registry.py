"""Proves the MOOD_PRESETS merge (4 solo + 3 duet = 7 entries) is complete and lossless."""

from __future__ import annotations

import pytest

from core.presets.mood_presets import MOOD_PRESETS
from core.presets.registry import get_preset, list_presets, list_solo_presets

SOLO_MOODS = {"dark_trip_hop", "ritual_tribal", "noir_slow_burn", "driving_cinematic"}
DUET_MOODS = {"sexy_duet", "simple_sexy_duet", "dorian_sexy_duet"}


def test_mood_presets_has_seven_entries():
    assert len(MOOD_PRESETS) == 7


def test_mood_presets_keys_match_all_five_sources():
    assert set(MOOD_PRESETS) == SOLO_MOODS | DUET_MOODS


def test_solo_moods_carry_theory_data_from_genre_ideas():
    for name in SOLO_MOODS:
        preset = MOOD_PRESETS[name]
        assert preset.progressions
        assert preset.modulations
        assert preset.mood_tips

    assert MOOD_PRESETS["dark_trip_hop"].feel == "темный, сексуальный, петлевой trip-hop groove"


def test_sexy_duet_preset_has_exact_divergent_length_rhythm():
    assert MOOD_PRESETS["sexy_duet"].duet_rhythm == {
        "cello": [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5],
        "violin": [1.0, 0.5, 0.5, 1.0, 1.0],
    }


def test_simple_sexy_duet_preserves_out_of_range_a1_note_verbatim():
    assert MOOD_PRESETS["simple_sexy_duet"].duet_bars["cello"][1] == ["A1", "E2", "G2", "C#3"]


def test_registry_get_and_list_presets():
    assert get_preset("dark_trip_hop").name == "dark_trip_hop"
    with pytest.raises(KeyError):
        get_preset("nonexistent")
    assert sorted(list_presets()) == sorted(MOOD_PRESETS)


def test_solo_presets_have_no_duet_fields_and_duet_presets_do():
    for name in SOLO_MOODS:
        preset = MOOD_PRESETS[name]
        assert preset.duet_rhythm is None
        assert preset.duet_bars is None
        assert preset.duet_tempo_bpm is None

    for name in DUET_MOODS:
        preset = MOOD_PRESETS[name]
        assert preset.duet_rhythm is not None
        assert preset.duet_bars is not None
        assert preset.duet_tempo_bpm is not None


def test_list_solo_presets_returns_only_the_four_solo_moods():
    assert list_solo_presets() == sorted(SOLO_MOODS)
