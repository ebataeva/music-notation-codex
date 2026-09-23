from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence

from music21 import pitch

from core.models import (
    LOOP_SEAM_MARKER,
    GenerationTrace,
    LoopVariant,
    MoodPreset,
    TheoryExplanation,
)
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


def _chord_inventory(chords: Sequence[ChordFacts], played_by_bar: Sequence[Sequence[str]] | None) -> str:
    """List what was supplied and, separately, what the loop actually sounds.

    READ-01 keeps a bar to a few notes, so a Dm9 bar usually plays D-F-A and
    not all five tones. Claiming the full chord as "the notes" would make the
    explanation describe the input rather than the loop the player reads.
    """
    items = []
    for chord in dict.fromkeys(chords):
        item = f"{chord.symbol}: {'-'.join(chord.tones)}"
        if chord.respellings:
            item += f" ({'; '.join(chord.respellings)}; enharmonic pitch-class reading)"
        items.append(item)
    text = "Chord tones: " + "; ".join(items) + "."
    if played_by_bar:
        bars = []
        for chord, names in zip(chords, played_by_bar):
            sounded = list(dict.fromkeys(_pitch_class(name) for name in names))
            # VAR-01: the written notes, octaves included, are the one detail
            # that always tells two takes apart -- the low and default takes
            # can differ by a single octave that no summary sentence catches.
            played = "-".join(written_name(name) for name in names)
            bars.append(f"{chord.symbol} sounds {'-'.join(sounded)} (played {played})")
        text += " Each bar keeps only a few of them so the line reads at sight; in this loop " + "; ".join(bars) + "."
    return text


_OCTAVE_NAME_RE = re.compile(r"^([A-Ga-g][#b\-x♭♯]*)(\d+)$")


def written_name(name: str) -> str:
    """The note as the stave prints it: "B-2" (music21's flat) -> "Bb2".

    SPELL-01: only the accidental's notation changes. The letter comes from the
    engine, which spelled it from the chord, and the octave digit is kept as
    written -- B#3 sounds as C4 but sits on the B line of octave 3.
    """
    match = _OCTAVE_NAME_RE.match(name.strip())
    if match is None:
        return _pitch_class(name)
    return _pitch_class(match.group(1)) + match.group(2)


# Cards are capped at this many words (see summaries); an optional take
# sentence is dropped from a card rather than pushing it over.
_CARD_WORD_LIMIT = 65


class _Take:
    """What one generated take actually plays, in written names.

    VAR-01: the progression, key and preset are shared by all takes, so this is
    the only per-take evidence the sections can draw on. Built from
    `played_pitches`; preset-verbatim traces have none and get no take clauses.
    """

    def __init__(self, played: Sequence[Sequence[str]]):
        self.bars = [[written_name(name) for name in bar] for bar in played if bar]
        notes = [name for bar in self.bars for name in bar]
        self.opening = notes[0]
        self.closing = notes[-1]
        # Counter keeps first-seen order on ties, so the choice is stable.
        self.center = Counter(notes).most_common(1)[0][0]
        heights = sorted(notes, key=lambda name: _absolute_semitone(name) or 0)
        self.span = f"{heights[0]}–{heights[-1]}"

    @classmethod
    def of(cls, trace: GenerationTrace) -> _Take | None:
        if not any(trace.played_pitches or []):
            return None
        return cls(trace.played_pitches)

    def outline(self) -> str:
        ends = (
            f"opens and closes on {self.opening}"
            if self.opening == self.closing
            else f"opens on {self.opening}, closes on {self.closing}"
        )
        return f"This take {ends}, stays within {self.span} and returns most often to {self.center}."

    def phrase(self) -> str:
        entries = [bar[0] for bar in self.bars]
        path = " -> ".join(entries[:4]) + (" -> ..." if len(entries) > 4 else "")
        return (
            f"Shape this take's bar entries {path} as one phrase inside {self.span}, "
            f"leaning on {self.center}, its most repeated note."
        )

    def last_bar(self) -> str:
        return f"This take's last bar plays {'-'.join(self.bars[-1])}; let its final {self.closing} settle."

    def hand_off(self) -> str:
        if self.opening == self.closing:
            return f"Carry the final {self.closing}, also this take's opening note, into the next phrase as its first note."
        return f"Carry the final {self.closing} into the next phrase and answer it from the opening {self.opening}."

    def register_hint(self) -> str:
        return f"Staying inside {self.span} keeps the new section in this take's voice."


def _lead(parts: Sequence[str], body: str) -> str:
    return " ".join(filter(None, [*parts, body]))


def _fit_card(required: str, optional: str, body: str) -> str:
    """Card text with the take sentence(s) up front, dropping `optional` when
    the card would otherwise exceed its word limit."""
    full = _lead([required, optional], body)
    if len(full.split()) <= _CARD_WORD_LIMIT:
        return full
    return _lead([required], body)


def _absolute_semitone(pitch_name: str) -> int | None:
    """Semitone height of an octave-bearing name like "A2" or "D-3" (music21
    spells flats with "-"), or None for the octave-less pitch classes some
    traces use.

    SPELL-01: the octave number belongs to the letter, not to the sound, so a
    name can cross the octave boundary -- B#3 is written on the B line of
    octave 3 but sounds as C4, and Cb4 sounds as B3. Adding twelve per octave
    to the pitch class therefore misplaces those names by a whole octave, which
    is how "B#3->D#4" was once reported as a leap of fifteen semitones instead
    of three. music21 resolves the name properly.
    """
    match = _OCTAVE_NAME_RE.match(pitch_name.strip())
    if match is None:
        return None
    return pitch.Pitch(pitch_name.strip().replace("b", "-")).midi


def _melodic_shape_clause(trace: GenerationTrace) -> str:
    """One short sentence about the line this variant actually produced.

    VAR-01: every other clause is derived from the progression and the preset,
    which are identical across the three variants, so the three cards used to
    read the same even though their notes differ. This reads
    `voice_leading_steps`, which is per-variant, and leads the card with it.
    """
    steps = trace.voice_leading_steps or []
    moves: list[tuple[str, str, int]] = []
    for step in steps:
        body = step[: -len(LOOP_SEAM_MARKER)] if step.endswith(LOOP_SEAM_MARKER) else step
        start_name, _, end_name = body.partition("->")
        start = _absolute_semitone(start_name)
        end = _absolute_semitone(end_name)
        if start is None or end is None:
            continue
        moves.append((written_name(start_name), written_name(end_name), end - start))
    if not moves:
        return ""

    stepwise = sum(1 for *_, delta in moves if 0 < abs(delta) <= 2)
    widest_start, widest_end, widest = max(moves, key=lambda m: abs(m[2]))
    if stepwise * 2 >= len(moves):
        shape = (
            f"This take mostly walks ({stepwise} of {len(moves)} moves are a step or less); "
            f"its widest move is {widest_start}->{widest_end}."
        )
    else:
        shape = (
            f"This take leaps: its widest move is {widest_start}->{widest_end} "
            f"({abs(widest)} semitones), so plan that shift."
        )
    repeated = [name for name, _, delta in moves if delta == 0]
    if repeated:
        held = max(set(repeated), key=repeated.count)
        shape += f" {held} repeats as a pedal and anchors the bar."
    return shape


def _loop_seam_clause(trace: GenerationTrace) -> str:
    """Name the step from the loop's last note back to its first.

    The player performs that step on every repeat, and it is the hardest
    physical moment in the loop. Returns "" when the trace carries no seam so
    preset-verbatim variants keep their wording.
    """
    steps = trace.voice_leading_steps or []
    seam = next((s for s in steps if s.endswith(LOOP_SEAM_MARKER)), None)
    if not seam:
        return ""
    move = seam[: -len(LOOP_SEAM_MARKER)]
    start_name, _, end_name = move.partition("->")
    start = _absolute_semitone(start_name)
    end = _absolute_semitone(end_name)
    if start is None or end is None:
        return ""
    distance = abs(end - start)
    move = f"{written_name(start_name)}->{written_name(end_name)}"
    if distance == 0:
        return f"The repeat lands back on {written_name(start_name)} itself; no shift is needed."
    unit = "semitone" if distance == 1 else "semitones"
    return f"The repeat is {move}, {distance} {unit} back to the top; keep that return in the hand."


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
    # VAR-01: lead with what makes THIS take different; everything after it is
    # progression- and preset-derived and identical across the three variants.
    # The shape alone is not enough -- the low and default takes often share
    # their widest move -- so the take's own notes come first.
    take = _Take.of(trace)
    outline = take.outline() if take else ""
    shape = _melodic_shape_clause(trace)
    clauses = [outline, shape, f"Using {tonic} as the reference tonic; the tonal center is not inferred from a preset."]
    if trace.pattern_strategy == "progression_driven_register_mapped":
        chords = [chord_facts(tones) for tones in tones_by_bar]
        clauses.append("Harmony: " + " -> ".join(roman_label(chord, tonic) for chord in chords) + ".")
        clauses.append("Roman numerals use major-scale degree numbers; case and suffixes describe the supplied chord quality.")
        clauses.append(_chord_inventory(chords, trace.played_pitches))
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
        take and take.phrase(),
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
    # LOOP-CYCLE: a loop is played round and round, so name the step back to
    # the top, the one gesture the player repeats every single pass.
    seam = _loop_seam_clause(trace)
    result = TheoryExplanation(
        why_it_works=" ".join(filter(None, clauses)),
        how_to_start=start,
        how_to_develop=develop,
        how_to_end=" ".join(filter(None, [ending, take and take.last_bar(), seam])),
        how_to_transition=_lead(
            [take.hand_off(), take.register_hint()] if take else [],
            f"{transition} {_transition_clause(preset, policy)}",
        ),
    )
    result.short_sections, result.term_ids = summarize_trace(variant, preset)
    # The cards show the short sections, so they carry the per-take sentence
    # and the seam too; otherwise three cards read identically on screen.
    short = result.short_sections
    short["why_it_works"] = _fit_card(outline, shape, short["why_it_works"])
    if take:
        short["how_to_develop"] = _fit_card(take.phrase(), "", short["how_to_develop"])
        short["how_to_transition"] = _fit_card(take.hand_off(), "", short["how_to_transition"])
    if seam:
        # Two sentences on the card: the return itself, then the seam. The
        # "not an inferred cadence" hedge stays in the long text only.
        first_sentence = result.short_sections["how_to_end"].split(". ")[0].rstrip(".") + "."
        result.short_sections["how_to_end"] = f"{first_sentence} {seam}"
    return result
