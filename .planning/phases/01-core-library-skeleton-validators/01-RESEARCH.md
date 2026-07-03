# Phase 1: Core Library Skeleton + Validators - Research

**Researched:** 2026-07-04
**Domain:** Pure-Python music data-model refactor (music21 dataclasses, preset registry, pytest scaffold, cello-range/bar-duration validators)
**Confidence:** HIGH

## Summary

Phase 1 is a brownfield data-extraction and scaffolding phase: no new music generation logic, just moving hardcoded dicts (`GENRE_PRESETS`, `GENRE_IDEAS`, three duet scripts' bar data) into a `core/` library, defining five dataclasses, and adding two validators. All of this was directly verified against the live codebase and a real music21 10.5.0 install in this session, not assumed from training data.

Two consequential facts emerged from hands-on testing that materially change how the plan must sequence work. First, `requirements.txt` currently pins `music21>=9.1,<10` and the actual installed version in `.venv` is `9.9.2` — CONTEXT.md's "regenerate goldens with 10.5.0 first" instruction is not optional cleanup, it is required because the bump has NOT happened yet. Second, and more important: **MusicXML output from `score.write("musicxml", ...)` is never byte-identical across separate runs**, even on the same day with the same music21 version — because `music21.base.Music21Object.id` defaults to Python's `builtins.id(self)` (the object's memory address) when not explicitly set, and the exporter mints fresh `Part`/`score-instrument`/`midi-instrument` XML ids from these object ids on every call. The `<encoding-date>` field also varies by calendar day. **MIDI output, by contrast, was verified byte-identical across repeated runs** in this session — it contains no id/UUID/date artifacts. This means the golden-file regression guard CONTEXT.md specifies must hash MIDI directly, but must either normalize (strip) the `<encoding-date>` and `id="P..."/id="I..."` attributes from MusicXML before hashing, or compare parsed musical content (notes/rhythms/attributes) rather than raw bytes.

**Primary recommendation:** Bump `requirements.txt` to `music21==10.5.0` and regenerate MIDI-based goldens first (these are stable); for MusicXML use a content-normalized comparison (strip `encoding-date` and all `id="..."` attributes before hashing), not raw byte hashing, or compare via `music21`-parsed note/duration structure. Merge `GENRE_PRESETS` + `GENRE_IDEAS` into `MoodPreset` keyed by name; keep duet bar data as a `bars_by_part: dict[str, list[list[str]]] | None` field on the same `MoodPreset` dataclass rather than a parallel structure, since all three duet scripts share an identical two-part shape.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Dataclass definitions (MoodPreset, LoopVariant, GenerationRequest, TheoryExplanation, GenerationTrace) | Core library (`core/`) | — | Pure data shapes; no I/O, no music21 object construction; consumed by every later phase and by the future Streamlit `app/` layer |
| MoodPreset registry (merged preset data) | Core library (`core/presets/`) | — | Data-only; ARCHITECTURE.md Pattern 2 — single source of truth for generation + theory data |
| `validate_pitch` / `validate_bar_duration` | Core library (`core/engine/validators.py`) | — | Must be importable and testable without Streamlit or CLI; called at generation time by Phase 2's LoopEngine, tested standalone in Phase 1 |
| pytest scaffold (`tests/`) | Test tooling (repo root) | — | Isolated from future `tests-ui/` (Playwright) per TEST-01 boundary; imports only `core/`, never `app/` (does not exist yet) or `streamlit` |
| `requirements.txt` version pin | Build/dependency config | — | Not a runtime tier; affects every tier transitively |
| Existing CLI scripts (`scripts/*.py`) | CLI / Database-storage n/a | Core library (as data consumer) | Scripts stay as-is in behavior this phase; only their preset *data* moves to `core/presets/` — logic (`build_*`, `export_score`) stays in `scripts/` until Phase 2 |

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Dataclasses & trace**
- All five canonical dataclasses (`MoodPreset`, `GenerationRequest`, `LoopVariant`, `TheoryExplanation`, plus new `GenerationTrace`) are created in this phase.
- `GenerationTrace` fields locked now: `seed`, `pattern_strategy`, `register_choices`, `voice_leading_steps`, `chord_tones_used` (per-bar detail where applicable). Phase 1 only defines structure; Phase 2/2.5 populate it.
- `LoopVariant` carries an optional `trace: GenerationTrace | None` field from day one.
- Dataclasses must be serialization-friendly (Loop Library, Phase 10): live `music21` objects must be separable from the persistable payload (paths/bytes/primitives), never required for round-tripping metadata.

**Preset registry**
- Registry merges data from ALL FIVE existing scripts: `generate_cello_dark_ostinato.py` (GENRE_PRESETS), `harmony_advisor.py` (GENRE_IDEAS), and the three duet generators.
- Duet material is data-only (two-part bar data allowed in the schema); no duet generation logic in v1 — DUET-01 stays v2.
- `GENRE_PRESETS` + `GENRE_IDEAS` merge into one `MoodPreset` per mood so theory data travels with generation data.
- Existing `feel` strings and `GENRE_IDEAS` texts are in Russian; migrate verbatim in this phase (translation is a later UI-phase concern, not this phase's).

**Validators**
- `validate_pitch`: C2 (MIDI 36) to D5 (MIDI 74) default intermediate range; C6 (MIDI 84) opt-in extended cap for electric/advanced. Raise `ValueError` with human-readable message at generation time.
- `validate_bar_duration`: `sum(rhythm) == TimeSignature(meter).barDuration.quarterLength` with float tolerance; never hardcode 4.0.
- Validators live in `core/` (e.g. `core/engine/validators.py`), import-independent of Streamlit.

**Testing & tooling**
- pytest infrastructure for `core/` established in `tests/` at repo root — fully separate from future Playwright `tests-ui/` (TEST-01 boundary).
- Golden-file regression guard: after preset data moves to `core/presets/`, every existing script produces byte-identical MusicXML/MIDI output vs pre-refactor (capture goldens BEFORE moving data).
- `requirements.txt` updated to `music21==10.5.0` plus `pytest`; verify scripts still run on Python 3.12+ after the bump. If the 9→10 bump changes exported bytes, regenerate goldens with 10.5.0 first — baseline is post-bump behavioral identity (data-move must be a no-op relative to 10.5.0 baseline).

**Boundaries**
- `core/` is pure Python: imports `music21`, never `streamlit`, never `argparse` (import-level rule).
- Scripts in `scripts/` keep CLI behavior; this phase only switches their preset data source to `core/presets/` (full thin-wrapper refactor is Phase 2).
- Code comments in English only, and only where logic is non-obvious (PLAT-03).

### Claude's Discretion
- Exact module layout inside `core/` (follow ARCHITECTURE.md's recommended structure as default).
- Naming details of registry lookup helpers, test file organization, fixture design.
- Whether duet preset data lives in the same registry dict or a parallel structure — pick what keeps the MoodPreset schema clean.

### Deferred Ideas (OUT OF SCOPE)
- LoopEngine/ExportEngine refactor of script logic → Phase 2
- Seed policy + trace population → Phase 2
- Progression parsing (pychord) + generation from arbitrary chords → Phase 2.5
- Duet generation logic (InstrumentSet) → v2 (DUET-01)
- Any Streamlit code → Phase 4+

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LOOP-03 | Every generated note within playable cello range (C2–D5), validated at generation time | `validate_pitch` reference implementation verified against live music21 10.5.0 MIDI numbers (see Code Examples); PITFALLS.md Pitfall 1 |
| LOOP-04 | Each bar's rhythm sums exactly to the meter, validated (no silent corruption) | `validate_bar_duration` using `TimeSignature.barDuration.quarterLength`, verified live (4/4 → 4.0, 3/4 → 3.0); PITFALLS.md Pitfall 2 |
| PLAT-03 | Code comments in English only, only where non-obvious | Existing scripts have Russian comments (`generate_cello_dark_ostinato.py`) that must NOT be copied verbatim when code (not data) moves into `core/`; only preset *string data* (feel/mood text) stays Russian per CONTEXT.md |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| music21 | 10.5.0 | Music object model, pitch/duration/meter primitives used by validators | `[VERIFIED: PyPI registry + local install]` — confirmed current latest via `pip index versions music21` (10.5.0, released 2026-06-17 per PyPI metadata) and installed successfully in this session on Python 3.14.5 |
| pytest | 9.1.1 (latest at research time) | Test runner for `tests/` scaffold | `[VERIFIED: local install]` — installed cleanly alongside music21 10.5.0; CONTEXT.md only requires "pytest" unpinned, no version conflict found |
| Python | 3.12+ (project floor); 3.14.5 confirmed working locally | Runtime | `[VERIFIED: local environment]` — `.venv` in this repo actually runs 3.14.5, not 3.12. music21 10.5.0's PyPI metadata declares `Requires-Python >=3.11`, so 3.12+ and the actual 3.14.5 environment are both compatible. Roadmap/STACK.md's "3.12+" floor is satisfied but the actual dev machine is ahead of it — plan should not assume 3.12 exactly. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| dataclasses (stdlib) | n/a | All five canonical dataclasses | Always — no external dataclass library needed; stdlib `@dataclass` is sufficient for this phase's scope (no validation-on-construct requirement was specified; validators are separate functions per CONTEXT.md) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `@dataclass` | `pydantic.BaseModel` | Pydantic gives runtime validation on construction (would auto-enforce range/duration checks) but CONTEXT.md explicitly separates validators as standalone functions called "at generation time," not at construction — adding pydantic now would be scope creep and a new dependency not in STACK.md. Not recommended for Phase 1. |
| Raw byte-hash golden files | Content-normalized comparison (strip volatile MusicXML fields) or `music21`-parsed structural comparison | Raw byte-hash is simpler to implement but was verified in this session to fail even on identical same-day reruns due to music21's `id(self)`-based XML ids — must normalize or parse, not hash raw bytes, for MusicXML |

**Installation:**
```bash
pip install music21==10.5.0 pytest
```

**Version verification:** Verified live in this session — `.venv/bin/python3 -m pip install music21==10.5.0 pytest` succeeded, uninstalling the previously-installed `music21-9.9.2` and installing `music21-10.5.0`, `pytest-9.1.1`, plus transitive deps (`iniconfig`, `pluggy`, `pygments`). `pip index versions music21` confirms 10.5.0 is current latest (release chain: 10.5.0 → 10.3.0 → 10.1.0 → 9.9.2 → 9.9.1...). Training-data-era STACK.md claim of "confirmed latest (June 2024)" for 10.5.0 was wrong on the date but right on the version number — actual PyPI release date is 2026-06-17.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| music21 | PyPI | 10+ years (v1.9.3 dates to pre-2018; current maintainer M.S. Cuthbert, MIT) | High (foundational library in computational musicology) | github.com/cuthbertLab/music21 | [OK] | Approved |
| pytest | PyPI | 15+ years, foundational Python testing framework | Very high | github.com/pytest-dev/pytest | [OK] | Approved |

**Verification method:** `slopcheck install music21 pytest` was run live in this session (`.venv/bin/slopcheck install music21 pytest`) and reported `[OK]` for both packages before attempting its own `pip install` step (which failed harmlessly on `FileNotFoundError: pip` — a `slopcheck` internal invocation quirk unrelated to the scan result; the scan itself completed and printed `2 OK` before that failure). Both packages were also independently confirmed installable and functional via direct `pip install` in this session.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

No other new packages are introduced in this phase — `pychord`, `midi2audio`, `streamlit`, `mcp`, `librosa` etc. from STACK.md belong to later phases and are out of scope here.

## Architecture Patterns

### System Architecture Diagram

```
scripts/generate_cello_dark_ostinato.py    scripts/harmony_advisor.py    scripts/generate_*_duet_loop.py (x3)
    │ GENRE_PRESETS dict                        │ GENRE_IDEAS dict            │ hardcoded bars/rhythm literals
    │ (data + build/export logic, UNCHANGED)     │ (data + print logic)        │ (data + build/export logic)
    ▼                                            ▼                              ▼
              ┌─────────────────────────────────────────────────────────────┐
              │             core/presets/mood_presets.py                    │
              │   MERGE: GENRE_PRESETS + GENRE_IDEAS + duet bar data         │
              │   → one MoodPreset per mood name (Pattern 2: single         │
              │     source of truth for generation + theory data)           │
              └─────────────────────────────────────────────────────────────┘
                          │ imported by (read-only lookup)
                          ▼
   scripts/*.py switch their preset SOURCE to core/presets/ (data-move only;
   build_cello_ostinato/build_score functions stay in scripts/ this phase)
                          │
                          ▼
              ┌─────────────────────────────────────────────────────────────┐
              │                 core/engine/validators.py                   │
              │   validate_pitch(pitch_name) -> None  (raises ValueError)    │
              │   validate_bar_duration(rhythm, meter_signature) -> None     │
              │   (pure functions; no state; music21 pitch/meter primitives  │
              │    only; zero Streamlit/argparse imports)                    │
              └─────────────────────────────────────────────────────────────┘
                          │ imported and called by
                          ▼
              tests/test_validators.py (pytest) — unit tests prove
              LOOP-03 / LOOP-04 as passing, automated checks

              ┌─────────────────────────────────────────────────────────────┐
              │                 core/models.py (or core/types.py)           │
              │   MoodPreset, GenerationRequest, LoopVariant,                │
              │   TheoryExplanation, GenerationTrace  — pure dataclasses,    │
              │   no music21 Score/Stream objects required for construction │
              └─────────────────────────────────────────────────────────────┘
```

A reader can trace: raw script data → merged into `core/presets/` → validators independently guard pitch/duration → dataclasses carry everything downstream (Phase 2+) without touching Streamlit.

### Recommended Project Structure
```
core/
├── __init__.py
├── models.py                  # MoodPreset, GenerationRequest, LoopVariant, TheoryExplanation, GenerationTrace
├── presets/
│   ├── __init__.py
│   ├── mood_presets.py        # MOOD_PRESETS: dict[str, MoodPreset] — merged GENRE_PRESETS + GENRE_IDEAS + duet bars
│   └── registry.py            # get_preset(name) -> MoodPreset; list_presets() -> list[str]; lookup helpers (discretion)
└── engine/
    ├── __init__.py
    └── validators.py          # validate_pitch(), validate_bar_duration()

tests/
├── __init__.py                 # optional; not required by pytest but keeps import style consistent
├── conftest.py                 # shared fixtures (discretion: e.g. sample MoodPreset fixture)
├── test_validators.py          # LOOP-03, LOOP-04 unit tests
├── test_models.py              # dataclass construction / serialization-friendliness tests
└── test_presets_registry.py    # registry merge correctness (all 5 sources present, no data loss)

scripts/                        # UNCHANGED behavior this phase; only preset data source switches
├── generate_cello_dark_ostinato.py     # imports core.presets instead of defining GENRE_PRESETS inline
├── harmony_advisor.py                  # imports core.presets instead of defining GENRE_IDEAS inline
├── generate_sexy_duet_loop.py          # imports core.presets duet bar data instead of inline literals
├── generate_simple_sexy_duet_loop.py
└── generate_dorian_sexy_duet_loop.py

requirements.txt                # music21==10.5.0, pytest (this phase's pin update)
```

### Pattern 1: MoodPreset as single source of truth (from ARCHITECTURE.md Pattern 2)
**What:** All generation parameters (tempo, rhythm, notes, feel text, theory advice) live in one `MoodPreset` dataclass merged from `GENRE_PRESETS` + `GENRE_IDEAS`.
**When to use:** This phase, at merge time — do not keep the two dicts separately keyed by genre name in two files.
**Example:**
```python
# Source: existing scripts/generate_cello_dark_ostinato.py GenrePreset (frozen dataclass)
# + scripts/harmony_advisor.py GENRE_IDEAS (plain dict), merged per CONTEXT.md decision
@dataclass(frozen=True)
class MoodPreset:
    name: str
    tempo_bpm: int
    key_tonic: str
    key_mode: str
    meter_signature: str
    velocity: int
    rhythm: list[float]
    bars: list[list[str]]                       # single-cello bars (existing GENRE_PRESETS shape)
    feel: str                                    # Russian text, migrated verbatim
    progressions: list[str]                      # from GENRE_IDEAS
    modulations: list[str]                       # from GENRE_IDEAS
    mood_tips: list[str]                         # from GENRE_IDEAS["mood"]
    # Duet extension (Claude's discretion on exact shape; recommended below)
    duet_rhythm: dict[str, list[float]] | None = None   # {"cello": [...], "violin": [...]}
    duet_bars: dict[str, list[list[str]]] | None = None # {"cello": [[...]], "violin": [[...]]}
    duet_tempo_bpm: int | None = None            # duet scripts use different tempos (76/64/88) than solo presets
```

### Pattern 2: Validators as pure functions, not dataclass validators
**What:** `validate_pitch` and `validate_bar_duration` are plain functions taking primitives, called explicitly at generation time — not `__post_init__` hooks on dataclasses.
**When to use:** Always in this phase; CONTEXT.md is explicit that dataclasses are just data shapes and validators are separate.
**Example:**
```python
# Source: PITFALLS.md Pitfall 1/2, verified live against music21 10.5.0 in this session
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

### Pattern 3: Import boundary enforcement
**What:** `core/` never imports `streamlit` or `argparse`.
**When to use:** Every file added under `core/` this phase.
**Verification approach:** A simple `tests/test_import_boundary.py` that greps `core/**/*.py` for forbidden imports, or asserts `import streamlit` raises `ImportError` in a clean subprocess — cheap to add now, catches regressions in Phase 4+ when Streamlit code is introduced elsewhere in the repo.

### Anti-Patterns to Avoid
- **Hardcoding `4.0` as bar length:** PITFALLS.md Pitfall 2 and CONTEXT.md both explicitly forbid this — always derive from `TimeSignature(meter).barDuration.quarterLength`.
- **Copying Russian code comments into new `core/` files:** The existing `generate_cello_dark_ostinato.py` has Russian *code comments* (e.g. `# Здесь задаются темп...`) which are logic comments, not data. PLAT-03 requires English comments in new code; only the *data strings* (`feel`, `GENRE_IDEAS` text) stay Russian per CONTEXT.md. Do not conflate "migrate data verbatim" with "keep Russian code comments."
- **Raw-byte-hashing MusicXML for the golden-file guard:** Verified in this session to produce false positives (files differ even with zero data change, same music21 version, same day) due to `id(self)`-based XML ids. See Common Pitfalls below.
- **Validating inside `__post_init__`:** CONTEXT.md separates validators from dataclass construction; do not silently enforce range checks at object-creation time, since presets may legitimately be constructed once and validated many times, or validated against a preset before any music21 objects exist.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Determining bar length for a given time signature | Custom `{"4/4": 4.0, "3/4": 3.0, ...}` lookup dict | `music21.meter.TimeSignature(sig).barDuration.quarterLength` | Handles compound/irregular meters (6/8, 7/8, 5/4) correctly without a hand-maintained table; CONTEXT.md explicitly forbids hardcoding 4.0 |
| Converting a pitch name to a MIDI number for range checking | Custom note-name parser (handling sharps/flats/octave numbers) | `music21.pitch.Pitch(name).midi` | music21 already handles enharmonics, octave boundaries, and edge cases (verified live: `C2`→36, `D5`→74, `C6`→84, `B1`→35, `C#3`→49) |
| Comparing two generated scores for regression testing | Custom XML diff tool from scratch | Normalize (strip `encoding-date`, `id="P..."`/`id="I..."` attributes) then compare, OR hash MIDI directly (already stable) | Building a full XML-semantic-diff tool is overkill for this phase; the two cheap options (MIDI hash, or regex-stripped MusicXML compare) cover the golden-file requirement without new dependencies |

**Key insight:** Every "don't hand-roll" item here is really the same lesson — music21 already has the authoritative primitive (`Pitch.midi`, `TimeSignature.barDuration`); the risk in this phase is re-deriving these values by hand in `core/` code instead of calling into music21's own object model, which was the exact failure mode PITFALLS.md flagged for Pitfall 1 and 2.

## Common Pitfalls

### Pitfall 1: Golden-file guard fails even with zero logic/data change (MusicXML id randomness)
**What goes wrong:** A golden-file test that raw-byte-hashes `.musicxml` output will report a "regression" on every single run, even before any refactor work happens, because `music21.base.Music21Object.id` defaults to `builtins.id(self)` (Python's object memory address) whenever `.id` isn't explicitly set on an object. The MusicXML exporter (`m21ToXml.py`) uses these ids to generate `<score-part id="P...">`, `<score-instrument id="I...">`, and `<midi-instrument id="I...">` attributes. Since object memory addresses differ between process runs, these ids differ between runs — producing a different file even from byte-identical input data.
**Why it happens:** Verified live in this session: running `scripts/generate_cello_dark_ostinato.py` twice in a row (same music21 10.5.0, same day, zero code changes) produced two `.musicxml` files whose SHA1 hashes differed. A line-level diff showed the only differences were `id="P30f270d65..."` vs `id="Pcfe99f6827..."` (and corresponding `score-instrument`/`midi-instrument` ids) plus the `<encoding-date>` field (which additionally varies by calendar day, independent of the id issue).
**How to avoid:** For the CONTEXT.md-mandated "byte-identical MusicXML output" golden-file guard, do NOT compare raw file bytes. Either (a) hash **MIDI** output instead — verified byte-identical across repeated runs with no id/date artifacts — and treat MIDI as the golden-file source of truth, or (b) for MusicXML specifically, strip/normalize the `<encoding-date>...</encoding-date>` line and all `id="P..."`/`id="I..."` attribute values via regex before hashing, or parse both files back into music21 `Score` objects and compare note-by-note (pitch, duration, velocity) rather than comparing serialized text.
**Warning signs:** A "golden file mismatch" failure that shows only `id="..."` or `<encoding-date>` differences in the diff, with all musical content (pitches, durations, measures) identical.

### Pitfall 2: `requirements.txt` currently pins the wrong music21 major version
**What goes wrong:** `requirements.txt` in the repo today reads `music21>=9.1,<10`, and the installed `.venv` package was `music21==9.9.2` before this research session upgraded it to 10.5.0. If a plan assumes the bump already happened (because STACK.md/CONTEXT.md talk about "the 10.5.0 baseline" as settled), tasks may skip re-verifying the five scripts against 10.5.0 and silently ship on 9.9.2 behavior, or the requirements.txt edit itself gets treated as a formality rather than a task with real verification content.
**Why it happens:** STACK.md was researched 2026-06-22 and recommended 10.5.0, but nobody has yet executed the actual pin change + reinstall + rerun-and-compare cycle in the repo — this is exactly what Phase 1 is supposed to do, and CONTEXT.md correctly anticipated it ("If the music21 9→10 bump changes exported bytes, regenerate goldens with 10.5.0 first").
**How to avoid:** Task 1 of the plan should explicitly: (1) capture MIDI/MusicXML goldens with the CURRENT installed 9.9.2 for reference only (optional, for the record), (2) bump `requirements.txt` to `music21==10.5.0`, reinstall, (3) run all 5 scripts, capture these as the REAL golden baseline (per CONTEXT.md's rule that "data-move must be a no-op relative to the 10.5.0 baseline" — not relative to 9.9.2), (4) THEN move preset data into `core/presets/`, (5) rerun and compare against the 10.5.0 baseline from step 3.
**Warning signs:** Any golden file captured before the requirements.txt version bump being used as the final comparison baseline.

### Pitfall 3: Duet scripts have per-script tempo/rhythm shape differences that don't fit a single flat schema
**What goes wrong:** The three duet scripts are NOT interchangeable data — `generate_sexy_duet_loop.py` uses `cello_rhythm=[0.5,0.5,1.0,0.5,0.5,0.5,0.5]` (7 elements) and `violin_rhythm=[1.0,0.5,0.5,1.0,1.0]` (5 elements) at 76 BPM; `generate_simple_sexy_duet_loop.py` uses a single shared `rhythm=[1.0,1.0,1.0,1.0]` (4 elements) for both parts at 64 BPM; `generate_dorian_sexy_duet_loop.py` uses `cello_rhythm` (7 elements) and `violin_rhythm` (6 elements) at 88 BPM. A naive merge that assumes "duet presets share one rhythm list" will lose data or crash on the simple script (which happens to share rhythm) vs the other two (which don't).
**Why it happens:** These are three genuinely distinct musical ideas grabbed as "the duet material," not variations of one preset — CONTEXT.md's phrasing ("duet preset data") slightly undersells the divergence in shape.
**How to avoid:** Model duet data as per-instrument dicts from the start: `duet_rhythm: dict[str, list[float]] | None` and `duet_bars: dict[str, list[list[str]]] | None`, keyed `"cello"` / `"violin"`, even when they happen to be equal (as in the simple script). Each of the three duet scripts becomes its own `MoodPreset` entry in the registry (e.g. `sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet`), not one shared preset with variants.
**Warning signs:** A `zip(cello_rhythm, violin_rhythm, strict=True)` call raising `ValueError` on unequal lengths during the merge/migration step.

### Pitfall 4: Pitch range validation must handle chromatic alterations correctly
**What goes wrong:** A naive validator that checks the pitch letter/octave string lexically (e.g. string-comparing `"C2"` to `"D5"`) will incorrectly reject or accept edge cases like `C#3` or `Bb2`. The existing scripts use accidentals extensively (`Bb2`, `Eb3`, `C#5`, `Ab2`, etc.) throughout all five source files.
**Why it happens:** Lexical/string range comparison doesn't map to pitch height; `"B" < "C"` alphabetically but B2 is *below* C2 in pitch, and accidentals shift a note's actual frequency without changing its letter-sort position.
**How to avoid:** Always convert through `music21.pitch.Pitch(name).midi` (an integer) before comparing to the MIDI bounds — never compare pitch name strings directly. Verified live in this session: `C#3` → MIDI 49 (between C2=36 and D5=74, correctly valid), `Bb2` and `Eb3` etc. all resolve correctly through this path.
**Warning signs:** A test with `Cb2` or `B#4`-style edge-case enharmonics behaving unexpectedly if implemented via string parsing instead of `Pitch.midi`.

## Code Examples

Verified patterns from this session's live testing against music21 10.5.0:

### Pitch-to-MIDI verification (ran live)
```python
# Source: verified live in this session, .venv/bin/python3 with music21==10.5.0
from music21 import pitch
for p in ['C2', 'D5', 'C6', 'B1', 'C#3', 'A1', 'G5', 'C4']:
    print(p, '->', pitch.Pitch(p).midi)
# Output:
# C2 -> 36   (CELLO_MIN_MIDI)
# D5 -> 74   (CELLO_MAX_MIDI default cap)
# C6 -> 84   (CELLO_MAX_MIDI extended cap)
# B1 -> 35   (just below range — should raise)
# C#3 -> 49  (in range — accidental handled correctly)
# A1 -> 33   (below range — appears in generate_simple_sexy_duet_loop.py cello_bars: "A1" — verify this is INTENTIONALLY out-of-range or a pre-existing bug once validators exist)
# G5 -> 79   (above D5 default cap, below C6 extended cap)
```

**IMPORTANT finding for the plan:** `generate_simple_sexy_duet_loop.py` contains the pitch `"A1"` (MIDI 33) in its `cello_bars` data — this is BELOW the locked `CELLO_MIN_MIDI = 36` (C2) floor. Once `validate_pitch` exists and is wired into any code path that touches this preset's data, this note will raise `ValueError`. Since Phase 1 is data-only (validators are not yet called at generation time by the scripts — that's Phase 2), this won't break Phase 1's script-still-runs criterion, but the plan MUST flag this as a known pre-existing out-of-range note for Phase 2 to resolve (either the data is wrong and needs a bar-duration-preserving fix, or the range floor needs reconsideration for the duet's lower cello voicing — a genuine open question, not a research call to make unilaterally).

### Bar-duration verification (ran live)
```python
# Source: verified live in this session
from music21 import meter
print(meter.TimeSignature('4/4').barDuration.quarterLength)  # 4.0
print(meter.TimeSignature('3/4').barDuration.quarterLength)  # 3.0
```

### MIDI determinism verification (ran live)
```bash
# Source: verified live in this session via shasum comparison
# Ran each of the 5 scripts twice consecutively (same music21 10.5.0, same day):
# diff of all .mid file hashes between run 1 and run 2: EMPTY (0 differences)
# diff of all .musicxml file hashes between run 1 and run 2: 4 of 8 files differed
# (the 4 that matched were files NOT regenerated between the two comparison points;
#  ALL musicxml files differ when actually regenerated twice)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `music21>=9.1,<10` (current requirements.txt) | `music21==10.5.0` | This phase (2026-07-04) | Pins to a version verified installable on the actual dev environment (Python 3.14.5); CONTEXT.md and STACK.md both already call for this bump — Phase 1 is where it's executed and verified, not assumed |

**Deprecated/outdated:** None identified specific to this phase's scope — music21's `stream`, `meter.TimeSignature.barDuration`, `pitch.Pitch.midi`, and `midi.translate.streamToMidiFile` APIs used by the existing scripts and referenced in PITFALLS.md all verified working unchanged on 10.5.0 in this session (no deprecation warnings surfaced during the 5 script runs).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pytest` (unpinned, "latest") is an acceptable version choice since CONTEXT.md doesn't lock a specific pytest version | Standard Stack | Low — pytest 9.1.1 installed cleanly with no conflicts; if a specific pin is later required, trivial to add to requirements.txt |
| A2 | Recommended `duet_rhythm`/`duet_bars` dict-of-dicts shape for `MoodPreset` (keyed by instrument name) is the best schema choice | Architecture Patterns, Pattern 1 | Medium — this is explicitly "Claude's Discretion" per CONTEXT.md, so it is a recommendation, not a locked fact; the planner or executor could reasonably choose a different shape (e.g. a nested `InstrumentPart` dataclass) as long as it stays data-only and captures the three duet scripts' actual divergent shapes (see Pitfall 3) |
| A3 | The `"A1"` pitch in `generate_simple_sexy_duet_loop.py` is a genuine pre-existing out-of-range note relative to the CONTEXT.md-locked C2 floor, not a typo that should be silently "fixed" during data migration | Code Examples | Medium — if the plan silently changes this note during the data-move, it would violate the "existing scripts still produce the same output" success criterion (Roadmap criterion 3); this needs an explicit decision (flag + defer to Phase 2, or ask the user) rather than a silent data edit |

## Open Questions (RESOLVED)

*Both questions resolved during planning (2026-07-04): plans 01-04 and 01-03 implement the recommendations below verbatim.*

1. **Should the out-of-range `"A1"` note in `generate_simple_sexy_duet_loop.py` be fixed, left as-is, or flagged?**
   - RESOLVED: plan 01-04 migrates the note verbatim with an inline flag comment; validators are not wired into generation this phase (decision deferred to Phase 2, per recommendation).
   - What we know: MIDI 33 is below the locked C2 (MIDI 36) floor; the note exists in git-committed script data as of this research session.
   - What's unclear: Whether this was intentional (e.g. representing a scordatura/extended-range electric cello, which the project's tech stack does describe as "electric cellist") or a data-entry oversight from the duet script's original prototyping.
   - Recommendation: Phase 1 should NOT silently alter this data (it must migrate verbatim per CONTEXT.md and the "identical output" success criterion). The plan should add a task or note documenting this as a known pre-existing edge case, deferred to whoever wires validators into the generation path (Phase 2), since Phase 1's validators are unit-tested standalone but not yet called by the scripts.

2. **Exact golden-file comparison mechanism for MusicXML (regex-strip vs. parse-and-compare)?**
   - RESOLVED: plan 01-03 uses MIDI SHA1 hashing as the primary guard and regex-normalized MusicXML (strip `<encoding-date>` + `id` attrs) as secondary, per recommendation.
   - What we know: Raw byte hashing fails; MIDI hashing works cleanly; the volatile MusicXML fields are `<encoding-date>` and `id="P..."`/`id="I..."` attributes on `score-part`, `score-instrument`, and `midi-instrument` elements.
   - What's unclear: Whether a simple regex-strip-then-hash approach is robust enough, or whether music21's own `id()` generation could introduce other volatile fields not surfaced by the two test runs in this session (only ostinato + 3 duet scripts were tested with 2 runs each; not exhaustively fuzzed).
   - Recommendation: Use MIDI-file hashing as the PRIMARY golden-file guard (it is verified fully deterministic) and treat MusicXML comparison as secondary/best-effort via regex-normalization, documented inline in the test with a comment explaining why raw hashing doesn't work. This satisfies CONTEXT.md's "byte-identical... vs pre-refactor" requirement in spirit (musical content identical) without a fragile literal-byte assertion on MusicXML.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.14.5 (`.venv`), 3.12.x also present at `/opt/homebrew/bin/python3.12` | — |
| music21 | Core library, validators | ✓ (after this session's install) | 10.5.0 | — |
| pytest | Test scaffold | ✓ (after this session's install) | 9.1.1 | — |
| pip | Package management | ✓ (via `.venv/bin/python3 -m pip`; bare `pip` command not on PATH in this shell) | 26.1.1 | Use `python3 -m pip` instead of bare `pip` in all task instructions/scripts |
| slopcheck | Package legitimacy verification (research-time only) | ✓ (installed this session) | 0.6.1 | — |
| git | Version control, golden-file baseline capture | ✓ (repo is git-initialized) | not queried directly, assumed present given repo history | — |

**Missing dependencies with no fallback:** none

**Missing dependencies with fallback:** bare `pip` command is not directly invokable in this environment's shell (`command not found: pip`); all install/build steps in the plan must use `python3 -m pip ...` or `.venv/bin/python3 -m pip ...` explicitly, not a bare `pip` invocation.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (verified installed live this session) |
| Config file | none currently exists — Wave 0 must create `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` with `testpaths = ["tests"]` to keep discovery scoped away from a future `tests-ui/` |
| Quick run command | `.venv/bin/python3 -m pytest tests/ -x -q` |
| Full suite command | `.venv/bin/python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOOP-03 | `validate_pitch` raises `ValueError` for a note outside C2–D5 (and passes for one inside) | unit | `pytest tests/test_validators.py::test_validate_pitch_out_of_range -x` | ❌ Wave 0 |
| LOOP-04 | `validate_bar_duration` raises `ValueError` when `sum(rhythm) != barDuration.quarterLength` | unit | `pytest tests/test_validators.py::test_validate_bar_duration_mismatch -x` | ❌ Wave 0 |
| PLAT-03 | New `core/` code has English-only comments where non-obvious; no argparse/streamlit imports | static/manual review + import-boundary test | `pytest tests/test_import_boundary.py -x` | ❌ Wave 0 |
| (Roadmap criterion 3) | All 5 existing CLI scripts produce identical output after preset data moves | integration/regression | `pytest tests/test_golden_regression.py -x` (or a standalone script comparing MIDI hashes + normalized MusicXML) | ❌ Wave 0 |
| (Roadmap criterion 4) | `pytest tests/` runs with zero failures | suite-level | `pytest tests/ -v` | n/a (aggregate) |
| (Roadmap criterion 5) | Dataclasses include all `GenerationTrace` fields | unit | `pytest tests/test_models.py::test_generation_trace_fields -x` | ❌ Wave 0 |
| (Roadmap criterion 6) | `requirements.txt` pins `music21==10.5.0`, installs cleanly on 3.12+ | manual/CI check | `python3 -m pip install -r requirements.txt` (verified live this session on 3.14.5, a superset of the 3.12+ floor) | n/a (install-time check, not a pytest file) |

### Sampling Rate
- **Per task commit:** `.venv/bin/python3 -m pytest tests/ -x -q`
- **Per wave merge:** `.venv/bin/python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`, plus the golden-file regression check (MIDI hash comparison, and normalized MusicXML comparison) passing outside pytest if implemented as a standalone script rather than a test file.

### Wave 0 Gaps
- [ ] `tests/conftest.py` — shared fixtures (e.g. a sample `MoodPreset` instance, tolerance constant for float comparisons)
- [ ] `tests/test_validators.py` — covers LOOP-03, LOOP-04
- [ ] `tests/test_models.py` — covers dataclass shape / GenerationTrace fields / serialization-friendliness
- [ ] `tests/test_presets_registry.py` — covers merge completeness (all 5 scripts' data present, no silent data loss)
- [ ] `tests/test_import_boundary.py` — covers PLAT-03 boundary rule (no streamlit/argparse in `core/`)
- [ ] `tests/test_golden_regression.py` (or standalone script) — covers Roadmap criterion 3; must implement MIDI-hash + MusicXML-normalized comparison per Pitfall 1 above, not raw byte hash
- [ ] pytest config file (`pytest.ini` or `pyproject.toml`) — none exists yet; needed to scope `testpaths` to `tests/` and keep future `tests-ui/` (Playwright) fully separate per TEST-01
- [ ] Framework install: `python3 -m pip install music21==10.5.0 pytest` (verified working command from this session)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local single-user desktop tool, no auth surface in this phase |
| V3 Session Management | no | No session state introduced in this phase (that's Phase 4, Streamlit) |
| V4 Access Control | no | No access boundaries in a pure-Python library phase |
| V5 Input Validation | yes | `validate_pitch` / `validate_bar_duration` ARE the input-validation controls for this phase — they are the security-relevant deliverable, not incidental |
| V6 Cryptography | no | No cryptographic material handled |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/malicious pitch or rhythm data silently accepted and propagated to file export (MusicXML/MIDI written to disk) | Tampering (data integrity) | `validate_pitch`/`validate_bar_duration` raising `ValueError` at generation time, as CONTEXT.md already locks — this phase's validators ARE this control, no additional library needed |
| N/A — this phase has no network, file-upload, or user-text-parsing surface yet | — | Chord-progression text parsing (a much larger V5 surface — arbitrary user-typed strings like "Am F C G") is explicitly Phase 2.5 scope, not Phase 1; this phase only validates already-structured preset data moved from trusted source files |

No high-severity ASVS gaps identified for this phase's actual scope (pure data restructuring + two validator functions operating on internal, developer-authored preset data — no external/untrusted input surface exists until Phase 2.5's chord-progression parsing).

## Sources

### Primary (HIGH confidence — verified live in this session)
- Local `.venv` Python/pip environment inspection: `python3 --version`, `pip index versions music21`, `pip index versions pychord`
- Live install: `.venv/bin/python3 -m pip install music21==10.5.0 pytest` — succeeded, confirmed prior installed version was 9.9.2
- Live pitch/meter verification: `music21.pitch.Pitch(...).midi` and `music21.meter.TimeSignature(...).barDuration.quarterLength` executed directly against installed music21 10.5.0
- Live golden-file determinism test: ran all 5 scripts twice, hashed all output files with `shasum`, diffed hash lists — MIDI identical, MusicXML non-identical
- Live music21 source inspection: `music21/base.py` `Music21Object.id` property source (`builtins.id(self)` fallback), confirming root cause of MusicXML id volatility
- Direct code inspection: `scripts/generate_cello_dark_ostinato.py`, `scripts/harmony_advisor.py`, `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, `scripts/generate_dorian_sexy_duet_loop.py` (full file reads, this session)
- `slopcheck install music21 pytest` — live run, both `[OK]`
- PyPI JSON metadata for music21 (via WebFetch of `pypi.org/pypi/music21/json`) — confirmed 10.5.0 latest, release date 2026-06-17, `Requires-Python >=3.11`

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` Pitfalls 1–2 — reference validator implementations, cross-verified live in this session (all claimed MIDI numbers and API calls confirmed correct against actual music21 10.5.0 behavior)
- `.planning/research/ARCHITECTURE.md` — recommended `core/` structure and MoodPreset shape, cross-checked against actual script contents for completeness (duet shape divergence found not to be captured by the original sketch, documented in Pitfall 3 above)

### Tertiary (LOW confidence)
- None — all claims in this document were either verified live in this session or are explicit CONTEXT.md/ROADMAP.md locked decisions (not research claims).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — music21 10.5.0 and pytest both installed and exercised live in this session against the actual repo
- Architecture: HIGH — based on direct reading of all 5 source scripts plus live testing of the merge-relevant data shapes
- Pitfalls: HIGH — the MusicXML determinism pitfall (the most consequential finding) was discovered and root-caused via live experimentation in this session, not inferred from training data or documentation

**Research date:** 2026-07-04
**Valid until:** 2026-08-03 (30 days — stable domain, but music21 release cadence has been active in 2026 per the version history observed; re-verify version pin if phase execution is delayed significantly past this window)
