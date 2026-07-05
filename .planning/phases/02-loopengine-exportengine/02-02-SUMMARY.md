---
phase: 02-loopengine-exportengine
plan: 02
subsystem: engine
tags: [music21, tdd, refactor, extraction, seed-reproducibility]

# Dependency graph
requires:
  - phase: 02-loopengine-exportengine
    provides: 02-01's hardened validate_pitch/validate_bar_duration (WR-02/WR-03)
provides:
  - core/engine/loop_engine.py with build_score() (music21 Score builder) and generate_variant() (traced LoopVariant builder)
  - core/export/exporter.py with ExportEngine (export_to_musicxml/export_to_midi/export)
  - core/presets/registry.py's list_solo_presets() (WR-01 fix)
  - scripts/generate_cello_dark_ostinato.py as a thin wrapper over the above
affects: [02-03 (remaining duet script wrappers if planned), Phase 2.5 (progression-driven generation extends build_score's seed/trace usage), Phase 3 (TheoryExplainer consumes GenerationTrace)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Seed resolution: _resolve_seed(seed) always returns a concrete int + random.Random, so an unset seed is generated once and recorded, never left None in the trace"
    - "Legacy pitch exception: module-level dict keyed by preset name, scoped to exact (preset, pitch) pairs, emits warnings.warn when skipping instead of silently bypassing validation"
    - "SAFE-02 bar-count guard duplicated at both build_score and generate_variant entry points so no Score construction begins for an oversized request regardless of which function is called first"
    - "ExportEngine base_dir defaults computed from the file's own __file__ depth (parents[2] for core/export/exporter.py vs parents[1] in scripts/) rather than a shared constant"

key-files:
  created:
    - core/engine/loop_engine.py
    - core/export/__init__.py
    - core/export/exporter.py
    - tests/test_loop_engine.py
    - tests/test_exporter.py
  modified:
    - core/presets/registry.py
    - scripts/generate_cello_dark_ostinato.py
    - tests/test_presets_registry.py

key-decisions:
  - "pattern_strategy literal fixed to \"preset_verbatim\" per D-04 guidance, consistently used across all generate_variant() calls this phase"
  - "register_choices uses a cheap lowest-octave-digit heuristic (low/mid/high register) rather than a full music-theoretic register model -- sufficient to satisfy the non-empty, one-per-bar trace requirement without fabricating unearned precision"
  - "Velocities/output-name defaults for the ostinato thin wrapper kept as-is (D-12 scope); only the WR-01 --genre/--list-genres source and the WR-04 environment fix were changed at the CLI layer"
  - "SAFE-02's 64-bar guard implemented as a length check on preset.bars in both build_score and generate_variant, since current presets are only 8 bars -- a forward-looking assertion per the plan's own framing"

patterns-established:
  - "core/engine and core/export modules import zero CLI-only symbols (argparse, streamlit, sys.path bootstrap) -- enforced by tests/test_import_boundary.py, confirmed still green"

requirements-completed: [LOOP-01, SAFE-02, SAFE-07]

# Metrics
duration: 35min
completed: 2026-07-04
---

# Phase 2 Plan 2: LoopEngine + ExportEngine Summary

**Extracted `build_cello_ostinato`/`export_score` into `core/engine/loop_engine.py`'s `build_score`/`generate_variant` and `core/export/exporter.py`'s `ExportEngine`, wiring in Phase 1's hardened validators, seed reproducibility, full GenerationTrace population, and a scoped legacy-pitch exception, while keeping `scripts/generate_cello_dark_ostinato.py`'s output byte-identical.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-07-04T21:26:00Z
- **Completed:** 2026-07-04T22:01:00Z
- **Tasks:** 3 completed
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments

- `core/engine/loop_engine.py` exposes `build_score(preset, seed=None) -> music21.stream.Score` (extracted from `build_cello_ostinato`) and `generate_variant(preset, seed=None) -> LoopVariant` (new high-level API, D-05), both enforcing the SAFE-02 64-bar guard and calling Phase 1's hardened `validate_pitch`/`validate_bar_duration` (D-06) before constructing notes
- Seed plumbing (D-01/D-02/D-03): `_resolve_seed` always returns a concrete seed even when the caller passes `None`, and `generate_variant`'s `trace.seed` is always populated — verified two identical-seed calls to `build_score` produce byte-identical MIDI output
- Every `generate_variant()` call now returns a fully populated `GenerationTrace`: `pattern_strategy="preset_verbatim"`, `register_choices` (one label per bar), `chord_tones_used` (verbatim per-bar pitch lists) — closing the D-04 gap where these fields were previously left `None`
- The `simple_sexy_duet` preset's known out-of-range `"A1"` note is skipped from `validate_pitch` via a module-level `_LEGACY_PITCH_EXCEPTIONS` dict scoped to exactly that (preset, pitch) pair, with a `warnings.warn` emitted on skip (D-07); confirmed any *other* preset/pitch combination still raises `ValueError`
- `core/presets/registry.py` gains `list_solo_presets()` (WR-01), filtering out the 3 duet-only presets whose `bars` list is empty
- `core/export/exporter.py`'s `ExportEngine` class exposes `export_to_musicxml`, `export_to_midi`, and a combined `export()` convenience method, all writing to a configurable `base_dir` (default `PROJECT_ROOT/scores`, computed from the file's own depth per D-08)
- `scripts/generate_cello_dark_ostinato.py` is now a thin wrapper (`parse_args()` + core calls + printing only): no `build_cello_ostinato`/`export_score` function bodies remain, `--genre`/`--list-genres` now source from `list_solo_presets()` (WR-01 fix — `sexy_duet` is rejected by argparse), a new `--seed` flag is wired end to end (D-03), and `environment.UserSettings()` was swapped for `environment.Environment()` (WR-04 fix — no more `~/.music21rc` rewrites)
- Golden regression suite (`tests/test_golden_regression.py`) confirmed byte-identical MIDI and normalized-MusicXML output for all 4 solo-genre invocations after the full refactor

## Task Commits

Each task was committed atomically, following RED-GREEN TDD for Tasks 1-2 (both `tdd="true"`):

1. **Task 1 (RED): add failing tests for build_score/generate_variant and list_solo_presets** - `60c02c9` (test)
2. **Task 1 (GREEN): implement build_score/generate_variant and list_solo_presets** - `efb9c54` (feat)
3. **Task 2 (RED): add failing tests for ExportEngine** - `8f96a01` (test)
4. **Task 2 (GREEN): implement ExportEngine** - `88abe51` (feat)
5. **Task 3: refactor generate_cello_dark_ostinato.py into a thin wrapper** - `69e556e` (refactor)

**Plan metadata:** committed alongside this SUMMARY

_Note: No REFACTOR commits were needed for Tasks 1-2 — both GREEN implementations were already minimal and matched 02-PATTERNS.md's reference shapes with no cleanup required._

## Files Created/Modified

- `core/engine/loop_engine.py` - `build_score()` (Score builder, extracted from the source script), `generate_variant()` (traced `LoopVariant` builder), `_resolve_seed()` (D-01/D-02 seed resolution), `_is_legacy_exception()` + `_LEGACY_PITCH_EXCEPTIONS` (D-07), `_classify_register()` (D-04 register heuristic), `MAX_BARS = 64` (SAFE-02)
- `core/export/__init__.py` - empty, makes `core.export` a package
- `core/export/exporter.py` - `ExportEngine` class with `export_to_musicxml`, `export_to_midi`, `export`, `PROJECT_ROOT` computed via `parents[2]`
- `core/presets/registry.py` - added `list_solo_presets()` (WR-01)
- `scripts/generate_cello_dark_ostinato.py` - rewritten as a thin wrapper delegating to `core.engine.loop_engine.build_score` and `core.export.exporter.ExportEngine`; `--seed` flag added; `environment.Environment()` replaces `environment.UserSettings()`
- `tests/test_loop_engine.py` - 11 new tests covering Score shape, seed reproducibility, trace population, legacy-exception scoping, validator wiring, and the SAFE-02 guard
- `tests/test_exporter.py` - 4 new tests covering `tmp_path`-based file writes and the default `base_dir`
- `tests/test_presets_registry.py` - 1 new test for `list_solo_presets()`

## Decisions Made

- Followed 02-PATTERNS.md's exact extraction shapes for `build_score` and `ExportEngine` rather than inventing new approaches
- `pattern_strategy` fixed to the literal `"preset_verbatim"` (D-04 discretion resolved consistently)
- `register_choices` uses a simple lowest-octave-digit heuristic rather than a full register-classification model — enough to satisfy "non-empty, one label per bar" without overclaiming musical sophistication
- Kept velocity/output-name literals in the thin wrapper as-is (D-12 scope: only the WR-01/WR-04 fixes and `--seed` addition touched the CLI layer)

## Deviations from Plan

None - plan executed exactly as written. All acceptance criteria for all 3 tasks were verified directly:
- `pytest tests/test_loop_engine.py tests/test_presets_registry.py tests/test_exporter.py -v` — 24 new/extended tests, zero failures
- `grep -c "import argparse\|import streamlit" core/engine/loop_engine.py` returns 0
- `grep "def build_score"` / `grep "def generate_variant"` both match in `core/engine/loop_engine.py`
- `pytest tests/test_import_boundary.py -v` passes (no forbidden imports introduced in `core/`)
- `grep "class ExportEngine"` and all three export method greps match in `core/export/exporter.py`
- `pytest tests/test_golden_regression.py -v` passes (byte-identical MIDI + normalized-MusicXML)
- `--genre dark_trip_hop` exits 0 and prints Genre/MusicXML/MIDI lines
- `--list-genres` output contains only the 4 solo genre names
- `--genre sexy_duet` exits non-zero (argparse rejects the choice)
- `--genre dark_trip_hop --seed 42` runs successfully
- `grep -c "^import\|^from"` shows no forbidden `music21` submodule imports beyond `environment`, no `core.models` import
- `grep "environment.UserSettings"` returns no match

**Total deviations:** 0
**Impact on plan:** None — plan executed as specified with no scope changes.

## Issues Encountered

- Same pre-existing, out-of-scope side effect documented in 02-01-SUMMARY.md (IN-04): running the golden regression suite (directly or via the full `pytest tests/` run) re-executes all 7 generator scripts as subprocesses, rewriting tracked `scores/musicxml/*.musicxml` files in place with new volatile `id="P..."`/`id="I..."` memory-address values (content is otherwise byte-identical, confirmed by the normalized-hash comparison passing every time). Discarded via targeted `git checkout -- scores/musicxml/...` (never a blanket reset/clean) after each test run, per the worktree destructive-git-operation prohibition. This happened 3 times during this plan's execution (after Task 3's golden regression run, after the full-suite run, and after the manual seed-reproducibility check) — each time confirmed to be only the known volatile-id diff before discarding.
- The worktree does not carry its own `.venv` (gitignored, not per-worktree, consistent with 02-01's note). All test/script invocations in this plan used the main repository's `.venv/bin/python3` interpreter (`/Users/ebataeva/Brain/Projects/music-notation-codex/.venv/bin/python3`) — read-only interpreter usage, no writes to the main checkout.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `build_score()`/`generate_variant()` are ready for Phase 2.5's progression-driven generation work to extend the seed/trace usage beyond the current `preset_verbatim` strategy
- `GenerationTrace` is now fully populated for every solo-preset variant, ready for Phase 3's `TheoryExplainer` to consume
- `ExportEngine` is ready for reuse by any remaining duet-script thin-wrapper refactors (out of this plan's declared file scope — only `generate_cello_dark_ostinato.py` was targeted)
- No blockers.

## Self-Check: PASSED

- FOUND: core/engine/loop_engine.py
- FOUND: core/export/__init__.py
- FOUND: core/export/exporter.py
- FOUND: core/presets/registry.py (list_solo_presets present)
- FOUND: scripts/generate_cello_dark_ostinato.py (thin wrapper)
- FOUND: tests/test_loop_engine.py
- FOUND: tests/test_exporter.py
- FOUND commit: 60c02c9 (test RED - loop_engine/registry)
- FOUND commit: efb9c54 (feat GREEN - loop_engine/registry)
- FOUND commit: 8f96a01 (test RED - exporter)
- FOUND commit: 88abe51 (feat GREEN - exporter)
- FOUND commit: 69e556e (refactor - thin wrapper)
- Full suite: 59/59 tests passed (`pytest tests/ -v`)
- Golden regression: both tests passed (byte-identical MIDI + normalized-MusicXML)
- Working tree clean before commit (volatile musicxml diffs discarded via targeted checkout)

---
*Phase: 02-loopengine-exportengine*
*Completed: 2026-07-04*
