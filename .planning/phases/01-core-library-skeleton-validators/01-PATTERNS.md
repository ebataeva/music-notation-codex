# Phase 1: Core Library Skeleton + Validators - Pattern Map

**Mapped:** 2026-07-04
**Files analyzed:** 12 (5 brownfield scripts read as source; 7+ new files to create in `core/`/`tests/`)
**Analogs found:** 12 / 12 (all files have a brownfield analog — this is a pure extraction phase, no greenfield-only files)

**Note on analog source:** There is no pre-existing `core/`, `app/`, or `tests/` directory in this repo — this is the first phase creating them. Every "analog" below is one of the 5 existing CLI scripts in `scripts/`, since they are the sole prior art for dataclass shapes, preset data, and music21 usage patterns in this codebase.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `core/__init__.py` | config | n/a | — (new package marker) | n/a |
| `core/models.py` | model | transform (pure dataclasses) | `scripts/generate_cello_dark_ostinato.py` (`GenrePreset` dataclass, lines 13-23) | role-match (frozen dataclass pattern), extended per ARCHITECTURE.md |
| `core/presets/__init__.py` | config | n/a | — (new package marker) | n/a |
| `core/presets/mood_presets.py` | model/data | batch (static registry) | `scripts/generate_cello_dark_ostinato.py` (`GENRE_PRESETS` dict, lines 26-107) + `scripts/harmony_advisor.py` (`GENRE_IDEAS` dict, lines 7-68) + 3 duet scripts' bar/rhythm literals | exact (data source is literally these dicts, merged) |
| `core/presets/registry.py` | service | CRUD (read-only lookup) | `scripts/generate_cello_dark_ostinato.py` (`GENRE_PRESETS[args.genre]` lookup, line 172; `--list-genres` loop, lines 167-170) | role-match |
| `core/engine/__init__.py` | config | n/a | — (new package marker) | n/a |
| `core/engine/validators.py` | utility | request-response (validate-or-raise) | none in `scripts/` (scripts never validate) — use RESEARCH.md/PITFALLS.md reference implementation | no analog (new validation logic; PITFALLS.md has the reference code) |
| `scripts/generate_cello_dark_ostinato.py` (modified) | controller (CLI) | CRUD (data source swap only) | itself (pre-modification) — only the `GENRE_PRESETS` dict body is replaced by an import | exact (modify in place) |
| `scripts/harmony_advisor.py` (modified) | controller (CLI) | CRUD (data source swap only) | itself (pre-modification) — only `GENRE_IDEAS` dict body replaced by import | exact (modify in place) |
| `scripts/generate_sexy_duet_loop.py` (modified) | controller (CLI) | CRUD (data source swap only) | itself + `generate_cello_dark_ostinato.py`'s import-swap pattern | exact (modify in place) |
| `scripts/generate_simple_sexy_duet_loop.py` (modified) | controller (CLI) | CRUD (data source swap only) | itself + `generate_cello_dark_ostinato.py`'s import-swap pattern | exact (modify in place) |
| `scripts/generate_dorian_sexy_duet_loop.py` (modified) | controller (CLI) | CRUD (data source swap only) | itself + `generate_cello_dark_ostinato.py`'s import-swap pattern | exact (modify in place) |
| `tests/conftest.py` | test | n/a (fixtures) | none in repo (no prior tests/ dir) | no analog — follow pytest stdlib conventions |
| `tests/test_validators.py` | test | request-response (assert raise/pass) | none — new; targets `core/engine/validators.py` | no analog |
| `tests/test_models.py` | test | transform (assert shape) | none — new; targets `core/models.py` | no analog |
| `tests/test_presets_registry.py` | test | CRUD (assert merge completeness) | none — new; targets `core/presets/registry.py` | no analog |
| `tests/test_import_boundary.py` | test | request-response (assert ImportError) | none — new; enforces PLAT-03 | no analog |
| `requirements.txt` | config | n/a | itself (version bump only) | exact |

## Pattern Assignments

### `core/models.py` (model, transform)

**Analog:** `scripts/generate_cello_dark_ostinato.py` lines 1-23, extended with ARCHITECTURE.md's canonical shapes (`.planning/research/ARCHITECTURE.md` lines 203-262) and CONTEXT.md's `GenerationTrace` addition.

**Existing dataclass pattern to follow** (`scripts/generate_cello_dark_ostinato.py` lines 1-23):
```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GenrePreset:
    name: str
    tempo_bpm: int
    key_tonic: str
    key_mode: str
    meter_signature: str
    velocity: int
    rhythm: list[float]
    bars: list[list[str]]
    feel: str
```
**Key convention to carry over:** `from __future__ import annotations` at top of file (used in all 5 scripts); `@dataclass(frozen=True)` for immutable preset data; plain `list[float]` / `list[list[str]]` type hints (no `Optional[...]`, use `X | None` union syntax — matches CONTEXT.md's `GenerationTrace` field style and the scripts' Python 3.12+ target).

**Canonical target shapes** (`.planning/research/ARCHITECTURE.md` lines 203-262, cross-checked against CONTEXT.md decisions — do NOT import `music21.stream.Score` as a required field per the serialization-friendliness requirement in CONTEXT.md):
```python
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
    seed: int | None
    pattern_strategy: str | None
    register_choices: list[str] | None
    voice_leading_steps: list[str] | None
    chord_tones_used: list[list[str]] | None   # per-bar detail

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
    trace: GenerationTrace | None = None
    # NOTE: live music21 Score is deliberately NOT a required field here —
    # CONTEXT.md requires music21 objects separable from the persistable payload.

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
```

---

### `core/presets/mood_presets.py` (model/data, batch)

**Analogs (3-way merge):**
1. `scripts/generate_cello_dark_ostinato.py` — `GENRE_PRESETS` dict (lines 26-107): 4 entries (`dark_trip_hop`, `ritual_tribal`, `noir_slow_burn`, `driving_cinematic`), each with `tempo_bpm`, `key_tonic`, `key_mode`, `meter_signature`, `velocity`, `rhythm`, `bars`, `feel`.
2. `scripts/harmony_advisor.py` — `GENRE_IDEAS` dict (lines 7-68): same 4 keys, each with `progressions`, `modulations`, `mood` (→ maps to `mood_tips`).
3. Three duet scripts — each is its OWN preset entry (not a variant of the 4 above), per CONTEXT.md/RESEARCH.md Pitfall 3.

**Merge key alignment** (verified: both dicts use identical keys `dark_trip_hop`, `ritual_tribal`, `noir_slow_burn`, `driving_cinematic` — a straightforward `{k: MoodPreset(**GENRE_PRESETS[k].__dict__, **_theory_fields(GENRE_IDEAS[k])) for k in GENRE_PRESETS}` style merge works with no key mismatches).

**Solo preset excerpt to migrate verbatim** (`scripts/generate_cello_dark_ostinato.py` lines 27-46, feel text stays Russian per CONTEXT.md):
```python
"dark_trip_hop": GenrePreset(
    name="dark_trip_hop",
    tempo_bpm=72,
    key_tonic="C",
    key_mode="minor",
    meter_signature="4/4",
    velocity=76,
    rhythm=[0.5] * 8,
    bars=[
        ["C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"],
        # ... 7 more bars
    ],
    feel="темный, сексуальный, петлевой trip-hop groove",
),
```

**Matching theory data to merge in** (`scripts/harmony_advisor.py` lines 8-22):
```python
"dark_trip_hop": {
    "progressions": [
        "i - VI - v - i: C minor -> Ab -> G minor -> C minor. Работает, потому что низкая тоника держит гипноз...",
        "i - bVII - VI - V: C minor -> Bb -> Ab -> G. Работает как спуск вниз...",
    ],
    "modulations": [
        "Через общий аккорд: C minor -> Eb major. ...",
        "Через доминанту: C minor -> G minor. ...",
    ],
    "mood": [   # maps to MoodPreset.mood_tips
        "Загадочность: добавь b2 или натуральную 7 ступень...",
        "Секси-эффект: оставь устойчивый низкий пульс...",
        "Драйв: укороти длительности до шестнадцатых...",
    ],
},
```

**Duet preset shape 1 — `sexy_duet`** (`scripts/generate_sexy_duet_loop.py` lines 44-69, 76 BPM, D minor, cello_rhythm has 7 elements, violin_rhythm has 5 elements):
```python
cello_rhythm = [0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5]
violin_rhythm = [1.0, 0.5, 0.5, 1.0, 1.0]

cello_bars = [
    ["D2", "A2", "D3", "C3", "A2", "F2", "A2"],
    # ... 7 more bars
]
violin_bars = [
    ["A4", "C5", "D5", "F5", "E5"],
    # ... 7 more bars
]
```
Velocities: cello=82, violin=70 (from `add_measure(cello, ..., velocity=82)` / `add_measure(violin, ..., velocity=70)`, lines 72/75).

**Duet preset shape 2 — `simple_sexy_duet`** (`scripts/generate_simple_sexy_duet_loop.py` lines 44-68, 64 BPM, D minor, single shared `rhythm = [1.0, 1.0, 1.0, 1.0]` for both parts — still store as `duet_rhythm={"cello": [...], "violin": [...]}` per CONTEXT.md discretion guidance, even though equal). Velocities: cello=68, violin=58.

**IMPORTANT — known pre-existing out-of-range note:** `cello_bars` row 2 (and repeats) contains `"A1"` (MIDI 33), below the locked `CELLO_MIN_MIDI = 36` (C2) floor (RESEARCH.md Code Examples + Assumptions Log A3). Migrate verbatim — do NOT silently fix. Flag with a code comment in `mood_presets.py` at this data point, e.g. `# NOTE: "A1" (MIDI 33) is below the C2 validator floor — pre-existing in source script, migrated verbatim, not yet validated at generation time (Phase 2 concern).`

**Duet preset shape 3 — `dorian_sexy_duet`** (`scripts/generate_dorian_sexy_duet_loop.py` lines 45-68, 88 BPM, D minor/Dorian, cello_rhythm has 7 elements, violin_rhythm has 6 elements). Velocities: cello=74, violin=62.

**Recommended registry entry naming** (Claude's discretion per CONTEXT.md, suggested for planner): `sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet` as three separate `MoodPreset` dict keys in the same `MOOD_PRESETS` registry as the 4 solo moods (7 total entries) — matches RESEARCH.md's Pitfall 3 recommendation.

---

### `core/presets/registry.py` (service, CRUD read-only)

**Analog:** `scripts/generate_cello_dark_ostinato.py` — the existing lookup/list pattern (lines 155-170):
```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cello ostinato MusicXML and MIDI files.")
    parser.add_argument("--genre", choices=sorted(GENRE_PRESETS), default="dark_trip_hop")
    parser.add_argument("--output-name", default=None, help="File name without extension.")
    parser.add_argument("--list-genres", action="store_true")
    return parser.parse_args()


def main() -> None:
    environment.UserSettings()["warnings"] = 0
    args = parse_args()

    if args.list_genres:
        for preset in GENRE_PRESETS.values():
            print(f"{preset.name}: {preset.feel}")
        return

    preset = GENRE_PRESETS[args.genre]
```
**Pattern to extract (CLI/argparse stripped since `core/` must never import `argparse`):** the two operations worth wrapping as registry helpers are (1) `sorted(GENRE_PRESETS)` → `list_presets() -> list[str]`, and (2) `GENRE_PRESETS[name]` → `get_preset(name: str) -> MoodPreset` (raise `KeyError` with a clear message on miss, matching the dict's natural `KeyError` rather than inventing a new exception type — no existing script wraps this lookup in a try/except, so keep it simple).

---

### `core/engine/validators.py` (utility, request-response)

**No analog in `scripts/`** — none of the 5 scripts perform validation; they trust hardcoded data. Use the verified reference implementation from RESEARCH.md (cross-checked live against music21 10.5.0 in the research session) and PITFALLS.md:

```python
# Source: RESEARCH.md "Code Examples" + "Pattern 2", verified live against music21 10.5.0
from music21 import pitch as m21pitch
from music21 import meter as m21meter

CELLO_MIN_MIDI = 36   # C2 — verified: pitch.Pitch("C2").midi == 36
CELLO_MAX_MIDI_DEFAULT = 74   # D5 — verified: pitch.Pitch("D5").midi == 74
CELLO_MAX_MIDI_EXTENDED = 84  # C6 — verified: pitch.Pitch("C6").midi == 84

def validate_pitch(pitch_name: str, extended: bool = False) -> None:
    p = m21pitch.Pitch(pitch_name)
    max_midi = CELLO_MAX_MIDI_EXTENDED if extended else CELLO_MAX_MIDI_DEFAULT
    if not (CELLO_MIN_MIDI <= p.midi <= max_midi):
        raise ValueError(
            f"Pitch {pitch_name} (MIDI {p.midi}) is outside playable cello range "
            f"({CELLO_MIN_MIDI}-{max_midi})."
        )

def validate_bar_duration(rhythm: list[float], meter_signature: str, tolerance: float = 1e-9) -> None:
    ts = m21meter.TimeSignature(meter_signature)
    expected_ql = ts.barDuration.quarterLength   # verified live: 4/4 -> 4.0, 3/4 -> 3.0
    actual_ql = sum(rhythm)
    if abs(actual_ql - expected_ql) > tolerance:
        raise ValueError(
            f"Bar duration {actual_ql} != {expected_ql} for meter {meter_signature}."
        )
```
**Import convention to match existing scripts** (all 5 use `from music21 import <submodule>` style, e.g. `scripts/generate_cello_dark_ostinato.py` line 7: `from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo`) — but validators only need `pitch` and `meter`, so import narrowly (`from music21 import meter, pitch`), do not import unused submodules like `instrument`/`clef`/`tempo` the scripts use for score-building.

**Error style to match:** all raised errors are `ValueError` with an f-string human-readable message — no custom exception classes exist anywhere in the codebase; do not introduce one.

---

### `scripts/*.py` (modified — data source swap only)

**Analog:** each script's own current preset-dict definition, replaced by an import from `core.presets`.

**Pattern for `generate_cello_dark_ostinato.py`:** replace the inline `GENRE_PRESETS: dict[str, GenrePreset] = {...}` block (lines 26-107) with:
```python
from core.presets.registry import list_presets, get_preset
# GENRE_PRESETS dict body removed; downstream code (`GENRE_PRESETS[args.genre]`,
# `sorted(GENRE_PRESETS)`, `GENRE_PRESETS.values()`) becomes `get_preset(args.genre)`,
# `sorted(list_presets())`, `[get_preset(n) for n in list_presets()]` respectively.
```
The `GenrePreset` dataclass itself (lines 13-23) is superseded by `core.models.MoodPreset` — remove the local class, import `MoodPreset` if the script needs the type for annotations (it likely doesn't, since `build_cello_ostinato(preset: GenrePreset)` at line 110 just needs duck-typed attribute access that `MoodPreset` also satisfies).

**Everything else in each script is UNCHANGED this phase** (per CONTEXT.md: "full engine refactor to thin wrappers is Phase 2") — `build_cello_ostinato`, `export_score`, `parse_args`, `main` all stay as-is, only their preset data source changes.

**Duet scripts' analogous swap** (`generate_sexy_duet_loop.py`, `generate_simple_sexy_duet_loop.py`, `generate_dorian_sexy_duet_loop.py`): each currently has hardcoded `cello_rhythm`/`violin_rhythm`/`cello_bars`/`violin_bars` module-level literals inside `build_score()` (e.g. `generate_sexy_duet_loop.py` lines 44-69). These get replaced by a `get_preset("sexy_duet")` call at the top of `build_score()`, reading `.duet_rhythm["cello"]`, `.duet_bars["cello"]`, etc. — same "swap data source, keep logic" pattern as the ostinato script.

---

### `tests/` scaffold (test)

**No analog** — first pytest infrastructure in this repo. No `conftest.py` or test files exist to pattern-match against. Follow plain pytest stdlib conventions (no project-specific test helper library found in a repo-wide search — none exists yet).

**Import boundary test target pattern** (from RESEARCH.md Pattern 3, `.planning/research/ARCHITECTURE.md`-aligned):
```python
# tests/test_import_boundary.py — verifies PLAT-03 / core import-boundary rule
import ast
from pathlib import Path

FORBIDDEN = {"streamlit", "argparse"}

def test_core_has_no_forbidden_imports():
    core_root = Path(__file__).resolve().parents[1] / "core"
    for py_file in core_root.rglob("*.py"):
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = {node.module.split(".")[0]}
            else:
                continue
            assert not (names & FORBIDDEN), f"{py_file} imports forbidden module(s): {names & FORBIDDEN}"
```

---

## Shared Patterns

### Dataclass style
**Source:** `scripts/generate_cello_dark_ostinato.py` lines 1-23 (only existing dataclass in the codebase)
**Apply to:** All of `core/models.py`
```python
from __future__ import annotations
from dataclasses import dataclass
# frozen=True for immutable preset/theory data; plain @dataclass for request/variant/trace objects that may be constructed incrementally
```

### music21 import style
**Source:** identical across all 5 scripts, e.g. `scripts/generate_cello_dark_ostinato.py` line 7
**Apply to:** `core/engine/validators.py` (narrowed to only what's needed)
```python
from music21 import clef, duration, environment, instrument, key, meter, midi, note, stream, tempo
# validators.py only needs: from music21 import meter, pitch
```

### Error handling
**Source:** No existing try/except pattern in any script (they crash on bad input today — no error handling precedent exists). RESEARCH.md/PITFALLS.md establishes the new precedent for this phase.
**Apply to:** `core/engine/validators.py` only (this phase does not wire validators into script call paths — that's Phase 2 per CONTEXT.md Deferred Ideas)
```python
raise ValueError(f"<human readable message with the offending value and the valid range/expected value>")
```

### Path handling
**Source:** identical across all 5 scripts, e.g. `scripts/generate_cello_dark_ostinato.py` line 10: `PROJECT_ROOT = Path(__file__).resolve().parents[1]`
**Apply to:** Not needed in `core/` this phase (no file I/O in models/validators/registry — pure data + pure functions). Relevant only if `tests/conftest.py` needs a `PROJECT_ROOT`-style fixture to locate `scores/` for any regression-script invocation.

### CLI entrypoint shape (for reference only — NOT part of `core/`)
**Source:** identical `argparse` + `main()` + `if __name__ == "__main__":` shape across all 5 scripts
**Apply to:** Nothing in this phase — explicitly excluded from `core/` per the import-boundary rule; scripts keep this shape unchanged.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `core/engine/validators.py` | utility | request-response | No validation logic exists anywhere in the current codebase; use PITFALLS.md/RESEARCH.md's verified reference implementation as the pattern source instead of a codebase analog |
| `tests/conftest.py`, `tests/test_*.py` (all 4 files) | test | varies | No `tests/` directory or pytest config exists yet in this repo; this phase establishes the first test infrastructure — follow stdlib pytest conventions, no project precedent to copy |

## Metadata

**Analog search scope:** `scripts/` (only application code directory besides the not-yet-existing `core/`/`app/`/`tests/`); confirmed via `find` that no `core/`, `tests/`, `.claude/skills/`, or `.agents/skills/` directories exist yet in this repo.
**Files scanned:** 5 (all scripts in `scripts/`, each read in full — none exceeded 2,000 lines, largest is `harmony_advisor.py` at 8.5KB / 107 lines)
**Pattern extraction date:** 2026-07-04
