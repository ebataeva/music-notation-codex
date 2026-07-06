from __future__ import annotations

import numpy as np
import soundfile as sf

from core.analysis.analyzer import AnalysisResult, analyze_pitch, analyze_playing, analyze_tempo


def _write_wav(path, audio: np.ndarray, sample_rate: int = 22050) -> None:
    sf.write(path, audio, sample_rate)


def test_analyze_pitch_detects_sustained_note(tmp_path):
    sample_rate = 22050
    t = np.linspace(0, 1.0, sample_rate, endpoint=False)
    audio = 0.4 * np.sin(2 * np.pi * 220.0 * t)
    wav_path = tmp_path / "a3.wav"
    _write_wav(wav_path, audio, sample_rate)

    result = analyze_pitch(str(wav_path))

    assert result["pitch_hz"] is not None
    assert 210.0 <= result["pitch_hz"] <= 230.0
    assert result["pitch_stability"] is not None
    assert result["pitch_stability"] > 0.7


def test_analyze_tempo_detects_regular_pulse(tmp_path):
    sample_rate = 22050
    audio = np.zeros(sample_rate * 4)
    for beat in range(8):
        start = int(beat * 0.5 * sample_rate)
        audio[start : start + 400] = np.hanning(400)
    wav_path = tmp_path / "pulse.wav"
    _write_wav(wav_path, audio, sample_rate)

    result = analyze_tempo(str(wav_path))

    assert result["tempo_bpm"] is not None
    assert 110.0 <= result["tempo_bpm"] <= 130.0
    assert result["beat_stability"] is not None
    assert result["beat_stability"] > 0.9


def test_analyze_playing_returns_combined_dataclass(tmp_path):
    sample_rate = 22050
    t = np.linspace(0, 1.0, sample_rate, endpoint=False)
    audio = 0.4 * np.sin(2 * np.pi * 146.83 * t)
    wav_path = tmp_path / "d3.wav"
    _write_wav(wav_path, audio, sample_rate)

    result = analyze_playing(str(wav_path))

    assert isinstance(result, AnalysisResult)
    assert result.raw_duration_sec > 0.9
    assert result.pitch_hz is not None
