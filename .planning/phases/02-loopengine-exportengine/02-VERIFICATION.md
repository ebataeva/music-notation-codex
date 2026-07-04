---
phase: 02-loopengine-exportengine
verified: 2026-07-05T00:30:00Z
status: human_needed
score: 12/12 must-haves verified
overrides_applied: 0
---

# Phase 2: LoopEngine + ExportEngine Verification Report

**Phase Goal:** Generation and export logic lives in core/ as a real engine — LoopEngine builds scores from presets, ExportEngine writes MusicXML/MIDI, all 4+3 generator scripts become thin wrappers with byte-identical output, with seeds, traces and hardened validators wired in.
**Verified:** 2026-07-05
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria, Phase 2)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Calling `build_score()` with a MoodPreset returns a music21 Score with no errors | VERIFIED | `core/engine/loop_engine.py:45-89`; ran `build_score(get_preset("dark_trip_hop"))` directly — returns `stream.Score`, no exception. `tests/test_loop_engine.py` covers all 4 solo presets. |
| 2 | `ExportEngine.export_to_musicxml()`/`.export_to_midi()` write valid files to `scores/musicxml/`/`scores/midi/` | VERIFIED | `core/export/exporter.py:24-37`; ran the ostinato script end-to-end — wrote real files, confirmed via `--genre dark_trip_hop --seed 7` run (exit 0, printed real paths). `tests/test_exporter.py` uses `tmp_path`. |
| 3 | `scripts/generate_cello_dark_ostinato.py` runs via its thin wrapper, byte-identical output | VERIFIED | Script contains only `parse_args()`+`main()`, no music21 score-building imports beyond `environment` (confirmed via grep and full-file read). Golden regression (`tests/test_golden_regression.py`) passes. Manually confirmed MIDI byte-identical across two `seed=42` runs; MusicXML differs only in volatile memory-address IDs (`P...`/`I...`), which is the documented, pre-existing IN-04 side effect the golden suite itself normalizes away — not a content difference. |
| 4 | Explicit seed reproduces identical variant; unspecified seed is generated and always recorded in trace | VERIFIED | `_resolve_seed` (`loop_engine.py:36-42`) always returns a concrete seed. Empirically: `generate_variant(preset)` (no seed) → `trace.seed = 3374546797` (non-None). Two `build_score(preset, seed=42)` calls produce byte-identical MIDI (verified directly, not just via SUMMARY claim). |
| 5 | Every generated variant carries a populated GenerationTrace (strategy, register, chord tones) | VERIFIED | Ran `generate_variant(get_preset("dark_trip_hop"))` directly: `pattern_strategy="preset_verbatim"`, `register_choices` = 8 non-empty labels (one per bar), `chord_tones_used` = 8 non-empty pitch lists matching `preset.bars`. |

**Score:** 5/5 ROADMAP success criteria verified.

### Additional Plan-Level Must-Haves (02-01/02-02/02-03 frontmatter)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | `validate_pitch` rejects octave-less pitch names with `ValueError` | VERIFIED | `validators.py:13-17`; `tests/test_validators.py` passes (27 tests, 65/65 full suite). |
| 7 | `validate_pitch` never lets a raw `PitchException` escape | VERIFIED | `validators.py:18-21` wraps `PitchException` → `ValueError` chained via `from exc`. |
| 8 | `validate_bar_duration` rejects any individual non-positive duration | VERIFIED | `validators.py:35-36`, guards before sum check. |
| 9 | Full pytest suite (incl. golden regression) passes after validator hardening | VERIFIED | `65 passed, 1 warning` — ran directly, not from SUMMARY claim. |
| 10 | `generate_cello_dark_ostinato.py --genre sexy_duet` no longer offered (WR-01) | VERIFIED | Ran directly: `--genre sexy_duet` → argparse rejects with exit code 2, `choose from 'dark_trip_hop', 'driving_cinematic', 'noir_slow_burn', 'ritual_tribal'`. `--list-genres` output confirmed to contain only the 4 solo names. |
| 11 | Request for >64 bars raises an error before Score is built (SAFE-02) | PARTIAL | Verified for the **solo path**: `build_score`/`generate_variant` both raise `ValueError` for a 65-bar preset (ran directly, confirmed). **NOT enforced on the duet path**: ran `build_duet_score()` with a 65-bar cello part directly — no error raised, Score is built anyway. This is a real, empirically-confirmed gap, already documented as WR-03 in `02-REVIEW.md` (code review, same phase, latest commit `748651a`, not yet fixed). |
| 12 | All 4 generator scripts (ostinato + 3 duet) are thin wrappers, no music21 score-building logic in `scripts/` | VERIFIED | Read all 4 scripts in full: none contain `make_note`/`add_measure`/local `build_score`/`export_score`; each imports its build function from `core.engine.loop_engine` and `ExportEngine` from `core.export.exporter`. `grep -L` pattern from the plan's own acceptance criteria confirmed no local score-building functions remain. |

**Score:** 12/12 must-haves pass or partially pass (11 fully VERIFIED, 1 PARTIAL — SAFE-02 duet gap, downgraded to WARNING below, not a BLOCKER since it does not violate any of the 5 ROADMAP success criteria which are solo-path-scoped).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `core/engine/validators.py` | Hardened validate_pitch/validate_bar_duration | VERIFIED | Read in full; contains 6 `raise ValueError` sites, no bare `except Exception`, no custom exception class. |
| `tests/test_validators.py` | New WR-02/WR-03 test cases | VERIFIED | 27 tests, all passing. |
| `core/engine/loop_engine.py` | `build_score`, `generate_variant`, `build_duet_score`, seed/trace/legacy-exception machinery | VERIFIED | All functions present, read in full, exercised directly (not just via tests). |
| `core/export/exporter.py` | `ExportEngine` with export_to_musicxml/export_to_midi/export | VERIFIED | Read in full; all 3 methods present and exercised directly via script run. |
| `core/export/__init__.py` | Package marker | VERIFIED | Exists (`ls` confirmed). |
| `core/presets/registry.py` | `list_solo_presets()` (WR-01) | VERIFIED | Present, returns 4 solo names, excludes 3 duet-only presets; confirmed via direct script CLI output. |
| `scripts/generate_cello_dark_ostinato.py` | Thin wrapper | VERIFIED | Read in full — parse_args + core calls + printing only. |
| `scripts/generate_sexy_duet_loop.py` | Thin wrapper | VERIFIED | Read in full — no local score-building functions. |
| `scripts/generate_simple_sexy_duet_loop.py` | Thin wrapper | VERIFIED | Read in full — no local score-building functions. |
| `scripts/generate_dorian_sexy_duet_loop.py` | Thin wrapper | VERIFIED | Read in full — no local score-building functions. |
| `tests/test_loop_engine.py` | Unit tests for build_score/generate_variant/build_duet_score | VERIFIED | 17 tests present, passing. |
| `tests/test_exporter.py` | ExportEngine unit tests using tmp_path | VERIFIED | 4 tests present, passing, no writes into real `scores/`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tests/test_validators.py` | `core/engine/validators.py` | `from core.engine.validators import validate_bar_duration, validate_pitch` | WIRED | Confirmed via grep. |
| `scripts/generate_cello_dark_ostinato.py` | `core/engine/loop_engine.py` | `from core.engine.loop_engine import build_score` | WIRED | Confirmed via grep + successful script run. |
| `scripts/generate_cello_dark_ostinato.py` | `core/export/exporter.py` | `from core.export.exporter import ExportEngine` | WIRED | Confirmed via grep + successful script run. |
| `core/engine/loop_engine.py` | `core/engine/validators.py` | `validate_pitch(...)`/`validate_bar_duration(...)` called during score assembly | WIRED | Confirmed both solo and duet paths call the validators (with instrument-appropriate `extended` flag). |
| `scripts/generate_sexy_duet_loop.py` (+2 more) | `core/engine/loop_engine.py` | `from core.engine.loop_engine import build_duet_score` | WIRED | Confirmed via grep across all 3 duet scripts. |
| `core/engine/loop_engine.py` | `core/engine/validators.py` | Legacy exception skip for `simple_sexy_duet` A1 note | WIRED | `_LEGACY_PITCH_EXCEPTIONS` present, consulted in both `build_score` and `build_duet_score`, test proves it does not raise (warning emitted instead). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `generate_variant()` | `trace.chord_tones_used` | `preset.bars` (real preset data, not hardcoded) | Yes — verified 8 non-empty per-bar pitch lists matching actual preset content | FLOWING |
| `generate_variant()` | `trace.register_choices` | Derived from `preset.bars` via `_classify_register` | Yes — verified 8 real register labels, not static placeholders | FLOWING |
| `ExportEngine.export()` | Written files | `score.write(...)`/`midi.translate.streamToMidiFile(score)` | Yes — actual files written and read back with real byte content, verified directly | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `.venv/bin/python -m pytest tests/ -q` | `65 passed, 1 warning` | PASS |
| WR-01 fix: `sexy_duet` rejected by argparse | `python3 scripts/generate_cello_dark_ostinato.py --genre sexy_duet` | exit 2, "invalid choice" | PASS |
| `--list-genres` shows only solo presets | `python3 scripts/generate_cello_dark_ostinato.py --list-genres` | 4 solo names only, no duet names | PASS |
| Seed reproducibility (MIDI) | Two `build_score(preset, seed=42)` calls, compared MIDI bytes | Identical | PASS |
| SAFE-02 guard (solo path) | `build_score`/`generate_variant` with a 65-bar preset (via `dataclasses.replace`) | `ValueError: Requested 65 bars exceeds the maximum of 64.` | PASS |
| SAFE-02 guard (duet path) | `build_duet_score` with a 65-bar cello preset (via `dataclasses.replace`) | No error raised — Score built anyway | FAIL (see gap below) |
| `--seed` flag wired end-to-end | `python3 scripts/generate_cello_dark_ostinato.py --genre dark_trip_hop --seed 7` | exit 0, prints Genre/MusicXML/MIDI | PASS |
| `environment.UserSettings` fully removed | `grep environment.UserSettings scripts/*.py` | 0 matches | PASS |
| Import boundary still enforced | `.venv/bin/python -m pytest tests/test_import_boundary.py -q` | `2 passed` | PASS |
| No debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER) in phase-modified files | grep across all 13 phase files | 0 matches | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| LOOP-01 | 02-01, 02-02, 02-03 | App generates a playable cello loop from the chord progression + mood | SATISFIED | `build_score`/`generate_variant` produce valid Scores for all 4 solo presets; verified directly, not just via tests. (Full LOOP-01 scope — arbitrary user chord progressions — is Phase 2.5's job; this phase satisfies the preset-driven portion, matching ROADMAP's "MoodPreset" wording.) |
| SAFE-02 | 02-02 | Max bars per loop — generation rejects requests for loops longer than 64 bars | PARTIALLY SATISFIED | Enforced and verified on the solo path (`build_score`, `generate_variant`). NOT enforced on the duet path (`build_duet_score`) — confirmed empirically, a 65-bar duet preset builds without error. Documented as WR-03 in `02-REVIEW.md` (same phase's own code review), not yet fixed in the codebase. |
| SAFE-07 | 02-02 | Variant generation depth guard — flat, no recursive sub-variant spawning | SATISFIED | `generate_variant`/`build_score`/`build_duet_score` read in full — no self-recursive or "generate more variants" call path exists in any of them. |

**No orphaned requirements** — REQUIREMENTS.md traceability table maps exactly LOOP-01 and SAFE-02/SAFE-07 to Phase 2 (SAFE-07 also mapped to Phase 2), matching what the plans declared.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `core/engine/loop_engine.py` (build_duet_score) | 154-219 | Missing SAFE-02 guard on the duet path | WARNING | Confirmed empirically (see spot-check table). Documented in `02-REVIEW.md` as WR-03. |
| `core/engine/loop_engine.py` (build_duet_score) | 177-180 | No None-check on `preset.duet_rhythm`/`duet_bars` before subscripting — raises raw `TypeError` if called with a solo preset | WARNING | Documented in `02-REVIEW.md` as WR-04. Confirmed by reading the code — `preset.duet_rhythm["cello"]` has no guard. |
| `core/engine/loop_engine.py` (build_duet_score) | 185-215 | No cello/violin bar-count alignment check | WARNING | Documented in `02-REVIEW.md` as WR-05. Confirmed by reading the code — two independent loops, no length-match assertion. |
| `core/engine/loop_engine.py` (generate_variant) | 92-105 | Calling `generate_variant()` on a duet preset (`bars=[]`) fails with an internal-data-shaped message ("Rhythm is empty") rather than a caller-oriented one | WARNING | Documented in `02-REVIEW.md` as WR-06. |
| `core/export/exporter.py` | 25, 31 | `output_name` interpolated directly into file path with no sanitization — path traversal possible (`../../escape`) | WARNING | Documented in `02-REVIEW.md` as WR-01. Low current risk (single-user local CLI) but ExportEngine will be reused in the Streamlit UI in later phases. |
| `core/engine/validators.py` | 37 | `validate_bar_duration` leaks a raw `Music21Exception` (not `ValueError`) for an invalid meter string — inconsistent with this same phase's own WR-02 exception-wrapping policy for pitches | WARNING | Documented in `02-REVIEW.md` as WR-02. |
| `core/export/exporter.py` | 34-36 | `export_to_midi` has no try/finally around the manual open/write/close — a file handle leaks on write failure | WARNING | Documented in `02-REVIEW.md` as WR-07. |

No BLOCKER anti-patterns and no unreferenced debt markers (TBD/FIXME/XXX) found in any file touched by this phase.

### Human Verification Required

### 1. Accept or reject the 02-REVIEW.md warnings as phase-blocking

**Test:** Review the 7 WARNING-level findings in `.planning/phases/02-loopengine-exportengine/02-REVIEW.md` (WR-01 through WR-07) and this verification's cross-check of them, especially WR-03 (missing SAFE-02 guard on the duet path — a declared phase requirement, SAFE-02, is not fully satisfied).
**Expected:** A decision on whether these are (a) fixed now via a follow-up plan before the phase is considered done, (b) accepted as a known deviation via a VERIFICATION.md override with a documented reason, or (c) explicitly deferred to a later phase with a roadmap update.
**Why human:** SAFE-02 is a declared phase requirement whose plain wording ("generation rejects requests for loops longer than 64 bars") does not scope itself to the solo path only. The duet path gap is real and empirically confirmed, but the phase's 5 ROADMAP success criteria (which only reference `MoodPreset`/`build_score` generically, and the primary vertical slice is solo) are all independently satisfied. This is a scope-interpretation judgment call, not something a grep/test can resolve — the codebase's own code-reviewer already flagged it as `issues_found` with 0 critical / 7 warning findings, and no override has been recorded yet.

## Gaps Summary

No BLOCKER-level gaps. All 5 ROADMAP success criteria for Phase 2 are independently verified to hold in the codebase (not just claimed in SUMMARY.md) — `build_score()` builds valid Scores, `ExportEngine` writes real files, the ostinato script (and all 3 duet scripts) are genuine thin wrappers with byte-identical output (confirmed by running the golden regression suite and manually diffing MIDI/MusicXML bytes), seed reproducibility holds, and GenerationTrace is fully populated with real per-bar data.

One WARNING-level item requires a human decision: SAFE-02 (max-64-bars guard), a requirement declared in this phase's own plan frontmatter, is enforced on the solo path but empirically confirmed absent on the duet path (`build_duet_score`). This gap is already self-documented in the phase's own `02-REVIEW.md` (code review, same commit history, not yet acted on) along with 6 other non-blocking warnings (path traversal in `ExportEngine`, raw exception leak in `validate_bar_duration` for invalid meters, missing None-checks and bar-count alignment checks on the duet path, and a file-handle leak in `export_to_midi`). None of these affect the 5 ROADMAP success criteria, all of which are scoped to the solo (`MoodPreset`/`build_score`) path — but SAFE-02 is a named requirement in the plan frontmatter that is only partially met, so this is surfaced for a human decision rather than silently passed or silently failed.

---

_Verified: 2026-07-05_
_Verifier: Claude (gsd-verifier)_
