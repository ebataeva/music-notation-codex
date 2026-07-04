"""Progression parser: chord text -> chord objects with per-token error reporting.

Wraps pychord (pinned 0.2.8) so downstream register-mapping code (Phase 2.5's
loop_engine extension) can consume chord names/component tones without
importing pychord directly. Follows the codebase-wide convention (01-PATTERNS.md,
core/engine/validators.py) of raising bare ValueError only -- no custom
exception classes.
"""

from __future__ import annotations

from dataclasses import dataclass

from pychord import Chord

# pychord 0.2.8's QUALITY_DICT only recognizes "M7" for a major-7th chord, not
# the more common lead-sheet spelling "maj7" (confirmed: Chord("Cmaj7") raises
# "Unknown quality maj7"). The plan's required behavior includes "Cmaj7"
# parsing successfully, so common aliases are normalized to pychord's own
# quality spellings before parsing. This keeps pychord itself untouched and
# pinned -- normalization happens in this module only.
_QUALITY_ALIASES: dict[str, str] = {
    "maj7": "M7",
    "maj9": "M9",
    "min": "m",
    "min7": "m7",
    "-7": "m7",
}


@dataclass(frozen=True)
class ParsedChord:
    """Thin wrapper around a pychord Chord result: chord name plus its
    component tones (pitch classes, no octave -- octave/register assignment
    is a downstream concern, not this parser's job)."""

    name: str
    components: list[str]


def _normalize_token(token: str) -> str:
    """Rewrite known quality aliases (e.g. "maj7" -> "M7") while leaving the
    root note and any unrecognized suffix untouched -- pychord's own parser
    reports unrecognized suffixes as errors, naming the original token."""
    if len(token) > 1 and token[1] in ("b", "#"):
        root, rest = token[:2], token[2:]
    else:
        root, rest = token[:1], token[1:]
    normalized_rest = _QUALITY_ALIASES.get(rest, rest)
    return root + normalized_rest


def parse_progression(text: str) -> list[ParsedChord]:
    """Parse a whitespace-separated chord progression string into an ordered
    list of ParsedChord objects.

    Raises ValueError (never a raw pychord/library exception) if the input is
    empty/whitespace-only, or if any token doesn't parse as a valid chord --
    the error message names the exact offending token verbatim.
    """
    tokens = text.split()
    if not tokens:
        raise ValueError(
            "Progression text must contain at least one chord (e.g. 'Am F C G'); "
            f"got {text!r}."
        )

    parsed: list[ParsedChord] = []
    for token in tokens:
        normalized = _normalize_token(token)
        try:
            chord = Chord(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Could not parse chord token {token!r} in progression {text!r}: {exc}"
            ) from exc
        parsed.append(ParsedChord(name=token, components=list(chord.components())))

    return parsed
