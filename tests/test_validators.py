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


# WR-02 regression tests: octave-less pitch names must raise ValueError instead
# of silently defaulting to octave 4, and malformed names must never leak a raw
# music21 PitchException.


def test_validate_pitch_octave_less_c_raises():
    with pytest.raises(ValueError):
        validate_pitch("C")


def test_validate_pitch_octave_less_bb_raises():
    with pytest.raises(ValueError):
        validate_pitch("Bb")


def test_validate_pitch_invalid_letter_raises_value_error_not_pitch_exception():
    with pytest.raises(ValueError):
        validate_pitch("H2")


def test_validate_pitch_c2_still_no_raise_after_hardening():
    validate_pitch("C2")


def test_validate_pitch_csharp3_still_no_raise_after_hardening():
    validate_pitch("C#3")


def test_validate_pitch_bb2_still_no_raise_after_hardening():
    validate_pitch("Bb2")


# WR-03 regression tests: non-positive individual rhythm durations must raise
# ValueError even when the sum happens to match the expected bar duration, and
# an empty rhythm list must raise ValueError naming the empty-rhythm problem.


def test_validate_bar_duration_negative_value_raises_despite_matching_sum():
    with pytest.raises(ValueError):
        validate_bar_duration([5.0, -1.0], "4/4")


def test_validate_bar_duration_zero_values_raise_despite_matching_sum():
    with pytest.raises(ValueError):
        validate_bar_duration([4.0, 0.0, 0.0], "4/4")


def test_validate_bar_duration_empty_rhythm_raises_with_empty_message():
    with pytest.raises(ValueError) as exc_info:
        validate_bar_duration([], "4/4")
    assert "empty" in str(exc_info.value).lower()


def test_validate_bar_duration_four_four_matches_no_raise_after_hardening():
    validate_bar_duration([1.0, 1.0, 1.0, 1.0], "4/4")


def test_validate_bar_duration_three_four_mismatch_raises_after_hardening():
    with pytest.raises(ValueError):
        validate_bar_duration([1.0, 0.5, 0.5, 1.0, 1.0], "3/4")


def test_validate_bar_duration_three_four_matches_no_raise_after_hardening():
    validate_bar_duration([1.0, 1.0, 1.0], "3/4")


def test_validate_bar_duration_sexy_duet_rhythm_matches_no_raise_after_hardening():
    validate_bar_duration([0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5], "4/4")
