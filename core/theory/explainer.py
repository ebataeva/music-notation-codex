from __future__ import annotations

from collections.abc import Sequence

from core.models import GenerationTrace, LoopVariant, MoodPreset, TheoryExplanation
from core.presets.style_policy import StylePolicy, get_style_policy
from core.theory.cues import cue_pair_for
from core.theory.summaries import summarize_trace
from core.theory.harmony import (
    COLLECTIONS, ChordFacts, chord_facts, compatible_collections, degree_name,
    pitch_class as _pitch_class, roman_label, semitone as _semitone, transpose_name,
)


def _select_anchor(trace: GenerationTrace) -> str:
    from core.theory.cues import primary_register

    if trace.pattern_strategy not in {"preset_verbatim", "progression_driven_register_mapped"}:
        raise ValueError(f"Unknown pattern_strategy {trace.pattern_strategy!r}.")
    for tones in trace.chord_tones_used or []:
        if tones:
            if trace.pattern_strategy == "preset_verbatim":
                return f"the opening cello tone {tones[0]}"
            return f"the chord tone {tones[0]} placed in the {primary_register(trace)}"
    raise ValueError(f"{trace.pattern_strategy} trace has no chord tones to explain.")


def _collection_clause(tones: Sequence[str], preset: MoodPreset) -> str:
    tonic = _pitch_class(preset.key_tonic)
    compatible = compatible_collections(tones, tonic)
    if len(compatible) == 1:
        return f"The supplied pitch classes fit {tonic} {compatible[0]}."
    if compatible:
        choices = ", ".join(f"{tonic} {name}" for name in compatible)
        return f"The supplied pitch classes fit {choices}; they do not distinguish these collections."
    return (
        f"The supplied pitch classes do not fit a single {tonic} major, natural minor, "
        "harmonic minor, Dorian, or Phrygian collection; chromatic color or another tonal reading is possible."
    )


def _chord_inventory(chords: Sequence[ChordFacts]) -> str:
    items = []
    for chord in dict.fromkeys(chords):
        item = f"{chord.symbol}: {'-'.join(chord.tones)}"
        if chord.respellings:
            item += f" ({'; '.join(chord.respellings)}; enharmonic pitch-class reading)"
        items.append(item)
    return "Chord tones: " + "; ".join(items) + "."


def _cadence_clause(chords: Sequence[ChordFacts], preset: MoodPreset) -> str:
    if len(chords) < 2:
        return "No chord change is available to identify a closing gesture."
    tonic = _pitch_class(preset.key_tonic)
    pairs = [(left, right, False) for left, right in zip(chords, chords[1:])]
    if chords[-1] != chords[0]:
        pairs.append((chords[-1], chords[0], True))
    gestures = []
    for left, right, on_repeat in pairs:
        if degree_name(right.root, tonic) != "1" or right.quality not in {"major", "minor"}:
            continue
        left_degree = degree_name(left.root, tonic)
        lead = transpose_name(tonic, "M7")
        location = "On repeat, " if on_repeat else ""
        label = f"{location}{left.symbol} -> {right.symbol}"
        if left_degree == "5" and left.quality == "major":
            detail = (
                f"contains the leading note {lead}, a semitone below {tonic}; "
                f"{lead} -> {tonic} is an available voice-leading move. "
                "This can support an authentic cadence at a phrase ending"
            )
        elif left_degree == "7" and left.quality == "diminished":
            detail = f"offers a leading-note diminished return, with {lead} -> {tonic} available"
        elif left_degree == "5" and left.quality == "minor":
            detail = "offers a minor-v modal return; it does not require a major V chord"
        elif left_degree == "4":
            detail = "offers a fourth-degree return, with a plagal color if used to end a phrase"
        elif left_degree == "b2" and left.quality == "major":
            detail = "offers a flat-II modal return, with the root a semitone above the tonic"
        elif left_degree == "b7" and left.quality == "major":
            detail = "offers a flat-VII modal return"
        else:
            continue
        gestures.append(f"{label} {detail}.")
    if not gestures:
        return "These changes do not establish a specific closing gesture; phrasing remains open."
    return " ".join(dict.fromkeys(gestures)) + " Chord sets do not specify the performed voices or phrase endings."


def _borrowed_clause(chords: Sequence[ChordFacts], preset: MoodPreset) -> str:
    if preset.key_mode.lower() != "major":
        return ""
    tonic = _pitch_class(preset.key_tonic)
    clauses = []
    for chord in dict.fromkeys(chords):
        offsets = {(_semitone(tone) - _semitone(tonic)) % 12 for tone in chord.tones}
        if not offsets <= COLLECTIONS["major"] and offsets <= COLLECTIONS["natural minor (Aeolian)"]:
            clauses.append(
                f"{chord.symbol} ({'-'.join(chord.tones)}) is possible borrowing from parallel "
                f"{tonic} natural minor; this alone does not establish a key change."
            )
    return " ".join(clauses)


def _style_context_clause(policy: StylePolicy) -> str:
    mode = policy.modal_center.lower()
    if "dorian" in mode:
        palette = "Dorian, the minor mode with a natural sixth and flat seventh"
    elif "phrygian" in mode:
        palette = "Phrygian, the minor mode with a flat second"
    elif "aeolian" in mode:
        palette = "Aeolian (natural minor)"
        if "harmonic" in mode:
            palette += " with an optional raised seventh for tonal turnarounds"
    elif "harmonic" in mode:
        palette = "harmonic minor, with a raised seventh"
    else:
        palette = policy.modal_center
    references = "; ".join(policy.genre_references[:2])
    return (
        f"Style option: {palette} is the preset's suggested palette, not an inferred key. "
        f"Preset listening references: {references}."
    )


def _chromatic_approach_clause(policy: StylePolicy, preset: MoodPreset) -> str:
    tonic = _pitch_class(preset.key_tonic)
    fifth = transpose_name(tonic, "P5")
    advice = []
    for raw_degree in policy.chromatic_approaches:
        degree = str(raw_degree)
        if degree in {"bII", "b2"}:
            neighbor = transpose_name(tonic, "m2")
            advice.append(
                f"Try {neighbor} (b2, the flat second; bII root), a semitone above {tonic}, "
                f"moving {neighbor} -> {tonic}. This adds Phrygian color."
            )
        elif degree == "b6":
            neighbor = transpose_name(tonic, "m6")
            advice.append(
                f"Try {neighbor} (b6) -> {fifth} (5), a semitone descent from above. "
                "The flat sixth belongs to natural and harmonic minor."
            )
        elif degree == "6":
            sixth = transpose_name(tonic, "M6")
            advice.append(f"Explore {sixth} (6), the natural sixth of {tonic} Dorian, as an optional color.")
        elif degree == "b7":
            seventh = transpose_name(tonic, "m7")
            advice.append(f"Try {seventh} (b7), the flat seventh shared by natural minor and Dorian.")
        elif degree in {"7", "V"}:
            lead = transpose_name(tonic, "M7")
            advice.append(
                f"For an optional tonal pull, try {lead} (7) -> {tonic} (1), a semitone rise. "
                "In a minor context this raises the seventh; it changes a natural-minor or Dorian palette."
            )
    return "Optional development: " + " ".join(advice[:3]) if advice else ""


def _note_development(chords: Sequence[ChordFacts]) -> str:
    clauses = []
    for chord in chords:
        if chord.quality == "minor":
            third = transpose_name(chord.root, "m3")
            clauses.append(f"{third} gives {chord.symbol} its minor color; this describes the chord, not a new tonal center.")
            break
    for left, right in zip(chords, chords[1:]):
        right_pcs = {_semitone(tone) for tone in right.tones}
        shared = [tone for tone in left.tones if _semitone(tone) in right_pcs]
        if shared:
            clauses.append(
                f"{'/'.join(shared)} can be retained between {left.symbol} and {right.symbol} "
                "if the voicing allows it."
            )
            break
    return " ".join(clauses)


def _transition_clause(preset: MoodPreset, policy: StylePolicy) -> str:
    tonic = _pitch_class(preset.key_tonic)
    if "dorian" in policy.modal_center.lower():
        sixth = transpose_name(tonic, "M6")
        flat_sixth = transpose_name(tonic, "m6")
        return (
            f"Optional mode shift: {tonic} Dorian -> {tonic} natural minor. "
            f"Change {sixth} -> {flat_sixth} (6 -> b6), keeping the tonic fixed. "
            "This applies when the starting phrase uses the Dorian collection."
        )
    if preset.key_mode.lower() == "major":
        third = transpose_name(tonic, "M3")
        flat_third = transpose_name(tonic, "m3")
        return f"For a minor tonic color, try {third} -> {flat_third} (3 -> b3) over the same root."
    third = transpose_name(tonic, "m3")
    fifth = transpose_name(tonic, "P5")
    return (
        f"To explore {third} major next, try {tonic}m ({tonic}-{third}-{fifth}) as a common chord. "
        f"Establish {third} as the new tonal center in the following phrase; a shared chord alone is not a modulation."
    )


def explain(variant: LoopVariant, preset: MoodPreset) -> TheoryExplanation:
    if variant.trace is None:
        raise ValueError("Theory explanation requires variant.trace.")
    trace = variant.trace
    anchor = _select_anchor(trace)
    tones_by_bar = [tones for tones in trace.chord_tones_used or [] if tones]
    all_tones = [tone for tones in tones_by_bar for tone in tones]
    tonic = _pitch_class(preset.key_tonic)
    policy = get_style_policy(preset.name)
    start, transition = cue_pair_for(preset, trace)
    chords = []
    clauses = [f"Using {tonic} as the reference tonic; the tonal center is not inferred from a preset."]
    if trace.pattern_strategy == "progression_driven_register_mapped":
        chords = [chord_facts(tones) for tones in tones_by_bar]
        clauses.append("Harmony: " + " -> ".join(roman_label(chord, tonic) for chord in chords) + ".")
        clauses.append("Roman numerals use major-scale degree numbers; case and suffixes describe the supplied chord quality.")
        clauses.append(_chord_inventory(chords))
        clauses.append(_collection_clause(all_tones, preset))
        clauses.append(_cadence_clause(chords, preset))
        clauses.append(_borrowed_clause(chords, preset))
    else:
        names = list(dict.fromkeys(_pitch_class(tone) for tone in all_tones))
        clauses.append(
            f"The trace contains sequential cello notes {'-'.join(names)}, beginning with {anchor}; "
            "these notes do not establish complete chords or the other instrument's part."
        )
        clauses.append(_collection_clause(all_tones, preset))
    clauses.append(_style_context_clause(policy))
    tempo = preset.duet_tempo_bpm or preset.tempo_bpm
    clauses.append(f"Use the preset's {tempo} BPM pulse as a performance starting point.")

    if trace.register_bias == "low":
        start += " Use the low register for weight; a low part alone does not establish a pedal point."
    elif trace.register_bias == "high":
        start += " Use a light bow so the upper register sings."
    develop = " ".join(filter(None, [
        _note_development(chords),
        _chromatic_approach_clause(policy, preset),
        "Keep the pulse steady and leave space after the color note.",
    ]))
    if chords:
        ending = (
            f"To close the loop, you can return to {chords[0].symbol} ({'-'.join(chords[0].tones)}), "
            f"beginning with {anchor}. Shape the phrase with a softer final bow stroke."
        )
    else:
        ending = f"To close, return to {anchor}, then soften the dynamics and let the final bow stroke decay."
    result = TheoryExplanation(
        why_it_works=" ".join(filter(None, clauses)),
        how_to_start=start,
        how_to_develop=develop,
        how_to_end=ending,
        how_to_transition=f"{transition} {_transition_clause(preset, policy)}",
    )
    result.short_sections, result.term_ids = summarize_trace(variant, preset)
    return result
