# Phase 3: TheoryExplainer - Pattern Map

**Mapped:** 2026-07-06
**Files analyzed:** 5 (2 new modules, 1 new data module, 1 refactored script, 1 new test file)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `core/theory/__init__.py` | config | n/a | `core/engine/__init__.py` / `core/presets/__init__.py` (empty package markers) | exact |
| `core/theory/explainer.py` | service (pure transform) | transform (request-response, no I/O) | `core/engine/loop_engine.py` — `generate_variant()` (module-level function, validate-then-build-then-return shape) | exact (same "flat function returning a populated dataclass" shape) |
| `core/theory/cues.py` | utility/model (data + lookup) | transform (dict-keyed classify) | `core/engine/loop_engine.py` — `_classify_register()` (bucket classifier) + `core/presets/registry.py` (registry lookup pattern) | role-match |
| `scripts/harmony_advisor.py` (refactored) | controller (CLI) | request-response (thin wrapper: generate → explain → print) | itself (pre-refactor) + `scripts/generate_sexy_duet_loop.py` (thin `main()` calling into `core/` and printing results) | exact (modify in place, same file) |
| `tests/test_theory_explainer.py` | test | request-response (assert dataclass fields / raise) | `tests/test_loop_engine.py` (literal-preset-driven assertions) + `tests/test_validators.py` (`pytest.raises(ValueError)` pattern) | role-match |

## Pattern Assignments

### `core/theory/explainer.py` (service, transform)

**Analog:** `core/engine/loop_engine.py` — `generate_variant()` (lines 115-168) and `_classify_register()` (lines 292-304)

**Imports pattern** (`core/engine/loop_engine.py` lines 1-23 — module bootstrap convention to mirror):
```python
from __future__ import annotations

import random
import warnings

from music21 import clef, duration, instrument, key, meter, note, pitch, stream, tempo

from core.engine.progression import ParsedChord
from core.engine.validators import (
    CELLO_MAX_MIDI_DEFAULT,
    CELLO_MIN_MIDI,
    validate_bar_duration,
    validate_pitch,
)
from core.models import GenerationTrace, LoopVariant, MoodPreset
from core.presets.registry import list_solo_presets
```
For `explainer.py`, the equivalent import block is much smaller (no music21 needed at all — confirmed by RESEARCH.md "Standard Stack": `explainer.py` touches neither music21 nor pychord):
```python
from __future__ import annotations

from core.models import GenerationTrace, LoopVariant, MoodPreset, TheoryExplanation
from core.theory.cues import cue_pair_for  # or equivalent name chosen at implementation time
```

**Core "validate-then-build-then-return dataclass" pattern** (`core/engine/loop_engine.py` lines 115-168, `generate_variant()`):
```python
def generate_variant(preset: MoodPreset, seed: int | None = None) -> LoopVariant:
    """High-level API (D-05): build a Score and a fully-populated GenerationTrace
    in one call. ..."""
    if not preset.bars:
        raise ValueError(
            f"Preset {preset.name!r} has no solo bars (duet-only preset); "
            f"choose one of: {', '.join(list_solo_presets())}."
        )
    ...
    generation_trace = GenerationTrace(
        seed=resolved_seed,
        pattern_strategy="preset_verbatim",
        register_choices=register_choices,
        voice_leading_steps=None,  # No voice-leading logic exists yet (Phase 2.5 concern).
        chord_tones_used=chord_tones_used,
    )

    return LoopVariant(
        id=f"{preset.name}-{resolved_seed}",
        preset_name=preset.name,
        label=preset.feel or preset.name,
        ...
        trace=generation_trace,
    )
```
**Apply this shape to `explain()`:** guard clause(s) raising plain `ValueError` first (D-06: `trace is None`), then pure computation, then construct-and-return the target dataclass in one place at the bottom — no early-return branches scattered through the middle, matching `generate_variant()`'s single terminal `return LoopVariant(...)`.

**Error handling pattern — plain `ValueError`, no custom exception types** (`core/engine/loop_engine.py` lines 123-127, and `core/engine/validators.py` lines 14-18):
```python
# loop_engine.py generate_variant()
if not preset.bars:
    raise ValueError(
        f"Preset {preset.name!r} has no solo bars (duet-only preset); "
        f"choose one of: {', '.join(list_solo_presets())}."
    )
```
```python
# validators.py validate_pitch()
if not any(ch.isdigit() for ch in pitch_name):
    raise ValueError(
        f"Pitch {pitch_name!r} must include an octave (e.g. 'C3'), "
        "not just a pitch class."
    )
```
**Apply directly to D-06:** `if variant.trace is None: raise ValueError("...")` — no `TheoryError`/`ExplainerError` class, no try/except wrapping. This is a hard project-wide convention (01-PATTERNS.md: "no custom exception type, no try/except — a miss ... propagates the dict's natural KeyError").

**Bucket-classifier idiom for cue selection** (`core/engine/loop_engine.py` lines 292-304, `_classify_register()`):
```python
def _classify_register(pitches: list[str]) -> str:
    """Cheap register label for a bar's pitches, based on the lowest octave digit
    present. Not a music-theoretic register model -- just enough to populate a
    non-empty, per-bar trace field (D-04)."""
    octaves = [int(ch) for pitch_name in pitches for ch in pitch_name if ch.isdigit()]
    if not octaves:
        return "unspecified register"
    lowest = min(octaves)
    if lowest <= 2:
        return "low register"
    if lowest == 3:
        return "mid register"
    return "high register"
```
**Apply directly to `tempo_band()` in `cues.py` and to `_select_anchor()`'s branch structure in `explainer.py`:** a small pure function, no side effects, returns a string label from a handful of if/elif buckets — never an if/elif chain keyed by *preset name* (that is the explicit anti-pattern D-08 rules out).

**Branch-on-`pattern_strategy` contract** (`core/models.py` lines 27-44, `GenerationTrace` docstring — IN-01):
```python
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
```
This docstring names Phase 3 explicitly as the consumer that must branch. `_select_anchor(trace)` must switch on `trace.pattern_strategy` as its *first* line (not infer shape from data), with a final `else: raise ValueError(f"Unknown pattern_strategy {trace.pattern_strategy!r}...")` — matching the loop_engine convention of failing loudly rather than duck-typing (see `build_duet_score`'s explicit `ValueError` guards at lines 201-204, 222-226).

**Two producers of `pattern_strategy`, confirmed by direct reading of `loop_engine.py`:**
- `generate_variant()` line 152: `pattern_strategy="preset_verbatim"`, `chord_tones_used` built at lines 144-148 as `list(pitches)` per bar — octave-bearing (e.g. `"C2"`).
- `generate_variant_from_progression()` line 548: `pattern_strategy="progression_driven_register_mapped"`, `chord_tones_used` built at lines 536-544 as `list(chord.components)` per bar — pitch classes only (e.g. `"A"`), with `register_choices` carrying the register separately.
- Both set `voice_leading_steps=None` explicitly (lines 154, 550) — confirms RESEARCH.md Pitfall 3: never reference this field.

**Preset field emptiness for duet presets** (`core/presets/mood_presets.py` lines 163-175, 204-216, 248-260 — verified directly):
```python
"sexy_duet": MoodPreset(
    name="sexy_duet",
    ...
    progressions=(),
    modulations=(),
    mood_tips=(),
    duet_rhythm={...},
    duet_bars={...},
    duet_tempo_bpm=76,
),
```
All 3 duet presets (`sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet`) have empty `progressions`/`modulations`/`mood_tips` tuples. Any field-mapping code doing `preset.progressions[0]` unconditionally will `IndexError` on these three. **Guard explicitly** (`_first_or_fallback` per RESEARCH.md) — this is the single most load-bearing pattern for this phase's D-11 requirement (all 7 presets must produce explanations).

---

### `core/theory/cues.py` (utility/model, transform)

**Analog:** `core/presets/registry.py` (registry/lookup shape) + `core/engine/loop_engine.py`'s `_classify_register()` (bucket-classifier idiom, reused above)

**Registry lookup pattern to mirror** (`core/presets/registry.py`, full file, 24 lines):
```python
"""Read-only lookup helpers over MOOD_PRESETS.

Kept intentionally simple (01-PATTERNS.md): no custom exception type, no
try/except -- a miss on get_preset() propagates the dict's natural KeyError.
"""

from __future__ import annotations

from core.models import MoodPreset
from core.presets.mood_presets import MOOD_PRESETS


def get_preset(name: str) -> MoodPreset:
    return MOOD_PRESETS[name]


def list_presets() -> list[str]:
    return sorted(MOOD_PRESETS)


def list_solo_presets() -> list[str]:
    """Solo-capable presets only (non-empty `.bars`) -- excludes duet-only presets (WR-01)."""
    return sorted(name for name, preset in MOOD_PRESETS.items() if preset.bars)
```
**Apply to `cues.py`:** a module-level dict constant (`TEMPO_BAND_CUES` or similar) plus tiny plain functions operating on it — no class, no `__init__`, matching this file's "data dict + free functions" shape exactly. Dataclass entries in the dict may use `@dataclass(frozen=True)` per `core/models.py`'s `MoodPreset` convention (frozen dataclass for static reference data — see below).

**Frozen-dataclass convention for static data records** (`core/models.py` lines 65-81, `MoodPreset`):
```python
# Collection fields are tuples, not lists (WR-05: frozen=True alone does not
# protect mutable list/dict fields; get_preset() must not be able to leak a
# mutation path into the shared MOOD_PRESETS registry).
@dataclass(frozen=True)
class MoodPreset:
    name: str
    tempo_bpm: int
    ...
```
If `cues.py` defines a `CueTemplate` dataclass (per RESEARCH.md Pattern 1), use `@dataclass(frozen=True)` and tuple fields for any collection, matching this exact rationale (module-level constant dict must not be mutable through a leaked reference).

---

### `scripts/harmony_advisor.py` (controller/CLI, request-response — refactor in place)

**Analog:** itself pre-refactor (full file, 51 lines, read above) + `scripts/generate_sexy_duet_loop.py` (thin `main()` shape)

**Current file to refactor** (`scripts/harmony_advisor.py`, full 51 lines):
```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Allows running the script directly (python3 scripts/...) without installing the package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.presets.registry import get_preset, list_presets  # noqa: E402


def print_section(title: str, items: list[str]) -> None:
    print()
    print(title)
    print("-" * len(title))
    for item in items:
        print(f"- {item}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Suggest harmonic development, modulation, and mood ideas.")
    parser.add_argument("--genre", choices=sorted(list_presets()), default="dark_trip_hop")
    parser.add_argument("--list-genres", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_genres:
        print("Available genres:")
        for genre in sorted(list_presets()):
            print(f"- {genre}")
        return

    preset = get_preset(args.genre)
    print(dedent(f"""
    Harmony advisor: {args.genre}
    This is not an auto-composer but a map of options: pick a direction, then change the notes/chords in the generator.
    """).strip())
    print_section("Harmonic development", preset.progressions)
    print_section("Modulations", preset.modulations)
    print_section("Mystery, drive, sexy effect", preset.mood_tips)


if __name__ == "__main__":
    main()
```
**Reusable pieces (keep as-is):** `PROJECT_ROOT`/`sys.path` bootstrap block (lines 8-11), `parse_args()` shape (extend with `--seed`, type `int | None`, per D-10), `print_section()` helper (still useful as a pure printing helper per RESEARCH.md's "State of the Art" note — only the `GENRE_IDEAS`-shaped iteration over raw preset lists is superseded, not the print helper itself).

**Generate-then-print orchestration shape to add** (mirrors `scripts/generate_sexy_duet_loop.py` full file, 34 lines — thin `main()` that imports from `core/`, calls one `core/` function, and prints results, no music21-building logic in the script itself):
```python
from __future__ import annotations

import sys
from pathlib import Path

from music21 import environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_duet_score  # noqa: E402
from core.export.exporter import ExportEngine  # noqa: E402
from core.presets.registry import get_preset  # noqa: E402

OUTPUT_NAME = "sexy_d_minor_violin_cello_loop"


def main() -> None:
    environment.Environment()["warnings"] = 0
    preset = get_preset("sexy_duet")
    score = build_duet_score(
        preset, tempo_bpm=preset.duet_tempo_bpm, cello_velocity=82, violin_velocity=70
    )
    musicxml_path, midi_path = ExportEngine().export(score, OUTPUT_NAME)
    print(f"Sexy duet loop: D minor, {preset.duet_tempo_bpm} bpm, 8 bars, violin + cello")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
```
**Apply to the refactored `harmony_advisor.py`:** `main()` calls `get_preset(args.genre)` → `generate_variant(preset, seed=args.seed)` (or the internal duet build path per D-11 for the 3 duet presets) → `explain(variant, preset)` → print all 5 `TheoryExplanation` fields plus the trace anchor, using `print_section()`-style formatting for each field so the D-10 manual review (success criterion #2) can read all 5 fields per preset in one pass (RESEARCH.md Pitfall 5 requires this side-by-side visibility).

---

### `tests/test_theory_explainer.py` (test, request-response)

**Analog:** `tests/test_loop_engine.py` (literal-preset-driven assertions, one behavior per test function) + `tests/test_validators.py` (`pytest.raises(ValueError)` pattern)

**Flat one-assertion-per-test style** (`tests/test_loop_engine.py` lines 1-14, 41-60):
```python
from __future__ import annotations

import pytest
from music21 import stream

from core.models import MoodPreset
from core.presets.registry import get_preset


def test_build_score_returns_music21_score_no_errors():
    from core.engine.loop_engine import build_score

    score = build_score(get_preset("dark_trip_hop"))
    assert isinstance(score, stream.Score)


def test_generate_variant_trace_seed_matches_explicit_seed():
    from core.engine.loop_engine import generate_variant

    variant = generate_variant(get_preset("dark_trip_hop"), seed=42)
    assert variant.trace.seed == 42


def test_generate_variant_pattern_strategy_is_non_empty_string():
    from core.engine.loop_engine import generate_variant

    variant = generate_variant(get_preset("dark_trip_hop"))
    assert isinstance(variant.trace.pattern_strategy, str)
    assert variant.trace.pattern_strategy
```
**Apply directly:** import inside each test function (matches this file's convention of `from core.engine.loop_engine import X` inside every `test_*` body, not at module top, except for stable imports like `get_preset`/`pytest`/`music21.stream`). Name tests descriptively, one behavior each (`test_explain_all_seven_presets_...`, `test_explain_trace_none_raises_value_error`, etc.), matching both files' naming convention (`test_<subject>_<condition>_<expectation>`).

**`pytest.raises(ValueError)` + message-content assertion pattern** (`tests/test_validators.py` lines 14-23):
```python
def test_validate_pitch_b1_below_floor_raises():
    with pytest.raises(ValueError):
        validate_pitch("B1")


def test_validate_pitch_b1_message_contains_pitch_and_midi():
    with pytest.raises(ValueError) as exc_info:
        validate_pitch("B1")
    assert "B1" in str(exc_info.value)
    assert "35" in str(exc_info.value)
```
**Apply directly to D-06's `trace=None` test:**
```python
def test_explain_trace_none_raises_value_error():
    with pytest.raises(ValueError):
        explain(variant_with_none_trace, preset)
```

**Literal `GenerationTrace` construction for isolated anchor-selection tests** (no analog file constructs `GenerationTrace` literals yet — this is new, but the *dataclass-literal-as-fixture* style already exists in `tests/test_models.py` for other dataclasses in `core/models.py`; construct directly rather than adding new pytest fixtures, per RESEARCH.md's explicit recommendation: "literal `GenerationTrace`/`MoodPreset` construction can happen inline per test, matching the style already used in `tests/test_loop_engine.py`"):
```python
def test_select_anchor_preset_verbatim_pedal_tone():
    from core.models import GenerationTrace
    from core.theory.explainer import _select_anchor

    trace = GenerationTrace(
        seed=1,
        pattern_strategy="preset_verbatim",
        register_choices=["low register"],
        voice_leading_steps=None,
        chord_tones_used=[["C2", "C2", "G2"]],
    )
    anchor = _select_anchor(trace)
    assert "C2" in anchor
```

## Shared Patterns

### No custom exception hierarchy — plain `ValueError` everywhere
**Source:** `core/engine/validators.py` (lines 14-18, 21-22, 43-45), `core/engine/loop_engine.py` (lines 70, 75, 123-127, 131-132, 137-138, 201-204, 222-226, 232-235), `core/presets/registry.py` docstring (line 3: "no custom exception type, no try/except")
**Apply to:** `explainer.py`'s D-06 guard (`trace is None`), the IN-01 unknown-strategy defensive branch, and any duet-preset empty-tuple guard.
```python
raise ValueError(f"...descriptive f-string with the offending value repr'd via !r...")
```
No `TheoryExplainerError`, no `class ExplainerError(Exception)` — a bare `ValueError` with an f-string message is the only error type used anywhere in `core/` to date.

### Module-level functions, not classes (Phase 1 style, reconfirmed by RESEARCH.md)
**Source:** `core/engine/loop_engine.py` (every public symbol is a module-level `def`, zero classes defined), `core/presets/registry.py` (3 free functions, no class)
**Apply to:** `explain()`, `_select_anchor()`, `_first_or_fallback()`, `_enforce_word_limit()`, `tempo_band()` — all plain functions in `explainer.py`/`cues.py`, no `TheoryExplainer` class wrapping them. RESEARCH.md's own recommendation matches this exactly ("Build `explainer.py` as a set of small pure functions").

### Dict-keyed bucket classifier (not if/elif on identity/name)
**Source:** `core/engine/loop_engine.py` `_classify_register()` (lines 292-304)
**Apply to:** `cues.py`'s `tempo_band()`/`TEMPO_BAND_CUES` dict lookup — bucket on a *derived discrete value* (tempo band, meter, feel-keyword), never on preset name/identity.

### `from __future__ import annotations` + PEP 604 union types (`X | None`)
**Source:** every file in `core/` (`core/models.py` line 1, `core/engine/loop_engine.py` line 1, `core/engine/validators.py` — no `from __future__` needed there since it only uses `music21` types directly, but `core/models.py`/`loop_engine.py` both use `int | None` style throughout)
**Apply to:** `explainer.py`, `cues.py` — first line of both new modules, and all optional-type annotations written as `X | None`, never `Optional[X]`.

### Frozen dataclass for static reference data with tuple (not list) collection fields
**Source:** `core/models.py` `MoodPreset` (lines 65-81) — explicit WR-05 comment on why tuples not lists
**Apply to:** any `CueTemplate`-style dataclass in `cues.py` if the planner chooses the dataclass-record approach from RESEARCH.md Pattern 1 (as opposed to a plain dict of strings, which is equally acceptable and has no mutability concern at all).

### Guard against empty-tuple preset fields (duet presets) before indexing
**Source:** new pattern this phase must introduce (no pre-existing `_first_or_fallback`-style helper exists yet) — but the *defensive-guard-before-use* style matches `loop_engine.py`'s existing guards, e.g.:
```python
# core/engine/loop_engine.py lines 199-204 (build_duet_score)
if preset.duet_rhythm is None or preset.duet_bars is None:
    raise ValueError(
        f"Preset {preset.name!r} has no duet data; use build_score() for solo presets."
    )
```
**Apply to:** `_first_or_fallback(items: tuple[str, ...], fallback: str) -> str` in `explainer.py`, called for `preset.progressions`/`preset.modulations`/`preset.mood_tips` — return `items[0] if items else fallback`, never raise here (RESEARCH.md is explicit: D-11 requires all 7 presets to succeed, so this must be a graceful fallback, not a `ValueError`, unlike the `build_duet_score` example above which *does* raise because it has no fallback data source).

## No Analog Found

None — every file in this phase's scope has at least a role-match analog in the existing codebase (this is the third phase in a project that has consistently used a small, uniform set of conventions since Phase 1).

## Metadata

**Analog search scope:** `core/`, `scripts/`, `tests/`, `.planning/phases/01-core-library-skeleton-validators/01-PATTERNS.md`
**Files scanned:** `core/models.py`, `core/engine/loop_engine.py`, `core/engine/validators.py`, `core/presets/registry.py`, `core/presets/mood_presets.py` (partial, lines 1-60 + grep for duet tuples), `scripts/harmony_advisor.py`, `scripts/generate_sexy_duet_loop.py`, `tests/test_loop_engine.py` (partial), `tests/test_validators.py` (partial), `tests/test_progression.py` (grep only), `01-PATTERNS.md` (partial)
**Pattern extraction date:** 2026-07-06
