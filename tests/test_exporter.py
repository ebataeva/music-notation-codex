from __future__ import annotations

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


def test_export_engine_defaults_base_dir_to_project_root_scores():
    from core.export.exporter import ExportEngine, PROJECT_ROOT

    engine = ExportEngine()
    assert engine.base_dir == PROJECT_ROOT / "scores"
