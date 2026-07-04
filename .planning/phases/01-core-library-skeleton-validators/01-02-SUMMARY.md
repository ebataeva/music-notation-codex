---
phase: 01-core-library-skeleton-validators
plan: 02
subsystem: validation
tags: [music21, pytest, tdd, validators]

# Dependency graph
requires: []
provides:
  - "core/engine/validators.py with validate_pitch and validate_bar_duration"
  - "tests/test_validators.py with 14 passing unit tests covering LOOP-03 and LOOP-04"
affects: [phase-02-generation-engine, phase-2.5-progression-driven-generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Plain-function validators raising stdlib ValueError, no custom exception classes"
    - "Narrow music21 submodule imports (from music21 import meter, pitch) instead of importing the whole package"
    - "Bar length always derived from music21.meter.TimeSignature(...).barDuration.quarterLength, never hardcoded"

key-files:
  created:
    - core/__init__.py
    - core/engine/__init__.py
    - core/engine/validators.py
    - tests/test_validators.py
  modified: []

key-decisions:
  - "Added top-level core/__init__.py (not listed in plan's files_modified) because 'from core.engine.validators import ...' requires core/ itself to be an importable package, not just core/engine/ — Rule 3 blocking-issue fix"

patterns-established:
  - "Pattern 2 validator style: plain function -> ValueError with human-readable f-string message containing both input value and computed/expected value"

requirements-completed: [LOOP-03, LOOP-04]

# Metrics
duration: 12min
completed: 2026-07-04
---

# Phase 01 Plan 02: Cello Range and Bar-Duration Validators Summary

**validate_pitch and validate_bar_duration as pure, Streamlit-independent functions verified against live music21 10.5.0 MIDI/meter primitives, proven by 14 passing pytest unit tests (LOOP-03, LOOP-04)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-04T07:37:23Z
- **Completed:** 2026-07-04T07:49:00Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 4 (3 created for implementation, 1 test file)

## Accomplishments
- `validate_pitch(pitch_name, extended=False)` rejects notes outside the C2-D5 default cello range (or C2-C6 with `extended=True`), using `music21.pitch.Pitch(...).midi` so accidentals (C#3, Bb2) resolve correctly instead of naive lexical string comparison
- `validate_bar_duration(rhythm, meter_signature, tolerance=1e-9)` rejects rhythm lists whose summed quarter-length does not match `music21.meter.TimeSignature(meter_signature).barDuration.quarterLength`, proven against both 4/4 and 3/4 meters so the 4.0 bar length is never assumed
- Both are plain functions (no dataclass `__post_init__`, no custom exception classes) raising stdlib `ValueError` with human-readable messages including the offending value and the expected value
- Full RED-GREEN TDD cycle followed: 14 tests written first and confirmed failing on `ModuleNotFoundError`, then made to pass without modifying the test file

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Write failing tests for validate_pitch and validate_bar_duration** - `366f347` (test)
2. **Task 2 (GREEN): Implement validate_pitch and validate_bar_duration** - `fe1cd92` (feat)

**Plan metadata:** committed separately per worktree protocol (SUMMARY.md only, STATE.md/ROADMAP.md excluded — orchestrator owns those)

## Files Created/Modified
- `core/__init__.py` - Top-level package marker (added beyond plan scope, see Deviations)
- `core/engine/__init__.py` - Empty package marker per plan
- `core/engine/validators.py` - `validate_pitch` and `validate_bar_duration`, narrow `from music21 import meter, pitch` import, three MIDI range constants (CELLO_MIN_MIDI, CELLO_MAX_MIDI_DEFAULT, CELLO_MAX_MIDI_EXTENDED)
- `tests/test_validators.py` - 14 individually-named test functions covering every behavior line from the plan, including accidental edge cases and the real `sexy_duet` rhythm pattern

## Decisions Made
- Added `core/__init__.py` at the repository root even though the plan's `files_modified` only listed `core/engine/__init__.py` — without it, `from core.engine.validators import ...` fails because `core` itself is not a recognized package. This is a Rule 3 (blocking issue) auto-fix, not a scope change to the validator logic itself.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added core/__init__.py**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Plan's `files_modified` only listed `core/engine/__init__.py`; without a top-level `core/__init__.py`, the import `from core.engine.validators import validate_pitch, validate_bar_duration` used by both the tests and the plan's own acceptance-criteria one-liners would fail to resolve `core` as a package
- **Fix:** Created empty `core/__init__.py` alongside `core/engine/__init__.py`
- **Files modified:** core/__init__.py
- **Verification:** `pytest tests/test_validators.py -v` collects and passes all 14 tests; `python3 -c "from core.engine.validators import validate_pitch; ..."` one-liners from the plan's acceptance criteria all exit 0/raise as expected
- **Committed in:** fe1cd92 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the plan's own stated acceptance criteria (the `from core.engine.validators import ...` one-liners) to be runnable at all. No scope creep into validator logic.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `validate_pitch` and `validate_bar_duration` are implemented, tested, and importable without Streamlit, ready to be wired into real generation call paths in Phase 2
- RESEARCH.md flagged that `generate_simple_sexy_duet_loop.py` contains pitch `"A1"` (MIDI 33), which is below `CELLO_MIN_MIDI` (36) — this is a known pre-existing data issue in preset data, not addressed by this plan (validators are not yet wired into generation), and must be resolved when Phase 2 wires `validate_pitch` into the real generation path
- No blockers for Plan 03/04 in this phase (this plan has no `depends_on`)

---
*Phase: 01-core-library-skeleton-validators*
*Completed: 2026-07-04*

## Self-Check: PASSED

All created files verified present (core/__init__.py, core/engine/__init__.py, core/engine/validators.py, tests/test_validators.py, 01-02-SUMMARY.md). All commit hashes verified in git log (366f347 test, fe1cd92 feat).
