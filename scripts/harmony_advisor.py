from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Позволяет запускать скрипт напрямую (python3 scripts/...), не устанавливая пакет.
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
        print("Доступные жанры:")
        for genre in sorted(list_presets()):
            print(f"- {genre}")
        return

    preset = get_preset(args.genre)
    print(dedent(f"""
    Harmony advisor: {args.genre}
    Это не автокомпозитор, а карта вариантов: выбирай направление, затем меняй ноты/аккорды в генераторе.
    """).strip())
    print_section("Гармоническое развитие", preset.progressions)
    print_section("Модуляции", preset.modulations)
    print_section("Загадочность, драйв, секси-эффект", preset.mood_tips)


if __name__ == "__main__":
    main()
