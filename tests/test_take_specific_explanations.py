"""VAR-01: each generated take is explained by its own notes.

The progression, key and preset are the same for all three takes, so every
clause derived from them reads identically on the three cards. These tests pin
the take-specific part: it comes from `trace.played_pitches`, it differs
whenever the notes differ, and it names notes the way the stave writes them.
"""

from __future__ import annotations

import re

import pytest

from core.engine.loop_engine import generate_variant, generate_variants
from core.engine.progression import parse_progression
from core.presets.registry import get_preset, list_solo_presets
from core.theory.explainer import explain, written_name

PROGRESSIONS = ["Am F C G", "Dm7 G7 Cmaj7", "C", "Em", "F#m D A E", "Bb Eb F Gm", "Cm Ab Eb Bb"]
FIELDS = ["why_it_works", "how_to_start", "how_to_develop", "how_to_end", "how_to_transition"]
MUSIC21_FLAT = re.compile(r"\b[A-G]-+\d")


def _takes(preset_name: str, progression: str, seed: int):
    preset = get_preset(preset_name)
    variants = generate_variants(parse_progression(progression), preset, seed=seed, count=3)
    return [(variant, explain(variant, preset)) for variant in variants]


def _opening(variant) -> str:
    return written_name(variant.trace.played_pitches[0][0])


def _closing(variant) -> str:
    return written_name(variant.trace.played_pitches[-1][-1])


@pytest.mark.parametrize(
    "name,written",
    [("B-2", "Bb2"), ("E-3", "Eb3"), ("F#3", "F#3"), ("C2", "C2"), ("B#3", "B#3"), ("C-4", "Cb4"), ("B--2", "Bbb2")],
)
def test_written_name_spells_flats_with_b_and_keeps_the_written_octave(name, written):
    # SPELL-01: B#3 sounds as C4 but is written on the B line of octave 3; the
    # card must name the note the stave prints, so the octave digit is kept.
    assert written_name(name) == written


@pytest.mark.parametrize("preset_name", list_solo_presets())
@pytest.mark.parametrize("progression", PROGRESSIONS)
def test_takes_with_different_notes_read_differently(preset_name, progression):
    for seed in range(6):
        takes = _takes(preset_name, progression, seed)
        for i in range(len(takes)):
            for j in range(i + 1, len(takes)):
                (left, left_text), (right, right_text) = takes[i], takes[j]
                if left.trace.played_pitches == right.trace.played_pitches:
                    continue
                where = f"{preset_name} {progression!r} seed={seed} takes {i}/{j}"
                # The long text writes every played note out, so any difference
                # in the notes shows up there.
                assert left_text.why_it_works != right_text.why_it_works, where
                # Cards summarise (opening, closing, span, centre); two takes
                # that differ only in one inner octave may share a summary, but
                # a difference in what the card summarises must reach it.
                left_bars, right_bars = left.trace.played_pitches, right.trace.played_pitches
                if (left_bars[0][0], left_bars[-1][-1]) != (right_bars[0][0], right_bars[-1][-1]):
                    assert left_text.short_sections["why_it_works"] != right_text.short_sections["why_it_works"], where
                if [bar[0] for bar in left_bars] != [bar[0] for bar in right_bars]:
                    assert left_text.how_to_develop != right_text.how_to_develop, where
                    assert left_text.short_sections["how_to_develop"] != right_text.short_sections["how_to_develop"], where


@pytest.mark.parametrize("progression", ["Am F C G", "Cm Ab Eb Bb"])
def test_long_explanation_writes_out_the_played_notes_bar_by_bar(progression):
    for variant, text in _takes("dark_trip_hop", progression, seed=1):
        for bar in variant.trace.played_pitches:
            assert "(played " + "-".join(written_name(name) for name in bar) + ")" in text.why_it_works


@pytest.mark.parametrize("preset_name", list_solo_presets())
@pytest.mark.parametrize("progression", ["Am F C G", "Bb Eb F Gm", "Cm Ab Eb Bb"])
def test_each_section_names_the_notes_of_its_own_take(preset_name, progression):
    for variant, text in _takes(preset_name, progression, seed=42):
        opening, closing = _opening(variant), _closing(variant)
        for sections in (vars(text), text.short_sections):
            assert opening in sections["why_it_works"]
            assert opening in sections["how_to_develop"]
            assert closing in sections["how_to_end"]
            assert closing in sections["how_to_transition"]
            assert opening in sections["how_to_transition"]


@pytest.mark.parametrize("preset_name", list_solo_presets())
@pytest.mark.parametrize("progression", ["Bb Eb F Gm", "Cm Ab Eb Bb", "Ebm Gb Db Ab"])
def test_player_facing_text_never_prints_music21_flats(preset_name, progression):
    for _variant, text in _takes(preset_name, progression, seed=7):
        for field in FIELDS:
            assert not MUSIC21_FLAT.search(getattr(text, field)), (field, getattr(text, field))
            assert not MUSIC21_FLAT.search(text.short_sections[field]), (field, text.short_sections[field])


@pytest.mark.parametrize("preset_name", list_solo_presets())
@pytest.mark.parametrize("progression", PROGRESSIONS)
def test_take_clauses_keep_cards_within_the_word_limit(preset_name, progression):
    for seed in range(3):
        for _variant, text in _takes(preset_name, progression, seed):
            for field, section in text.short_sections.items():
                assert len(section.split()) <= 65, (field, section)


@pytest.mark.parametrize("preset_name", list_solo_presets())
def test_preset_verbatim_takes_get_no_take_clause(preset_name):
    # The preset-verbatim path records no played_pitches; its wording must not
    # grow a take sentence built from nothing.
    preset = get_preset(preset_name)
    variant = generate_variant(preset, seed=42)
    assert variant.trace.played_pitches is None
    text = explain(variant, preset)
    for field in FIELDS:
        assert "This take" not in getattr(text, field)
        assert "this take" not in getattr(text, field)
