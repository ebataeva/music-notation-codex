from __future__ import annotations

from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "simple_sexy_d_minor_violin_cello_loop"
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
    score = stream.Score(id="simple_sexy_d_minor_violin_cello_loop")

    violin = stream.Part(id="violin")
    violin.append(instrument.Violin())
    violin.append(clef.TrebleClef())

    cello = stream.Part(id="cello")
    cello.append(instrument.Violoncello())
    cello.append(clef.BassClef())

    for part in (violin, cello):
        part.append(tempo.MetronomeMark(number=64))
        part.append(key.Key("D", "minor"))
        part.append(meter.TimeSignature("4/4"))

    # Two-chord vamp: Dm9 for breath, A7 for heat, repeated without heroic movement.
    cello_bars = [
        ["D2", "A2", "D3", "E3"],
        ["A1", "E2", "G2", "C#3"],
        ["D2", "A2", "D3", "E3"],
        ["A1", "E2", "G2", "C#3"],
        ["D2", "A2", "F2", "E2"],
        ["A1", "E2", "G2", "C#3"],
        ["D2", "A2", "D3", "E3"],
        ["A1", "E2", "G2", "C#3"],
    ]

    # The violin whispers around F-E-D, then lets C# pull back into D.
    violin_bars = [
        ["F4", "E4", "D4", "E4"],
        ["E4", "G4", "C#5", "Bb4"],
        ["F4", "E4", "D4", "A4"],
        ["G4", "E4", "C#4", "D4"],
        ["A4", "F4", "E4", "D4"],
        ["E4", "G4", "C#5", "Bb4"],
        ["F4", "E4", "D4", "E4"],
        ["C#4", "E4", "G4", "D4"],
    ]

    rhythm = [1.0, 1.0, 1.0, 1.0]

    for measure_number, pitches in enumerate(cello_bars, start=1):
        add_measure(cello, measure_number, pitches, rhythm, velocity=68)

    for measure_number, pitches in enumerate(violin_bars, start=1):
        add_measure(violin, measure_number, pitches, rhythm, velocity=58)

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
    print("Simple sexy duet loop: Dm9 <-> A7, 64 bpm, 8 bars, violin + cello")
    print(f"MusicXML: {MUSICXML_PATH}")
    print(f"MIDI: {MIDI_PATH}")


if __name__ == "__main__":
    main()
