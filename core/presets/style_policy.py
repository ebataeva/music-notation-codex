"""Style-aware harmony policy for presets.

Loads YAML research data and provides API for accessing harmonic language
per preset: modal center, core degrees, bass movement, chromatic approaches,
cadences, texture idiom.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class StylePolicy:
    """Harmonic language policy for a preset."""

    preset: str
    genre_references: tuple[str, ...]
    modal_center: str
    core_degrees: dict[str, str]
    bass_movement: str
    chromatic_approaches: dict[str, str]
    cadences: dict[str, str]
    texture_idiom: str
    progressions: tuple[str, ...] = ()
    modulations: tuple[str, ...] = ()
    mood_tips: tuple[str, ...] = ()


_RESEARCH_DIR = Path(__file__).parent.parent.parent / "research"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load YAML file from research directory."""
    path = _RESEARCH_DIR / filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _normalize_texture_idiom(raw: Any) -> str:
    """Normalize texture_idiom to a plain str.

    PyYAML parses an indented plain scalar containing a mid-sentence colon
    (e.g. "...Duet texture: bass foundation...") as a single-key mapping
    instead of a string. Reconstruct the original prose in that case so the
    StylePolicy.texture_idiom: str contract holds for every preset.
    """
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return ". ".join(f"{key}: {value}" for key, value in raw.items())
    if not raw:
        return ""
    return str(raw)


def _parse_style_policy(data: dict[str, Any]) -> StylePolicy:
    """Parse YAML data into StylePolicy."""
    # Convert lists to dicts where needed
    core_degrees = {}
    for item in data.get("core_degrees", []):
        if isinstance(item, dict):
            core_degrees.update(item)

    chromatic_approaches = {}
    for item in data.get("chromatic_approaches", []):
        if isinstance(item, dict):
            chromatic_approaches.update(item)

    cadences_raw = data.get("cadences", {})
    cadences = {}
    if isinstance(cadences_raw, dict):
        cadences = cadences_raw
    elif isinstance(cadences_raw, list):
        for item in cadences_raw:
            if isinstance(item, dict):
                cadences.update(item)

    return StylePolicy(
        preset=data.get("preset", ""),
        genre_references=tuple(data.get("genre_references", [])),
        modal_center=data.get("modal_center", ""),
        core_degrees=core_degrees,
        bass_movement=data.get("bass_movement", ""),
        chromatic_approaches=chromatic_approaches,
        cadences=cadences,
        texture_idiom=_normalize_texture_idiom(data.get("texture_idiom", "")),
        progressions=tuple(data.get("progressions", [])),
        modulations=tuple(data.get("modulations", [])),
        mood_tips=tuple(data.get("mood_tips", [])),
    )


# Cache loaded policies
_POLICY_CACHE: dict[str, StylePolicy] = {}


def get_style_policy(preset_name: str) -> StylePolicy:
    """Get style policy for a preset.

    Args:
        preset_name: Name of the preset (e.g., "dark_trip_hop")

    Returns:
        StylePolicy with harmonic language data

    Raises:
        ValueError: If preset not found
    """
    if preset_name in _POLICY_CACHE:
        return _POLICY_CACHE[preset_name]

    # Map preset names to YAML files
    yaml_files = {
        "dark_trip_hop": "dark_trip_hop.yaml",
        "ritual_tribal": "ritual_tribal.yaml",
        "noir_slow_burn": "noir_slow_burn.yaml",
        "driving_cinematic": "driving_cinematic.yaml",
        "sexy_duet": "sexy_duet.yaml",
        "simple_sexy_duet": "simple_sexy_duet.yaml",
        "dorian_sexy_duet": "dorian_sexy_duet.yaml",
    }

    if preset_name not in yaml_files:
        raise ValueError(f"No style policy found for preset: {preset_name}")

    data = _load_yaml(yaml_files[preset_name])
    if not data:
        raise ValueError(f"Failed to load style policy for preset: {preset_name}")

    policy = _parse_style_policy(data)
    _POLICY_CACHE[preset_name] = policy
    return policy


def list_presets_with_policy() -> list[str]:
    """List all presets that have style policy data."""
    return [
        "dark_trip_hop",
        "ritual_tribal",
        "noir_slow_burn",
        "driving_cinematic",
        "sexy_duet",
        "simple_sexy_duet",
        "dorian_sexy_duet",
    ]
