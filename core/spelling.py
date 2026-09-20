"""SPELL-01: the one place that decides what a chord tone is *called*.

A note's name is its position on the line of fifths: C is 0, G is +1, D is +2,
A is +3, and downwards F is -1, Bb is -2, Eb is -3. Both the letter and the
accidental follow from that single integer, so neither is stored. How the note
*sounds* is the map k -> 7k mod 12 onto the twelve pitch classes; two names an
octave of fifths apart (a difference of 12) are the same sound spelled two ways,
which is exactly what an enharmonic pair is.

Intervals are therefore addition, not a lookup table: a major third is +4 on the
line, a minor third -3, a fifth +1, a minor seventh -2. A7 is A(+3) plus
{0, +4, +1, -2} = {+3, +7, +4, -1} = A, C#, E, G -- the third is C# in every key,
because it is the letter C raised, not the letter D lowered.

This matters because pychord spells by pitch class rather than by function: it
hands back G-A#-D for Gm and would let a raised leading tone print as a flattened
tonic. Both the notation and the explanation text read their spellings from here,
so a card can no longer say "A7: A-C#-E-G" while the stave next to it prints Db.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from functools import lru_cache

from music21 import interval, pitch

# The line of fifths, one octave of it: each step right adds a sharp once the
# seven letters are used up, each step left adds a flat.
LETTERS = "FCGDAEB"

# Distances above the root that a tertian chord actually names: root, ninth,
# both thirds, fifth, both sevenths. Everything else depends on the quality and
# is added by _named_offsets below.
_TERTIAN_OFFSETS = frozenset({0, 2, 3, 4, 7, 10, 11})


@lru_cache(maxsize=512)
def pitch_class(tone: str) -> str:
    match = re.fullmatch(r"([A-Ga-g])([#b\-x♭♯]*)(\d*)", tone.strip())
    if not match:
        raise ValueError(f"Invalid pitch in theory trace: {tone!r}.")
    letter, accidental, _ = match.groups()
    accidental = accidental.replace("♭", "b").replace("♯", "#").replace("x", "##")
    return pitch.Pitch(letter.upper() + accidental.replace("b", "-")).name.replace("-", "b")


@lru_cache(maxsize=512)
def semitone(tone: str) -> int:
    return pitch.Pitch(pitch_class(tone).replace("b", "-")).pitchClass


@lru_cache(maxsize=512)
def transpose_name(tone: str, distance: str) -> str:
    source = pitch.Pitch(pitch_class(tone).replace("b", "-"))
    return interval.Interval(distance).transposePitch(source).name.replace("-", "b")


def spell(fifths: int) -> str:
    """The note that sits at this position on the line of fifths."""
    letter = LETTERS[(fifths + 1) % 7]
    accidentals = (fifths + 1) // 7
    return letter + ("#" * accidentals if accidentals > 0 else "b" * -accidentals)


@lru_cache(maxsize=512)
def fifths_of(tone: str) -> int:
    """Where this note sits on the line of fifths -- the inverse of spell()."""
    name = pitch_class(tone)
    fifths = LETTERS.index(name[0]) - 1
    for mark in name[1:]:
        fifths += 7 if mark == "#" else -7
    return fifths


def fifths_shift(semitones: int, quality: str) -> int:
    """How far along the line of fifths a distance of `semitones` reaches.

    Of all shifts s satisfying 7s = semitones (mod 12), take the one nearest
    zero: three semitones is -3, a minor third, rather than +9, an augmented
    second. Two distances would otherwise tie, and the chord's quality breaks
    the tie -- a tritone is a diminished fifth in a diminished chord and an
    augmented fourth elsewhere; six semitones is a minor sixth unless the chord
    is augmented, where it is an augmented fifth. This is the only thing the
    quality is consulted for.
    """
    if quality == "diminished":
        if semitones == 6:
            return -6
        if semitones == 9:
            return -9
    elif quality == "augmented" and semitones == 8:
        return 8
    shift = semitones * 7 % 12  # 7 is its own inverse modulo 12
    return shift - 12 if shift > 6 else shift


def chord_quality(offsets: frozenset[int] | set[int]) -> str:
    """The quality these semitone distances above the root add up to, or
    "incomplete" when the sonority does not name one (carrying both thirds,
    for instance)."""
    if not {3, 4}.issubset(offsets):
        for candidate, required in (
            ("diminished", {0, 3, 6}), ("minor", {0, 3, 7}),
            ("major", {0, 4, 7}), ("augmented", {0, 4, 8}),
        ):
            if required <= offsets:
                return candidate
    if not offsets & {3, 4}:
        if offsets == {0, 5, 7}:
            return "sus4"
        if offsets == {0, 2, 7}:
            return "sus2"
        if offsets == {0, 7}:
            return "power"
    return "incomplete"


def _named_offsets(quality: str) -> frozenset[int]:
    """Distances above the root whose function this quality actually names.
    A tone outside the set keeps whatever spelling it arrived with, because the
    chord gives no grounds to rename it."""
    extra = {"diminished": {6, 9}, "augmented": {8}}.get(quality, {9})
    return _TERTIAN_OFFSETS | extra | ({5} if quality == "sus4" else set())


def chord_tone_spellings(tones: Sequence[str]) -> list[str | None]:
    """One entry per tone given, in the same order and of the same length.

    The entry is the name the tone carries as an interval above the chord's
    root, or None when the chord does not imply one -- an ambiguous sonority, or
    an alteration the chord never names -- in which case the caller keeps the
    incoming spelling. Order and length are preserved because callers index back
    into their own tone list.
    """
    names = [pitch_class(tone) for tone in tones]
    if not names:
        return []
    root = names[0]
    root_semitone = semitone(root)
    offsets = frozenset((semitone(name) - root_semitone) % 12 for name in names)
    quality = chord_quality(offsets)
    if quality == "incomplete":
        return [None] * len(names)

    named = _named_offsets(quality)
    root_fifths = fifths_of(root)
    spellings: list[str | None] = []
    for name in names:
        offset = (semitone(name) - root_semitone) % 12
        if offset in named:
            spellings.append(spell(root_fifths + fifths_shift(offset, quality)))
        else:
            spellings.append(None)
    return spellings
