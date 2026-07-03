# Phase 1: Core Library Skeleton + Validators - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning
**Source:** Session decisions — project review + user-approved plan (2026-07-04), in lieu of discuss-phase

<domain>
## Phase Boundary

Pure-Python `core/` library skeleton: all shared dataclasses, a MoodPreset registry merged from the existing CLI scripts' data, a pytest scaffold for core unit tests, and the two must-do-early validators (cello range, bar duration). No Streamlit, no engine refactor (Phase 2), no progression parsing (Phase 2.5). Existing scripts keep working unchanged in behavior — only their preset data moves into `core/presets/`.

</domain>

<decisions>
## Implementation Decisions

### Dataclasses & trace
- All canonical dataclasses from ARCHITECTURE.md are created in this phase: `MoodPreset`, `GenerationRequest`, `LoopVariant`, `TheoryExplanation`, plus a new `GenerationTrace`.
- `GenerationTrace` fields locked now (cheap now, expensive to retrofit): `seed`, `pattern_strategy`, `register_choices`, `voice_leading_steps`, `chord_tones_used` (per-bar detail where applicable). Phase 1 only defines the structure; Phase 2/2.5 populate it.
- `LoopVariant` carries an optional `trace: GenerationTrace | None` field from day one.
- Dataclasses must be serialization-friendly (Loop Library, Phase 10): live `music21` objects must be separable from the persistable payload (paths/bytes/primitives), never required for round-tripping metadata.

### Preset registry
- The registry merges data from ALL FIVE existing scripts, not two: `generate_cello_dark_ostinato.py` (GENRE_PRESETS), `harmony_advisor.py` (GENRE_IDEAS), and the three duet generators (`generate_sexy_duet_loop.py`, `generate_simple_sexy_duet_loop.py`, `generate_dorian_sexy_duet_loop.py`).
- Duet material is included as **data only** (preset entries with two-part bar data allowed in the schema); no duet generation logic in v1 — DUET-01 stays v2.
- `GENRE_PRESETS` + `GENRE_IDEAS` merge into one `MoodPreset` per mood so theory data travels with generation data (ARCHITECTURE.md Pattern 2).
- Existing `feel` strings and `GENRE_IDEAS` texts are currently in Russian; migrate them verbatim in this phase (translation to English UI copy is a later concern for UI phases; PLAT-02 covers UI copy, not preset source data).

### Validators
- `validate_pitch`: C2 (MIDI 36) to D5 (MIDI 74) as the default intermediate range; C6 (MIDI 84) as an opt-in extended cap for electric/advanced. Raise `ValueError` with a human-readable message at generation time.
- `validate_bar_duration`: `sum(rhythm) == TimeSignature(meter).barDuration.quarterLength` with float tolerance; never hardcode 4.0.
- Validators live in `core/` (e.g. `core/engine/validators.py`) and are import-independent of Streamlit.

### Testing & tooling
- pytest infrastructure for `core/` is established in this phase, in `tests/` at repo root — fully separate from the future Playwright `tests-ui/` (TEST-01 boundary).
- Golden-file regression guard: after preset data moves to `core/presets/`, every existing script produces byte-identical MusicXML/MIDI output vs pre-refactor (capture goldens BEFORE moving data).
- `requirements.txt` is updated in this phase to the approved stack pin (`music21==10.5.0`) plus `pytest`; verify scripts still run on Python 3.12+ after the bump. If the music21 9→10 bump changes exported bytes, regenerate goldens with 10.5.0 first and document that the baseline is post-bump behavioral identity (data-move must be a no-op relative to the 10.5.0 baseline).

### Boundaries
- `core/` is a pure Python library: imports `music21`, never `streamlit`, never `argparse` (import-level rule from ARCHITECTURE.md).
- Scripts in `scripts/` keep their CLI behavior; in this phase they only switch their preset data source to `core/presets/` (full engine refactor to thin wrappers is Phase 2).
- Code comments in English only, and only where logic is non-obvious (PLAT-03).

### Claude's Discretion
- Exact module layout inside `core/` (follow ARCHITECTURE.md's recommended structure as the default).
- Naming details of registry lookup helpers, test file organization, fixture design.
- Whether duet preset data lives in the same registry dict or a parallel structure — pick what keeps the MoodPreset schema clean.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & data model
- `.planning/research/ARCHITECTURE.md` — recommended `core/` structure, canonical dataclass shapes, MoodPreset merge rationale (Pattern 2), import-boundary rules
- `.planning/research/PITFALLS.md` — Pitfalls 1–2 with reference implementations of `validate_pitch` / `validate_bar_duration`

### Stack
- `.planning/research/STACK.md` — approved versions (music21 10.5.0, Python 3.12+)
- `CLAUDE.md` — project constraints (locked decisions, testing/report stack)

### Source material (brownfield)
- `scripts/generate_cello_dark_ostinato.py` — GENRE_PRESETS + build/export logic
- `scripts/harmony_advisor.py` — GENRE_IDEAS theory data
- `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, `scripts/generate_dorian_sexy_duet_loop.py` — duet preset data (two-part bars)

</canonical_refs>

<specifics>
## Specific Ideas

- Validator reference code exists in PITFALLS.md (MIDI-number based checks) — use as the starting point.
- ARCHITECTURE.md's `MoodPreset` sketch already lists the merged fields (`rhythm`, `bars`, `feel`, `progressions`, `modulations`, `mood_tips`) — extend with whatever the duet scripts add (e.g. per-instrument bars).
- Golden-file test flow: run all 5 scripts → hash outputs → move data → run again → compare hashes.

</specifics>

<deferred>
## Deferred Ideas

- LoopEngine/ExportEngine refactor of script logic → Phase 2
- Seed policy + trace population → Phase 2
- Progression parsing (pychord) + generation from arbitrary chords → Phase 2.5
- Duet generation logic (InstrumentSet) → v2 (DUET-01)
- Any Streamlit code → Phase 4+

</deferred>

---

*Phase: 01-core-library-skeleton-validators*
*Context gathered: 2026-07-04 via session decisions (user-approved plan)*
