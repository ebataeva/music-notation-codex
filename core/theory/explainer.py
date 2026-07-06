from __future__ import annotations

import re
from collections.abc import Sequence

from core.models import GenerationTrace, LoopVariant, MoodPreset, TheoryExplanation
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

    headline_clause = _headline_harmony_clause(trace, preset)
    if headline_clause:
        core_reason = headline_clause
    else:
        core_reason = (
            f"{anchor} gives the listener a concrete point of return in "
            f"{_strip_sentence_end(harmony_focus)}"
        )

    analysis_clauses = []
    for clause in (_function_path(trace, preset), register_clause):
        if clause:
            analysis_clauses.append(clause)

    why_it_works = (
        f"This works because {_strip_sentence_end(core_reason)}. {' '.join(analysis_clauses)} "
        f"The {tempo} BPM {feel} keeps the loop identity clear."
    )

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
        note_clauses = [
            clause
            for clause in (
                _minor_color_clause(trace),
                _anchor_role(trace, preset),
                _voice_leading_clause(trace),
            )
            if clause
        ]
        note_intro = ""
        if note_clauses:
            note_intro = " ".join(note_clauses) + " "
        how_to_develop = (
            f"{note_intro}Develop it by changing one harmonic parameter at a time: "
            f"keep the same rhythm, then vary color, tension, or register. {mood_tip}"
        )
    else:
        how_to_develop = (
            "Develop it by keeping the pulse steady and changing one harmonic detail at a time: "
            "keep the bow close to the string and let small dynamic changes create motion."
        )

    how_to_end = (
        f"End by returning to {anchor}, then remove harmonic tension by softening the dynamics "
        "and letting the final bow stroke decay."
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
