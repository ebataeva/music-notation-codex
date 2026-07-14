"""Tests for style-aware harmony policy."""

from __future__ import annotations

import pytest

from core.presets.style_policy import (
    StylePolicy,
    get_style_policy,
    list_presets_with_policy,
)


def test_list_presets_with_policy_returns_all_seven() -> None:
    presets = list_presets_with_policy()
    assert len(presets) == 7
    assert "dark_trip_hop" in presets
    assert "dorian_sexy_duet" in presets


def test_get_style_policy_returns_policy_for_each_preset() -> None:
    for preset_name in list_presets_with_policy():
        policy = get_style_policy(preset_name)
        assert isinstance(policy, StylePolicy)
        assert policy.preset == preset_name
        assert policy.modal_center
        assert policy.core_degrees
        assert policy.bass_movement
        assert policy.texture_idiom
        assert isinstance(policy.texture_idiom, str)


def test_dark_trip_hop_policy_has_aeolian_modal_center() -> None:
    policy = get_style_policy("dark_trip_hop")
    assert policy.modal_center == "Aeolian"
    assert "i" in policy.core_degrees
    assert "bVI" in policy.core_degrees


def test_ritual_tribal_policy_has_phrygian_modal_center() -> None:
    policy = get_style_policy("ritual_tribal")
    assert policy.modal_center == "Phrygian"
    assert "bII" in policy.core_degrees


def test_noir_slow_burn_policy_has_harmonic_minor() -> None:
    policy = get_style_policy("noir_slow_burn")
    assert policy.modal_center == "HarmonicMinor"
    assert "V" in policy.core_degrees


def test_dorian_sexy_duet_policy_has_dorian_modal_center() -> None:
    policy = get_style_policy("dorian_sexy_duet")
    assert "Dorian" in policy.modal_center
    assert policy.progressions
    assert policy.mood_tips


def test_duet_presets_have_filled_progressions() -> None:
    for preset_name in ["sexy_duet", "simple_sexy_duet", "dorian_sexy_duet"]:
        policy = get_style_policy(preset_name)
        assert policy.progressions, f"{preset_name} should have progressions"
        assert policy.modulations, f"{preset_name} should have modulations"
        assert policy.mood_tips, f"{preset_name} should have mood_tips"


def test_get_style_policy_raises_for_unknown_preset() -> None:
    with pytest.raises(ValueError, match="No style policy found"):
        get_style_policy("nonexistent_preset")


def test_policy_is_cached() -> None:
    policy1 = get_style_policy("dark_trip_hop")
    policy2 = get_style_policy("dark_trip_hop")
    assert policy1 is policy2


def test_texture_idiom_is_always_a_string_even_when_yaml_has_colon() -> None:
    sexy_duet = get_style_policy("sexy_duet")
    assert isinstance(sexy_duet.texture_idiom, str)
    assert sexy_duet.texture_idiom == (
        "8th-note arpeggiated patterns establishing harmony with passing "
        "tones. Violin sings sustained melody with chromatic neighbor "
        "tones. Duet texture: bass foundation + lyrical soprano line with "
        "harmonic minor touches."
    )

    dorian_sexy_duet = get_style_policy("dorian_sexy_duet")
    assert isinstance(dorian_sexy_duet.texture_idiom, str)
    assert "Duet texture: cello provides harmonic foundation" in (
        dorian_sexy_duet.texture_idiom
    )

    simple_sexy_duet = get_style_policy("simple_sexy_duet")
    dark_trip_hop = get_style_policy("dark_trip_hop")
    assert isinstance(simple_sexy_duet.texture_idiom, str)
    assert isinstance(dark_trip_hop.texture_idiom, str)

    for preset_name in list_presets_with_policy():
        policy = get_style_policy(preset_name)
        assert isinstance(policy.texture_idiom, str)
