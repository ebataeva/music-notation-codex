"""LOOP-CYCLE: a generated loop must be playable as a *cycle*, not just as a line.

The leap guards in tests/test_loop_engine.py walk ``zip(notes, notes[1:])`` --
the linear adjacencies, n-1 pairs out of n. But the product ships a loop:
``app/pages/loop_coach.py`` renders ``<audio ... loop>`` and the cellist repeats
the figure live, so the wrap-around pair (last note -> first note) is an
adjacency the player actually performs. Before this guard existed it was
checked nowhere, and 17% of generated loops jumped more than an octave there --
up to 22 semitones -- while every other test stayed green.

Reference standard, measured rather than invented: the four hand-authored solo
presets close their loops 0, 7, 0 and 0 semitones from their own opening note,
three of them returning to it exactly. The human author freely takes
14-semitone leaps *inside* a bar but never at the seam.
"""

from __future__ import annotations

from music21 import stream

from core.engine.loop_engine import (
    MAX_MELODIC_LEAP_SEMITONES,
    build_progression_score,
    build_score,
    generate_variant,
    generate_variant_from_progression,
    loop_rhythm_for,
)
from core.engine.progression import parse_progression
from core.models import LOOP_SEAM_MARKER
from core.presets.registry import get_preset, list_solo_presets
from core.theory.explainer import explain

# The curated presets never exceed a perfect fifth at the seam; generated loops
# are held to the same bar.
MAX_SEAM_SEMITONES = 7

PROGRESSIONS = ["Am", "Am F", "C G", "Am F C G", "Bb Eb Ab F"]
PRESETS = ["dark_trip_hop", "driving_cinematic"]
BIASES = ["low", "default", "high"]
SEEDS = range(12)


def cyclic_adjacencies(items: list) -> list[tuple[int, object, object]]:
    """Every pair a player performs when the material repeats, seam included.

    Use this instead of ``zip(xs, xs[1:])`` for any invariant about a looped
    artifact -- register continuity, enharmonic spelling, dynamics, string
    crossings. The class of bug it catches is "invariant verified on the linear
    sequence while the artifact is cyclic".
    """
    return [(i, items[i], items[(i + 1) % len(items)]) for i in range(len(items))]


def _loop_notes(score: stream.Score) -> list:
    return [n for m in score.parts[0].getElementsByClass(stream.Measure) for n in m.notes]


def test_generated_loop_has_no_unplayable_adjacency_including_the_seam():
    violations = []
    for progression in PROGRESSIONS:
        chords = parse_progression(progression)
        for preset_name in PRESETS:
            preset = get_preset(preset_name)
            for bias in BIASES:
                for seed in SEEDS:
                    notes = _loop_notes(
                        build_progression_score(
                            chords, preset, seed=seed, register_bias=bias
                        )
                    )
                    for i, current, following in cyclic_adjacencies(notes):
                        leap = abs(following.pitch.midi - current.pitch.midi)
                        if leap > MAX_MELODIC_LEAP_SEMITONES:
                            where = (
                                "SEAM (repeat)"
                                if i == len(notes) - 1
                                else f"note {i}->{i + 1}"
                            )
                            violations.append(
                                f"{progression!r}/{preset_name}/{bias}/seed={seed}: "
                                f"{current.pitch.nameWithOctave}->"
                                f"{following.pitch.nameWithOctave} "
                                f"= {leap} st at {where}"
                            )

    assert not violations, (
        f"{len(violations)} unplayable adjacencies in looped playback "
        f"(cap {MAX_MELODIC_LEAP_SEMITONES} st):\n  " + "\n  ".join(violations[:10])
        + (f"\n  ... +{len(violations) - 10} more" if len(violations) > 10 else "")
    )


def test_generated_loop_closes_on_or_near_its_opening_note():
    # Stronger than the leap cap above: the loop must actually come home, the
    # way the curated presets do, so the repeat needs no position shift.
    violations = []
    for progression in PROGRESSIONS:
        chords = parse_progression(progression)
        for preset_name in PRESETS:
            preset = get_preset(preset_name)
            for bias in BIASES:
                for seed in SEEDS:
                    notes = _loop_notes(
                        build_progression_score(
                            chords, preset, seed=seed, register_bias=bias
                        )
                    )
                    seam = abs(notes[-1].pitch.midi - notes[0].pitch.midi)
                    if seam > MAX_SEAM_SEMITONES:
                        violations.append(
                            f"{progression!r}/{preset_name}/{bias}/seed={seed}: "
                            f"{notes[-1].pitch.nameWithOctave}->"
                            f"{notes[0].pitch.nameWithOctave} = {seam} st"
                        )

    assert not violations, (
        f"{len(violations)} loops fail to close within {MAX_SEAM_SEMITONES} st:\n  "
        + "\n  ".join(violations[:10])
    )


def test_trace_records_the_seam_step():
    # The seam used to be invisible to the coaching layer too: voice_leading_steps
    # was hardcoded to None, so the trace described every bar except the moment
    # the player actually repeats.
    chords = parse_progression("Am F C G")
    variant = generate_variant_from_progression(chords, get_preset("dark_trip_hop"), seed=42)

    steps = variant.trace.voice_leading_steps
    assert steps, "voice_leading_steps must be populated, not None"

    notes_per_loop = len(chords) * len(loop_rhythm_for(get_preset("dark_trip_hop")))
    assert len(steps) == notes_per_loop, "one step per performed adjacency, seam included"
    assert steps[-1].endswith(LOOP_SEAM_MARKER)
    assert not any(s.endswith(LOOP_SEAM_MARKER) for s in steps[:-1]), "exactly one seam"


def test_how_to_end_names_the_seam():
    chords = parse_progression("Am F C G")
    preset = get_preset("dark_trip_hop")
    variant = generate_variant_from_progression(chords, preset, seed=42)

    how_to_end = explain(variant, preset).how_to_end

    seam = variant.trace.voice_leading_steps[-1][: -len(LOOP_SEAM_MARKER)]
    opening_note = seam.split("->")[1]
    assert opening_note in how_to_end, (
        f"how_to_end must name the note the repeat lands on ({opening_note}): {how_to_end!r}"
    )


def test_how_to_end_unchanged_when_trace_has_no_seam():
    # Preset-verbatim variants carry no voice_leading_steps; their coaching text
    # must not sprout a dangling seam sentence.
    variant = generate_variant(get_preset("dark_trip_hop"), seed=1)

    assert variant.trace.voice_leading_steps is None
    assert "the repeat itself" not in explain(variant, get_preset("dark_trip_hop")).how_to_end.lower()


def test_curated_presets_still_close_their_own_loops():
    # The reference the generated bound is calibrated against. Guards future
    # preset authoring from quietly eroding the standard.
    for preset_name in list_solo_presets():
        notes = _loop_notes(build_score(get_preset(preset_name), seed=0))
        seam = abs(notes[-1].pitch.midi - notes[0].pitch.midi)
        assert seam <= MAX_SEAM_SEMITONES, (
            f"Preset {preset_name!r} closes {notes[-1].pitch.nameWithOctave}->"
            f"{notes[0].pitch.nameWithOctave} = {seam} st, "
            f"above the {MAX_SEAM_SEMITONES} st reference."
        )


def test_interval_in_coaching_text_matches_the_sounding_distance():
    # SPELL-01: the octave number belongs to the letter, not to the sound.
    # B#3 is written on the B line of octave 3 but sounds as C4, and Cb4 sounds
    # as B3, so adding twelve per octave to the pitch class misplaces those
    # names by a whole octave. That made the card report "B#3->D#4" -- three
    # semitones -- as a leap of fifteen, telling a cellist to prepare a shift
    # that is not there. Unreachable until chord-driven spelling could print
    # B# at all, which is why it surfaced only now.
    from music21 import pitch

    from core.theory.explainer import _absolute_semitone

    for name in ("B#3", "D#4", "A2", "D-3", "C-4", "F##3", "B--4"):
        assert _absolute_semitone(name) == pitch.Pitch(name).midi, (
            f"{name} must report the height it actually sounds at"
        )

    assert _absolute_semitone("D#4") - _absolute_semitone("B#3") == 3
    assert _absolute_semitone("C-4") - _absolute_semitone("B3") == 0
    assert _absolute_semitone("C") is None  # octave-less names stay unreadable
