"""Read-only lookup helpers over MOOD_PRESETS.

Kept intentionally simple (01-PATTERNS.md): no custom exception type, no
try/except -- a miss on get_preset() propagates the dict's natural KeyError.
"""

from __future__ import annotations

from core.models import MoodPreset
from core.presets.mood_presets import MOOD_PRESETS


def get_preset(name: str) -> MoodPreset:
    return MOOD_PRESETS[name]


def list_presets() -> list[str]:
    return sorted(MOOD_PRESETS)


def list_solo_presets() -> list[str]:
    """Solo-capable presets only (non-empty `.bars`) -- excludes duet-only presets (WR-01)."""
    return sorted(name for name, preset in MOOD_PRESETS.items() if preset.bars)
