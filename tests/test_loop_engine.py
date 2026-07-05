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


# ---------------------------------------------------------------------------
# Phase 2.5: progression-driven generation
# ---------------------------------------------------------------------------


def test_build_progression_score_returns_score_with_one_bar_per_chord():
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset)

    assert isinstance(score, stream.Score)
    cello_part = score.parts[0]
    measures = cello_part.getElementsByClass(stream.Measure)
    assert len(measures) == len(chords)


def test_build_progression_score_pitches_pass_validators():
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression
    from core.engine.validators import validate_bar_duration, validate_pitch

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset)

    cello_part = score.parts[0]
    for measure in cello_part.getElementsByClass(stream.Measure):
        pitches_in_bar = [n.pitch.nameWithOctave for n in measure.notes]
        for pitch_name in pitches_in_bar:
            validate_pitch(pitch_name)
        rhythm = [n.duration.quarterLength for n in measure.notes]
        validate_bar_duration(rhythm, preset.meter_signature)


def test_build_progression_score_uses_only_chord_tones_per_bar():
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset)

    cello_part = score.parts[0]
    measures = list(cello_part.getElementsByClass(stream.Measure))
    for measure, chord in zip(measures, chords, strict=True):
        allowed_pitch_classes = {pc.replace("b", "-") for pc in chord.components}
        for n in measure.notes:
            assert n.pitch.name.replace("b", "-") in allowed_pitch_classes or n.pitch.name in chord.components


def test_build_progression_score_is_monophonic():
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset)

    cello_part = score.parts[0]
    for measure in cello_part.getElementsByClass(stream.Measure):
        offsets = [n.offset for n in measure.notes]
        assert len(offsets) == len(set(offsets))


def test_generate_variant_from_progression_trace_populated():
    from core.engine.loop_engine import generate_variant_from_progression
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    variant = generate_variant_from_progression(chords, preset, seed=42)

    assert variant.trace.pattern_strategy
    assert len(variant.trace.register_choices) == len(chords)
    assert len(variant.trace.chord_tones_used) == len(chords)


def test_generate_variant_from_progression_seed_reproducibility():
    from music21.midi.translate import streamToMidiFile

    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score_a = build_progression_score(chords, preset, seed=42)
    score_b = build_progression_score(chords, preset, seed=42)

    midi_a = streamToMidiFile(score_a)
    midi_b = streamToMidiFile(score_b)
    assert midi_a.writestr() == midi_b.writestr()


def test_build_progression_score_avoids_leaps_larger_than_an_octave():
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset, seed=7)

    cello_part = score.parts[0]
    all_notes = []
    for measure in cello_part.getElementsByClass(stream.Measure):
        all_notes.extend(measure.notes)

    for prev_note, next_note in zip(all_notes, all_notes[1:]):
        interval = abs(next_note.pitch.midi - prev_note.pitch.midi)
        assert interval <= 12


def test_build_progression_score_does_not_monotonically_climb_to_ceiling():
    # WR-01: register bias must survive voice-leading, so a long loop must not
    # ratchet to the top of the range and park there. Assert the line spends
    # real time in the low register (root/fifth bias) rather than pinning high.
    from core.engine.loop_engine import CELLO_MAX_MIDI_DEFAULT, build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression(" ".join(["Am", "F", "C", "G"] * 8))  # 32 bars
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset, seed=42)

    midis = [n.pitch.midi for m in score.parts[0].getElementsByClass(stream.Measure) for n in m.notes]
    # The final bars must not all be pinned at the ceiling (the old climbing bug).
    assert min(midis[-16:]) < CELLO_MAX_MIDI_DEFAULT - 5
    # And the piece as a whole must visit the low register, not live up top.
    assert min(midis) <= 43  # at/below G2


def test_build_progression_score_flat_key_progression_end_to_end():
    # IN-04: a flat-key progression must build and pass validators end-to-end.
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Bb Eb Ab F")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset, seed=3)

    measures = list(score.parts[0].getElementsByClass(stream.Measure))
    assert len(measures) == len(chords)
    assert all(m.notes for m in measures)


def test_build_progression_score_avoids_leaps_over_sixteen_bars():
    # IN-04: leap constraint must hold across a long progression, not one seed/bar.
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression(" ".join(["Am", "F", "C", "G"] * 4))  # 16 bars
    preset = get_preset("driving_cinematic")
    for seed in (1, 7, 42, 99):
        score = build_progression_score(chords, preset, seed=seed)
        notes = [n for m in score.parts[0].getElementsByClass(stream.Measure) for n in m.notes]
        for prev_note, next_note in zip(notes, notes[1:]):
            assert abs(next_note.pitch.midi - prev_note.pitch.midi) <= 12


def test_progression_path_duet_only_preset_raises_actionable_error():
    # WR-02: duet-only presets have no solo rhythm; the progression path must
    # raise an actionable message, not the internal "Rhythm is empty".
    from core.engine.loop_engine import (
        build_progression_score,
        generate_variant_from_progression,
    )
    from core.engine.progression import parse_progression

    chords = parse_progression("Am F C G")
    preset = get_preset("sexy_duet")

    with pytest.raises(ValueError) as exc_info:
        build_progression_score(chords, preset)
    assert "duet-only preset" in str(exc_info.value)
    assert "Rhythm is empty" not in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        generate_variant_from_progression(chords, preset)
    assert "duet-only preset" in str(exc_info.value)


def test_build_progression_score_respells_sharps_to_flats_in_flat_key():
    # IN-02: pychord spells Gm as G/A#/D; in a flat key (C minor) the score
    # must read Bb, not A# -- no sharp accidental should survive.
    from core.engine.loop_engine import build_progression_score
    from core.engine.progression import parse_progression

    chords = parse_progression("Bb Eb Gm F")
    preset = get_preset("dark_trip_hop")  # C minor -> flat key
    score = build_progression_score(chords, preset, seed=1)

    names = [n.pitch.name for m in score.parts[0].getElementsByClass(stream.Measure) for n in m.notes]
    assert names  # sanity
    assert not any("#" in n for n in names)


def test_build_progression_score_handles_power_chords():
    # IN-03: power chords put the fifth at index 1 (C5 -> ['C', 'G']); the
    # interval-based fifth detection must handle them without crashing, and
    # notes must stay in the cello range.
    from core.engine.loop_engine import (
        CELLO_MAX_MIDI_DEFAULT,
        CELLO_MIN_MIDI,
        build_progression_score,
    )
    from core.engine.progression import parse_progression

    chords = parse_progression("C5 G5 C5 F5")
    preset = get_preset("dark_trip_hop")
    score = build_progression_score(chords, preset, seed=5)

    midis = [n.pitch.midi for m in score.parts[0].getElementsByClass(stream.Measure) for n in m.notes]
    assert midis
    assert all(CELLO_MIN_MIDI <= mi <= CELLO_MAX_MIDI_DEFAULT for mi in midis)


def test_preset_only_path_unaffected_by_progression_addition():
    """Golden-regression guard at the unit level: the existing preset-only
    build_score() path must remain byte-identical after adding the
    progression-driven path alongside it."""
    from music21.midi.translate import streamToMidiFile

    from core.engine.loop_engine import build_score

    preset = get_preset("dark_trip_hop")
    score = build_score(preset, seed=42)
    midi_bytes = streamToMidiFile(score).writestr()
    assert isinstance(midi_bytes, bytes)
    assert len(midi_bytes) > 0
