"""LoopEngine: build music21 Scores from MoodPresets and generate traced variants.

Extracted from scripts/generate_cello_dark_ostinato.py's build_cello_ostinato()
(Phase 2 Plan 2). No music21-building logic remains in scripts/ once this
module is wired in -- see 02-PATTERNS.md for the extraction map.
"""

from __future__ import annotations

import random
import warnings

from music21 import clef, duration, instrument, key, meter, note, pitch, stream, tempo

from core.engine.progression import ParsedChord
from core.engine.validators import (
    CELLO_MAX_MIDI_DEFAULT,
    CELLO_MIN_MIDI,
    validate_bar_duration,
    validate_pitch,
)
from core.models import GenerationTrace, LoopVariant, MoodPreset
from core.presets.registry import list_solo_presets

# Maximum bars a single generation request may produce (SAFE-02: denial-of-service
# guard against unbounded loop generation).
MAX_BARS = 64

# Per-preset set of pitch names known to violate validate_pitch's playable-range
# check but which must survive byte-identically (D-07). The only known case is
# simple_sexy_duet's "A1" (MIDI 33, below the C2 validator floor) -- pre-existing
# in the source script, migrated verbatim in Phase 1's data move, not previously
# validated at generation time.
_LEGACY_PITCH_EXCEPTIONS: dict[str, set[str]] = {
    "simple_sexy_duet": {"A1"},
}


def _is_legacy_exception(preset_name: str, pitch_name: str) -> bool:
    return pitch_name in _LEGACY_PITCH_EXCEPTIONS.get(preset_name, set())


def _resolve_seed(seed: int | None) -> tuple[int, random.Random]:
    """Resolve an explicit or generated seed (D-01/D-02): always return a concrete
    seed value plus a random.Random instance seeded with it, so the resolved seed
    can always be recorded in the trace even when the caller passed None."""
    if seed is None:
        seed = random.Random().getrandbits(32)
    return seed, random.Random(seed)


def build_score(preset: MoodPreset, seed: int | None = None) -> stream.Score:
    """Build a music21 Score for a solo cello preset (extracted from
    build_cello_ostinato). Validates pitch and rhythm data before construction
    (D-06) and enforces the SAFE-02 bar-count guard.
    """
    # SAFE-02: reject oversized requests before any Score object is constructed.
    if len(preset.bars) > MAX_BARS:
        raise ValueError(f"Requested {len(preset.bars)} bars exceeds the maximum of {MAX_BARS}.")

    # D-01/D-02: resolve seed up front. The preset-verbatim strategy doesn't
    # consume randomness yet, but threading the Random instance through now
    # avoids an interface change when Phase 2.5 adds real variation.
    _resolved_seed, _rng = _resolve_seed(seed)

    validate_bar_duration(preset.rhythm, preset.meter_signature)

    score = stream.Score(id=f"cello_{preset.name}")
    cello_part = stream.Part(id="cello")

    cello_part.append(instrument.Violoncello())
    cello_part.append(clef.BassClef())

    cello_part.append(tempo.MetronomeMark(number=preset.tempo_bpm))
    cello_part.append(key.Key(preset.key_tonic, preset.key_mode))
    cello_part.append(meter.TimeSignature(preset.meter_signature))

    for measure_number, pitches in enumerate(preset.bars, start=1):
        measure = stream.Measure(number=measure_number)
        for pitch_name, quarter_length in zip(pitches, preset.rhythm, strict=True):
            if _is_legacy_exception(preset.name, pitch_name):
                warnings.warn(
                    f"Skipping validate_pitch for legacy out-of-range note "
                    f"{pitch_name!r} in preset {preset.name!r} (D-07).",
                    stacklevel=2,
                )
            else:
                validate_pitch(pitch_name)
            cello_note = note.Note(pitch_name)
            cello_note.duration = duration.Duration(quarterLength=quarter_length)
            cello_note.volume.velocity = preset.velocity
            measure.append(cello_note)
        cello_part.append(measure)

    score.insert(0, cello_part)
    return score


def generate_variant(preset: MoodPreset, seed: int | None = None) -> LoopVariant:
    """High-level API (D-05): build a Score and a fully-populated GenerationTrace
    in one call. This function itself contains no recursive/self-call path
    (SAFE-07): it builds exactly one Score per invocation, enforced by this
    flat, non-recursive structure rather than by documentation alone.
    """
    # WR-06: duet-only presets carry empty solo bars/rhythm; failing here gives
    # the caller an actionable message instead of the internal "Rhythm is empty".
    if not preset.bars:
        raise ValueError(
            f"Preset {preset.name!r} has no solo bars (duet-only preset); "
            f"choose one of: {', '.join(list_solo_presets())}."
        )

    # SAFE-02: guard here too, before build_score is even invoked, so the trace
    # accumulation loop below never starts for an oversized request either.
    if len(preset.bars) > MAX_BARS:
        raise ValueError(f"Requested {len(preset.bars)} bars exceeds the maximum of {MAX_BARS}.")

    resolved_seed, _rng = _resolve_seed(seed)

    score = build_score(preset, seed=resolved_seed)

    register_choices: list[str] = []
    chord_tones_used: list[list[str]] = []
    for pitches in preset.bars:
        chord_tones_used.append(list(pitches))
        register_choices.append(_classify_register(pitches))

    generation_trace = GenerationTrace(
        seed=resolved_seed,
        pattern_strategy="preset_verbatim",
        register_choices=register_choices,
        voice_leading_steps=None,  # No voice-leading logic exists yet (Phase 2.5 concern).
        chord_tones_used=chord_tones_used,
    )

    return LoopVariant(
        id=f"{preset.name}-{resolved_seed}",
        preset_name=preset.name,
        label=preset.feel or preset.name,
        musicxml_path=None,
        midi_path=None,
        svg_bytes=None,
        midi_bytes=None,
        theory_explanation=None,  # Phase 3 (TheoryExplainer) concern.
        trace=generation_trace,
    )


def make_note(pitch_name: str, quarter_length: float, velocity: int) -> note.Note:
    """Build a single music21 Note with duration and velocity set (extracted
    verbatim from the 3 duet scripts' identical helper -- Plan 03, D-13)."""
    n = note.Note(pitch_name)
    n.duration = duration.Duration(quarterLength=quarter_length)
    n.volume.velocity = velocity
    return n


def add_measure(
    part: stream.Part, number: int, pitches: list[str], rhythm: list[float], velocity: int
) -> None:
    """Append one Measure built from pitches/rhythm/velocity to a Part
    (extracted verbatim from the 3 duet scripts' identical helper -- Plan 03)."""
    measure = stream.Measure(number=number)
    for pitch_name, quarter_length in zip(pitches, rhythm, strict=True):
        measure.append(make_note(pitch_name, quarter_length, velocity))
    part.append(measure)


def build_duet_score(
    preset: MoodPreset, tempo_bpm: int, cello_velocity: int, violin_velocity: int
) -> stream.Score:
    """Internal-only two-part (cello+violin) path (D-13) -- not exposed via
    generate_variant(); DUET-01 public duet API is v2 scope. Called directly
    by the 3 duet scripts only. Extracted from their identical build_score()
    (renamed here to avoid colliding with this module's solo build_score).
    """
    # WR-04: duet fields are typed `dict | None` -- fail with a diagnosable
    # ValueError instead of a raw TypeError when handed a solo preset.
    if preset.duet_rhythm is None or preset.duet_bars is None:
        raise ValueError(
            f"Preset {preset.name!r} has no duet data; use build_score() for solo presets."
        )

    cello_rhythm = preset.duet_rhythm["cello"]
    violin_rhythm = preset.duet_rhythm["violin"]
    cello_bars = preset.duet_bars["cello"]
    violin_bars = preset.duet_bars["violin"]

    # SAFE-02 (WR-03): reject oversized requests before any Score object is
    # constructed, matching the solo path's guard in build_score/generate_variant.
    for part_name, bars in (("cello", cello_bars), ("violin", violin_bars)):
        if len(bars) > MAX_BARS:
            raise ValueError(
                f"{part_name} part: {len(bars)} bars exceeds the maximum of {MAX_BARS}."
            )

    # WR-05: parts of different lengths would silently produce a misaligned
    # score -- enforce inter-part bar-count alignment, matching the strictness
    # of the intra-bar zip(..., strict=True) check in add_measure.
    if len(cello_bars) != len(violin_bars):
        raise ValueError(
            f"Duet parts have mismatched bar counts: "
            f"cello={len(cello_bars)}, violin={len(violin_bars)}."
        )

    validate_bar_duration(cello_rhythm, preset.meter_signature)
    validate_bar_duration(violin_rhythm, preset.meter_signature)

    score = stream.Score(id=f"duet_{preset.name}")

    violin = stream.Part(id="violin")
    violin.append(instrument.Violin())
    violin.append(clef.TrebleClef())

    cello = stream.Part(id="cello")
    cello.append(instrument.Violoncello())
    cello.append(clef.BassClef())

    for part in (violin, cello):
        part.append(tempo.MetronomeMark(number=tempo_bpm))
        part.append(key.Key(preset.key_tonic, preset.key_mode))
        part.append(meter.TimeSignature(preset.meter_signature))

    for measure_number, pitches in enumerate(cello_bars, start=1):
        for pitch_name in pitches:
            if _is_legacy_exception(preset.name, pitch_name):
                warnings.warn(
                    f"Skipping validate_pitch for legacy out-of-range note "
                    f"{pitch_name!r} in preset {preset.name!r} (D-07).",
                    stacklevel=2,
                )
            else:
                # Cello part: default (non-extended) cello range, matching build_score.
                validate_pitch(pitch_name)
        add_measure(cello, measure_number, pitches, cello_rhythm, velocity=cello_velocity)

    for measure_number, pitches in enumerate(violin_bars, start=1):
        for pitch_name in pitches:
            if _is_legacy_exception(preset.name, pitch_name):
                warnings.warn(
                    f"Skipping validate_pitch for legacy out-of-range note "
                    f"{pitch_name!r} in preset {preset.name!r} (D-07).",
                    stacklevel=2,
                )
            else:
                # Violin part sits in a higher register than the cello-tuned
                # default range (max MIDI 74) -- e.g. sexy_duet's F5 (MIDI 77).
                # validate_pitch's range check is cello-specific throughout
                # this module (CELLO_MIN_MIDI/CELLO_MAX_MIDI_*); pass
                # extended=True so legitimate violin notes aren't rejected as
                # if they were out-of-range cello notes (Rule 1 fix -- the
                # plan's action text didn't account for this range mismatch).
                validate_pitch(pitch_name, extended=True)
        add_measure(violin, measure_number, pitches, violin_rhythm, velocity=violin_velocity)

    score.insert(0, violin)
    score.insert(0, cello)
    return score


def _classify_register(pitches: list[str]) -> str:
    """Cheap register label for a bar's pitches, based on the lowest octave digit
    present. Not a music-theoretic register model -- just enough to populate a
    non-empty, per-bar trace field (D-04)."""
    octaves = [int(ch) for pitch_name in pitches for ch in pitch_name if ch.isdigit()]
    if not octaves:
        return "unspecified register"
    lowest = min(octaves)
    if lowest <= 2:
        return "low register"
    if lowest == 3:
        return "mid register"
    return "high register"


# ---------------------------------------------------------------------------
# Phase 2.5: progression-driven generation
# ---------------------------------------------------------------------------
#
# Chord-tone -> cello-register mapping. Given a chord's pitch-class tones
# (from core.engine.progression.ParsedChord), choose concrete octave-bearing
# pitches within C2-D5 (the same range validate_pitch's default enforces --
# confirmed C2 == MIDI 36 == CELLO_MIN_MIDI, D5 == MIDI 74 ==
# CELLO_MAX_MIDI_DEFAULT). This is new logic with no direct extraction
# analog: the preset-verbatim path (build_score/generate_variant) already
# has its pitches baked into MoodPreset.bars and is left completely
# untouched by everything below.

# All candidate octaves within the cello's default playable range, low to
# high -- register choice tries these in order, preferring the lowest
# register that satisfies root/fifth preference and the max-leap constraint.
_CANDIDATE_OCTAVES = [2, 3, 4, 5]


def _all_candidate_pitches(pitch_class: str) -> list[pitch.Pitch]:
    """Every concrete Pitch for a pitch class across the cello's playable
    octaves (C2-D5 inclusive), sorted low to high."""
    candidates = []
    for octave in _CANDIDATE_OCTAVES:
        p = pitch.Pitch(pitch_class)
        p.octave = octave
        if CELLO_MIN_MIDI <= p.midi <= CELLO_MAX_MIDI_DEFAULT:
            candidates.append(p)
    return sorted(candidates, key=lambda p: p.midi)


def _choose_register_for_chord_tone(
    pitch_class: str,
    is_root_or_fifth: bool,
    previous_pitch: pitch.Pitch | None,
    rng: random.Random,
) -> pitch.Pitch:
    """Pick one concrete octave for a chord-tone pitch class.

    Judgment call (per the plan's autonomy contract -- register mapping has
    no single obviously-correct answer, but this stays within Task 2's blast
    radius as an algorithmic choice, not an architectural one): root/fifth
    tones are biased toward the low register (octaves 2-3); other chord
    tones (e.g. the third) default to the mid register (octave 3-4) so the
    line doesn't collapse onto a single drone pitch. Whenever a previous
    note exists, the candidate closest to it -- within an octave leap -- is
    preferred over the register bias, so voice-leading stays smooth.
    """
    candidates = _all_candidate_pitches(pitch_class)
    if not candidates:
        # Chord tone has no representative pitch inside the cello's playable
        # range at all (shouldn't happen for natural/sharp/flat pitch
        # classes given the 4-octave candidate span, but fail loudly rather
        # than silently producing an unplayable note).
        raise ValueError(
            f"No playable octave found for pitch class {pitch_class!r} within "
            f"the cello's default range (MIDI {CELLO_MIN_MIDI}-{CELLO_MAX_MIDI_DEFAULT})."
        )

    # WR-01: the max-leap rule *constrains* the candidate set, it does not by
    # itself pick the note. Short-circuiting on "closest to previous" made the
    # line ratchet upward (root->third->fifth cycles up 3-5 semitones each
    # time, always closer than the octave-down neighbour) until it parked at
    # the top of the range, leaving the low-register bias dead after note 1.
    # Instead: narrow to within-leap candidates, then apply the register bias
    # inside that set so root/fifth tones still favour the low octaves.
    if previous_pitch is not None:
        within_leap = [c for c in candidates if abs(c.midi - previous_pitch.midi) <= 12]
        if within_leap:
            candidates = within_leap

    if is_root_or_fifth:
        pool = [c for c in candidates if c.octave <= 3] or candidates
    else:
        pool = [c for c in candidates if c.octave in (3, 4)] or candidates

    return rng.choice(pool)


def _register_map_chord(
    chord: ParsedChord,
    count: int,
    previous_pitch: pitch.Pitch | None,
    rng: random.Random,
) -> tuple[list[pitch.Pitch], pitch.Pitch]:
    """Map a single chord's tones onto `count` concrete pitches (one per
    rhythm slot in a bar), monophonic, favoring root/fifth in the low
    register and avoiding leaps larger than an octave between consecutive
    notes. Returns (pitches, last_pitch) so the caller can thread
    voice-leading continuity into the next bar."""
    root = chord.components[0]
    # IN-03: find the fifth by interval from the root (6/7/8 semitones =
    # dim/perfect/aug fifth) rather than assuming triadic index 2 -- power
    # chords like C5 put the fifth at index 1, and non-triadic qualities can
    # push it elsewhere. Only affects which tones get the low-register bias.
    root_pc = pitch.Pitch(root).pitchClass
    fifth = next(
        (c for c in chord.components[1:]
         if (pitch.Pitch(c).pitchClass - root_pc) % 12 in (6, 7, 8)),
        None,
    )

    bar_pitches: list[pitch.Pitch] = []
    current_previous = previous_pitch
    for i in range(count):
        pitch_class = chord.components[i % len(chord.components)]
        is_root_or_fifth = pitch_class in (root, fifth)
        chosen = _choose_register_for_chord_tone(
            pitch_class, is_root_or_fifth, current_previous, rng
        )
        bar_pitches.append(chosen)
        current_previous = chosen

    return bar_pitches, current_previous


def _respell_pitch_to_key(p: pitch.Pitch, key_obj: key.Key) -> pitch.Pitch:
    """IN-02: pychord spells some qualities with sharps regardless of key
    context (Gm -> G, A#, D), so a flat-key progression can leak A# where the
    notation should read Bb. Respell a single-accidental pitch to match the
    key's flat/sharp preference; leave naturals and neutral keys (0 sharps)
    untouched. Playback is unchanged -- getEnharmonic preserves pitch/MIDI."""
    if p.accidental is None or p.accidental.alter == 0:
        return p
    has_sharp = p.accidental.alter > 0
    if key_obj.sharps < 0 and has_sharp:
        return p.getEnharmonic()
    if key_obj.sharps > 0 and not has_sharp:
        return p.getEnharmonic()
    return p


def build_progression_score(
    chords: list[ParsedChord],
    preset: MoodPreset,
    seed: int | None = None,
) -> stream.Score:
    """Build a music21 Score from an arbitrary parsed chord progression, using
    `preset` only for its rhythm/tempo/meter/velocity strategy (the *when* --
    existing MoodPreset data), while this function decides *which* pitch (the
    chord-tone -> register mapping above). One bar per chord, matching the
    preset's rhythm pattern per bar. The preset-verbatim build_score() path
    above is completely untouched by this function.
    """
    # SAFE-02: same bar-count guard as the preset-only path, applied to the
    # progression's chord count (each chord produces exactly one bar here).
    if len(chords) > MAX_BARS:
        raise ValueError(f"Requested {len(chords)} bars exceeds the maximum of {MAX_BARS}.")
    if not chords:
        raise ValueError("Progression must contain at least one chord to build a score.")

    # WR-02: the progression path drives its bars from preset.rhythm; a
    # duet-only preset has none, so guard here with an actionable message
    # instead of leaking the internal "Rhythm is empty for meter 4/4."
    if not preset.rhythm:
        raise ValueError(
            f"Preset {preset.name!r} has no solo rhythm (duet-only preset); "
            f"choose one of: {', '.join(list_solo_presets())}."
        )

    _resolved_seed, rng = _resolve_seed(seed)

    validate_bar_duration(preset.rhythm, preset.meter_signature)
    notes_per_bar = len(preset.rhythm)

    score = stream.Score(id=f"progression_{preset.name}")
    cello_part = stream.Part(id="cello")

    cello_part.append(instrument.Violoncello())
    cello_part.append(clef.BassClef())

    cello_part.append(tempo.MetronomeMark(number=preset.tempo_bpm))
    preset_key = key.Key(preset.key_tonic, preset.key_mode)
    cello_part.append(preset_key)
    cello_part.append(meter.TimeSignature(preset.meter_signature))

    previous_pitch: pitch.Pitch | None = None
    for measure_number, chord in enumerate(chords, start=1):
        bar_pitches, previous_pitch = _register_map_chord(
            chord, notes_per_bar, previous_pitch, rng
        )

        measure = stream.Measure(number=measure_number)
        for concrete_pitch, quarter_length in zip(bar_pitches, preset.rhythm, strict=True):
            pitch_name = _respell_pitch_to_key(concrete_pitch, preset_key).nameWithOctave
            validate_pitch(pitch_name)
            cello_note = note.Note(pitch_name)
            cello_note.duration = duration.Duration(quarterLength=quarter_length)
            cello_note.volume.velocity = preset.velocity
            measure.append(cello_note)
        cello_part.append(measure)

    score.insert(0, cello_part)
    return score


def generate_variant_from_progression(
    chords: list[ParsedChord],
    preset: MoodPreset,
    seed: int | None = None,
) -> LoopVariant:
    """High-level API mirroring generate_variant(), but for an arbitrary
    parsed chord progression instead of a preset's own baked-in bars.
    Populates a full per-bar GenerationTrace: chord tones chosen, register
    decision, and pattern strategy used.
    """
    if len(chords) > MAX_BARS:
        raise ValueError(f"Requested {len(chords)} bars exceeds the maximum of {MAX_BARS}.")
    if not chords:
        raise ValueError("Progression must contain at least one chord to generate a variant.")

    resolved_seed, _rng = _resolve_seed(seed)

    score = build_progression_score(chords, preset, seed=resolved_seed)

    register_choices: list[str] = []
    chord_tones_used: list[list[str]] = []
    cello_part = score.parts[0]
    for measure, chord in zip(
        cello_part.getElementsByClass(stream.Measure), chords, strict=True
    ):
        bar_pitch_names = [n.pitch.nameWithOctave for n in measure.notes]
        chord_tones_used.append(list(chord.components))
        register_choices.append(_classify_register(bar_pitch_names))

    generation_trace = GenerationTrace(
        seed=resolved_seed,
        pattern_strategy="progression_driven_register_mapped",
        register_choices=register_choices,
        voice_leading_steps=None,  # Explicit step-interval trace is a future refinement.
        chord_tones_used=chord_tones_used,
    )

    progression_label = " ".join(chord.name for chord in chords)
    return LoopVariant(
        id=f"progression-{preset.name}-{resolved_seed}",
        preset_name=preset.name,
        label=f"{progression_label} ({preset.feel or preset.name})",
        musicxml_path=None,
        midi_path=None,
        svg_bytes=None,
        midi_bytes=None,
        theory_explanation=None,  # Phase 3 (TheoryExplainer) concern.
        trace=generation_trace,
    )
