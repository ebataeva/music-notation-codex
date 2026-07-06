"""Phase 7 tests: multi-variant generation (3 distinct cello loops per request).

Covers generate_variants() -- the high-level API that produces N variants from
a single chord progression by cycling register biases (low -> default -> high)
and deriving unique seeds per variant. Each test verifies one facet of the
Phase 7 contract: count, distinctness, reproducibility, and register-bias
effects on the generated MIDI output.
"""

from __future__ import annotations

import pytest

from core.engine.loop_engine import (
    build_progression_score,
    generate_variants,
)
from core.engine.progression import parse_progression
from core.models import LoopVariant
from core.presets.registry import get_preset

# Default fixtures shared across all Phase 7 variant tests.
DEFAULT_PRESET_NAME = "dark_trip_hop"
DEFAULT_PROGRESSION = "Am F C G"


def _make_chords():
    """Parse the default progression into ParsedChord objects."""
    return parse_progression(DEFAULT_PROGRESSION)


def _make_preset():
    """Load the default dark_trip_hop preset."""
    return get_preset(DEFAULT_PRESET_NAME)


def _score_to_midi_bytes(score):
    """Convert a music21 Score to raw MIDI bytes for byte-level comparison."""
    from music21.midi.translate import streamToMidiFile

    return streamToMidiFile(score).writestr()


def test_generate_variants_returns_three_variants():
    # generate_variants with count=3 must return exactly 3 LoopVariant instances.
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    assert len(results) == 3
    assert all(isinstance(v, LoopVariant) for v in results)


def test_generate_variants_distinct_seeds():
    # Each variant must carry a unique derived seed (base_seed + i * 1000).
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    seeds = [v.trace.seed for v in results]
    assert len(seeds) == len(set(seeds)), f"Seeds must be distinct, got {seeds}"


def test_generate_variants_distinct_register_biases():
    # The 3 variants must cycle through low -> default -> high register biases.
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    biases = [v.trace.register_bias for v in results]
    assert biases == ["low", "default", "high"]


def test_generate_variants_midi_bytes_distinct():
    # Building scores with each variant's seed + bias must yield pairwise-distinct
    # MIDI bytes (all 3 choose 2 = 3 pairs must differ).
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    midi_bytes_list = []
    for variant in results:
        score = build_progression_score(
            chords,
            preset,
            seed=variant.trace.seed,
            register_bias=variant.trace.register_bias,
        )
        midi_bytes_list.append(_score_to_midi_bytes(score))

    for i in range(len(midi_bytes_list)):
        for j in range(i + 1, len(midi_bytes_list)):
            assert midi_bytes_list[i] != midi_bytes_list[j], (
                f"MIDI bytes for variant {i} and {j} must differ"
            )


def test_generate_variants_share_chord_skeleton():
    # All variants use the same chord tones (same chords, different realizations).
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    first_skeleton = results[0].trace.chord_tones_used
    for i, variant in enumerate(results):
        assert variant.trace.chord_tones_used == first_skeleton, (
            f"Variant {i} chord skeleton differs from variant 0"
        )


def test_generate_variants_reproducible_with_same_seed():
    # Generating twice with the same seed must produce identical seeds and MIDI bytes.
    chords = _make_chords()
    preset = _make_preset()

    results1 = generate_variants(chords, preset, seed=42, count=3)
    results2 = generate_variants(chords, preset, seed=42, count=3)

    # Seeds must match position-for-position.
    for i, (v1, v2) in enumerate(zip(results1, results2)):
        assert v1.trace.seed == v2.trace.seed, f"Variant {i} seed mismatch"

    # MIDI bytes for the first variant must be byte-identical.
    score1 = build_progression_score(
        chords,
        preset,
        seed=results1[0].trace.seed,
        register_bias=results1[0].trace.register_bias,
    )
    score2 = build_progression_score(
        chords,
        preset,
        seed=results2[0].trace.seed,
        register_bias=results2[0].trace.register_bias,
    )
    assert _score_to_midi_bytes(score1) == _score_to_midi_bytes(score2)


def test_generate_variants_different_seed_new_results():
    # Different base seeds must produce at least one variant whose MIDI differs.
    chords = _make_chords()
    preset = _make_preset()

    results_42 = generate_variants(chords, preset, seed=42, count=3)
    results_99 = generate_variants(chords, preset, seed=99, count=3)

    found_difference = False
    for v42, v99 in zip(results_42, results_99):
        score42 = build_progression_score(
            chords,
            preset,
            seed=v42.trace.seed,
            register_bias=v42.trace.register_bias,
        )
        score99 = build_progression_score(
            chords,
            preset,
            seed=v99.trace.seed,
            register_bias=v99.trace.register_bias,
        )
        if _score_to_midi_bytes(score42) != _score_to_midi_bytes(score99):
            found_difference = True
            break

    assert found_difference, "At least one variant must differ between seed=42 and seed=99"


def test_register_bias_affects_register_choices():
    # At least 2 of the 3 variants must have different register_choices lists,
    # proving the register bias actually shifts the realized register.
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    choices = [v.trace.register_choices for v in results]
    distinct = len(set(tuple(c) for c in choices))
    assert distinct >= 2, (
        f"Expected at least 2 distinct register_choices lists, got {distinct}"
    )


def test_generate_variants_count_parameter():
    # count=1 returns exactly 1 variant; count=2 returns exactly 2.
    chords = _make_chords()
    preset = _make_preset()

    results_one = generate_variants(chords, preset, seed=42, count=1)
    assert len(results_one) == 1

    results_two = generate_variants(chords, preset, seed=42, count=2)
    assert len(results_two) == 2


def test_generate_variants_invalid_count_raises():
    # count=0 must raise ValueError (guard against empty result lists).
    chords = _make_chords()
    preset = _make_preset()

    with pytest.raises(ValueError):
        generate_variants(chords, preset, seed=42, count=0)


def test_variant_trace_has_register_bias():
    # Every variant's trace.register_bias must be non-None and one of the valid values.
    chords = _make_chords()
    preset = _make_preset()

    results = generate_variants(chords, preset, seed=42, count=3)

    valid_biases = {"low", "default", "high"}
    for i, variant in enumerate(results):
        assert variant.trace.register_bias is not None, (
            f"Variant {i} register_bias is None"
        )
        assert variant.trace.register_bias in valid_biases, (
            f"Variant {i} register_bias {variant.trace.register_bias!r} not in {valid_biases}"
        )
