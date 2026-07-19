"""Shared helpers for the unified Streamlit pages."""

from __future__ import annotations

import base64

import streamlit as st

from app.services.generation import analyze_progression, generate_loop_variants
from core.presets.registry import list_presets


FRIENDLY_PRESETS: dict[str, str] = {
    "dark_trip_hop": "Dark trip-hop · 72 BPM",
    "ritual_tribal": "Ritual tribal · 88 BPM",
    "noir_slow_burn": "Noir slow burn · 58 BPM",
    "driving_cinematic": "Driving cinematic · 104 BPM",
    "sexy_duet": "Violin + cello sensual duet · 76 BPM",
    "simple_sexy_duet": "Violin + cello intimate duet · 64 BPM",
    "dorian_sexy_duet": "Violin + cello Dorian duet · 88 BPM",
}

DEFAULT_PROGRESSION = "Dm9 G9 Dm9 G9 Bbmaj7 A7 Dm9 A7"
DEFAULT_PRESET = "dorian_sexy_duet"


def preset_names() -> list[str]:
    return list_presets()


def preset_label(name: str) -> str:
    friendly = FRIENDLY_PRESETS.get(name, name.replace("_", " ").title())
    return f"{friendly} · {name}"


def preset_from_label(label: str, names: list[str]) -> str:
    return next((name for name in names if preset_label(name) == label), names[0])


def default_preset_index(names: list[str]) -> int:
    return names.index(DEFAULT_PRESET) if DEFAULT_PRESET in names else 0


def decode_b64(value: str | None) -> bytes:
    return base64.b64decode(value) if value else b""


def audio_source_label(source: str | None) -> str:
    if source == "fluidsynth":
        return "FluidSynth + soundfont"
    if source == "cello_synth_reverb":
        return "Cloud synth + reverb"
    return "Audio renderer unavailable"


@st.cache_data(show_spinner=False)
def generate_cached(
    progression: str,
    preset_name: str,
    *,
    include_audio: bool,
    count: int = 3,
) -> list[dict]:
    return generate_loop_variants(
        chord_progression=progression,
        preset_name=preset_name,
        seed=0,
        include_audio=include_audio,
        count=count,
    )


@st.cache_data(show_spinner=False)
def analyze_cached(progression: str, preset_name: str) -> list[dict]:
    return analyze_progression(progression, preset_name, seed=0)
