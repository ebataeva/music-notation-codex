---
phase: 02-loopengine-exportengine
plan: 01
subsystem: validators
tags: [music21, validation, tdd, error-handling]

# Dependency graph
requires:
  - phase: 01-core-library-skeleton-validators
    provides: core/engine/validators.py (validate_pitch, validate_bar_duration) and their original test suite
provides:
  - Hardened validate_pitch that rejects octave-less pitch names and never leaks a raw music21 PitchException
  - Hardened validate_bar_duration that rejects empty rhythm lists and non-positive individual durations
  - 13 new regression tests in tests/test_validators.py proving both fixes
affects: [02-02 (LoopEngine wiring these validators into score assembly, D-06)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Guard-before-construct: reject malformed input via cheap string checks before invoking a library constructor that may raise its own exception type"
    - "Exception translation: catch a third-party library exception (music21.pitch.PitchException) and re-raise as the codebase's sole ValueError contract, chained via `from exc`"

key-files:
  created: []
  modified:
    - core/engine/validators.py
    - tests/test_validators.py

key-decisions:
  - "Followed 02-PATTERNS.md's exact reference fix shapes (octave-digit-presence check, PitchException wrap, empty/non-positive rhythm guards) rather than inventing new approaches"
  - "No REFACTOR commit needed - GREEN implementation was already minimal and matched the pattern map; no cleanup required"

patterns-established:
  - "Validator hardening pattern: reject-before-construct + wrap-third-party-exception, keeping ValueError as the only public failure mode (codebase-wide convention, no custom exception classes)"

requirements-completed: [LOOP-01]

# Metrics
duration: 15min
completed: 2026-07-04
---

# Phase 2 Plan 1: Validator Hardening (WR-02/WR-03) Summary

**Hardened `validate_pitch`/`validate_bar_duration` via TDD so octave-less names, malformed pitch letters, and non-positive/empty rhythm entries all raise the documented `ValueError` instead of silently passing or leaking a raw `music21.pitch.PitchException`.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-07-04T21:08:00Z
- **Completed:** 2026-07-04T21:23:26Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments

- `validate_pitch` now rejects octave-less pitch names (e.g. `"C"`, `"Bb"`) before constructing a `music21.pitch.Pitch`, closing the WR-02 gap where such names silently defaulted to octave 4
- `validate_pitch` wraps `music21.pitch.PitchException` (raised on malformed letters like `"H2"`) into `ValueError`, chained via `from exc`, so no raw music21 exception can escape the documented contract
- `validate_bar_duration` now rejects empty rhythm lists with a message naming the empty-rhythm problem, and rejects any individual non-positive duration even when the sum happens to match the expected bar length (WR-03)
- 13 new regression tests added to `tests/test_validators.py` (6 for WR-02, 7 for WR-03/regression guards), all passing alongside the 14 pre-existing tests (27 total in the file)
- Full existing pytest suite (43 tests across 6 files, including both golden regression byte-identity tests) confirmed green after the change — the hardening has zero effect on current preset data, since no validator is wired into any generation path yet

## Task Commits

Each task was committed atomically, following RED-GREEN TDD since Task 1 was `tdd="true"`:

1. **Task 1 (RED): add failing tests for WR-02/WR-03** - `323d02a` (test)
2. **Task 1 (GREEN): harden validate_pitch and validate_bar_duration** - `c7e911f` (feat)
3. **Task 2: confirm full suite stays green** - verification-only, no code changes, no commit (nothing to stage)

**Plan metadata:** committed alongside this SUMMARY

_Note: No REFACTOR commit was needed — the GREEN implementation matched 02-PATTERNS.md's reference shape exactly with no cleanup required._

## Files Created/Modified

- `core/engine/validators.py` - `validate_pitch` gains an octave-digit-presence guard and a `try/except PitchException` wrap around `pitch.Pitch(pitch_name)` construction; `validate_bar_duration` gains an empty-rhythm guard and a per-element non-positive guard, both raised before the existing sum-comparison logic. Signatures unchanged.
- `tests/test_validators.py` - 13 new test functions covering WR-02 (octave-less names, invalid letters, valid-octave regression guards) and WR-03 (negative/zero durations despite matching sum, empty rhythm, existing pass/fail cases re-verified after hardening)

## Decisions Made

- Followed the exact reference fix shapes documented in `02-PATTERNS.md` (lines 236-274) rather than deviating — octave-detection via `any(ch.isdigit() for ch in pitch_name)`, catching the specific `PitchException` type (not a bare `except Exception`) per the codebase's existing precision, and guard-before-sum-check ordering for rhythm validation.
- Used the main repository's `.venv` (`/Users/ebataeva/Brain/Projects/music-notation-codex/.venv/bin/python3`) to run tests from within this worktree, since worktrees do not carry their own `.venv` (gitignored, not per-worktree). This is read-only interpreter usage, not a worktree write.

## Deviations from Plan

None - plan executed exactly as written. Both tasks' acceptance criteria were met without requiring any auto-fixes:
- `grep -c "raise ValueError" core/engine/validators.py` returns 6 (≥4 required)
- No bare `except Exception:` present
- No custom exception class defined
- All 27 tests in `tests/test_validators.py` pass; all 43 tests in the full suite pass including both golden regression tests

**Total deviations:** 0
**Impact on plan:** None — plan executed as specified with no scope changes.

## Issues Encountered

- Running the full test suite (`pytest tests/`) triggers the golden regression tests' subprocess side effect (documented in Phase 1's `01-REVIEW.md` IN-04): all 7 generator scripts re-run and rewrite their output `.musicxml`/`.midi` files in place, producing non-deterministic byte diffs (timestamps/memory-address ids) in already-tracked `scores/musicxml/*.musicxml` files even though content is unchanged (the golden test's own normalized-hash comparison confirms this and passes). This is a pre-existing, out-of-scope side effect unrelated to this plan's changes — discarded via targeted `git checkout -- <file>` (not a blanket reset) to keep the worktree clean before committing. Logged here for visibility; a proper fix (module-scoped fixture / temp-dir redirection per IN-04's suggested fix) is out of scope for this plan and not otherwise blocking.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `validate_pitch`/`validate_bar_duration` now guarantee `ValueError` as the sole failure mode, satisfying the prerequisite for Plan 02-02's D-06 requirement (LoopEngine calling these validators inside score assembly)
- No blockers. Plan 02-02 can proceed to wire these validators into `core/engine/loop_engine.py` and `core/export/exporter.py` extraction work.

## Self-Check: PASSED

- FOUND: core/engine/validators.py
- FOUND: tests/test_validators.py
- FOUND: .planning/phases/02-loopengine-exportengine/02-01-SUMMARY.md
- FOUND commit: 323d02a (test RED)
- FOUND commit: c7e911f (feat GREEN)
- FOUND commit: 93d8f77 (docs SUMMARY)

---
*Phase: 02-loopengine-exportengine*
*Completed: 2026-07-04*
