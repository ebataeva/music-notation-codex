from __future__ import annotations

from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_NAME = "sexy_d_minor_violin_cello_loop"
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
    score = stream.Score(id="sexy_d_minor_violin_cello_loop")

    violin = stream.Part(id="violin")
    violin.append(instrument.Violin())
    violin.append(clef.TrebleClef())

    cello = stream.Part(id="cello")
    cello.append(instrument.Violoncello())
    cello.append(clef.BassClef())

    for part in (violin, cello):
        part.append(tempo.MetronomeMark(number=76))
        part.append(key.Key("D", "minor"))
        part.append(meter.TimeSignature("4/4"))

    cello_rhythm = [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5]
    violin_rhythm = [1.0, 0.5, 0.5, 1.0, 1.0]

    # The cello keeps the body of the loop: low pulse, fifths, and a chromatic pull back home.
    cello_bars = [
        ["D2", "A2", "D3", "C3", "A2", "F2", "A2"],
        ["D2", "A2", "F3", "E3", "C3", "A2", "F2"],
        ["Bb2", "F3", "A3", "G3", "F3", "D3", "Bb2"],
        ["A2", "E3", "G3", "F3", "E3", "C#3", "D2"],
        ["D2", "A2", "D3", "C3", "A2", "F2", "A2"],
        ["F2", "C3", "E3", "D3", "C3", "A2", "F2"],
        ["G2", "D3", "F3", "E3", "D3", "Bb2", "G2"],
        ["A2", "E3", "G3", "F3", "E3", "C#3", "D2"],
    ]

    # The violin answers in a breathy register: suspensions and half-step tension make it seductive.
    violin_bars = [
        ["A4", "C5", "D5", "F5", "E5"],
        ["A4", "C5", "E5", "D5", "C5"],
        ["Bb4", "D5", "F5", "E5", "D5"],
        ["A4", "C#5", "E5", "G5", "F5"],
        ["A4", "C5", "D5", "F5", "E5"],
        ["C5", "A4", "D5", "E5", "F5"],
        ["Bb4", "D5", "G5", "F5", "E5"],
        ["A4", "C#5", "E5", "G5", "D5"],
    ]

    for measure_number, pitches in enumerate(cello_bars, start=1):
        add_measure(cello, measure_number, pitches, cello_rhythm, velocity=82)

    for measure_number, pitches in enumerate(violin_bars, start=1):
        add_measure(violin, measure_number, pitches, violin_rhythm, velocity=70)

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
    print("Sexy duet loop: D minor, 76 bpm, 8 bars, violin + cello")
    print(f"MusicXML: {MUSICXML_PATH}")
    print(f"MIDI: {MIDI_PATH}")


if __name__ == "__main__":
    main()
