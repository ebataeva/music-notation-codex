from __future__ import annotations

import pytest

from core.engine.progression import parse_progression


def test_parse_simple_progression_returns_ordered_chords():
    chords = parse_progression("Am F C G")
    assert len(chords) == 4
    assert [c.name for c in chords] == ["Am", "F", "C", "G"]


def test_parse_progression_exposes_component_tones():
    chords = parse_progression("Am F C G")
    am = chords[0]
    assert am.components == ["A", "C", "E"]


def test_parse_progression_with_extended_qualities():
    chords = parse_progression("F#m7 Gsus4 Cmaj7 Bdim")
    assert [c.name for c in chords] == ["F#m7", "Gsus4", "Cmaj7", "Bdim"]
    assert chords[0].components == ["F#", "A", "C#", "E"]
    assert chords[1].components == ["G", "C", "D"]
    assert chords[2].components == ["C", "E", "G", "B"]
    assert chords[3].components == ["B", "D", "F"]


def test_parse_progression_unrecognized_token_names_bad_token_in_message():
    with pytest.raises(ValueError) as exc_info:
        parse_progression("Am Xz9 C G")
    assert "Xz9" in str(exc_info.value)


def test_parse_progression_empty_input_raises_clear_error():
    with pytest.raises(ValueError):
        parse_progression("")


def test_parse_progression_whitespace_only_input_raises_clear_error():
    with pytest.raises(ValueError):
        parse_progression("   ")


def test_parse_progression_tolerates_surrounding_and_duplicate_whitespace():
    chords_normal = parse_progression("Am F C G")
    chords_messy = parse_progression("  Am  F   C G  ")
    assert [c.name for c in chords_messy] == [c.name for c in chords_normal]
