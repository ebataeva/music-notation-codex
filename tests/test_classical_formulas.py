"""Tests for classical harmony formulas reference."""

from __future__ import annotations

import pytest

from core.theory.classical_formulas import (
    HarmonyFormula,
    format_formula_for_explanation,
    get_all_formulas,
    get_formula,
    list_formulas,
)


def test_list_formulas_returns_twelve() -> None:
    formulas = list_formulas()
    assert len(formulas) == 12
    assert "T35" in formulas
    assert "D7" in formulas
    assert "K64" in formulas


def test_get_formula_returns_formula_for_each_name() -> None:
    for name in list_formulas():
        formula = get_formula(name)
        assert isinstance(formula, HarmonyFormula)
        assert formula.formula == name
        assert formula.full_name
        assert formula.structure
        assert formula.function


def test_t35_is_tonic() -> None:
    formula = get_formula("T35")
    assert "Tonic" in formula.full_name
    assert "Tonic" in formula.function


def test_d7_is_dominant() -> None:
    formula = get_formula("D7")
    assert "Dominant" in formula.full_name
    assert "Dominant" in formula.function
    assert "T35" in formula.resolution


def test_k64_resolves_to_d7() -> None:
    formula = get_formula("K64")
    assert "D7" in formula.resolution


def test_get_formula_raises_for_unknown() -> None:
    with pytest.raises(ValueError, match="Formula not found"):
        get_formula("X99")


def test_format_formula_for_explanation() -> None:
    formula = get_formula("D7")
    text = format_formula_for_explanation(formula)
    assert "D7" in text
    assert "Dominant" in text
    assert "T35" in text


def test_get_all_formulas_returns_dict() -> None:
    formulas = get_all_formulas()
    assert isinstance(formulas, dict)
    assert len(formulas) == 12
