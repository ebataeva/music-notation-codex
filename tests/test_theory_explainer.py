from __future__ import annotations

import re
from pathlib import Path

import pytest

from core.models import GenerationTrace, LoopVariant
from core.presets.registry import get_preset, list_presets
from core.theory.explainer import _select_anchor, explain


def make_variant(trace: GenerationTrace | None) -> LoopVariant:
    return LoopVariant(
        id="test-variant",
        preset_name="dark_trip_hop",
        label="Test variant",
        musicxml_path=None,
        midi_path=None,
        svg_bytes=None,
        midi_bytes=None,
        theory_explanation=None,
        trace=trace,
    )


def trace_for_preset(preset_name: str) -> GenerationTrace:
    preset = get_preset(preset_name)
    if preset.bars:
        chord_tones = [list(bar) for bar in preset.bars]
    else:
        assert preset.duet_bars is not None
        chord_tones = [list(bar) for bar in preset.duet_bars["cello"]]

    return GenerationTrace(
        seed=42,
        pattern_strategy="preset_verbatim",
        register_choices=["low register"] * len(chord_tones),
        voice_leading_steps=None,
        chord_tones_used=chord_tones,
    )


def all_text(explanation) -> str:
    return " ".join(
        [
            explanation.why_it_works,
            explanation.how_to_start,
            explanation.how_to_develop,
            explanation.how_to_end,
            explanation.how_to_transition,
        ]
    )


def test_explain_populates_all_fields_for_every_preset() -> None:
    for preset_name in list_presets():
        preset = get_preset(preset_name)
        explanation = explain(make_variant(trace_for_preset(preset_name)), preset)
        assert explanation.why_it_works
        assert explanation.how_to_start
        assert explanation.how_to_develop
        assert explanation.how_to_end
        assert explanation.how_to_transition


def test_duet_presets_with_empty_theory_tuples_use_fallback_text() -> None:
    for preset_name in ["sexy_duet", "simple_sexy_duet", "dorian_sexy_duet"]:
        preset = get_preset(preset_name)
        assert preset.progressions == ()
        assert preset.modulations == ()
        assert preset.mood_tips == ()
        explanation = explain(make_variant(trace_for_preset(preset_name)), preset)
        assert "IndexError" not in all_text(explanation)
        assert preset.key_tonic in all_text(explanation)


def test_explain_requires_trace() -> None:
    with pytest.raises(ValueError, match="variant.trace"):
        explain(make_variant(None), get_preset("dark_trip_hop"))


def test_explain_is_deterministic_for_same_input() -> None:
    preset = get_preset("dark_trip_hop")
    variant = make_variant(trace_for_preset("dark_trip_hop"))
    assert explain(variant, preset) == explain(variant, preset)


def test_preset_verbatim_anchor_uses_octave_bearing_pitch() -> None:
    trace = GenerationTrace(
        seed=1,
        pattern_strategy="preset_verbatim",
        register_choices=["low register"],
        voice_leading_steps=None,
        chord_tones_used=[["C2", "G2"]],
    )
    assert _select_anchor(trace) == "the repeated cello tone C2"


def test_progression_anchor_uses_pitch_class_with_register_choice() -> None:
    trace = GenerationTrace(
        seed=1,
        pattern_strategy="progression_driven_register_mapped",
        register_choices=["mid register"],
        voice_leading_steps=None,
        chord_tones_used=[["A", "C", "E"]],
    )
    assert _select_anchor(trace) == "the chord tone A placed in the mid register"


def test_unknown_pattern_strategy_raises_value_error() -> None:
    trace = GenerationTrace(
        seed=1,
        pattern_strategy="surprise",
        register_choices=["low register"],
        voice_leading_steps=None,
        chord_tones_used=[["C2"]],
    )
    with pytest.raises(ValueError, match="Unknown pattern_strategy"):
        _select_anchor(trace)


def test_explanation_contains_trace_anchor() -> None:
    preset = get_preset("dark_trip_hop")
    explanation = explain(make_variant(trace_for_preset("dark_trip_hop")), preset)
    assert "C2" in explanation.why_it_works


def test_cello_and_looper_cues_are_present() -> None:
    preset = get_preset("ritual_tribal")
    text = all_text(explain(make_variant(trace_for_preset("ritual_tribal")), preset)).lower()
    assert any(term in text for term in ["bow", "low string", "pulse", "loop", "dynamics", "register"])


def test_explanation_text_contains_no_cyrillic() -> None:
    preset = get_preset("dark_trip_hop")
    text = all_text(explain(make_variant(trace_for_preset("dark_trip_hop")), preset))
    assert re.search(r"[\u0400-\u04ff]", text) is None


def test_explanation_avoids_unexplained_jargon_terms() -> None:
    preset = get_preset("dark_trip_hop")
    text = all_text(explain(make_variant(trace_for_preset("dark_trip_hop")), preset)).lower()
    banned_terms = ["phrygian", "dominant", "subdominant", "tritone", "cadence"]
    assert not any(term in text for term in banned_terms)


def test_cue_selection_is_not_keyed_by_preset_name() -> None:
    source = Path("core/theory/cues.py").read_text(encoding="utf-8")
    assert "preset.name ==" not in source
    assert "preset.name in" not in source
