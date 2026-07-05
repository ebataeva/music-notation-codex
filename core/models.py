from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GenerationRequest:
    chord_progression: str
    key_tonic: str
    key_mode: str
    mood: str
    num_variants: int = 3
    bars: int = 8
    instrument_set: str = "cello"


@dataclass
class TheoryExplanation:
    why_it_works: str
    how_to_start: str
    how_to_develop: str
    how_to_end: str
    how_to_transition: str


@dataclass
class GenerationTrace:
    """Per-generation provenance for a LoopVariant.

    IN-01: `chord_tones_used` is one inner list per bar, but its element
    shape depends on `pattern_strategy` -- consumers (e.g. Phase-3
    TheoryExplainer) must branch on the strategy, not assume one shape:
      - "preset_verbatim": concrete octave-bearing pitches, e.g. ["C2", "C2"].
      - "progression_driven_register_mapped": octave-less pitch classes taken
        from the parsed chord, e.g. ["A", "C", "E"] -- the register actually
        chosen per bar is recorded separately in `register_choices`.
    """

    seed: int | None
    pattern_strategy: str | None
    register_choices: list[str] | None
    voice_leading_steps: list[str] | None
    chord_tones_used: list[list[str]] | None


@dataclass
class LoopVariant:
    id: str
    preset_name: str
    label: str
    musicxml_path: Path | None
    midi_path: Path | None
    svg_bytes: bytes | None
    midi_bytes: bytes | None
    theory_explanation: TheoryExplanation | None
    # trace defaults to None so Phase 1 callers can construct a LoopVariant
    # before Phase 2/2.5 start populating generation trace data.
    trace: GenerationTrace | None = None


@dataclass(frozen=True)
class MoodPreset:
    name: str
    tempo_bpm: int
    key_tonic: str
    key_mode: str
    meter_signature: str
    velocity: int
    rhythm: list[float]
    bars: list[list[str]]
    feel: str
    progressions: list[str]
    modulations: list[str]
    mood_tips: list[str]
    duet_rhythm: dict[str, list[float]] | None = None
    duet_bars: dict[str, list[list[str]]] | None = None
    duet_tempo_bpm: int | None = None
