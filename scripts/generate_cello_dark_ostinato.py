from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GenrePreset:
    name: str
    tempo_bpm: int
    key_tonic: str
    key_mode: str
    meter_signature: str
    velocity: int
    rhythm: list[float]
    bars: list[list[str]]
    feel: str


GENRE_PRESETS: dict[str, GenrePreset] = {
    "dark_trip_hop": GenrePreset(
        name="dark_trip_hop",
        tempo_bpm=72,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=76,
        rhythm=[0.5] * 8,
        bars=[
            ["C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"],
            ["C2", "C2", "G2", "Bb2", "C3", "Bb2", "G2", "Eb2"],
            ["Ab2", "Ab2", "Eb3", "G3", "Ab3", "G3", "Eb3", "C3"],
            ["G2", "G2", "D3", "F3", "G3", "F3", "D3", "Bb2"],
            ["C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"],
            ["Eb2", "Eb2", "Bb2", "C3", "Eb3", "C3", "Bb2", "G2"],
            ["F2", "F2", "C3", "Eb3", "F3", "Eb3", "C3", "Ab2"],
            ["G2", "G2", "D3", "F3", "G3", "F3", "D3", "C2"],
        ],
        feel="темный, сексуальный, петлевой trip-hop groove",
    ),
    "ritual_tribal": GenrePreset(
        name="ritual_tribal",
        tempo_bpm=88,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=88,
        rhythm=[0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5],
        bars=[
            ["D2", "D2", "A2", "D3", "C3", "A2", "F2"],
            ["D2", "D2", "A2", "F3", "E3", "C3", "A2"],
            ["Bb2", "Bb2", "F3", "E3", "D3", "A2", "F2"],
            ["C3", "C3", "G2", "Bb2", "A2", "F2", "D2"],
            ["D2", "D2", "A2", "D3", "C3", "A2", "F2"],
            ["F2", "F2", "C3", "F3", "E3", "C3", "A2"],
            ["G2", "G2", "D3", "F3", "E3", "C3", "Bb2"],
            ["A2", "A2", "E3", "G3", "F3", "E3", "D2"],
        ],
        feel="ритуальный пульс с акцентами, больше тела и движения",
    ),
    "noir_slow_burn": GenrePreset(
        name="noir_slow_burn",
        tempo_bpm=58,
        key_tonic="A",
        key_mode="minor",
        meter_signature="4/4",
        velocity=68,
        rhythm=[1.0, 0.5, 0.5, 1.0, 1.0],
        bars=[
            ["A2", "E3", "G3", "C3", "B2"],
            ["A2", "E3", "G3", "C3", "D3"],
            ["F2", "C3", "E3", "A2", "G2"],
            ["E2", "B2", "D3", "G2", "A2"],
            ["A2", "E3", "G3", "C3", "B2"],
            ["C3", "G2", "Bb2", "Eb3", "D3"],
            ["F2", "C3", "E3", "A2", "G2"],
            ["E2", "B2", "D3", "G2", "A2"],
        ],
        feel="медленный нуар, недосказанность, напряженная пауза",
    ),
    "driving_cinematic": GenrePreset(
        name="driving_cinematic",
        tempo_bpm=104,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=94,
        rhythm=[0.25] * 16,
        bars=[
            ["C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"],
            ["C2", "G2", "C3", "G2", "C2", "G2", "F3", "G2", "C2", "G2", "Eb3", "G2", "Bb2", "G2", "C3", "G2"],
            ["Ab2", "Eb3", "Ab3", "Eb3", "Ab2", "Eb3", "G3", "Eb3", "Ab2", "Eb3", "F3", "Eb3", "C3", "Eb3", "Ab2", "Eb3"],
            ["G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "Bb2", "D3", "G2", "D3"],
            ["C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"],
            ["Eb2", "Bb2", "Eb3", "Bb2", "Eb2", "Bb2", "G3", "Bb2", "Eb2", "Bb2", "F3", "Bb2", "C3", "Bb2", "G2", "Bb2"],
            ["F2", "C3", "F3", "C3", "F2", "C3", "Ab3", "C3", "F2", "C3", "Eb3", "C3", "Ab2", "C3", "F2", "C3"],
            ["G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "C3", "G2", "C2", "G2"],
        ],
        feel="быстрый кинематографичный мотор, драйв и нарастание",
    ),
}


def build_cello_ostinato(preset: GenrePreset) -> stream.Score:
    score = stream.Score(id=f"cello_{preset.name}")
    cello_part = stream.Part(id="cello")

    cello_part.append(instrument.Violoncello())
    cello_part.append(clef.BassClef())

    # Здесь задаются темп, тональность и размер.
    cello_part.append(tempo.MetronomeMark(number=preset.tempo_bpm))
    cello_part.append(key.Key(preset.key_tonic, preset.key_mode))
    cello_part.append(meter.TimeSignature(preset.meter_signature))

    # Здесь задаются ноты: каждый жанр использует свой набор тактов.
    for measure_number, pitches in enumerate(preset.bars, start=1):
        measure = stream.Measure(number=measure_number)

        # Здесь определяется ритм: длительности нот берутся из жанрового пресета.
        for pitch_name, quarter_length in zip(pitches, preset.rhythm, strict=True):
            cello_note = note.Note(pitch_name)
            cello_note.duration = duration.Duration(quarterLength=quarter_length)
            cello_note.volume.velocity = preset.velocity
            measure.append(cello_note)

        cello_part.append(measure)

    score.insert(0, cello_part)
    return score


def export_score(score: stream.Score, output_name: str) -> tuple[Path, Path]:
    musicxml_path = PROJECT_ROOT / "scores" / "musicxml" / f"{output_name}.musicxml"
    midi_path = PROJECT_ROOT / "scores" / "midi" / f"{output_name}.mid"
    musicxml_path.parent.mkdir(parents=True, exist_ok=True)
    midi_path.parent.mkdir(parents=True, exist_ok=True)

    # Здесь происходит экспорт: MusicXML для MuseScore, MIDI для Ableton.
    score.write("musicxml", fp=str(musicxml_path))

    midi_file = midi.translate.streamToMidiFile(score)
    midi_file.open(str(midi_path), "wb")
    midi_file.write()
    midi_file.close()
    return musicxml_path, midi_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cello ostinato MusicXML and MIDI files.")
    parser.add_argument("--genre", choices=sorted(GENRE_PRESETS), default="dark_trip_hop")
    parser.add_argument("--output-name", default=None, help="File name without extension.")
    parser.add_argument("--list-genres", action="store_true")
    return parser.parse_args()


def main() -> None:
    environment.UserSettings()["warnings"] = 0
    args = parse_args()

    if args.list_genres:
        for preset in GENRE_PRESETS.values():
            print(f"{preset.name}: {preset.feel}")
        return

    preset = GENRE_PRESETS[args.genre]
    output_name = args.output_name or f"cello_{preset.name}_ostinato"
    score = build_cello_ostinato(preset)
    musicxml_path, midi_path = export_score(score, output_name)
    print(f"Genre: {preset.name} - {preset.feel}")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
