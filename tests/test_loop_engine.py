from __future__ import annotations

import pytest
from music21 import stream

from core.models import MoodPreset
from core.presets.registry import get_preset


def test_build_score_returns_music21_score_no_errors():
    from core.engine.loop_engine import build_score

    score = build_score(get_preset("dark_trip_hop"))
    assert isinstance(score, stream.Score)


def test_build_score_has_expected_measure_count():
    from core.engine.loop_engine import build_score

    preset = get_preset("dark_trip_hop")
    score = build_score(preset)
    cello_part = score.parts[0]
    measures = cello_part.getElementsByClass(stream.Measure)
    assert len(measures) == len(preset.bars)


def test_build_score_seed_reproducibility_via_midi_bytes():
    from music21.midi.translate import streamToMidiFile

    from core.engine.loop_engine import build_score

    preset = get_preset("dark_trip_hop")
    score_a = build_score(preset, seed=42)
    score_b = build_score(preset, seed=42)

    midi_a = streamToMidiFile(score_a)
    midi_b = streamToMidiFile(score_b)
    assert midi_a.writestr() == midi_b.writestr()


def test_generate_variant_trace_seed_matches_explicit_seed():
    from core.engine.loop_engine import generate_variant

    variant = generate_variant(get_preset("dark_trip_hop"), seed=42)
    assert variant.trace.seed == 42


def test_generate_variant_without_seed_always_records_a_seed():
    from core.engine.loop_engine import generate_variant

    variant = generate_variant(get_preset("dark_trip_hop"))
    assert variant.trace.seed is not None


def test_generate_variant_pattern_strategy_is_non_empty_string():
    from core.engine.loop_engine import generate_variant

    variant = generate_variant(get_preset("dark_trip_hop"))
    assert isinstance(variant.trace.pattern_strategy, str)
    assert variant.trace.pattern_strategy


def test_generate_variant_register_choices_one_per_bar():
    from core.engine.loop_engine import generate_variant

    preset = get_preset("dark_trip_hop")
    variant = generate_variant(preset)
    assert len(variant.trace.register_choices) == len(preset.bars)


def test_generate_variant_chord_tones_used_matches_bars():
    from core.engine.loop_engine import generate_variant

    preset = get_preset("dark_trip_hop")
    variant = generate_variant(preset)
    assert variant.trace.chord_tones_used
    assert len(variant.trace.chord_tones_used) == len(preset.bars)
    for bar_tones, expected_bar in zip(variant.trace.chord_tones_used, preset.bars, strict=True):
        assert bar_tones == expected_bar


def test_legacy_exception_scoped_to_simple_sexy_duet_a1_only():
    from core.engine.loop_engine import _is_legacy_exception

    assert _is_legacy_exception("simple_sexy_duet", "A1") is True
    assert _is_legacy_exception("dark_trip_hop", "A1") is False


def test_build_score_raises_value_error_for_out_of_range_pitch_not_excepted():
    from core.engine.loop_engine import build_score

    bad_preset = MoodPreset(
        name="synthetic_bad_preset",
        tempo_bpm=100,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=80,
        rhythm=[1.0, 1.0, 1.0, 1.0],
        bars=[["B1", "C3", "D3", "E3"]],
        feel="synthetic test preset",
        progressions=[],
        modulations=[],
        mood_tips=[],
    )
    with pytest.raises(ValueError):
        build_score(bad_preset)


def test_generate_variant_raises_for_more_than_64_bars_before_score_built():
    from core.engine.loop_engine import generate_variant

    too_many_bars_preset = MoodPreset(
        name="synthetic_too_long_preset",
        tempo_bpm=100,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=80,
        rhythm=[1.0, 1.0, 1.0, 1.0],
        bars=[["C2", "C2", "C2", "C2"] for _ in range(65)],
        feel="synthetic test preset",
        progressions=[],
        modulations=[],
        mood_tips=[],
    )
    with pytest.raises(ValueError):
        generate_variant(too_many_bars_preset)


def test_build_duet_score_returns_score_with_no_exception():
    from core.engine.loop_engine import build_duet_score

    score = build_duet_score(get_preset("sexy_duet"), tempo_bpm=76, cello_velocity=82, violin_velocity=70)
    assert isinstance(score, stream.Score)


def test_build_duet_score_has_violin_and_cello_parts():
    from core.engine.loop_engine import build_duet_score

    score = build_duet_score(get_preset("sexy_duet"), tempo_bpm=76, cello_velocity=82, violin_velocity=70)
    part_ids = {part.id for part in score.parts}
    assert part_ids == {"violin", "cello"}


def test_build_duet_score_measure_counts_match_preset_duet_bars():
    from core.engine.loop_engine import build_duet_score

    preset = get_preset("sexy_duet")
    score = build_duet_score(preset, tempo_bpm=76, cello_velocity=82, violin_velocity=70)
    parts_by_id = {part.id: part for part in score.parts}

    cello_measures = parts_by_id["cello"].getElementsByClass(stream.Measure)
    violin_measures = parts_by_id["violin"].getElementsByClass(stream.Measure)

    assert len(cello_measures) == len(preset.duet_bars["cello"])
    assert len(violin_measures) == len(preset.duet_bars["violin"])


def test_build_duet_score_simple_sexy_duet_a1_legacy_note_does_not_raise():
    from core.engine.loop_engine import build_duet_score

    score = build_duet_score(
        get_preset("simple_sexy_duet"), tempo_bpm=64, cello_velocity=68, violin_velocity=58
    )
    assert isinstance(score, stream.Score)


def test_build_duet_score_dorian_sexy_duet_returns_score_with_no_exception():
    from core.engine.loop_engine import build_duet_score

    score = build_duet_score(
        get_preset("dorian_sexy_duet"), tempo_bpm=88, cello_velocity=74, violin_velocity=62
    )
    assert isinstance(score, stream.Score)


def test_generate_variant_signature_has_no_duet_parameter():
    import inspect

    from core.engine.loop_engine import generate_variant

    params = inspect.signature(generate_variant).parameters
    assert "instrument_set" not in params
    assert "duet" not in params
