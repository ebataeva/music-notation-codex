from __future__ import annotations

import argparse
import sys
from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Позволяет запускать скрипт напрямую (python3 scripts/...), не устанавливая пакет.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models import MoodPreset  # noqa: E402
from core.presets.registry import get_preset, list_presets  # noqa: E402


def build_cello_ostinato(preset: MoodPreset) -> stream.Score:
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
    parser.add_argument("--genre", choices=sorted(list_presets()), default="dark_trip_hop")
    parser.add_argument("--output-name", default=None, help="File name without extension.")
    parser.add_argument("--list-genres", action="store_true")
    return parser.parse_args()


def main() -> None:
    environment.UserSettings()["warnings"] = 0
    args = parse_args()

    if args.list_genres:
        for preset in [get_preset(n) for n in list_presets()]:
            print(f"{preset.name}: {preset.feel}")
        return

    preset = get_preset(args.genre)
    output_name = args.output_name or f"cello_{preset.name}_ostinato"
    score = build_cello_ostinato(preset)
    musicxml_path, midi_path = export_score(score, output_name)
    print(f"Genre: {preset.name} - {preset.feel}")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
