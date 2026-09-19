"""The player names a key; everything downstream must obey it.

Three defects are locked down here, all found together:

KEY-01  The key selectors were written to storage and nowhere else, so the
        score was always built in the preset's own key. Choosing A minor and
        playing "D A G" printed a C-minor signature and respelled F# as Gb.
READ-01 Every preset ran 5-16 notes per bar -- authored for the CLI ostinato
        scripts, not for a cellist sight-reading a bar and looping it live.
VAR-01  The three register variants produced 50-100% different notes but
        near-identical coaching text, because every clause was derived from
        the progression and preset rather than from the notes.
"""

from __future__ import annotations

import re

import pytest
from music21 import stream

from app.services.generation import generate_loop_variants, suggest_progressions_for_key
from core.engine.loop_engine import build_progression_score, loop_rhythm_for
from core.engine.progression import parse_progression
from core.engine.validators import validate_bar_duration
from core.presets.registry import get_preset, list_solo_presets
from core.theory.progression_advisor import suggest_progressions

MAX_LOOP_NOTES_PER_BAR = 4


# --- READ-01: sight-readable density -------------------------------------


@pytest.mark.parametrize("preset_name", list_solo_presets())
def test_loop_rhythm_is_sight_readable(preset_name: str):
    preset = get_preset(preset_name)
    rhythm = loop_rhythm_for(preset)

    assert len(rhythm) <= MAX_LOOP_NOTES_PER_BAR, (
        f"{preset_name} generates {len(rhythm)} notes per bar; "
        f"the cap for a readable loop is {MAX_LOOP_NOTES_PER_BAR}."
    )
    # Still a legal bar in the preset's own meter.
    validate_bar_duration(list(rhythm), preset.meter_signature)
    # Nothing shorter than an eighth note, which is what makes it readable at
    # tempo rather than merely short.
    assert min(rhythm) >= 0.5, f"{preset_name} contains sub-eighth durations: {rhythm}"


@pytest.mark.parametrize("preset_name", list_solo_presets())
def test_generated_bars_honour_the_loop_rhythm(preset_name: str):
    preset = get_preset(preset_name)
    score = build_progression_score(parse_progression("Am F C G"), preset, seed=3)

    for measure in score.parts[0].getElementsByClass(stream.Measure):
        assert len(measure.notes) <= MAX_LOOP_NOTES_PER_BAR


def test_cli_preset_rhythm_is_left_alone():
    # The CLI ostinato scripts and the golden baseline read preset.rhythm, which
    # must keep its authored density even though the coach no longer uses it.
    assert len(get_preset("driving_cinematic").rhythm) == 16
    assert len(get_preset("dark_trip_hop").rhythm) == 8


# --- KEY-01: the chosen key reaches the score ----------------------------


def _key_fifths(musicxml: str) -> int:
    return int(re.search(r"<fifths>(-?\d+)</fifths>", musicxml).group(1))


def _accidentals(musicxml: str) -> set[str]:
    pairs = re.findall(r"<step>([A-G])</step>\s*<alter>(-?\d+)</alter>", musicxml)
    return {
        f"{step}{'#' * int(alter) if int(alter) > 0 else 'b' * -int(alter)}"
        for step, alter in pairs
    }


def test_chosen_key_drives_signature_and_spelling():
    # "D A G" in A minor: the D chord's third is F#. Before the fix the score
    # was built in dark_trip_hop's own C minor (3 flats), which printed a
    # C-minor signature and respelled that F# as Gb.
    result = generate_loop_variants(
        "D A G", "dark_trip_hop", seed=952013977, count=1,
        key_tonic="A", key_mode="minor",
    )[0]

    assert _key_fifths(result["musicxml_string"]) == 0, "A minor has no accidentals"
    spelled = _accidentals(result["musicxml_string"])
    assert "F#" in spelled
    assert "Gb" not in spelled


def test_key_defaults_to_the_preset_when_not_supplied():
    # Existing callers that pass no key keep the old behaviour exactly.
    result = generate_loop_variants("D A G", "dark_trip_hop", seed=952013977, count=1)[0]
    assert _key_fifths(result["musicxml_string"]) == -3  # C minor


# --- VAR-01: the three variants must not read the same --------------------


def test_variant_explanations_are_distinct():
    results = generate_loop_variants(
        "Am F C G", "dark_trip_hop", seed=42, count=3,
        key_tonic="A", key_mode="minor",
    )
    texts = [r["why_it_works"] for r in results]

    assert len(set(texts)) == len(texts), (
        "All three variant cards read identically; the explanation is not "
        "reflecting the notes each variant actually chose."
    )


# --- KEY-02: suggest a progression from a key ----------------------------


@pytest.mark.parametrize(
    "tonic,mode", [("A", "minor"), ("D", "minor"), ("C", "major"), ("G", "major")]
)
def test_suggestions_are_playable_in_the_requested_key(tonic: str, mode: str):
    suggestions = suggest_progressions(tonic, mode)
    assert suggestions, f"No progressions offered for {tonic} {mode}"

    for suggestion in suggestions:
        # The whole point is that the suggestion can be fed straight back in.
        parsed = parse_progression(suggestion.chords)
        assert len(parsed) == len(suggestion.formula.split("-"))
        assert suggestion.resolutions
        assert len(suggestion.resolutions) == len(parsed)


@pytest.mark.parametrize("tonic,mode", [("C", "major"), ("G", "major")])
def test_major_keys_get_a_major_tonic(tonic: str, mode: str):
    # Every mood preset is minor-mode. Applying their formulas to a major key
    # handed back a minor tonic (C major -> "Cm ..."), which is why the major
    # formulas are separate data.
    for suggestion in suggest_progressions(tonic, mode):
        first_chord = suggestion.chords.split()[0]
        assert not first_chord.startswith(f"{tonic}m"), (
            f"{tonic} {mode} suggested {suggestion.chords!r}, which opens on a minor tonic."
        )


def test_rationale_does_not_name_the_preset_key():
    # The authored prose spells each formula in the preset's own key ("C minor
    # -> Ab -> G minor"). Transposed to A minor that caption contradicts the
    # chords shown beside it, so it must be stripped.
    for suggestion in suggest_progressions("A", "minor"):
        opening_sentence = suggestion.why.split(".")[0]
        assert "->" not in opening_sentence, (
            f"{suggestion.chords!r} is captioned with another key's realisation: "
            f"{suggestion.why!r}"
        )


def test_suggestions_are_deduplicated_by_sounding_chords():
    suggestions = suggest_progressions("A", "minor")
    rendered = [s.chords for s in suggestions]
    assert len(rendered) == len(set(rendered))


def test_resolutions_close_the_cycle():
    # The progression is a loop too: the last chord resolves into the first on
    # the repeat, not into nothing.
    suggestion = suggest_progressions("A", "minor")[0]
    first_chord = suggestion.chords.split()[0]

    assert "on the repeat" in suggestion.resolutions[-1]
    assert first_chord in suggestion.resolutions[-1]


def test_service_wrapper_returns_serializable_dicts():
    payload = suggest_progressions_for_key("A", "minor")
    assert payload
    for item in payload:
        assert set(item) == {"chords", "formula", "why", "resolutions", "source_preset"}
        assert isinstance(item["resolutions"], list)


def test_service_wrapper_returns_empty_for_a_bad_key():
    assert suggest_progressions_for_key("H", "minor") == []
