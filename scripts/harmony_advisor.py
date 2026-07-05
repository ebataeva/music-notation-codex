from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Allows running the script directly (python3 scripts/...) without installing the package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.presets.registry import get_preset, list_presets  # noqa: E402


def print_section(title: str, items: list[str]) -> None:
    print()
    print(title)
    print("-" * len(title))
    for item in items:
        print(f"- {item}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Suggest harmonic development, modulation, and mood ideas.")
    parser.add_argument("--genre", choices=sorted(list_presets()), default="dark_trip_hop")
    parser.add_argument("--list-genres", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_genres:
        print("Available genres:")
        for genre in sorted(list_presets()):
            print(f"- {genre}")
        return

    preset = get_preset(args.genre)
    print(dedent(f"""
    Harmony advisor: {args.genre}
    This is not an auto-composer but a map of options: pick a direction, then change the notes/chords in the generator.
    """).strip())
    print_section("Harmonic development", preset.progressions)
    print_section("Modulations", preset.modulations)
    print_section("Mystery, drive, sexy effect", preset.mood_tips)


if __name__ == "__main__":
    main()
