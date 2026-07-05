"""Phase 2 Nyquist validation gap-fill tests (LOOP-01, SAFE-02, SAFE-07).

Added by the Nyquist validation audit (see 02-VALIDATION.md) to close
coverage gaps left after 02-VERIFICATION.md: the SAFE-02 bar-count guard was
verified only on the solo preset path at verification time; this file proves
the guard also holds -- with a real, executed assertion, not a code-reading
claim -- on the duet path and on both progression-driven entry points. It
also proves SAFE-07 (flat, non-recursive variant generation) behaviorally
via call-count instrumentation rather than by reading the source.

Does NOT touch core/ or any existing tests/ file, per the audit's hard
constraint. Does NOT depend on the in-progress MAX_NOTES=512 (SAFE-01) guard.
"""

from __future__ import annotations

import dataclasses

import pytest

from core.engine.loop_engine import (
    build_duet_score,
    build_progression_score,
    generate_variant,
    generate_variant_from_progression,
)
from core.engine.progression import parse_progression
from core.presets.registry import get_preset


def test_build_duet_score_rejects_more_than_64_bars_per_part():
    """SAFE-02 on the duet path: build_duet_score must reject an oversized
    per-instrument bar count before any Score is constructed -- this is the
    exact gap 02-VERIFICATION.md flagged as PARTIAL/FAIL (WR-03) at
    verification time, on the same preset family used elsewhere in the suite.
    """
    base_preset = get_preset("sexy_duet")
    too_many_cello_bars = dataclasses.replace(
        base_preset,
        duet_bars={
            "cello": [["D2", "A2", "D3", "C3", "A2", "F2", "A2"] for _ in range(65)],
            "violin": base_preset.duet_bars["violin"],
        },
        duet_rhythm={
            "cello": [0.5] * 7,
            "violin": base_preset.duet_rhythm["violin"],
        },
    )

    with pytest.raises(ValueError, match="exceeds the maximum"):
        build_duet_score(
            too_many_cello_bars, tempo_bpm=76, cello_velocity=82, violin_velocity=70
        )


def test_build_progression_score_rejects_more_than_64_chords():
    """SAFE-02 on the progression-build path: a progression with 65 chords
    must be rejected before Score construction begins."""
    preset = get_preset("dark_trip_hop")
    chords = parse_progression(" ".join(["Am", "F", "C", "G"] * 17))  # 68 chords

    with pytest.raises(ValueError, match="exceeds the maximum"):
        build_progression_score(chords, preset)


def test_generate_variant_from_progression_rejects_more_than_64_chords():
    """SAFE-02 on the progression-variant path: same guard, exercised through
    the higher-level generate_variant_from_progression() entry point that the
    UI/CLI will actually call."""
    preset = get_preset("dark_trip_hop")
    chords = parse_progression(" ".join(["Am", "F", "C", "G"] * 17))  # 68 chords

    with pytest.raises(ValueError, match="exceeds the maximum"):
        generate_variant_from_progression(chords, preset)


def test_generate_variant_does_not_recursively_generate_further_variants():
    """SAFE-07: variant generation must be flat -- generating one variant must
    not, in turn, trigger further variant generation calls. Proven
    behaviorally via call-count instrumentation (a monkeypatched counting
    wrapper around generate_variant itself), not by reading the source.
    """
    import core.engine.loop_engine as loop_engine_module

    call_count = 0
    real_generate_variant = loop_engine_module.generate_variant

    def counting_generate_variant(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_generate_variant(*args, **kwargs)

    loop_engine_module.generate_variant = counting_generate_variant
    try:
        preset = get_preset("dark_trip_hop")
        loop_engine_module.generate_variant(preset, seed=1)
    finally:
        loop_engine_module.generate_variant = real_generate_variant

    # If generate_variant recursed into itself (directly or via a module-level
    # self-call), the counting wrapper would have observed more than 1 call.
    assert call_count == 1


def test_generate_variant_from_progression_does_not_recursively_spawn_variants():
    """SAFE-07 on the progression-variant path: same flatness guarantee must
    hold for generate_variant_from_progression, the newer of the two
    high-level variant-producing entry points."""
    import core.engine.loop_engine as loop_engine_module

    call_count = 0
    real_fn = loop_engine_module.generate_variant_from_progression

    def counting_fn(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_fn(*args, **kwargs)

    loop_engine_module.generate_variant_from_progression = counting_fn
    try:
        preset = get_preset("dark_trip_hop")
        chords = parse_progression("Am F C G")
        loop_engine_module.generate_variant_from_progression(chords, preset, seed=1)
    finally:
        loop_engine_module.generate_variant_from_progression = real_fn

    assert call_count == 1


def test_generate_variant_produces_playable_loop_from_preset_no_errors():
    """LOOP-01 smoke: the core observable promise of the requirement --
    'App generates a playable cello loop from the chord progression + mood'
    -- holds end-to-end for the preset-driven path with a real preset,
    returning a populated LoopVariant rather than raising or returning None.
    """
    preset = get_preset("dark_trip_hop")
    variant = generate_variant(preset, seed=42)

    assert variant.trace is not None
    assert variant.trace.pattern_strategy
    assert len(variant.trace.chord_tones_used) == len(preset.bars)
    assert len(variant.trace.register_choices) == len(preset.bars)
