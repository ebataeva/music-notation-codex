from __future__ import annotations

import base64
import copy
from dataclasses import asdict
from functools import lru_cache

from app.services.generation import _render_wav, _score_to_midi_bytes, _score_to_musicxml_string
from core.theory.dictionary import ENTRIES, build_dictionary_example
from core.theory.transitions import normalize_context, transition_guides


def dictionary_entries() -> list[dict]:
    return [asdict(entry) for entry in ENTRIES]


@lru_cache(maxsize=192)
def _example_assets(term: str, tonic: str, mode: str, preset_name: str) -> dict:
    example = build_dictionary_example(term, tonic, mode, preset_name)
    midi = _score_to_midi_bytes(example.score)
    result = {
        **asdict(example.entry),
        "tonic": tonic,
        "mode": mode,
        "caption": example.caption,
        "musicxml_string": _score_to_musicxml_string(example.score),
        "midi_bytes_b64": base64.b64encode(midi).decode("ascii"),
        "guide": asdict(example.guide) if example.guide else None,
    }
    return result


@lru_cache(maxsize=64)
def _example_audio(term: str, tonic: str, mode: str, preset_name: str) -> tuple[str, str]:
    assets = _example_assets(term, tonic, mode, preset_name)
    wav, source = _render_wav(base64.b64decode(assets["midi_bytes_b64"]))
    return base64.b64encode(wav).decode("ascii"), source


def dictionary_example(term: str, tonic: str = "C", mode: str = "major", preset_name: str = "", include_audio: bool = True) -> dict:
    tonic, mode = normalize_context(tonic, mode)
    result = copy.deepcopy(_example_assets(term, tonic, mode, preset_name))
    if include_audio:
        try:
            result["wav_bytes_b64"], result["audio_source"] = _example_audio(term, tonic, mode, preset_name)
        except Exception:
            result["audio_error"] = "Audio could not be rendered. The notation remains available; try again."
    return result


def transition_examples(tonic: str, mode: str, preset_name: str = "") -> list[dict]:
    return [asdict(guide) for guide in transition_guides(tonic, mode, preset_name)]
