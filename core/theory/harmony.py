from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache

from music21 import interval, pitch


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


def degree_name(tone: str, tonic: str) -> str:
    letters = "CDEFGAB"
    step = (letters.index(pitch_class(tone)[0]) - letters.index(pitch_class(tonic)[0])) % 7
    expected = (0, 2, 4, 5, 7, 9, 11)[step]
    alteration = ((semitone(tone) - semitone(tonic) - expected + 6) % 12) - 6
    prefix = "#" * alteration if alteration > 0 else "b" * -alteration
    return f"{prefix}{step + 1}"


@dataclass(frozen=True)
class ChordFacts:
    root: str
    quality: str
    symbol: str
    tones: tuple[str, ...]
    respellings: tuple[str, ...]
    extension: str
    additional_tones: tuple[str, ...]


def chord_facts(tones: Sequence[str]) -> ChordFacts:
    # Progression traces contain root-first pitch classes, not performed voicings.
    names = tuple(dict.fromkeys(pitch_class(tone) for tone in tones))
    root = names[0]
    offsets = {(semitone(name) - semitone(root)) % 12 for name in names}
    quality = "incomplete"
    if not {3, 4}.issubset(offsets):
        for candidate, required in (
            ("diminished", {0, 3, 6}), ("minor", {0, 3, 7}),
            ("major", {0, 4, 7}), ("augmented", {0, 4, 8}),
        ):
            if required <= offsets:
                quality = candidate
                break
    if quality == "incomplete" and not offsets & {3, 4}:
        if offsets == {0, 5, 7}:
            quality = "sus4"
        elif offsets == {0, 2, 7}:
            quality = "sus2"
        elif offsets == {0, 7}:
            quality = "power"

    suffix = {"major": "", "minor": "m", "diminished": "dim", "augmented": "aug",
              "sus4": "sus4", "sus2": "sus2", "power": "5",
              "incomplete": " (incomplete or ambiguous sonority)"}[quality]
    extension = ""
    if quality in {"major", "minor", "diminished", "augmented"}:
        if quality == "diminished" and 9 in offsets:
            suffix, extension = "dim7", "°7"
        elif quality == "diminished" and 10 in offsets:
            suffix, extension = "m7b5", "ø7"
        elif 11 in offsets:
            extension = "maj9" if 2 in offsets else "maj7"
            suffix += f"({extension})" if quality == "minor" else extension
        elif 10 in offsets:
            extension = "9" if 2 in offsets else "7"
            suffix += extension
        elif 2 in offsets:
            suffix += "add9"
            extension = "add9"
        elif 9 in offsets:
            suffix += "6"
            extension = "6"

    # pychord can return G-A#-D for Gm. Disclose analytical respelling rather
    # than presenting its augmented-second spelling as a written minor third.
    spellings = {0: "P1", 2: "M9", 3: "m3", 4: "M3", 7: "P5", 10: "m7", 11: "M7"}
    if quality == "diminished":
        spellings.update({6: "d5", 9: "d7"})
    elif quality == "augmented":
        spellings[8] = "A5"
    else:
        spellings[9] = "M6"
    if quality == "sus4":
        spellings[5] = "P4"
    corrected, respellings = [], []
    for name in names:
        offset = (semitone(name) - semitone(root)) % 12
        spelled = transpose_name(root, spellings[offset]) if offset in spellings and quality != "incomplete" else name
        if spelled != name:
            respellings.append(f"{spelled} is supplied as {name}")
        if spelled not in corrected:
            corrected.append(spelled)
    encoded = {
        "major": {0, 4, 7}, "minor": {0, 3, 7}, "diminished": {0, 3, 6},
        "augmented": {0, 4, 8}, "sus2": {0, 2, 7}, "sus4": {0, 5, 7},
        "power": {0, 7}, "incomplete": offsets,
    }[quality] | {
        "7": {10}, "9": {2, 10}, "maj7": {11}, "maj9": {2, 11},
        "°7": {9}, "ø7": {10}, "add9": {2}, "6": {9},
    }.get(extension, set())
    additional = tuple(name for name in corrected if (_semitone_offset(name, root)) not in encoded)
    symbol = root + suffix
    if additional:
        symbol += f" (plus {', '.join(additional)})"
    return ChordFacts(root, quality, symbol, tuple(corrected), tuple(respellings), extension, additional)


def _semitone_offset(tone: str, root: str) -> int:
    return (semitone(tone) - semitone(root)) % 12


def _roman_base(chord: ChordFacts, tonic: str) -> str:
    degree = degree_name(chord.root, tonic)
    number = int(degree[-1])
    roman = ("I", "II", "III", "IV", "V", "VI", "VII")[number - 1]
    if chord.quality in {"minor", "diminished"}:
        roman = roman.lower()
    roman = degree[:-1] + roman
    if chord.quality == "diminished":
        return roman + (chord.extension or "°")
    if chord.quality == "augmented":
        roman += "+"
    if chord.quality == "minor" and chord.extension.startswith("maj"):
        return roman + f"({chord.extension})"
    if chord.quality in {"sus2", "sus4"}:
        return roman + chord.quality
    if chord.quality == "power":
        return roman + "5 (no third)"
    if chord.quality == "incomplete":
        return f"degree {degree} (incomplete or ambiguous)"
    if chord.extension == "6":
        return roman + "(add6)"
    return roman + chord.extension


def roman_label(chord: ChordFacts, tonic: str) -> str:
    label = _roman_base(chord, tonic)
    if chord.additional_tones:
        label += f" (plus {', '.join(chord.additional_tones)})"
    return label


COLLECTIONS = {
    "major": frozenset({0, 2, 4, 5, 7, 9, 11}),
    "natural minor (Aeolian)": frozenset({0, 2, 3, 5, 7, 8, 10}),
    "harmonic minor": frozenset({0, 2, 3, 5, 7, 8, 11}),
    "Dorian": frozenset({0, 2, 3, 5, 7, 9, 10}),
    "Phrygian": frozenset({0, 1, 3, 5, 7, 8, 10}),
}


def compatible_collections(tones: Sequence[str], tonic: str) -> list[str]:
    offsets = {(semitone(tone) - semitone(tonic)) % 12 for tone in tones}
    return [name for name, collection in COLLECTIONS.items() if offsets <= collection]
