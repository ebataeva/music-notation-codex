from __future__ import annotations

from collections.abc import Sequence

from core.models import GenerationTrace, LoopVariant, MoodPreset, TheoryExplanation
from core.theory.cues import cue_pair_for, primary_register


def _first_or_fallback(values: Sequence[str], fallback: str) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return fallback


def _select_anchor(trace: GenerationTrace) -> str:
    if trace.pattern_strategy == "preset_verbatim":
        tones = trace.chord_tones_used or []
        for bar_tones in tones:
            for tone in bar_tones:
                if tone:
                    return f"the repeated cello tone {tone}"
        raise ValueError("preset_verbatim trace has no chord tones to explain.")

    if trace.pattern_strategy == "progression_driven_register_mapped":
        tones = trace.chord_tones_used or []
        register = primary_register(trace)
        for bar_tones in tones:
            for tone in bar_tones:
                if tone:
                    return f"the chord tone {tone} placed in the {register}"
        raise ValueError("progression_driven_register_mapped trace has no chord tones to explain.")

    raise ValueError(f"Unknown pattern_strategy {trace.pattern_strategy!r}.")


def _register_quality_clause(trace: GenerationTrace) -> str:
    """Return a plain-language clause describing the variant's register character.

    ``register_bias`` is set by the Phase 7 variant generator. When it is
    ``None`` (preset-verbatim path) we return an empty string so the
    explanation stays verbatim-stable for Phase 1 variants.
    """
    bias = trace.register_bias
    if bias == "low":
        return (
            "Low-register mapping gives the loop warmth and depth, grounding the "
            "line in the cello's lowest voice so the harmony feels settled and dark."
        )
    if bias == "high":
        return (
            "High-register mapping lifts the loop into the cello's upper voice, "
            "adding brightness and a touch of tension so the melody wants to soar "
            "above the harmony."
        )
    # "default" or None: keep the explanation stable for the verbatim path.
    return ""


def explain(variant: LoopVariant, preset: MoodPreset) -> TheoryExplanation:
    if variant.trace is None:
        raise ValueError("Theory explanation requires variant.trace.")

    trace = variant.trace
    anchor = _select_anchor(trace)
    start_cue, transition_cue = cue_pair_for(preset, trace)
    tempo = preset.duet_tempo_bpm or preset.tempo_bpm
    feel = preset.feel.strip() or f"{preset.key_tonic} {preset.key_mode} cello loop"
    harmony_focus = f"{preset.key_tonic} {preset.key_mode}"

    # D-09: Surface preset theory data into the explanation fields.
    progression = _first_or_fallback(preset.progressions, "")
    modulation = _first_or_fallback(preset.modulations, "")
    mood_tip = _first_or_fallback(preset.mood_tips, "")

    if progression:
        harmony_focus = f"{harmony_focus} — {progression}"
    else:
        harmony_focus = f"{harmony_focus} with a clear repeated anchor"

    # Phase 7: vary the explanation per register_bias so sibling variants read
    # as clearly different tonal characters, not as identical copy.
    register_clause = _register_quality_clause(trace)

    why_it_works = (
        f"This works because {anchor} gives the listener a concrete point of return in "
        f"{harmony_focus} while the {tempo} BPM {feel} keeps the loop identity clear."
    )
    if register_clause:
        why_it_works = f"{why_it_works} {register_clause}"

    # Slightly vary the opening cue per register_bias so each variant's
    # how_to_start is distinguishable while staying grounded in the trace.
    bias = trace.register_bias
    if bias == "low":
        how_to_start = f"{start_cue} Lean into the weight of the lowest register so the loop feels rooted."
    elif bias == "high":
        how_to_start = f"{start_cue} Let the bow float lightly so the upper register sings and carries upward."
    else:
        how_to_start = start_cue

    if mood_tip:
        how_to_develop = f"Develop it by keeping the pulse steady and changing one detail at a time: {mood_tip}"
    else:
        how_to_develop = (
            "Develop it by keeping the pulse steady and changing one detail at a time: "
            "keep the bow close to the string and let small dynamic changes create motion."
        )

    how_to_end = (
        f"End by returning to {anchor}, softening the dynamics, and letting the final bow stroke decay."
    )

    if modulation:
        how_to_transition = f"{transition_cue} {modulation}"
    else:
        how_to_transition = (
            f"{transition_cue} "
            "Move by repeating the anchor once, then shift the next loop entry to a nearby pitch."
        )

    return TheoryExplanation(
        why_it_works=why_it_works,
        how_to_start=how_to_start,
        how_to_develop=how_to_develop,
        how_to_end=how_to_end,
        how_to_transition=how_to_transition,
    )
