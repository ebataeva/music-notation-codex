"""Suggest chord progressions and their resolutions for a chosen key.

The loop coach used to demand that the player type a progression before it
would do anything. This module inverts that: give it a key (and optionally a
mood), and it returns playable progressions already spelled in that key,
each one carrying the roman-numeral formula it came from, why it works, and
where every chord wants to resolve.

Nothing here invents harmony. The formulas come from the mood presets'
authored `progressions` prose, and the resolution guidance is pulled from
`core.theory.classical_formulas` (the T35/D7/K64 set), so the coaching text
stays anchored to the same theory the rest of the app teaches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from music21 import key as m21key
from music21 import roman

from core.presets.registry import get_preset, list_solo_presets
from core.theory.classical_formulas import get_formula

# A formula line in MoodPreset.progressions reads
# "i - VI - v - i: C minor -> Ab -> G minor -> C minor. Works because ..."
# so the roman-numeral formula is everything before the first colon.
_FORMULA_SPLIT = re.compile(r"^\s*([^:]+?)\s*:\s*(.+)$", re.DOTALL)

# Roman numerals as written in the preset data, which uses pop/rock notation
# relative to the *major* scale ("bVI", "bVII"). In a minor key those degrees
# are already diatonic, and music21 would read the extra flat as a second
# lowering -- bVI in A minor becomes F-flat rather than F. Strip it.
_MINOR_REDUNDANT_FLATS = {"bIII": "III", "bVI": "VI", "bVII": "VII"}

# music21 common names -> chord suffixes pychord can parse back.
_QUALITY_SUFFIX = {
    "major triad": "",
    "minor triad": "m",
    "diminished triad": "dim",
    "augmented triad": "aug",
    "dominant seventh chord": "7",
    "minor seventh chord": "m7",
    "major seventh chord": "maj7",
    "half-diminished seventh chord": "m7b5",
    "diminished seventh chord": "dim7",
}

# Degrees whose resolution behaviour the classical formula set already
# describes. Only *unstable* degrees are mapped: a formula's `resolution` field
# says where that chord is pulled to, which is meaningful for a dominant and
# meaningless for a tonic (T35's reads "Goal for dominant and subdominant" --
# true, but not an answer to "where does the tonic go next"). Stable degrees
# fall through to the common-tone description instead.
_DEGREE_FORMULA = {
    "V": "D7",
    "V7": "D7",
    "vii": "VII7",
    "viio": "VII7",
    "vii°": "VII7",
    "ii": "II7",
    "iiø": "SII7",
    "ii°": "SII6",
    "iio": "SII6",
}

# The mood presets are all minor-mode, so their authored formulas cannot serve
# a major key -- applying "i - VI - v - i" to C major yields a C minor tonic.
# These are the common-practice major-key staples, kept as data next to the
# minor formulas rather than synthesised at call time.
_MAJOR_FORMULAS: tuple[tuple[str, str], ...] = (
    (
        "I - V - vi - IV",
        "The most-played loop in popular music: the tonic leaves, the dominant "
        "pulls, the relative minor darkens it, and IV walks home without a hard "
        "cadence -- so it never quite stops turning.",
    ),
    (
        "I - vi - IV - V",
        "The older cousin: vi shades the tonic before the subdominant lifts and "
        "V demands the return. Stronger sense of arrival than I - V - vi - IV.",
    ),
    (
        "vi - IV - I - V",
        "The same four chords starting on the relative minor, which reads much "
        "darker while staying diatonic -- useful when the mood wants minor "
        "colour without leaving the major key.",
    ),
    (
        "I - IV - V - I",
        "The plain authentic frame. Every degree is stable and the cadence is "
        "unambiguous, which makes it the easiest loop to re-enter after a "
        "mistake.",
    ),
    (
        "ii - V - I - vi",
        "The jazz turnaround: ii sets up V, V resolves, and vi reopens the loop "
        "so the resolution never feels final.",
    ),
)


@dataclass(frozen=True)
class SuggestedProgression:
    """One progression, already spelled in the player's chosen key."""

    chords: str
    """Space-separated chord symbols ready for the chord input, e.g. "Am Dm F E"."""

    formula: str
    """The roman-numeral formula it was built from, e.g. "i - iv - VI - V"."""

    why: str
    """The authored rationale for this formula."""

    resolutions: tuple[str, ...]
    """One line per step, saying where that chord pulls and why."""

    source_preset: str


def _normalize_figure(figure: str, mode: str) -> str:
    figure = figure.strip()
    if mode.lower().startswith("min"):
        return _MINOR_REDUNDANT_FLATS.get(figure, figure)
    return figure


def _chord_symbol(numeral: roman.RomanNumeral) -> str:
    """Render a roman numeral as a chord symbol pychord can parse back.

    Flats print as "b" rather than music21's "-", and no slash chords are ever
    emitted -- pychord 0.2.8 corrupts a process-global quality cache on the
    slash path, so the parser this feeds rejects them outright.
    """
    root = numeral.root().name.replace("-", "b")
    suffix = _QUALITY_SUFFIX.get(numeral.commonName)
    if suffix is None:
        # Unknown quality: fall back to the plain triad rather than emitting a
        # symbol the chord parser would choke on.
        suffix = "m" if numeral.isMinorTriad() else ""
    return f"{root}{suffix}"


def _resolution_line(
    figure: str,
    symbol: str,
    next_figure: str,
    next_symbol: str,
    key_obj: m21key.Key,
    is_wrap: bool = False,
) -> str:
    """Say where this chord pulls, and cite the classical formula when one
    describes exactly this degree.

    The progression is read as a cycle, so the last chord resolves into the
    first one on the repeat rather than trailing off -- that step is played on
    every pass of the loop and is where a V chord actually earns its pull.
    """
    head = f"{symbol} ({figure}) → {next_symbol} ({next_figure})"
    if is_wrap:
        head += " on the repeat"

    formula_name = _DEGREE_FORMULA.get(figure)
    if formula_name:
        try:
            return f"{head}: {get_formula(formula_name).resolution}"
        except (KeyError, ValueError):
            pass

    # No formula covers this degree; describe the voice-leading that is
    # actually there instead of inventing a functional label.
    try:
        current = roman.RomanNumeral(figure, key_obj)
        following = roman.RomanNumeral(next_figure, key_obj)
    except Exception:
        return f"{head}."

    shared = sorted(
        {p.name for p in current.pitches} & {p.name for p in following.pitches}
    )
    if shared:
        return f"{head}: {'/'.join(shared)} is common to both, so hold it and move the rest."
    return f"{head}: no common tone, so move to the nearest chord tone by step."


def _parse_formula_line(line: str) -> tuple[str, str] | None:
    match = _FORMULA_SPLIT.match(line)
    if not match:
        return None
    formula, rationale = match.group(1), match.group(2)
    if "-" not in formula:
        return None
    return formula.strip(), _strip_preset_key_realisation(rationale.strip())


def _strip_preset_key_realisation(rationale: str) -> str:
    """Drop the leading sentence that spells the formula in the preset's own key.

    The authored prose reads "C minor -> Ab -> G minor -> C minor. Works
    because ...". Once the formula has been transposed into the player's key
    that first sentence is actively wrong -- it would caption "Am F Em Am"
    with "C minor -> Ab -> G minor". The reasoning after it is key-agnostic
    and is what we want to keep.
    """
    head, separator, tail = rationale.partition(". ")
    if separator and "->" in head:
        return tail.strip() or rationale
    return rationale


def _formula_sources(
    key_mode: str, preset_name: str | None
) -> list[tuple[str, str, str]]:
    """(source, formula, rationale) triples appropriate to the mode.

    Minor keys read the mood presets' own authored formulas; major keys read
    the common-practice set above, because every preset in this project is
    minor-mode and its formulas would hand a major key a minor tonic.
    """
    if not key_mode.lower().startswith("min"):
        return [("common practice", f, why) for f, why in _MAJOR_FORMULAS]

    sources: list[tuple[str, str, str]] = []
    for name in [preset_name] if preset_name else list_solo_presets():
        for line in get_preset(name).progressions:
            parsed = _parse_formula_line(line)
            if parsed:
                sources.append((name, parsed[0], parsed[1]))
    return sources


def suggest_progressions(
    key_tonic: str,
    key_mode: str,
    preset_name: str | None = None,
) -> list[SuggestedProgression]:
    """Progressions for a key, drawn from the authored mood-preset formulas.

    Pass `preset_name` to stay inside one mood; omit it to sweep every solo
    preset, which is what "give me the key and suggest something" needs.
    """
    try:
        key_obj = m21key.Key(key_tonic, key_mode)
    except Exception as exc:
        raise ValueError(f"Not a usable key: {key_tonic!r} {key_mode!r} ({exc})") from exc

    suggestions: list[SuggestedProgression] = []
    seen_chords: set[str] = set()

    for name, formula, rationale in _formula_sources(key_mode, preset_name):
        figures = [
            _normalize_figure(part, key_mode)
            for part in formula.split("-")
            if part.strip()
        ]
        try:
            numerals = [roman.RomanNumeral(fig, key_obj) for fig in figures]
        except Exception:
            # A figure this key cannot spell is skipped rather than surfaced
            # as a broken suggestion.
            continue

        symbols = [_chord_symbol(n) for n in numerals]
        chords = " ".join(symbols)
        # Two differently-written formulas can land on the same chords in a
        # given key (minor "i - iv - VI - V" and "i - iv - bVI - V" both give
        # Am Dm F E). Showing that twice is noise, so dedupe on what the
        # player actually reads.
        if chords in seen_chords:
            continue

        resolutions = tuple(
            _resolution_line(
                figures[i],
                symbols[i],
                figures[(i + 1) % len(figures)],
                symbols[(i + 1) % len(symbols)],
                key_obj,
                is_wrap=(i == len(figures) - 1),
            )
            for i in range(len(figures))
        )

        seen_chords.add(chords)
        suggestions.append(
            SuggestedProgression(
                chords=chords,
                formula=formula,
                why=rationale,
                resolutions=resolutions,
                source_preset=name,
            )
        )

    return suggestions
