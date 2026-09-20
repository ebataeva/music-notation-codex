from __future__ import annotations

from pathlib import Path

from music21 import clef, instrument, key, meter, note, stream, tempo


def _make_minimal_score() -> stream.Score:
    score = stream.Score(id="test_score")
    part = stream.Part(id="cello")
    part.append(instrument.Violoncello())
    part.append(clef.BassClef())
    part.append(tempo.MetronomeMark(number=100))
    part.append(key.Key("C", "minor"))
    part.append(meter.TimeSignature("4/4"))
    measure = stream.Measure(number=1)
    measure.append(note.Note("C2", quarterLength=4.0))
    part.append(measure)
    score.insert(0, part)
    return score


def test_export_to_musicxml_writes_file_to_base_dir(tmp_path):
    from core.export.exporter import ExportEngine

    engine = ExportEngine(base_dir=tmp_path)
    score = _make_minimal_score()

    path = engine.export_to_musicxml(score, "sample")

    expected = tmp_path / "musicxml" / "sample.musicxml"
    assert path == expected
    assert expected.exists()


def test_export_to_midi_writes_file_to_base_dir(tmp_path):
    from core.export.exporter import ExportEngine

    engine = ExportEngine(base_dir=tmp_path)
    score = _make_minimal_score()

    path = engine.export_to_midi(score, "sample")

    expected = tmp_path / "midi" / "sample.mid"
    assert path == expected
    assert expected.exists()


def test_export_combined_returns_both_paths_and_writes_both_files(tmp_path):
    from core.export.exporter import ExportEngine

    engine = ExportEngine(base_dir=tmp_path)
    score = _make_minimal_score()

    musicxml_path, midi_path = engine.export(score, "sample")

    assert musicxml_path == tmp_path / "musicxml" / "sample.musicxml"
    assert midi_path == tmp_path / "midi" / "sample.mid"
    assert musicxml_path.exists()
    assert midi_path.exists()


def test_export_engine_defaults_base_dir_to_project_root_scores(monkeypatch):
    from core.export.exporter import ExportEngine

    # Drop the test-isolation override so the default path is exercised even
    # when the golden regression test left it set in the ambient environment.
    monkeypatch.delenv("MNC_SCORES_DIR", raising=False)
    engine = ExportEngine()
    # Compute the project root independently of the module under test
    # (tests/ sits one level below the root) so a parents[] miscount
    # in exporter.PROJECT_ROOT would be caught instead of restated.
    expected_root = Path(__file__).resolve().parents[1]
    assert engine.base_dir == expected_root / "scores"


def test_export_engine_honours_scores_dir_env_override(monkeypatch, tmp_path):
    from core.export.exporter import ExportEngine

    monkeypatch.setenv("MNC_SCORES_DIR", str(tmp_path))

    assert ExportEngine().base_dir == tmp_path


def test_export_engine_explicit_base_dir_beats_env_override(monkeypatch, tmp_path):
    from core.export.exporter import ExportEngine

    monkeypatch.setenv("MNC_SCORES_DIR", str(tmp_path))
    explicit = tmp_path / "explicit"

    assert ExportEngine(base_dir=explicit).base_dir == explicit


def test_export_engine_ignores_empty_scores_dir_env(monkeypatch):
    from core.export.exporter import ExportEngine

    # An empty value is treated as unset, not as "write to the cwd".
    monkeypatch.setenv("MNC_SCORES_DIR", "")

    expected_root = Path(__file__).resolve().parents[1]
    assert ExportEngine().base_dir == expected_root / "scores"
