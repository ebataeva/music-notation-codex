from __future__ import annotations

import sys
from pathlib import Path

from music21 import environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Позволяет запускать скрипт напрямую (python3 scripts/...), не устанавливая пакет.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_duet_score  # noqa: E402
from core.export.exporter import ExportEngine  # noqa: E402
from core.presets.registry import get_preset  # noqa: E402

OUTPUT_NAME = "simple_sexy_d_minor_violin_cello_loop"


def main() -> None:
    environment.Environment()["warnings"] = 0  # WR-04 fix -- in-memory only, no disk write
    preset = get_preset("simple_sexy_duet")
    score = build_duet_score(
        preset, tempo_bpm=preset.duet_tempo_bpm, cello_velocity=68, violin_velocity=58
    )
    musicxml_path, midi_path = ExportEngine().export(score, OUTPUT_NAME)
    print(f"Simple sexy duet loop: Dm9 <-> A7, {preset.duet_tempo_bpm} bpm, 8 bars, violin + cello")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
