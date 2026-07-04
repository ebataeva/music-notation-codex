---
phase: 02-loopengine-exportengine
plan: 03
subsystem: engine
tags: [music21, tdd, refactor, extraction, duet]

# Dependency graph
requires:
  - phase: 02-loopengine-exportengine
    provides: 02-02's core/engine/loop_engine.py (build_score, _resolve_seed, _LEGACY_PITCH_EXCEPTIONS) and core/export/exporter.py (ExportEngine)
provides:
  - core/engine/loop_engine.py extended with build_duet_score() (internal-only two-part builder, D-13), make_note()/add_measure() helpers
  - scripts/generate_sexy_duet_loop.py, scripts/generate_simple_sexy_duet_loop.py, scripts/generate_dorian_sexy_duet_loop.py as thin wrappers over build_duet_score + ExportEngine
  - Full 7-invocation golden regression suite green (all 4 solo generators + all 3 duet generators)
affects: [Phase 2.5 (progression-driven generation may extend build_duet_score's seed/trace usage), Phase 3 (TheoryExplainer), any future DUET-01 v2 work building a public duet API on top of this internal path]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Instrument-specific validation range: validate_pitch's MIDI range check is cello-tuned (CELLO_MIN_MIDI/CELLO_MAX_MIDI_*); violin notes must call validate_pitch(pitch_name, extended=True) rather than the cello part's default range, or legitimate high violin notes are rejected as out-of-range cello notes"
    - "Legacy pitch exception mechanism (D-07) reused identically for the duet path: same _LEGACY_PITCH_EXCEPTIONS dict, keyed by (preset_name, pitch_name), no separate/looser bypass introduced (closes T-02-09)"
    - "build_duet_score kept as a genuinely internal function: not imported by generate_variant() or any public engine API surface, only by the 3 duet scripts (closes T-02-10)"

key-files:
  created: []
  modified:
    - core/engine/loop_engine.py
    - tests/test_loop_engine.py
    - scripts/generate_sexy_duet_loop.py
    - scripts/generate_simple_sexy_duet_loop.py
    - scripts/generate_dorian_sexy_duet_loop.py

key-decisions:
  - "Cello-part validation uses validate_pitch(pitch_name) (default, non-extended range) to match build_score's existing behavior; violin-part validation uses validate_pitch(pitch_name, extended=True) since violin notes (up to MIDI 79 in sexy_duet) exceed the cello-tuned default ceiling of 74 -- an auto-fixed Rule 1 bug not anticipated by the plan's action text"
  - "Velocities and tempo kept as call-site literals in each thin wrapper's main() (matching each script's pre-existing hardcoded values exactly), not pushed into MoodPreset -- per 02-PATTERNS.md's 'minimal-risk choice' guidance"
  - "validate_bar_duration called once per instrument's rhythm list per preset (cello_rhythm and violin_rhythm each validated once), not per bar, matching the existing convention from build_score"

patterns-established:
  - "Two-part builders in loop_engine.py validate each instrument's pitches against that instrument's own realistic range, not a single shared range check"

requirements-completed: [LOOP-01]

# Metrics
duration: 20min
completed: 2026-07-04
---

# Phase 2 Plan 3: Duet Script Extraction Summary

**Extracted the three duet scripts' identical two-part score-assembly logic into an internal-only `build_duet_score()` in `core/engine/loop_engine.py`, refactored all three duet scripts into thin wrappers, and fixed an instrument-range validation bug (cello-tuned `validate_pitch` incorrectly rejecting legitimate high violin notes) discovered while wiring in Phase 1's validators for the first time on this path.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-07-04T21:42:00Z
- **Completed:** 2026-07-04T22:02:24Z
- **Tasks:** 2 completed
- **Files modified:** 5 (2 new function additions to an existing file, 3 scripts rewritten in place)

## Accomplishments

- `core/engine/loop_engine.py` gains `make_note()`/`add_measure()` module-level helpers (extracted verbatim from the 3 duet scripts' identical functions) and `build_duet_score(preset, tempo_bpm, cello_velocity, violin_velocity) -> stream.Score` (D-13): builds a two-part Score with `violin`/`cello` parts, each carrying its own `instrument`/`clef`/`tempo`/`key`/`meter` metadata, reusing the D-07 legacy-exception mechanism from Plan 02-02 for the `simple_sexy_duet` A1 note
- Explicitly scoped `build_duet_score` as internal-only via a code comment and by leaving `generate_variant()` completely unmodified — verified `generate_variant`'s signature has no `instrument_set`/`duet` parameter (D-13, closes T-02-10)
- Discovered and fixed (Rule 1) an instrument-range validation bug: `validate_pitch`'s MIDI range check is cello-tuned (`CELLO_MIN_MIDI=36`/`CELLO_MAX_MIDI_DEFAULT=74`); violin notes in `sexy_duet` reach MIDI 79 (`F5`), which the default range rejects as an out-of-range cello note. Fixed by calling `validate_pitch(pitch_name, extended=True)` for the violin part (extended ceiling 84 covers all 3 duet presets' violin ranges) while keeping the cello part on the default (non-extended) range, matching `build_score`'s existing behavior
- All 3 duet scripts (`generate_sexy_duet_loop.py`, `generate_simple_sexy_duet_loop.py`, `generate_dorian_sexy_duet_loop.py`) rewritten as thin wrappers: no local `make_note`/`add_measure`/`build_score`/`export_score` function bodies remain, each delegates to `build_duet_score(get_preset(...), tempo_bpm=..., cello_velocity=..., violin_velocity=...)` and `ExportEngine().export(score, OUTPUT_NAME)`, printing the paths `ExportEngine` actually returns
- Applied the WR-04 fix (`environment.Environment()` replacing `environment.UserSettings()`) to all 3 duet scripts' `main()`, matching Plan 02-02's fix to the ostinato script
- Removed now-unused `music21` submodule imports (`clef, duration, instrument, key, meter, midi, note, stream, tempo`) from all 3 scripts — only `from music21 import environment` remains
- Full 7-invocation golden regression suite (`tests/test_golden_regression.py`) confirmed byte-identical MIDI and normalized-MusicXML output across all 4 solo genres and all 3 duets after the refactor, including `simple_sexy_d_minor_violin_cello_loop` (the invocation touching the A1 legacy note through the newly validator-wired duet path)

## Task Commits

Each task was committed atomically, following RED-GREEN TDD for Task 1 (`tdd="true"`):

1. **Task 1 (RED): add failing tests for build_duet_score** - `711d39e` (test)
2. **Task 1 (GREEN): implement build_duet_score** - `05b6941` (feat)
3. **Task 2: refactor all 3 duet scripts into thin wrappers** - `759c377` (refactor)

**Plan metadata:** committed alongside this SUMMARY

_Note: No REFACTOR commit was needed for Task 1 -- the GREEN implementation already matched 02-PATTERNS.md's reference shape, with only the range-validation fix (folded into the GREEN commit as part of making the tests pass correctly, not a separate cleanup pass)._

## Files Created/Modified

- `core/engine/loop_engine.py` - added `make_note()`, `add_measure()`, `build_duet_score()` (internal two-part builder, D-13)
- `tests/test_loop_engine.py` - 6 new tests covering duet Score shape, part ids, measure counts per `duet_bars`, the `simple_sexy_duet` A1 legacy-note non-raise case, `dorian_sexy_duet` build success, and `generate_variant`'s signature staying duet-free
- `scripts/generate_sexy_duet_loop.py` - rewritten as a thin wrapper delegating to `build_duet_score`/`ExportEngine`; `environment.Environment()` replaces `environment.UserSettings()`
- `scripts/generate_simple_sexy_duet_loop.py` - same thin-wrapper rewrite, preset `"simple_sexy_duet"`, tempo 64, velocities 68/58
- `scripts/generate_dorian_sexy_duet_loop.py` - same thin-wrapper rewrite, preset `"dorian_sexy_duet"`, tempo 88, velocities 74/62

## Decisions Made

- Cello-part pitches validated via `validate_pitch(pitch_name)` (default range, matches `build_score`); violin-part pitches validated via `validate_pitch(pitch_name, extended=True)` since the violin's realistic register exceeds the cello-tuned default ceiling
- Velocities/tempo kept as literal call-site arguments in each wrapper's `main()`, matching each script's pre-existing hardcoded constants exactly -- not moved into `MoodPreset` (02-PATTERNS.md's minimal-risk-choice guidance)
- `validate_bar_duration` called once per instrument's rhythm list per preset (not per-bar), consistent with `build_score`'s existing convention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed cello-range validation incorrectly rejecting valid violin notes**
- **Found during:** Task 1 (GREEN phase -- running the new duet tests for the first time against a straightforward transcription of the plan's `<action>` guidance)
- **Issue:** `core/engine/validators.py`'s `validate_pitch()` enforces a cello-tuned MIDI range (`CELLO_MIN_MIDI=36`, `CELLO_MAX_MIDI_DEFAULT=74`, `CELLO_MAX_MIDI_EXTENDED=84`). The plan's action text said to apply "the SAME legacy-exception check used in build_score" to both instruments uniformly, but didn't anticipate that a plain (non-extended) call would reject legitimate violin notes: `sexy_duet`'s violin part reaches `F5` (MIDI 77), above the default ceiling of 74. Running the new tests surfaced `ValueError: Pitch F5 (MIDI 77) is outside playable cello range (36-74)` for a note that is not actually out of range for a violin and is not the known/legacy A1 exception.
- **Fix:** Kept the cello part on `validate_pitch(pitch_name)` (default range, matching `build_score`'s existing behavior) but changed the violin part to `validate_pitch(pitch_name, extended=True)`. Confirmed the extended ceiling (MIDI 84) covers the highest violin note across all 3 duet presets (max observed: MIDI 79 in `sexy_duet`) and that all non-exception cello notes across all 3 presets stay within the default range (max observed: MIDI 57).
- **Files modified:** `core/engine/loop_engine.py`
- **Verification:** All 17 tests in `tests/test_loop_engine.py` pass; full golden regression suite (both MIDI and normalized-MusicXML) passes byte-identical for all 7 invocations, including the 3 duet scripts whose violin parts exercise this exact code path
- **Committed in:** `05b6941` (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary for correctness -- without this fix, `build_duet_score` would raise `ValueError` on every call for all 3 duet presets (every preset's violin part contains notes above MIDI 74), making the function unusable for its stated purpose. No scope creep: the fix stays within the validator-range semantics already established by Plan 01/02 (`extended` parameter already existed on `validate_pitch`, just needed to be threaded through correctly per instrument).

## Issues Encountered

- Same pre-existing, out-of-scope side effect documented in prior plans' summaries (IN-04): running the golden regression suite (directly or via the full `pytest tests/` run) re-executes all 7 generator scripts as subprocesses, rewriting tracked `scores/musicxml/*.musicxml` files in place with new volatile `id="P..."`/`id="I..."` values (content otherwise byte-identical, confirmed by the normalized-hash comparison passing every time). Discarded via targeted `git checkout -- scores/musicxml/` (never a blanket reset/clean) after each test run. This happened twice during this plan's execution (after Task 2's golden regression run, and after the final full-suite verification run) -- each time confirmed to be only the known volatile-id diff before discarding.
- The worktree does not carry its own `.venv` (gitignored, not per-worktree). All test/script invocations used the main repository's `.venv/bin/python3` interpreter (`/Users/ebataeva/Brain/Projects/music-notation-codex/.venv/bin/python3`) -- read-only interpreter usage, no writes to the main checkout.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 generator scripts (1 solo + 3 duet) are now thin wrappers with zero music21 score-building logic remaining in `scripts/` -- Phase 2's brownfield-extraction scope is complete
- `build_duet_score` is ready for Phase 2.5's progression-driven generation work if it chooses to extend the duet path's seed/trace usage, though it currently has no seed parameter (out of this plan's declared scope -- `build_duet_score`'s signature matches exactly what the plan specified: `preset, tempo_bpm, cello_velocity, violin_velocity`)
- `generate_variant()` remains cello-only and unmodified; any future public duet API (DUET-01, v2 scope) will need its own design work rather than simply exposing `build_duet_score`
- No blockers.

## Self-Check: PASSED

- FOUND: core/engine/loop_engine.py (build_duet_score present)
- FOUND: scripts/generate_sexy_duet_loop.py (thin wrapper)
- FOUND: scripts/generate_simple_sexy_duet_loop.py (thin wrapper)
- FOUND: scripts/generate_dorian_sexy_duet_loop.py (thin wrapper)
- FOUND: tests/test_loop_engine.py (6 new duet tests)
- FOUND commit: 711d39e (test RED - build_duet_score)
- FOUND commit: 05b6941 (feat GREEN - build_duet_score + range-validation fix)
- FOUND commit: 759c377 (refactor - 3 duet scripts as thin wrappers)
- Full suite: 65/65 tests passed (`pytest tests/ -v`)
- Golden regression: both tests passed (byte-identical MIDI + normalized-MusicXML) for all 7 invocations
- `grep "def build_duet_score" core/engine/loop_engine.py` matches
- `grep -c "def generate_variant" core/engine/loop_engine.py` returns exactly 1, no duet/instrument_set parameter in its signature
- `grep -c "environment.UserSettings" scripts/generate_*_duet_loop.py` returns 0 total matches
- `grep -L "def make_note\|def add_measure\|def build_score"` lists all 3 duet scripts (no local score-building functions remain)
- Working tree clean before commit (volatile musicxml diffs discarded via targeted checkout, never blanket reset/clean)

---
*Phase: 02-loopengine-exportengine*
*Completed: 2026-07-04*
