"""Tests for effects policy."""

from __future__ import annotations

import pytest

from core.presets.effects_policy import (
    EffectSpec,
    EffectsPolicy,
    get_effects_policy,
    list_presets_with_effects,
)


def test_list_presets_with_effects_returns_all_seven() -> None:
    presets = list_presets_with_effects()
    assert len(presets) == 7


def test_get_effects_policy_returns_policy_for_each_preset() -> None:
    for preset_name in list_presets_with_effects():
        policy = get_effects_policy(preset_name)
        assert isinstance(policy, EffectsPolicy)
        assert policy.preset == preset_name
        assert len(policy.effects) >= 3, f"{preset_name} should have at least 3 effects"


def test_each_effect_has_required_fields() -> None:
    for preset_name in list_presets_with_effects():
        policy = get_effects_policy(preset_name)
        for effect in policy.effects:
            assert isinstance(effect, EffectSpec)
            assert effect.effect_type
            assert effect.preset_name
            assert effect.purpose
            assert effect.parameters


def test_get_effects_policy_raises_for_unknown_preset() -> None:
    with pytest.raises(ValueError, match="No effects policy found"):
        get_effects_policy("nonexistent_preset")


def test_policy_is_cached() -> None:
    policy1 = get_effects_policy("dark_trip_hop")
    policy2 = get_effects_policy("dark_trip_hop")
    assert policy1 is policy2
