from music21 import meter, pitch
from music21.pitch import PitchException

# Cello playable range, expressed in MIDI note numbers.
CELLO_MIN_MIDI = 36  # C2 -- lowest open string
CELLO_MAX_MIDI_DEFAULT = 74  # D5 -- default upper bound for generated material
CELLO_MAX_MIDI_EXTENDED = 84  # C6 -- extended upper bound (thumb position)


def validate_pitch(pitch_name: str, extended: bool = False) -> None:
    # Reject octave-less names (e.g. "C", "Bb") before construction -- music21
    # would otherwise silently default them to octave 4 (WR-02).
    if not any(ch.isdigit() for ch in pitch_name):
        raise ValueError(
            f"Pitch {pitch_name!r} must include an octave (e.g. 'C3'), "
            "not just a pitch class."
        )
    try:
        p = pitch.Pitch(pitch_name)
    except PitchException as exc:
        raise ValueError(f"Pitch {pitch_name!r} is not a valid pitch name: {exc}") from exc
    max_midi = CELLO_MAX_MIDI_EXTENDED if extended else CELLO_MAX_MIDI_DEFAULT
    if not (CELLO_MIN_MIDI <= p.midi <= max_midi):
        raise ValueError(
            f"Pitch {pitch_name} (MIDI {p.midi}) is outside playable cello range "
            f"({CELLO_MIN_MIDI}-{max_midi})."
        )


def validate_bar_duration(
    rhythm: list[float], meter_signature: str, tolerance: float = 1e-9
) -> None:
    if not rhythm:
        raise ValueError(f"Rhythm is empty for meter {meter_signature}.")
    if any(quarter_length <= 0 for quarter_length in rhythm):
        raise ValueError(f"Rhythm contains non-positive duration(s): {rhythm}")
    ts = meter.TimeSignature(meter_signature)
    expected_ql = ts.barDuration.quarterLength
    actual_ql = sum(rhythm)
    if abs(actual_ql - expected_ql) > tolerance:
        raise ValueError(
            f"Bar duration {actual_ql} != {expected_ql} for meter {meter_signature}."
        )
