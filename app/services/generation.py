"""GenerationService: orchestrates LoopEngine + TheoryExplainer for the UI layer.

This is the app-layer bridge between core/ and the NiceGUI UI. It calls
core/ functions and returns a JSON-serializable dict — no music21 objects
leak into the app layer (D-02).
"""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_progression_score, generate_variant_from_progression, generate_variants
from core.engine.progression import parse_progression
from core.models import LoopVariant
from core.presets.registry import get_preset, list_presets
from core.theory.explainer import explain

MAX_EXPLANATION_WORDS = 500
SOUNDFONT_PATH = "/opt/homebrew/Cellar/fluid-synth/2.5.5/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2"


def _truncate(text: str, max_words: int = MAX_EXPLANATION_WORDS) -> str:
    """SAFE-05: truncate explanation fields at max_words to prevent wall-of-text."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


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


def _midi_to_wav_pretty_midi(midi_bytes: bytes) -> bytes:
    """Render MIDI bytes to WAV via pretty_midi sine synthesis (no FluidSynth).

    This is a cloud-compatible fallback — the audio is basic sine waves
    but works anywhere (Streamlit Cloud, CI, etc.).
    """
    import io as _io

    import pretty_midi
    import soundfile as sf

    pm = pretty_midi.PrettyMIDI(_io.BytesIO(midi_bytes))
    audio = pm.synthesize(fs=44100)
    # soundfile wants float32; pretty_midi returns float64
    audio = audio.astype("float32")
    buf = _io.BytesIO()
    sf.write(buf, audio, 44100, format="WAV")
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

    Returns (wav_bytes, source) where source is 'fluidsynth' or 'pretty_midi'.
    """
    try:
        return _midi_to_wav_bytes(midi_bytes), "fluidsynth"
    except (FileNotFoundError, OSError):
        return _midi_to_wav_pretty_midi(midi_bytes), "pretty_midi"


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
    """Generate N distinct cello loop variants from the same chord progression.

    Returns a list of JSON-serializable dicts (same structure as generate_loop),
    one per variant. Each variant has a different register_bias for audible
    distinctness (Phase 7 LOOP-02).
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