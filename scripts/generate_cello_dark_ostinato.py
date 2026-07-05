from __future__ import annotations

import argparse
import sys
from pathlib import Path

from music21 import environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Позволяет запускать скрипт напрямую (python3 scripts/...), не устанавливая пакет.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_score  # noqa: E402
from core.export.exporter import ExportEngine  # noqa: E402
from core.presets.registry import get_preset, list_solo_presets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cello ostinato MusicXML and MIDI files.")
    parser.add_argument("--genre", choices=sorted(list_solo_presets()), default="dark_trip_hop")
    parser.add_argument("--output-name", default=None, help="File name without extension.")
    parser.add_argument("--list-genres", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    environment.Environment()["warnings"] = 0
    args = parse_args()

    if args.list_genres:
        for preset in [get_preset(n) for n in list_solo_presets()]:
            print(f"{preset.name}: {preset.feel}")
        return

    preset = get_preset(args.genre)
    output_name = args.output_name or f"cello_{preset.name}_ostinato"
    score = build_score(preset, seed=args.seed)
    musicxml_path, midi_path = ExportEngine().export(score, output_name)
    print(f"Genre: {preset.name} - {preset.feel}")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
