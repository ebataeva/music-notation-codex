"""ExportEngine: writes music21 Scores to MusicXML/MIDI files.

Extracted from scripts/generate_cello_dark_ostinato.py's export_score()
(Phase 2 Plan 2). See 02-PATTERNS.md for the extraction map and D-08/D-09/D-10
decisions this class implements.
"""

from __future__ import annotations

from pathlib import Path

from music21 import midi
from music21 import stream

# core/export/exporter.py -> core/export -> core -> project root: parents[2]
# (NOT parents[1] as used in scripts/, which lives one directory shallower).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ExportEngine:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (PROJECT_ROOT / "scores")

    def export_to_musicxml(self, score: stream.Score, output_name: str) -> Path:
        musicxml_path = self.base_dir / "musicxml" / f"{output_name}.musicxml"
        musicxml_path.parent.mkdir(parents=True, exist_ok=True)
        score.write("musicxml", fp=str(musicxml_path))
        return musicxml_path

    def export_to_midi(self, score: stream.Score, output_name: str) -> Path:
        midi_path = self.base_dir / "midi" / f"{output_name}.mid"
        midi_path.parent.mkdir(parents=True, exist_ok=True)
        midi_file = midi.translate.streamToMidiFile(score)
        midi_file.open(str(midi_path), "wb")
        midi_file.write()
        midi_file.close()
        return midi_path

    def export(self, score: stream.Score, output_name: str) -> tuple[Path, Path]:
        """Convenience method (D-09): writes both formats, returns (musicxml_path, midi_path)."""
        musicxml_path = self.export_to_musicxml(score, output_name)
        midi_path = self.export_to_midi(score, output_name)
        return musicxml_path, midi_path
