import dataclasses

import pytest

from core.models import (
    GenerationRequest,
    GenerationTrace,
    LoopVariant,
    MoodPreset,
    TheoryExplanation,
)


def test_models_import_without_error():
    # Import already happened at module load time above; a fresh import call
    # here proves there is no circular-import or partial-module issue.
    from core.models import (  # noqa: F401
        GenerationRequest,
        GenerationTrace,
        LoopVariant,
        MoodPreset,
        TheoryExplanation,
    )


def test_generation_trace_fields():
    trace = GenerationTrace(
        seed=42,
        pattern_strategy="ostinato",
        register_choices=["low"],
        voice_leading_steps=["C2->G2"],
        chord_tones_used=[["C", "Eb", "G"]],
    )
    field_names = {f.name for f in dataclasses.fields(trace)}
    assert field_names == {
        "seed",
        "pattern_strategy",
        "register_choices",
        "voice_leading_steps",
        "chord_tones_used",
    }


def test_loop_variant_trace_defaults_to_none():
    variant = LoopVariant(
        id="v1",
        preset_name="dark_trip_hop",
        label="Variant 1",
        musicxml_path=None,
        midi_path=None,
        svg_bytes=None,
        midi_bytes=None,
        theory_explanation=None,
    )
    assert variant.trace is None


def test_mood_preset_defaults_and_frozen():
    preset = MoodPreset(
        name="dark_trip_hop",
        tempo_bpm=72,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=76,
        rhythm=(0.5,) * 8,
        bars=(("C2",) * 8,),
        feel="dark, sexy, loopy trip-hop groove",
        progressions=("i - VI - v - i",),
        modulations=("Through a common chord",),
        mood_tips=("Keep the low pulse steady",),
    )
    assert preset.duet_rhythm is None
    assert preset.duet_bars is None
    assert preset.duet_tempo_bpm is None

    with pytest.raises(dataclasses.FrozenInstanceError):
        preset.name = "changed"


def test_generation_request_defaults():
    request = GenerationRequest(
        chord_progression="Am F C G",
        key_tonic="A",
        key_mode="minor",
        mood="dark_trip_hop",
    )
    assert request.num_variants == 3
    assert request.bars == 8
    assert request.instrument_set == "cello"
