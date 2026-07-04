import pytest

from core.engine.validators import validate_bar_duration, validate_pitch


def test_validate_pitch_c2_floor_no_raise():
    validate_pitch("C2")


def test_validate_pitch_d5_default_ceiling_no_raise():
    validate_pitch("D5")


def test_validate_pitch_b1_below_floor_raises():
    with pytest.raises(ValueError):
        validate_pitch("B1")


def test_validate_pitch_b1_message_contains_pitch_and_midi():
    with pytest.raises(ValueError) as exc_info:
        validate_pitch("B1")
    assert "B1" in str(exc_info.value)
    assert "35" in str(exc_info.value)


def test_validate_pitch_g5_above_default_ceiling_raises():
    with pytest.raises(ValueError):
        validate_pitch("G5")


def test_validate_pitch_g5_extended_true_no_raise():
    validate_pitch("G5", extended=True)


def test_validate_pitch_c6_extended_ceiling_no_raise():
    validate_pitch("C6", extended=True)


def test_validate_pitch_sharp_accidental_in_range_no_raise():
    validate_pitch("C#3")


def test_validate_pitch_flat_accidental_in_range_no_raise():
    validate_pitch("Bb2")


def test_validate_bar_duration_four_four_matches_no_raise():
    validate_bar_duration([1.0, 1.0, 1.0, 1.0], "4/4")


def test_validate_bar_duration_three_four_mismatch_raises():
    with pytest.raises(ValueError):
        validate_bar_duration([1.0, 0.5, 0.5, 1.0, 1.0], "3/4")


def test_validate_bar_duration_three_four_matches_no_raise():
    validate_bar_duration([1.0, 1.0, 1.0], "3/4")


def test_validate_bar_duration_sexy_duet_rhythm_matches_no_raise():
    validate_bar_duration([0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5], "4/4")


def test_validate_bar_duration_three_four_message_contains_sum_and_expected():
    with pytest.raises(ValueError) as exc_info:
        validate_bar_duration([1.0, 1.0, 1.0, 1.0], "3/4")
    assert "4.0" in str(exc_info.value)
    assert "3.0" in str(exc_info.value)
