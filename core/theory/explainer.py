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


def explain(variant: LoopVariant, preset: MoodPreset) -> TheoryExplanation:
    if variant.trace is None:
        raise ValueError("Theory explanation requires variant.trace.")

    trace = variant.trace
    anchor = _select_anchor(trace)
    start_cue, transition_cue = cue_pair_for(preset, trace)
    tempo = preset.duet_tempo_bpm or preset.tempo_bpm
    feel = preset.feel.strip() or f"{preset.key_tonic} {preset.key_mode} cello loop"
    harmony_focus = f"{preset.key_tonic} {preset.key_mode}"
    if _first_or_fallback(preset.progressions, ""):
        harmony_focus = f"{harmony_focus} with a clear repeated anchor"
    mood_tip = "Keep the bow close to the string and let small dynamic changes create motion."
    modulation = "Move by repeating the anchor once, then shift the next loop entry to a nearby pitch."

    why_it_works = (
        f"This works because {anchor} gives the listener a concrete point of return in {harmony_focus} while "
        f"the {tempo} BPM {feel} keeps the loop identity clear."
    )
    how_to_develop = (
        f"Develop it by keeping the pulse steady and changing one detail at a time: {mood_tip}"
    )
    how_to_end = (
        f"End by returning to {anchor}, softening the dynamics, and letting the final bow stroke decay."
    )

    return TheoryExplanation(
        why_it_works=why_it_works,
        how_to_start=start_cue,
        how_to_develop=how_to_develop,
        how_to_end=how_to_end,
        how_to_transition=f"{transition_cue} {modulation}",
    )
