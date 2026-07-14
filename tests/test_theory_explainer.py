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


def test_duet_presets_with_theory_tuples_generate_explanations() -> None:
    """Duet presets now have theory data (progressions/modulations/mood_tips filled)."""
    for preset_name in ["sexy_duet", "simple_sexy_duet", "dorian_sexy_duet"]:
        preset = get_preset(preset_name)
        assert preset.progressions  # No longer empty
        assert preset.modulations   # No longer empty
        assert preset.mood_tips     # No longer empty
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
    # Stage 4: anchor moves to how_to_end (cadence-driven resolution)
    assert "C2" in explanation.how_to_end


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


def test_explain_with_progression_driven_trace_surfaces_chord_tone() -> None:
    """Stage 4: chord tone appears in how_to_end (via anchor), not necessarily in why_it_works for single-chord traces."""
    preset = get_preset("dark_trip_hop")
    trace = GenerationTrace(
        seed=7,
        pattern_strategy="progression_driven_register_mapped",
        register_choices=["mid register"],
        voice_leading_steps=None,
        chord_tones_used=[["A", "C", "E"]],
    )
    variant = make_variant(trace)
    explanation = explain(variant, preset)
    # Chord tone surfaces via anchor in how_to_end
    assert "A" in explanation.how_to_end
    assert "mid register" in explanation.how_to_start


def test_noir_progression_explains_notes_and_resolutions() -> None:
    preset = get_preset("noir_slow_burn")
    trace = GenerationTrace(
        seed=7,
        pattern_strategy="progression_driven_register_mapped",
        register_choices=["low register"] * 4,
        voice_leading_steps=None,
        chord_tones_used=[
            ["A", "C", "E"],
            ["D", "F", "A"],
            ["F", "A", "C"],
            ["E", "G#", "B"],
        ],
        register_bias="low",
    )
    explanation = explain(make_variant(trace), preset)
    text = all_text(explanation)

    assert "A connects Am, Dm and F" in text
    assert "C gives Am its minor color" in text
    assert "G# wants to resolve up to A" in text
    assert "E major creates the strongest pull back to Am" in text


def test_noir_progression_still_names_harmonic_function_path() -> None:
    preset = get_preset("noir_slow_burn")
    trace = GenerationTrace(
        seed=7,
        pattern_strategy="progression_driven_register_mapped",
        register_choices=["low register"] * 4,
        voice_leading_steps=None,
        chord_tones_used=[
            ["A", "C", "E"],
            ["D", "F", "A"],
            ["F", "A", "C"],
            ["E", "G#", "B"],
        ],
        register_bias="low",
    )
    explanation = explain(make_variant(trace), preset)

    assert "i (tonic)" in explanation.why_it_works
    assert "iv (subdominant pull)" in explanation.why_it_works
    assert "bVI (dark warmth)" in explanation.why_it_works
    assert "V (leading-tone tension)" in explanation.why_it_works


def test_solo_preset_why_it_works_includes_style_policy_modal_center() -> None:
    """Stage 4: why_it_works now uses style_policy modal_center (not preset.progressions)."""
    preset = get_preset("dark_trip_hop")
    explanation = explain(make_variant(trace_for_preset("dark_trip_hop")), preset)
    # dark_trip_hop policy has modal_center: Aeolian
    assert "Aeolian" in explanation.why_it_works


def test_solo_preset_mood_tip_text_appears_in_how_to_develop() -> None:
    """FINDING-1: D-09 — preset.mood_tips text surfaces in how_to_develop for solo presets."""
    preset = get_preset("ritual_tribal")
    explanation = explain(make_variant(trace_for_preset("ritual_tribal")), preset)
    # ritual_tribal mood_tips[0] mentions "Phrygian b2 degree"
    assert "phrygian" in explanation.how_to_develop.lower()


def test_solo_preset_modulation_text_appears_in_how_to_transition() -> None:
    """FINDING-1: D-09 — preset.modulations text surfaces in how_to_transition for solo presets."""
    preset = get_preset("noir_slow_burn")
    explanation = explain(make_variant(trace_for_preset("noir_slow_burn")), preset)
    # noir_slow_burn modulations[0] mentions "common chord"
    assert "common chord" in explanation.how_to_transition.lower()


def test_duet_presets_use_style_policy_data() -> None:
    """Stage 4: duet presets use style_policy for explanations (not preset.progressions directly)."""
    preset = get_preset("sexy_duet")
    explanation = explain(make_variant(trace_for_preset("sexy_duet")), preset)
    assert explanation.why_it_works
    assert explanation.how_to_develop
    assert explanation.how_to_transition
    # sexy_duet policy has modal_center: Aeolian (with harmonic minor)
    assert "aeolian" in explanation.why_it_works.lower()
    # mood_tip text should appear in how_to_develop
    assert "chromatic" in explanation.how_to_develop.lower() or "mystery" in explanation.how_to_develop.lower()


# ── Stage 4: Style-policy-driven snapshot tests ──

def test_generic_phrase_keeps_loop_identity_clear_is_removed() -> None:
    """Stage 4: why_it_works no longer contains the generic 'keeps the loop identity clear'."""
    for preset_name in list_presets():
        preset = get_preset(preset_name)
        explanation = explain(make_variant(trace_for_preset(preset_name)), preset)
        assert "keeps the loop identity clear" not in explanation.why_it_works


def test_generic_phrase_changing_one_harmonic_parameter_is_removed() -> None:
    """Stage 4: how_to_develop no longer says 'changing one harmonic parameter at a time'."""
    for preset_name in list_presets():
        preset = get_preset(preset_name)
        explanation = explain(make_variant(trace_for_preset(preset_name)), preset)
        assert "changing one harmonic parameter" not in explanation.how_to_develop


def test_why_it_works_includes_modal_center_for_all_solo_presets() -> None:
    """Stage 4: every solo preset's why_it_works mentions its style_policy modal center."""
    expected_modal = {
        "dark_trip_hop": "Aeolian",
        "ritual_tribal": "Phrygian",
        "noir_slow_burn": "Harmonic",
        "driving_cinematic": "Aeolian",
    }
    for preset_name, modal in expected_modal.items():
        preset = get_preset(preset_name)
        explanation = explain(make_variant(trace_for_preset(preset_name)), preset)
        assert modal.lower() in explanation.why_it_works.lower(), (
            f"{preset_name}: expected '{modal}' in why_it_works"
        )


def test_how_to_end_includes_cadence_from_policy() -> None:
    """Stage 4: how_to_end references the first cadence from style_policy for presets with cadences."""
    # dark_trip_hop has cadences like i - bVI - v - i
    preset = get_preset("dark_trip_hop")
    explanation = explain(make_variant(trace_for_preset("dark_trip_hop")), preset)
    # dark_trip_hop's first cadence is "i - bVI - v - i"
    assert "i - bVI - v - i" in explanation.how_to_end


def test_how_to_develop_includes_chromatic_approaches() -> None:
    """Stage 4: presets with chromatic_approaches in policy get concrete suggestions in how_to_develop."""
    # ritual_tribal has bII as primary chromatic approach
    preset = get_preset("ritual_tribal")
    explanation = explain(make_variant(trace_for_preset("ritual_tribal")), preset)
    # The chromatic_approach clause says "try bII"
    assert "bII" in explanation.how_to_develop


def test_different_presets_produce_different_explanations() -> None:
    """Stage 4: explanations are preset-specific, not generic copy-paste."""
    explanations = {}
    for preset_name in ["dark_trip_hop", "ritual_tribal", "noir_slow_burn", "driving_cinematic"]:
        preset = get_preset(preset_name)
        explanations[preset_name] = explain(
            make_variant(trace_for_preset(preset_name)), preset
        )

    # All why_it_works texts should be different
    why_texts = {name: expl.why_it_works for name, expl in explanations.items()}
    assert len(set(why_texts.values())) == 4, (
        "All 4 presets should produce distinct why_it_works text"
    )

    # All how_to_develop texts should be different
    develop_texts = {name: expl.how_to_develop for name, expl in explanations.items()}
    assert len(set(develop_texts.values())) == 4, (
        "All 4 presets should produce distinct how_to_develop text"
    )


def test_dark_trip_hop_explanation_is_note_specific() -> None:
    """Stage 4: dark_trip_hop explanation contains note-specific policy content."""
    preset = get_preset("dark_trip_hop")
    explanation = explain(make_variant(trace_for_preset("dark_trip_hop")), preset)

    # Modal center
    assert "Aeolian" in explanation.why_it_works
    # First cadence: "i - bVI - v - i"
    assert "i - bVI - v - i" in explanation.why_it_works or "i - bVI - v - i" in explanation.how_to_end
    # Chromatic approaches: bII
    assert "bII" in explanation.how_to_develop
    # Genre references: Massive Attack / Portishead
    assert "Portishead" in explanation.why_it_works or "Massive Attack" in explanation.why_it_works


def test_ritual_tribal_explanation_is_note_specific() -> None:
    """Stage 4: ritual_tribal explanation contains Phrygian-specific content."""
    preset = get_preset("ritual_tribal")
    explanation = explain(make_variant(trace_for_preset("ritual_tribal")), preset)

    assert "Phrygian" in explanation.why_it_works
    # First cadence: bII → i
    assert "bII" in explanation.why_it_works or "bII" in explanation.how_to_end
    # Mood tip: "Phrygian b2 degree"
    assert "phrygian" in explanation.how_to_develop.lower()


def test_noir_slow_burn_explanation_is_note_specific() -> None:
    """Stage 4: noir_slow_burn explanation contains Harmonic Minor-specific content."""
    preset = get_preset("noir_slow_burn")
    explanation = explain(make_variant(trace_for_preset("noir_slow_burn")), preset)

    assert "HarmonicMinor" in explanation.why_it_works or "harmonic" in explanation.why_it_works.lower()


def test_driving_cinematic_explanation_is_note_specific() -> None:
    """Stage 4: driving_cinematic explanation contains Aeolian/cinematic content."""
    preset = get_preset("driving_cinematic")
    explanation = explain(make_variant(trace_for_preset("driving_cinematic")), preset)

    assert "Aeolian" in explanation.why_it_works

