"""ExportEngine: writes music21 Scores to MusicXML/MIDI files.

Extracted from scripts/generate_cello_dark_ostinato.py's export_score()
(Phase 2 Plan 2). See 02-PATTERNS.md for the extraction map and D-08/D-09/D-10
decisions this class implements.
"""

from __future__ import annotations

from pathlib import Path

from music21 import stream

# core/export/exporter.py -> core/export -> core -> project root: parents[2]
# (NOT parents[1] as used in scripts/, which lives one directory shallower).
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ExportEngine:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (PROJECT_ROOT / "scores")

    def _safe_path(self, subdir: str, output_name: str, ext: str) -> Path:
        # WR-01: output_name must be a bare file name -- reject separators and
        # traversal components so writes can never escape base_dir.
        if Path(output_name).name != output_name or output_name in ("", ".", ".."):
            raise ValueError(f"output_name {output_name!r} must be a bare file name.")
        return self.base_dir / subdir / f"{output_name}{ext}"

    def export_to_musicxml(self, score: stream.Score, output_name: str) -> Path:
        musicxml_path = self._safe_path("musicxml", output_name, ".musicxml")
        musicxml_path.parent.mkdir(parents=True, exist_ok=True)
        score.write("musicxml", fp=str(musicxml_path))
        return musicxml_path

    def export_to_midi(self, score: stream.Score, output_name: str) -> Path:
        midi_path = self._safe_path("midi", output_name, ".mid")
        midi_path.parent.mkdir(parents=True, exist_ok=True)
        # WR-07: music21 exports MIDI natively; the manual open/write/close dance
        # leaked the file handle when write() raised.
        score.write("midi", fp=str(midi_path))
        return midi_path

    def export(self, score: stream.Score, output_name: str) -> tuple[Path, Path]:
        """Convenience method (D-09): writes both formats, returns (musicxml_path, midi_path)."""
        musicxml_path = self.export_to_musicxml(score, output_name)
        midi_path = self.export_to_midi(score, output_name)
        return musicxml_path, midi_path
