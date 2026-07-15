"""GenerationService: orchestrates LoopEngine + TheoryExplainer for the UI layer.

This is the app-layer bridge between core/ and the NiceGUI UI. It calls
core/ functions and returns a JSON-serializable dict — no music21 objects
leak into the app layer (D-02).
"""

from __future__ import annotations

import base64
import copy
import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import (
    build_duet_score,
    build_progression_score,
    generate_variant_from_progression,
    generate_variants,
)
from core.engine.progression import parse_progression
from core.models import LoopVariant
from core.presets.registry import get_preset, list_presets
from core.theory.explainer import explain

MAX_EXPLANATION_WORDS = 500
SOUNDFONT_PATH = "/opt/homebrew/Cellar/fluid-synth/2.5.5/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2"
DUET_VELOCITIES = {
    "sexy_duet": (82, 70),
    "simple_sexy_duet": (68, 58),
    "dorian_sexy_duet": (74, 62),
}
DUET_SHOWCASE_TRANSPOSE = {
    "sexy_duet": "P8",
    "simple_sexy_duet": "P8",
    "dorian_sexy_duet": "P8",
}


def _truncate(text: str, max_words: int = MAX_EXPLANATION_WORDS) -> str:
    """SAFE-05: truncate explanation fields at max_words to prevent wall-of-text."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def _prepare_duet_showcase_score(score, preset_name: str):
    """Make authored duet material clearer for a live demo without changing source presets."""
    from music21 import key

    transpose_interval = DUET_SHOWCASE_TRANSPOSE.get(preset_name)
    if transpose_interval:
        score = score.transpose(transpose_interval)

    if preset_name == "dorian_sexy_duet":
        for part in score.parts:
            for key_obj in list(part.getElementsByClass(key.Key)):
                part.replace(key_obj, key.KeySignature(0))

    return score


def _duet_showcase_copy(preset_name: str, preset) -> dict:
    if preset_name == "dorian_sexy_duet":
        return {
            "why_it_works": (
                "Dorian color, not generic minor: the loop is Dm9 <-> G9. "
                "Listen for B natural: it is the warm 6th that keeps the phrase from sounding funeral-dark."
            ),
            "how_to_start": (
                "Think in two-bar blocks. Bars 1-2 state the cell: cello pulses D/G, "
                "violin sings A-B-C-B-A, then answers downward."
            ),
            "how_to_develop": (
                "Bars 3-4 repeat the idea with a small lift. Bars 5-6 vary the contour. "
                "Bars 7-8 return home, so the loop is easy to hear and rehearse."
            ),
            "how_to_end": (
                "End by letting the violin release first, then let the cello land quietly on D."
            ),
            "how_to_transition": (
                "For another pass, keep the last cello pulse soft and let the violin re-enter on A."
            ),
            "phrase_map": [
                "Bars 1-2: statement",
                "Bars 3-4: answer",
                "Bars 5-6: variation",
                "Bars 7-8: return",
            ],
            "notation_note": "No key signature is shown for the Dorian showcase, so the B natural reads as part of the mode rather than a page full of natural signs.",
        }

    return {
        "why_it_works": f"{preset.feel}. {preset.progressions[0] if preset.progressions else ''}".strip(),
        "how_to_start": "Cello sets the pulse first; violin enters as a close answer above it.",
        "how_to_develop": "Hear it in short call-and-response chunks instead of one long melody.",
        "how_to_end": "Let the violin soften first, then let the cello close the loop.",
        "how_to_transition": "Repeat the last cello pulse quietly and bring the violin back by step.",
        "phrase_map": ["Bars 1-2: statement", "Bars 3-4: answer", "Bars 5-6: variation"],
        "notation_note": "The duet is transposed up an octave in the showcase so the parts speak more clearly.",
    }


def _score_to_musicxml_string(score) -> str:
    """Export a music21 Score to MusicXML string (for OSMD rendering)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".musicxml", mode="r", delete=False) as f:
        path = f.name
    score.write("musicxml", fp=path)
    with open(path, "r", encoding="utf-8") as f:
        result = f.read()
    Path(path).unlink(missing_ok=True)
    return result


def _score_to_midi_bytes(score) -> bytes:
    """Export a music21 Score to MIDI bytes."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        path = f.name
    score.write("midi", fp=path)
    with open(path, "rb") as f:
        result = f.read()
    Path(path).unlink(missing_ok=True)
    return result


def _part_to_midi_bytes(score, part_name: str) -> bytes:
    """Export one named duet part as a standalone MIDI loop."""
    from music21 import stream

    matching_parts = [
        part for part in score.parts
        if part_name.lower() in (part.partName or part.id or "").lower()
    ]
    if not matching_parts:
        raise ValueError(f"Duet part not found: {part_name}")

    isolated_score = stream.Score(id=f"{part_name.lower()}_loop")
    isolated_score.insert(0, copy.deepcopy(matching_parts[0]))
    return _score_to_midi_bytes(isolated_score)


def _midi_to_wav_pretty_midi(midi_bytes: bytes) -> bytes:
    """Render MIDI bytes to WAV via a small cello-like synth with reverb.

    This is a cloud-compatible fallback for Streamlit Cloud when FluidSynth or
    the local soundfont is unavailable.
    """
    import io as _io

    import numpy as np
    import pretty_midi
    import soundfile as sf

    sample_rate = 44100
    pm = pretty_midi.PrettyMIDI(_io.BytesIO(midi_bytes))

    end_time = max((instrument.get_end_time() for instrument in pm.instruments), default=0.0)
    total_samples = max(int((end_time + 1.8) * sample_rate), sample_rate)
    audio = np.zeros(total_samples, dtype=np.float64)

    for instrument in pm.instruments:
        if instrument.is_drum:
            continue
        for midi_note in instrument.notes:
            start = max(int(midi_note.start * sample_rate), 0)
            end = min(int((midi_note.end + 0.35) * sample_rate), total_samples)
            if end <= start:
                continue

            note_samples = end - start
            t = np.arange(note_samples, dtype=np.float64) / sample_rate
            duration = max(midi_note.end - midi_note.start, 0.05)
            release_start = min(int(duration * sample_rate), note_samples)

            frequency = pretty_midi.note_number_to_hz(midi_note.pitch)
            vibrato = 1.0 + 0.0035 * np.sin(2.0 * np.pi * 5.2 * t)
            phase_base = 2.0 * np.pi * frequency * vibrato * t

            tone = (
                0.82 * np.sin(phase_base)
                + 0.34 * np.sin(2.0 * phase_base + 0.4)
                + 0.18 * np.sin(3.0 * phase_base + 0.9)
                + 0.08 * np.sin(4.0 * phase_base + 1.2)
            )

            # Gentle bow noise gives the fallback less of a pure-organ/sine quality.
            bow_noise = np.random.default_rng(midi_note.pitch + start).normal(0.0, 0.006, note_samples)
            tone = tone + bow_noise

            attack = max(int(0.055 * sample_rate), 1)
            release = max(int(0.22 * sample_rate), 1)
            envelope = np.ones(note_samples, dtype=np.float64)
            envelope[: min(attack, note_samples)] = np.linspace(0.0, 1.0, min(attack, note_samples))
            if release_start < note_samples:
                release_len = note_samples - release_start
                envelope[release_start:] *= np.linspace(1.0, 0.0, release_len)
            elif note_samples > release:
                envelope[-release:] *= np.linspace(1.0, 0.0, release)

            amplitude = 0.22 * (midi_note.velocity / 127.0)
            audio[start:end] += tone * envelope * amplitude

    # Roll off harsh upper partials so the harmonic stack behaves more like a bowed string.
    if np.any(audio):
        kernel_size = 9
        audio = np.convolve(audio, np.ones(kernel_size) / kernel_size, mode="same")

        delay_times = (0.029, 0.037, 0.053, 0.071)
        reverb = np.zeros_like(audio)
        for i, delay_time in enumerate(delay_times):
            delay = int(delay_time * sample_rate)
            gain = 0.22 / (i + 1)
            reverb[delay:] += audio[:-delay] * gain

        tail = np.zeros_like(audio)
        feedback = 0.62
        block = max(int(0.011 * sample_rate), 1)
        for start in range(0, len(reverb), block):
            end = min(start + block, len(reverb))
            previous = tail[start - block:end - block] if start >= block else 0.0
            tail[start:end] = reverb[start:end] + feedback * previous
        tail *= 0.18
        audio = audio + tail

        peak = float(np.max(np.abs(audio)))
        if peak > 0:
            audio = audio / peak * 0.88

    audio = audio.astype("float32")
    buf = _io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV")
    buf.seek(0)
    return buf.read()


def _midi_to_wav_bytes(midi_bytes: bytes) -> bytes:
    """Render MIDI bytes to WAV via FluidSynth CLI (SAFE-03: 30s timeout)."""
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as midi_file:
        midi_file.write(midi_bytes)
        midi_path = midi_file.name

    wav_path = midi_path.replace(".mid", ".wav")
    try:
        subprocess.run(
            ["fluidsynth", "-a", "file", "-F", wav_path, SOUNDFONT_PATH, midi_path],
            capture_output=True,
            timeout=30,
            check=True,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        Path(midi_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)


def _render_wav(midi_bytes: bytes) -> tuple[bytes, str]:
    """Try FluidSynth first, then fall back to pretty_midi.

    Returns (wav_bytes, source) where source is 'fluidsynth' or 'cello_synth_reverb'.
    """
    try:
        return _midi_to_wav_bytes(midi_bytes), "fluidsynth"
    except (FileNotFoundError, OSError):
        return _midi_to_wav_pretty_midi(midi_bytes), "cello_synth_reverb"


def _soundfont_exists() -> bool:
    return Path(SOUNDFONT_PATH).exists()


def sound_font_path() -> str:
    return SOUNDFONT_PATH


def generate_loop(
    chord_progression: str,
    preset_name: str,
    seed: int | None = None,
    include_audio: bool = False,
) -> dict:
    """Generate a cello loop from chord text + mood preset.

    Returns a JSON-serializable dict with:
    - theory explanation fields (truncated per SAFE-05)
    - musicxml_string (for OSMD notation rendering)
    - midi_bytes_b64 (base64-encoded MIDI for audio playback)
    - wav_bytes_b64 (base64-encoded WAV, only if include_audio=True)
    - seed used
    - error message if generation failed
    """
    try:
        chords = parse_progression(chord_progression)
    except ValueError as exc:
        return {"error": f"Chord parsing failed: {exc}"}

    if not chords:
        return {"error": "Progression must contain at least one chord."}

    try:
        preset = get_preset(preset_name)
    except KeyError:
        return {"error": f"Unknown mood preset: {preset_name!r}"}

    try:
        variant: LoopVariant = generate_variant_from_progression(
            chords, preset, seed=seed
        )
    except ValueError as exc:
        return {"error": f"Generation failed: {exc}"}

    explanation = explain(variant, preset)

    # Build the score again for MusicXML/MIDI export (the variant doesn't carry it)
    score = build_progression_score(chords, preset, seed=variant.trace.seed)
    musicxml_str = _score_to_musicxml_string(score)
    midi_bytes = _score_to_midi_bytes(score)

    result = {
        "why_it_works": _truncate(explanation.why_it_works),
        "how_to_start": _truncate(explanation.how_to_start),
        "how_to_develop": _truncate(explanation.how_to_develop),
        "how_to_end": _truncate(explanation.how_to_end),
        "how_to_transition": _truncate(explanation.how_to_transition),
        "musicxml_string": musicxml_str,
        "midi_bytes_b64": base64.b64encode(midi_bytes).decode("ascii"),
        "wav_bytes_b64": "",
        "seed": variant.trace.seed if variant.trace else None,
        "preset_name": preset_name,
        "chord_progression": chord_progression,
        "error": None,
    }

    if include_audio:
        try:
            wav_bytes, source = _render_wav(midi_bytes)
            result["wav_bytes_b64"] = base64.b64encode(wav_bytes).decode("ascii")
            result["audio_source"] = source
        except Exception as exc:
            result["audio_error"] = f"Audio render failed: {exc}"

    return result


def available_presets() -> list[str]:
    """Return sorted list of mood preset names for the dropdown."""
    return list_presets()


def generate_loop_variants(
    chord_progression: str,
    preset_name: str,
    seed: int | None = None,
    include_audio: bool = False,
    count: int = 3,
) -> list[dict]:
    """Generate N distinct loop variants from the same chord progression.

    Returns a list of JSON-serializable dicts (same structure as generate_loop),
    one per variant. Solo presets return three cello takes. Duet presets return
    one two-part violin+cello showcase because their authored material already
    contains fixed interlocking parts.
    """
    try:
        chords = parse_progression(chord_progression)
    except ValueError as exc:
        return [{"error": f"Chord parsing failed: {exc}"}]

    if not chords:
        return [{"error": "Progression must contain at least one chord."}]

    try:
        preset = get_preset(preset_name)
    except KeyError:
        return [{"error": f"Unknown mood preset: {preset_name!r}"}]

    if preset.duet_bars is not None:
        try:
            cello_velocity, violin_velocity = DUET_VELOCITIES.get(
                preset.name, (preset.velocity, max(preset.velocity - 12, 48))
            )
            score = build_duet_score(
                preset,
                tempo_bpm=preset.duet_tempo_bpm or preset.tempo_bpm,
                cello_velocity=cello_velocity,
                violin_velocity=violin_velocity,
            )
            score = _prepare_duet_showcase_score(score, preset.name)
        except ValueError as exc:
            return [{"error": f"Generation failed: {exc}"}]

        musicxml_str = _score_to_musicxml_string(score)
        midi_bytes = _score_to_midi_bytes(score)

        copy = _duet_showcase_copy(preset.name, preset)
        result = {
            "variant_index": 0,
            "variant_label": "Violin + cello duet",
            "register_bias": "duet",
            "ensemble": "violin_cello",
            "is_duet": True,
            "instruments": ["violin", "cello"],
            "why_it_works": _truncate(copy["why_it_works"]),
            "how_to_start": _truncate(copy["how_to_start"]),
            "how_to_develop": _truncate(copy["how_to_develop"]),
            "how_to_end": _truncate(copy["how_to_end"]),
            "how_to_transition": _truncate(copy["how_to_transition"]),
            "phrase_map": copy["phrase_map"],
            "notation_note": copy["notation_note"],
            "musicxml_string": musicxml_str,
            "midi_bytes_b64": base64.b64encode(midi_bytes).decode("ascii"),
            "wav_bytes_b64": "",
            "seed": seed,
            "preset_name": preset_name,
            "chord_progression": chord_progression,
            "error": None,
        }

        if include_audio:
            try:
                wav_bytes, source = _render_wav(midi_bytes)
                result["wav_bytes_b64"] = base64.b64encode(wav_bytes).decode("ascii")
                result["audio_source"] = source
                for part_name in ("violin", "cello"):
                    part_midi = _part_to_midi_bytes(score, part_name)
                    part_wav, part_source = _render_wav(part_midi)
                    result[f"{part_name}_wav_bytes_b64"] = base64.b64encode(part_wav).decode("ascii")
                    result[f"{part_name}_audio_source"] = part_source
            except Exception as exc:
                result["audio_error"] = f"Audio render failed: {exc}"

        return [result]

    try:
        variants = generate_variants(chords, preset, seed=seed, count=count)
    except ValueError as exc:
        return [{"error": f"Generation failed: {exc}"}]

    results: list[dict] = []
    for i, variant in enumerate(variants):
        explanation = explain(variant, preset)

        bias = variant.trace.register_bias or "default"
        score = build_progression_score(
            chords, preset, seed=variant.trace.seed, register_bias=bias
        )
        musicxml_str = _score_to_musicxml_string(score)
        midi_bytes = _score_to_midi_bytes(score)

        result = {
            "variant_index": i,
            "variant_label": f"Variant {i + 1} ({bias} register)",
            "register_bias": bias,
            "why_it_works": _truncate(explanation.why_it_works),
            "how_to_start": _truncate(explanation.how_to_start),
            "how_to_develop": _truncate(explanation.how_to_develop),
            "how_to_end": _truncate(explanation.how_to_end),
            "how_to_transition": _truncate(explanation.how_to_transition),
            "musicxml_string": musicxml_str,
            "midi_bytes_b64": base64.b64encode(midi_bytes).decode("ascii"),
            "wav_bytes_b64": "",
            "seed": variant.trace.seed,
            "preset_name": preset_name,
            "chord_progression": chord_progression,
            "error": None,
        }

        if include_audio:
            try:
                wav_bytes, source = _render_wav(midi_bytes)
                result["wav_bytes_b64"] = base64.b64encode(wav_bytes).decode("ascii")
                result["audio_source"] = source
            except Exception as exc:
                result["audio_error"] = f"Audio render failed: {exc}"

        results.append(result)

    return results
