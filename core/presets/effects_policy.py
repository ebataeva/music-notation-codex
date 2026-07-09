"""Effects policy for presets.

Loads YAML research data and provides API for accessing characteristic
audio effects per preset.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class EffectSpec:
    """Specification for a single audio effect."""

    effect_type: str
    preset_name: str
    purpose: str
    parameters: str


@dataclass(frozen=True)
class EffectsPolicy:
    """Audio effects policy for a preset."""

    preset: str
    effects: tuple[EffectSpec, ...]


_RESEARCH_DIR = Path(__file__).parent.parent.parent / "research"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load YAML file from research directory."""
    path = _RESEARCH_DIR / filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _parse_effects_policy(preset_name: str, data: list[dict[str, Any]]) -> EffectsPolicy:
    """Parse YAML data into EffectsPolicy."""
    effects = []
    for item in data:
        effects.append(
            EffectSpec(
                effect_type=item.get("effect_type", ""),
                preset_name=item.get("preset_name", ""),
                purpose=item.get("purpose", ""),
                parameters=item.get("parameters", ""),
            )
        )
    return EffectsPolicy(preset=preset_name, effects=tuple(effects))


# Cache loaded policies
_POLICY_CACHE: dict[str, EffectsPolicy] = {}


def get_effects_policy(preset_name: str) -> EffectsPolicy:
    """Get effects policy for a preset.

    Args:
        preset_name: Name of the preset (e.g., "dark_trip_hop")

    Returns:
        EffectsPolicy with audio effects data

    Raises:
        ValueError: If preset not found
    """
    if preset_name in _POLICY_CACHE:
        return _POLICY_CACHE[preset_name]

    # Load from both solo and duet effect files
    solo_data = _load_yaml("effects_solo.yaml")
    duet_data = _load_yaml("effects_duet.yaml")

    # Merge
    all_effects = {**solo_data, **duet_data}

    if preset_name not in all_effects:
        raise ValueError(f"No effects policy found for preset: {preset_name}")

    policy = _parse_effects_policy(preset_name, all_effects[preset_name])
    _POLICY_CACHE[preset_name] = policy
    return policy


def list_presets_with_effects() -> list[str]:
    """List all presets that have effects policy data."""
    return [
        "dark_trip_hop",
        "ritual_tribal",
        "noir_slow_burn",
        "driving_cinematic",
        "sexy_duet",
        "simple_sexy_duet",
        "dorian_sexy_duet",
    ]
