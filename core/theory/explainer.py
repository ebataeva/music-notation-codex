from __future__ import annotations

import re
from collections.abc import Sequence

from core.models import GenerationTrace, LoopVariant, MoodPreset, TheoryExplanation
from core.presets.style_policy import StylePolicy, get_style_policy
from core.theory.cues import cue_pair_for, primary_register


_PITCH_CLASS_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

_MINOR_DEGREES = {
    0: ("i", "tonic"),
    2: ("ii", "supertonic color"),
    3: ("bIII", "relative-major color"),
    5: ("iv", "subdominant pull"),
    7: ("v", "fifth-degree support"),
    8: ("bVI", "dark warmth"),
    10: ("bVII", "modal lift"),
    11: ("V", "leading-tone tension"),
}

_MAJOR_DEGREES = {
    0: ("I", "tonic"),
    2: ("ii", "pre-dominant color"),
    4: ("iii", "mediant color"),
    5: ("IV", "subdominant lift"),
    7: ("V", "dominant pull"),
    9: ("vi", "relative-minor color"),
    10: ("bVII", "modal color"),
    11: ("vii", "leading-tone tension"),
}

_SEMITONE_TO_SHARP_NAME = {
    0: "C",
    1: "C#",
    2: "D",
    3: "D#",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "G#",
    9: "A",
    10: "A#",
    11: "B",
}


def _first_or_fallback(values: Sequence[str], fallback: str) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return fallback


def _strip_sentence_end(value: str) -> str:
    return value.rstrip().rstrip(".!?")


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


def _pitch_class(tone: str) -> str:
    match = re.match(r"^([A-Ga-g])([#b-]?)", tone.strip())
    if not match:
        return tone.strip()
    letter, accidental = match.groups()
    accidental = "b" if accidental == "-" else accidental
    return f"{letter.upper()}{accidental}"


def _semitone(tone: str) -> int | None:
    return _PITCH_CLASS_TO_SEMITONE.get(_pitch_class(tone).upper())


def _tone_name(semitone: int) -> str:
    return _SEMITONE_TO_SHARP_NAME[semitone % 12]


def _degree_for_root(root: str, preset: MoodPreset) -> tuple[str, str] | None:
    root_semitone = _semitone(root)
    tonic_semitone = _semitone(preset.key_tonic)
    if root_semitone is None or tonic_semitone is None:
        return None

    interval = (root_semitone - tonic_semitone) % 12
    if preset.key_mode.lower() == "major":
        return _MAJOR_DEGREES.get(interval)
    return _MINOR_DEGREES.get(interval)


def _degree_for_chord(tones: Sequence[str], preset: MoodPreset) -> tuple[str, str] | None:
    if not tones:
        return None
    degree = _degree_for_root(tones[0], preset)
    if (
        degree == ("v", "fifth-degree support")
        and preset.key_mode.lower() == "minor"
        and _chord_quality(tones) == "major"
    ):
        return ("V", "leading-tone tension")
    return degree


def _chord_quality(tones: Sequence[str]) -> str:
    if not tones:
        return "harmony"

    root = tones[0]
    root_semitone = _semitone(root)
    intervals = {
        (_semitone(tone) - root_semitone) % 12
        for tone in tones[1:]
        if root_semitone is not None and _semitone(tone) is not None
    }

    if {3, 6}.issubset(intervals):
        return "diminished"
    if 3 in intervals:
        return "minor"
    if 4 in intervals:
        return "major"
    if 7 in intervals:
        return "power-chord"
    return "open"


def _chord_name(tones: Sequence[str]) -> str:
    if not tones:
        return "the chord"

    root = _pitch_class(tones[0])
    quality = _chord_quality(tones)
    suffix = {
        "major": "major",
        "minor": "minor",
        "diminished": "diminished",
        "power-chord": "power chord",
        "open": "open chord",
    }.get(quality, quality)
    return f"{root} {suffix}"


def _chord_symbol(tones: Sequence[str]) -> str:
    if not tones:
        return ""
    root = _pitch_class(tones[0])
    quality = _chord_quality(tones)
    if quality == "minor":
        return f"{root}m"
    if quality == "diminished":
        return f"{root}dim"
    return root


def _function_path(trace: GenerationTrace, preset: MoodPreset) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    functions: list[str] = []
    seen: set[str] = set()
    for bar_tones in trace.chord_tones_used or []:
        if not bar_tones:
            continue
        degree = _degree_for_chord(bar_tones, preset)
        if degree is None:
            continue
        roman, function = degree
        label = f"{roman} ({function})"
        if label not in seen:
            functions.append(label)
            seen.add(label)

    if not functions:
        return ""
    return "The generated harmony outlines " + " -> ".join(functions) + "."


def _format_chord_list(symbols: Sequence[str]) -> str:
    if not symbols:
        return ""
    if len(symbols) == 1:
        return symbols[0]
    if len(symbols) == 2:
        return f"{symbols[0]} and {symbols[1]}"
    return ", ".join(symbols[:-1]) + f" and {symbols[-1]}"


def _minor_color_clause(trace: GenerationTrace) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    for tones in trace.chord_tones_used or []:
        if _chord_quality(tones) != "minor":
            continue
        root_semitone = _semitone(tones[0])
        if root_semitone is None:
            continue
        minor_third = _tone_name(root_semitone + 3)
        tone_names = {_pitch_class(tone) for tone in tones}
        if minor_third in tone_names:
            root = _pitch_class(tones[0])
            fifth = _tone_name(root_semitone + 7)
            return (
                f"In {root} minor, {root} is the home note, "
                f"{minor_third} gives {root}m its minor color, "
                f"and {fifth} stabilizes the fifth."
            )

    return ""


def _tonic_common_tone_clause(trace: GenerationTrace) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    tones_by_chord = trace.chord_tones_used or []
    tonic = _pitch_class(trace.chord_tones_used[0][0]) if tones_by_chord and tones_by_chord[0] else ""
    if not tonic:
        return ""

    connected_symbols = []
    for tones in tones_by_chord:
        if tonic in {_pitch_class(tone) for tone in tones}:
            connected_symbols.append(_chord_symbol(tones))

    connected_symbols = list(dict.fromkeys(symbol for symbol in connected_symbols if symbol))
    if len(connected_symbols) < 2:
        return ""

    connection = _format_chord_list(connected_symbols)
    return f"{tonic} connects {connection}, so the progression feels related instead of jumpy."


def _leading_tone_clause(trace: GenerationTrace, preset: MoodPreset) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    tonic_semitone = _semitone(preset.key_tonic)
    if tonic_semitone is None:
        return ""
    leading_tone = _tone_name(tonic_semitone - 1)
    tonic = _pitch_class(preset.key_tonic)

    for tones in trace.chord_tones_used or []:
        tone_names = {_pitch_class(tone) for tone in tones}
        if leading_tone not in tone_names:
            continue
        chord_name = _chord_name(tones)
        return (
            f"{leading_tone} is outside natural {tonic} minor; "
            f"in {chord_name}, {leading_tone} wants to resolve up to {tonic}. "
            f"{chord_name} creates the strongest pull back to {tonic}m."
        )

    return ""


def _note_resolution_clauses(trace: GenerationTrace, preset: MoodPreset) -> list[str]:
    clauses = [
        _minor_color_clause(trace),
        _tonic_common_tone_clause(trace),
        _leading_tone_clause(trace, preset),
    ]
    return [clause for clause in clauses if clause]


def _headline_harmony_clause(trace: GenerationTrace, preset: MoodPreset) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    tonic_connection = _tonic_common_tone_clause(trace)
    leading_tone = _leading_tone_clause(trace, preset)
    clauses = [clause for clause in (tonic_connection, leading_tone) if clause]
    return " ".join(clauses)


def _anchor_role(trace: GenerationTrace, preset: MoodPreset) -> str:
    if trace.pattern_strategy != "progression_driven_register_mapped":
        return ""

    for bar_tones in trace.chord_tones_used or []:
        if not bar_tones:
            continue
        anchor = bar_tones[0]
        degree = _degree_for_chord(bar_tones, preset)
        quality = _chord_quality(bar_tones)
        if degree is None:
            return f"{anchor} is the root of the opening {quality} sonority."
        roman, function = degree
        return (
            f"{anchor} is the {function} root of the opening {quality} sonority "
            f"({roman}), so the listener hears both a home base and a harmonic job."
        )

    return ""


def _voice_leading_clause(trace: GenerationTrace) -> str:
    tones = trace.chord_tones_used or []
    if len(tones) < 2:
        return ""

    shared_tone_clauses = []
    for left, right in zip(tones, tones[1:], strict=False):
        left_classes = {_pitch_class(tone) for tone in left}
        right_classes = {_pitch_class(tone) for tone in right}
        shared = sorted(left_classes & right_classes)
        if shared:
            shared_tone_clauses.append(
                f"{'/'.join(shared)} stays between {_chord_symbol(left)} and {_chord_symbol(right)}"
            )

    if shared_tone_clauses:
        examples = "; ".join(shared_tone_clauses[:2])
        return f"{examples}, smoothing the bar-to-bar voice-leading."

    return (
        "Because adjacent chords avoid common tones, the line needs the steady rhythm "
        "and register plan to make the harmonic changes feel intentional."
    )


def _register_quality_clause(trace: GenerationTrace) -> str:
    """Return a plain-language clause describing the variant's register character.

    ``register_bias`` is set by the Phase 7 variant generator. When it is
    ``None`` (preset-verbatim path) we return an empty string so the
    explanation stays verbatim-stable for Phase 1 variants.
    """
    bias = trace.register_bias
    if bias == "low":
        return (
            "Low-register mapping makes roots and fifths behave like a pedal point, "
            "so the listener feels harmonic gravity before hearing melody."
        )
    if bias == "high":
        return (
            "High-register mapping lifts the loop into the cello's upper voice, "
            "so thirds, sevenths, and leading tones read as color rather than bass weight."
        )
    # "default" or None: keep the explanation stable for the verbatim path.
    return ""


def _cadence_clause(policy: StylePolicy) -> str:
    """Generate a note-specific cadence clause from the style policy.

    Picks the first cadence entry that has a meaningful 'why it works' comment
    and formats it as a prose clause describing the loop's harmonic closure.
    """
    cadences = policy.cadences
    if not cadences:
        return ""

    # Pick the first cadence — it's the most characteristic one
    for gesture, comment in cadences.items():
        if gesture and comment:
            return f"The loop's harmonic pull comes from the {gesture} gesture — {comment.lower().rstrip('.')}."
    return ""


def _style_context_clause(policy: StylePolicy) -> str:
    """Generate a genre-aware context clause describing the modal/textural identity."""
    parts = []
    if policy.modal_center:
        parts.append(f"Rooted in {policy.modal_center} modality")
    if policy.texture_idiom:
        # Take first sentence of texture idiom for a concise clause
        first_sentence = policy.texture_idiom.split(".")[0].strip()
        if first_sentence:
            parts.append(first_sentence.lower())
    if policy.genre_references:
        refs = policy.genre_references[:2]
        parts.append(
            f"drawing from {refs[0]} and {refs[1]}" if len(refs) > 1 else f"drawing from {refs[0]}"
        )
    if not parts:
        return ""
    return ". ".join(parts) + "."


def _chromatic_approach_clause(policy: StylePolicy) -> str:
    """Generate concrete chromatic approach suggestions from the style policy.

    Uses chromatic_approaches to suggest specific semitone moves the player
    can use to develop the loop — replacing the generic 'change one harmonic
    parameter at a time'.
    """
    approaches = policy.chromatic_approaches
    if not approaches:
        return ""

    clues = []
    for degree, description in approaches.items():
        desc_lower = description.lower()
        clues.append(f"try {degree} — {desc_lower.rstrip('.')}")

    if not clues:
        return ""

    return "Color-wise: " + "; ".join(clues[:3]) + "."



def _mood_tip_clause(preset: MoodPreset) -> str:
    """Pick the most relevant mood tip — the first one is most characteristic."""
    tips = preset.mood_tips
    if not tips:
        return ""
    return tips[0]



def _why_it_works_core(trace: GenerationTrace, preset: MoodPreset, policy: StylePolicy, anchor: str) -> str:
    """Build a note-specific 'why it works' explanation.

    Prioritizes: 1) chord-tone analysis from the trace, 2) policy cadence,
    3) style context, 4) register quality. Removes generic phrases like
    'keeps the loop identity clear'.
    """
    clauses = []

    # Chord-tone analysis (existing note-specific functions)
    headline = _headline_harmony_clause(trace, preset)
    if headline:
        clauses.append(headline)

    function_path = _function_path(trace, preset)
    if function_path:
        clauses.append(function_path)

    # Style policy: cadence gesture
    cadence = _cadence_clause(policy)
    if cadence:
        clauses.append(cadence)

    # Style context: modal center + texture idiom + genre references
    context = _style_context_clause(policy)
    if context:
        clauses.append(context)

    # Register quality
    register = _register_quality_clause(trace)
    if register:
        clauses.append(register)

    # Fallback: if nothing specific, use the anchor-based fallback
    if not clauses:
        return (
            f"{anchor} gives the listener a concrete point of return "
            f"in {preset.key_tonic} {preset.key_mode}."
        )

    return " ".join(clauses)


def explain(variant: LoopVariant, preset: MoodPreset) -> TheoryExplanation:
    if variant.trace is None:
        raise ValueError("Theory explanation requires variant.trace.")

    trace = variant.trace
    anchor = _select_anchor(trace)
    start_cue, transition_cue = cue_pair_for(preset, trace)
    tempo = preset.duet_tempo_bpm or preset.tempo_bpm

    # Load style-aware harmony policy
    policy = get_style_policy(preset.name)

    # --- why_it_works: note-specific, policy-driven ---
    core_clauses = _why_it_works_core(trace, preset, policy, anchor)
    feel = preset.feel.strip() or f"{preset.key_tonic} {preset.key_mode} cello loop"
    why_it_works = (
        f"This works because {_strip_sentence_end(core_clauses)}. "
        f"At {tempo} BPM, the {feel} stays grounded in its {policy.modal_center} character."
    )

    # --- how_to_start: register-aware cue ---
    bias = trace.register_bias
    if bias == "low":
        how_to_start = f"{start_cue} Lean into the weight of the lowest register so the loop feels rooted."
    elif bias == "high":
        how_to_start = f"{start_cue} Let the bow float lightly so the upper register sings and carries upward."
    else:
        how_to_start = start_cue

    # --- how_to_develop: chromatic approaches + mood tips ---
    mood_tip = _mood_tip_clause(preset)
    chromatic = _chromatic_approach_clause(policy)

    # Build note-specific intro clauses
    note_clauses = [
        clause
        for clause in (
            _minor_color_clause(trace),
            _anchor_role(trace, preset),
            _voice_leading_clause(trace),
        )
        if clause
    ]
    note_intro = " ".join(note_clauses) + " " if note_clauses else ""

    develop_parts = []
    if chromatic:
        develop_parts.append(chromatic)
    if mood_tip:
        develop_parts.append(mood_tip)

    if develop_parts:
        how_to_develop = f"{note_intro}{' '.join(develop_parts)}"
    else:
        how_to_develop = (
            f"{note_intro}Develop it by keeping the pulse steady and exploring the "
            f"{policy.modal_center} color palette — let small dynamic changes create motion "
            f"within the {policy.texture_idiom.split('.')[0].lower()} texture."
        )

    # --- how_to_end: cadence-driven ---
    cadences = policy.cadences
    if cadences:
        # Use the first cadence as the closing gesture
        closing_gesture = next(iter(cadences.keys()))
        how_to_end = (
            f"End by resolving through the {closing_gesture} gesture, "
            f"returning to {anchor}, then soften the dynamics and let the final bow stroke decay."
        )
    else:
        how_to_end = (
            f"End by returning to {anchor}, then remove harmonic tension by softening the dynamics "
            "and letting the final bow stroke decay."
        )

    # --- how_to_transition: modulation-driven ---
    modulation = _first_or_fallback(preset.modulations, "")
    if modulation:
        how_to_transition = f"{transition_cue} {modulation}"
    else:
        how_to_transition = (
            f"{transition_cue} "
            f"Move by repeating the {policy.modal_center} anchor once, "
            f"then shift the next loop entry to a nearby pitch within the mode."
        )

    return TheoryExplanation(
        why_it_works=why_it_works,
        how_to_start=how_to_start,
        how_to_develop=how_to_develop,
        how_to_end=how_to_end,
        how_to_transition=how_to_transition,
    )
