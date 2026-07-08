from __future__ import annotations

import io

import numpy as np
import soundfile as sf
from music21 import clef, instrument, key, meter, note, stream, tempo

from app.services import generation


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
