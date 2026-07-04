from __future__ import annotations

import sys
from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Позволяет запускать скрипт напрямую (python3 scripts/...), не устанавливая пакет.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.presets.registry import get_preset  # noqa: E402

OUTPUT_NAME = "dorian_sexy_violin_cello_loop"
MUSICXML_PATH = PROJECT_ROOT / "scores" / "musicxml" / f"{OUTPUT_NAME}.musicxml"
MIDI_PATH = PROJECT_ROOT / "scores" / "midi" / f"{OUTPUT_NAME}.mid"


def make_note(pitch_name: str, quarter_length: float, velocity: int) -> note.Note:
    n = note.Note(pitch_name)
    n.duration = duration.Duration(quarterLength=quarter_length)
    n.volume.velocity = velocity
    return n


def add_measure(part: stream.Part, number: int, pitches: list[str], rhythm: list[float], velocity: int) -> None:
    measure = stream.Measure(number=number)
    for pitch_name, quarter_length in zip(pitches, rhythm, strict=True):
        measure.append(make_note(pitch_name, quarter_length, velocity))
    part.append(measure)


def build_score() -> stream.Score:
    score = stream.Score(id="dorian_sexy_violin_cello_loop")

    violin = stream.Part(id="violin")
    violin.append(instrument.Violin())
    violin.append(clef.TrebleClef())

    cello = stream.Part(id="cello")
    cello.append(instrument.Violoncello())
    cello.append(clef.BassClef())

    for part in (violin, cello):
        part.append(tempo.MetronomeMark(number=88))
        part.append(key.Key("D", "minor"))
        part.append(meter.TimeSignature("4/4"))

    # D Dorian vamp: Dm9 -> G9. The B natural keeps it warm instead of funeral-dark.
    preset = get_preset("dorian_sexy_duet")
    cello_rhythm = preset.duet_rhythm["cello"]
    violin_rhythm = preset.duet_rhythm["violin"]
    cello_bars = preset.duet_bars["cello"]
    violin_bars = preset.duet_bars["violin"]

    for measure_number, pitches in enumerate(cello_bars, start=1):
        add_measure(cello, measure_number, pitches, cello_rhythm, velocity=74)

    for measure_number, pitches in enumerate(violin_bars, start=1):
        add_measure(violin, measure_number, pitches, violin_rhythm, velocity=62)

    score.insert(0, violin)
    score.insert(0, cello)
    return score


def export_score(score: stream.Score) -> None:
    MUSICXML_PATH.parent.mkdir(parents=True, exist_ok=True)
    MIDI_PATH.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(MUSICXML_PATH))

    midi_file = midi.translate.streamToMidiFile(score)
    midi_file.open(str(MIDI_PATH), "wb")
    midi_file.write()
    midi_file.close()


def main() -> None:
    environment.UserSettings()["warnings"] = 0
    score = build_score()
    export_score(score)
    print("Dorian sexy duet loop: Dm9 -> G9, 88 bpm, 8 bars, violin + cello")
    print(f"MusicXML: {MUSICXML_PATH}")
    print(f"MIDI: {MIDI_PATH}")


if __name__ == "__main__":
    main()
