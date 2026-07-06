"""Local audio analysis for uploaded or browser-recorded practice WAV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class AnalysisResult:
    pitch_hz: float | None
    pitch_stability: float | None
    tempo_bpm: float | None
    beat_stability: float | None
    intonation_notes: list[str]
    raw_duration_sec: float


def _load_mono(wav_path: str) -> tuple[np.ndarray, int]:
    audio, sample_rate = sf.read(wav_path, always_2d=False)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return np.asarray(audio, dtype=float), int(sample_rate)


def _duration(audio: np.ndarray, sample_rate: int) -> float:
    if sample_rate <= 0:
        return 0.0
    return float(len(audio) / sample_rate)


def _fundamental_from_fft(frame: np.ndarray, sample_rate: int) -> float | None:
    if len(frame) < 2 or not np.any(frame):
        return None

    windowed = frame * np.hanning(len(frame))
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), d=1 / sample_rate)
    valid = (freqs >= 65.0) & (freqs <= 1200.0)
    if not np.any(valid):
        return None

    valid_spectrum = spectrum[valid]
    if float(np.max(valid_spectrum)) <= 1e-9:
        return None
    return float(freqs[valid][int(np.argmax(valid_spectrum))])


def _fallback_pitch_track(audio: np.ndarray, sample_rate: int) -> list[float]:
    frame_size = max(1024, int(sample_rate * 0.08))
    hop = max(512, frame_size // 2)
    pitches: list[float] = []
    for start in range(0, max(1, len(audio) - frame_size + 1), hop):
        frame = audio[start : start + frame_size]
        if float(np.sqrt(np.mean(frame**2))) < 0.005:
            continue
        pitch = _fundamental_from_fft(frame, sample_rate)
        if pitch is not None:
            pitches.append(pitch)
    return pitches


def _librosa_pitch_track(audio: np.ndarray, sample_rate: int) -> list[float] | None:
    try:
        import librosa
    except Exception:
        return None

    try:
        pitches = librosa.yin(audio, fmin=65.0, fmax=1200.0, sr=sample_rate)
    except Exception:
        return None

    clean = [float(pitch) for pitch in pitches if np.isfinite(pitch) and 65.0 <= pitch <= 1200.0]
    return clean or None


def _stability(values: list[float]) -> float | None:
    if not values:
        return None
    arr = np.asarray(values, dtype=float)
    median = float(np.median(arr))
    if median <= 0:
        return None
    cents = 1200.0 * np.log2(arr / median)
    spread = float(np.std(cents))
    return max(0.0, min(1.0, 1.0 - spread / 60.0))


def _intonation_notes(avg_pitch: float | None, stability: float | None) -> list[str]:
    notes: list[str] = []
    if avg_pitch is None:
        return ["No stable pitch detected. Try recording a clear sustained cello note."]
    if stability is not None and stability >= 0.85:
        notes.append("Your pitch is stable — good intonation control.")
    elif stability is not None and stability < 0.55:
        notes.append("The pitch wavers noticeably. Try a slower bow and one sustained note at a time.")
    if avg_pitch > 220.0 and stability is not None and stability < 0.75:
        notes.append("Higher notes sound less settled. Relax the left hand before shifting up.")
    return notes


def analyze_pitch(wav_path: str) -> dict:
    audio, sample_rate = _load_mono(wav_path)
    if len(audio) == 0:
        return {"pitch_hz": None, "pitch_stability": None, "intonation_notes": ["Recording is empty."]}

    pitches = _librosa_pitch_track(audio, sample_rate) or _fallback_pitch_track(audio, sample_rate)
    avg_pitch = float(np.mean(pitches)) if pitches else None
    stability = _stability(pitches)
    return {
        "pitch_hz": avg_pitch,
        "pitch_stability": stability,
        "intonation_notes": _intonation_notes(avg_pitch, stability),
    }


def _fallback_onsets(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    frame_size = max(256, int(sample_rate * 0.02))
    hop = frame_size
    energies = []
    for start in range(0, max(1, len(audio) - frame_size + 1), hop):
        frame = audio[start : start + frame_size]
        energies.append(float(np.sqrt(np.mean(frame**2))))
    if len(energies) < 3:
        return np.asarray([], dtype=float)

    arr = np.asarray(energies)
    threshold = float(np.mean(arr) + np.std(arr))
    peaks = []
    for i in range(1, len(arr) - 1):
        if arr[i] >= threshold and arr[i] > arr[i - 1] and arr[i] >= arr[i + 1]:
            peaks.append(i * hop / sample_rate)
    return np.asarray(peaks, dtype=float)


def _tempo_from_onsets(onsets: np.ndarray) -> tuple[float | None, float | None]:
    if len(onsets) < 2:
        return None, None
    intervals = np.diff(onsets)
    intervals = intervals[(intervals > 0.2) & (intervals < 2.0)]
    if len(intervals) == 0:
        return None, None
    median_interval = float(np.median(intervals))
    bpm = 60.0 / median_interval
    spread = float(np.std(intervals) / median_interval) if median_interval else 1.0
    stability = max(0.0, min(1.0, 1.0 - spread))
    return bpm, stability


def _librosa_tempo(audio: np.ndarray, sample_rate: int) -> tuple[float | None, float | None] | None:
    try:
        import librosa
    except Exception:
        return None

    try:
        tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=sample_rate)
        beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
    except Exception:
        return None

    tempo_value = float(np.asarray(tempo).reshape(-1)[0]) if np.asarray(tempo).size else None
    _, stability = _tempo_from_onsets(np.asarray(beat_times, dtype=float))
    return tempo_value, stability


def analyze_tempo(wav_path: str) -> dict:
    audio, sample_rate = _load_mono(wav_path)
    if len(audio) == 0:
        return {"tempo_bpm": None, "beat_stability": None}

    tempo = _librosa_tempo(audio, sample_rate)
    if tempo is None:
        tempo = _tempo_from_onsets(_fallback_onsets(audio, sample_rate))

    tempo_bpm, beat_stability = tempo
    return {"tempo_bpm": tempo_bpm, "beat_stability": beat_stability}


def analyze_playing(wav_path: str) -> AnalysisResult:
    path = Path(wav_path)
    if not path.exists():
        raise FileNotFoundError(wav_path)

    audio, sample_rate = _load_mono(wav_path)
    pitch = analyze_pitch(wav_path)
    tempo = analyze_tempo(wav_path)
    return AnalysisResult(
        pitch_hz=pitch["pitch_hz"],
        pitch_stability=pitch["pitch_stability"],
        tempo_bpm=tempo["tempo_bpm"],
        beat_stability=tempo["beat_stability"],
        intonation_notes=list(pitch["intonation_notes"]),
        raw_duration_sec=_duration(audio, sample_rate),
    )
