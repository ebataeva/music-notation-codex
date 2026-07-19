from __future__ import annotations

import io
import base64

import numpy as np
import soundfile as sf
from music21 import clef, instrument, key, meter, note, stream, tempo

from app.services import generation
from core.engine.loop_engine import build_duet_score
from core.presets.mood_presets import MOOD_PRESETS
from core.presets.registry import get_preset


def _minimal_midi_bytes() -> bytes:
    score = stream.Score(id="audio_test")
    part = stream.Part(id="cello")
    part.append(instrument.Violoncello())
    part.append(clef.BassClef())
    part.append(tempo.MetronomeMark(number=72))
    part.append(key.Key("A", "minor"))
    part.append(meter.TimeSignature("4/4"))
    measure = stream.Measure(number=1)
    measure.append(note.Note("A2", quarterLength=1.0))
    measure.append(note.Note("E3", quarterLength=1.0))
    measure.append(note.Note("C3", quarterLength=2.0))
    part.append(measure)
    score.insert(0, part)
    return generation._score_to_midi_bytes(score)


def test_cello_synth_reverb_fallback_returns_valid_non_silent_wav() -> None:
    midi_bytes = _minimal_midi_bytes()

    wav_bytes = generation._midi_to_wav_pretty_midi(midi_bytes)
    audio, sample_rate = sf.read(io.BytesIO(wav_bytes), dtype="float32")

    assert wav_bytes
    assert sample_rate == 44100
    assert audio.size > 0
    assert np.max(np.abs(audio)) > 0.01
    assert np.max(np.abs(audio)) <= 1.0
    assert 4.0 <= len(audio) / sample_rate <= 7.0


def test_render_wav_reports_cello_synth_reverb_when_fluidsynth_unavailable(monkeypatch) -> None:
    midi_bytes = _minimal_midi_bytes()

    def raise_missing(_midi_bytes: bytes) -> bytes:
        raise FileNotFoundError("fluidsynth")

    monkeypatch.setattr(generation, "_midi_to_wav_bytes", raise_missing)

    wav_bytes, source = generation._render_wav(midi_bytes)
    audio, _sample_rate = sf.read(io.BytesIO(wav_bytes), dtype="float32")

    assert source == "cello_synth_reverb"
    assert audio.size > 0


def test_generate_loop_audio_source_uses_cello_synth_reverb_on_fallback(monkeypatch) -> None:
    def raise_missing(_midi_bytes: bytes) -> bytes:
        raise FileNotFoundError("fluidsynth")

    monkeypatch.setattr(generation, "_midi_to_wav_bytes", raise_missing)

    result = generation.generate_loop("Am Dm F E", "noir_slow_burn", seed=7, include_audio=True)

    assert result["error"] is None
    assert result["audio_source"] == "cello_synth_reverb"
    assert result["wav_bytes_b64"]


def test_available_presets_returns_all_showcase_presets() -> None:
    assert generation.available_presets() == sorted(MOOD_PRESETS)


def test_streamlit_mood_label_keeps_raw_preset_id_visible() -> None:
    from apps.ear_check_streamlit import _mood_label

    label = _mood_label("dorian_sexy_duet")

    assert label.startswith("dorian_sexy_duet ·")
    assert "Violin + cello Dorian duet" in label


def test_duet_preset_generates_violin_cello_musicxml_and_midi() -> None:
    results = generation.generate_loop_variants(
        "Dm9 G9 Dm9 G9 Bbmaj7 A7 Dm9 A7",
        "dorian_sexy_duet",
        seed=0,
        include_audio=False,
    )

    assert len(results) == 1
    result = results[0]
    assert result["error"] is None
    assert result["is_duet"] is True
    assert result["ensemble"] == "violin_cello"
    assert result["instruments"] == ["violin", "cello"]
    assert "Violin" in result["musicxml_string"]
    assert "Violoncello" in result["musicxml_string"]
    assert result["phrase_map"] == [
        "Bars 1-2: statement",
        "Bars 3-4: answer",
        "Bars 5-6: variation",
        "Bars 7-8: return",
    ]
    assert "<alter>0</alter>" not in result["musicxml_string"]
    assert base64.b64decode(result["midi_bytes_b64"])


def test_theory_analyzes_entered_duet_progression_instead_of_static_vamp() -> None:
    result = generation.analyze_progression("Dm9 Eb", "dorian_sexy_duet")[0]

    assert result["error"] is None
    assert result["variant_label"] == "Harmony analysis: Dm9 Eb"
    assert "Dm9 (D, F, A, C, E)" in result["why_it_works"]
    assert "Eb (Eb, G, Bb)" in result["why_it_works"]
    assert "flat-II" in result["why_it_works"]
    assert "loop is Dm9 <-> G9" not in result["why_it_works"]


def test_dorian_showcase_keeps_violin_in_readable_written_register() -> None:
    preset = get_preset("dorian_sexy_duet")
    score = build_duet_score(
        preset,
        tempo_bpm=preset.duet_tempo_bpm,
        cello_velocity=74,
        violin_velocity=62,
    )

    prepared = generation._prepare_duet_showcase_score(score, preset.name)
    violin = next(part for part in prepared.parts if part.id == "violin")
    written_midis = [item.pitch.midi for item in violin.recurse().notes]

    assert max(written_midis) <= note.Note("C5").pitch.midi


def test_duet_audio_contains_full_violin_and_cello_rehearsal_loops(monkeypatch) -> None:
    rendered_midis: list[bytes] = []

    def render_stub(midi_bytes: bytes) -> tuple[bytes, str]:
        rendered_midis.append(midi_bytes)
        return b"test-wav", "test-renderer"

    monkeypatch.setattr(generation, "_render_wav", render_stub)

    result = generation.generate_loop_variants(
        "Dm9 G9 Dm9 G9 Bbmaj7 A7 Dm9 A7",
        "dorian_sexy_duet",
        seed=0,
        include_audio=True,
    )[0]

    assert result["error"] is None
    assert len(rendered_midis) == 3
    assert len(set(rendered_midis)) == 3
    assert base64.b64decode(result["wav_bytes_b64"]) == b"test-wav"
    assert base64.b64decode(result["violin_wav_bytes_b64"]) == b"test-wav"
    assert base64.b64decode(result["cello_wav_bytes_b64"]) == b"test-wav"
    assert result["audio_source"] == "test-renderer"
    assert result["violin_audio_source"] == "test-renderer"
    assert result["cello_audio_source"] == "test-renderer"


def test_solo_preset_still_generates_three_variants() -> None:
    results = generation.generate_loop_variants(
        "Am F C G",
        "dark_trip_hop",
        seed=0,
        include_audio=False,
        count=3,
    )

    assert len(results) == 3
    assert all(result["error"] is None for result in results)
    assert [result["register_bias"] for result in results] == ["low", "default", "high"]


def test_unknown_preset_error_remains_readable() -> None:
    results = generation.generate_loop_variants("Am F C G", "missing_preset", seed=0)

    assert results == [{"error": "Unknown mood preset: 'missing_preset'"}]
