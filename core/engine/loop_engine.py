"""LoopEngine: build music21 Scores from MoodPresets and generate traced variants.

Extracted from scripts/generate_cello_dark_ostinato.py's build_cello_ostinato()
(Phase 2 Plan 2). No music21-building logic remains in scripts/ once this
module is wired in -- see 02-PATTERNS.md for the extraction map.
"""

from __future__ import annotations

import random
import warnings

from music21 import clef, duration, instrument, key, meter, note, stream, tempo

from core.engine.validators import validate_bar_duration, validate_pitch
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
