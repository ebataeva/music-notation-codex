from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Allows running the script directly (python3 scripts/...) without installing the package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.models import GenerationTrace, LoopVariant  # noqa: E402
from core.engine.loop_engine import generate_variant  # noqa: E402
from core.presets.registry import get_preset, list_presets  # noqa: E402
from core.theory import explain  # noqa: E402


def print_section(title: str, items: list[str]) -> None:
    print()
    print(title)
    print("-" * len(title))
    for item in items:
        print(f"- {item}")


def variant_for_advice(genre: str, seed: int | None = None) -> LoopVariant:
    preset = get_preset(genre)
    try:
        return generate_variant(preset, seed=seed)
    except ValueError:
        if preset.duet_bars is None:
            raise
        cello_bars = preset.duet_bars["cello"]
        trace = GenerationTrace(
            seed=seed,
            pattern_strategy="preset_verbatim",
            register_choices=["low register"] * len(cello_bars),
            voice_leading_steps=None,
            chord_tones_used=[list(bar) for bar in cello_bars],
        )
        return LoopVariant(
            id=f"{preset.name}-advice",
            preset_name=preset.name,
            label=preset.feel or preset.name,
            musicxml_path=None,
            midi_path=None,
            svg_bytes=None,
            midi_bytes=None,
            theory_explanation=None,
            trace=trace,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Suggest harmonic development, modulation, and mood ideas.")
    parser.add_argument("--genre", choices=sorted(list_presets()), default="dark_trip_hop")
    parser.add_argument("--seed", type=int, default=None, help="Reproducible generation seed.")
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
    explanation = explain(variant_for_advice(args.genre, seed=args.seed), preset)
    print(dedent(f"""
    Harmony advisor: {args.genre}
    This is not an auto-composer but a map of options: pick a direction, then change the notes/chords in the generator.
    """).strip())
    print_section("Why it works", [explanation.why_it_works])
    print_section("How to start", [explanation.how_to_start])
    print_section("How to develop", [explanation.how_to_develop])
    print_section("How to end", [explanation.how_to_end])
    print_section("How to transition", [explanation.how_to_transition])


if __name__ == "__main__":
    main()
