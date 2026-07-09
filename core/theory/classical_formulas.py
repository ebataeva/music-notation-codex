"""Classical harmony formulas reference.

Provides structured data for traditional harmony formulas: T35, T6, T64,
D7, D65, D43, D2, SII6, SII7, K64, VII7, II7.

Each formula includes structure, function, resolution, usage, and example.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class HarmonyFormula:
    """A classical harmony formula."""

    formula: str
    full_name: str
    structure: str
    function: str
    resolution: str
    usage: str
    example: str


_RESEARCH_DIR = Path(__file__).parent.parent.parent / "research"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load YAML file from research directory."""
    path = _RESEARCH_DIR / filename
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _parse_formula(name: str, data: dict[str, str]) -> HarmonyFormula:
    """Parse YAML data into HarmonyFormula."""
    return HarmonyFormula(
        formula=name,
        full_name=data.get("full_name", ""),
        structure=data.get("structure", ""),
        function=data.get("function", ""),
        resolution=data.get("resolution", ""),
        usage=data.get("usage", ""),
        example=data.get("example", ""),
    )


# Cache loaded formulas
_FORMULAS_CACHE: dict[str, HarmonyFormula] | None = None


def _load_all_formulas() -> dict[str, HarmonyFormula]:
    """Load all formulas from YAML files."""
    global _FORMULAS_CACHE
    if _FORMULAS_CACHE is not None:
        return _FORMULAS_CACHE

    part1 = _load_yaml("classical_formulas_part1.yaml")
    part2 = _load_yaml("classical_formulas_part2.yaml")

    formulas = {}
    for name, data in {**part1, **part2}.items():
        formulas[name] = _parse_formula(name, data)

    _FORMULAS_CACHE = formulas
    return formulas


def get_formula(formula_name: str) -> HarmonyFormula:
    """Get a classical harmony formula by name.

    Args:
        formula_name: Formula name (e.g., "T35", "D7", "K64")

    Returns:
        HarmonyFormula with structure, function, resolution, usage, example

    Raises:
        ValueError: If formula not found
    """
    formulas = _load_all_formulas()
    if formula_name not in formulas:
        raise ValueError(f"Formula not found: {formula_name}")
    return formulas[formula_name]


def list_formulas() -> list[str]:
    """List all available formula names."""
    return list(_load_all_formulas().keys())


def get_all_formulas() -> dict[str, HarmonyFormula]:
    """Get all classical harmony formulas."""
    return _load_all_formulas()


def format_formula_for_explanation(formula: HarmonyFormula) -> str:
    """Format a formula for inclusion in theory explanations.

    Returns a concise, plain-language description suitable for user-facing text.
    """
    parts = [
        f"{formula.formula} ({formula.full_name})",
        f"Function: {formula.function}",
        f"Resolves to: {formula.resolution}",
    ]
    return ". ".join(parts)
