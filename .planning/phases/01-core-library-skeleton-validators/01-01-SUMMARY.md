---
phase: 01-core-library-skeleton-validators
plan: 01
subsystem: core
tags: [dataclasses, pytest, python, music21]

# Dependency graph
requires: []
provides:
  - "core/models.py with the five canonical dataclasses (GenerationRequest, TheoryExplanation, GenerationTrace, LoopVariant, MoodPreset)"
  - "First pytest scaffold in the repo (pytest.ini, tests/ package) scoped away from future tests-ui/"
  - "AST-based import-boundary guard proving core/ never imports streamlit or argparse"
affects: [01-02, 01-03, 01-04, phase-2, phase-2.5, phase-4]

# Tech tracking
tech-stack:
  added: [pytest (dev/test only, not yet pinned in requirements.txt)]
  patterns: ["frozen dataclasses for immutable preset/theory data", "plain dataclasses for request/variant/trace objects", "AST-walk import boundary enforcement"]

key-files:
  created:
    - core/__init__.py
    - core/models.py
    - pytest.ini
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_models.py
    - tests/test_import_boundary.py
  modified: []

key-decisions:
  - "No sys.path bootstrap needed in conftest.py — pytest.ini at repo root plus rootdir insertion already makes `core` importable from tests/"
  - "Import-boundary checker logic extracted into a shared _forbidden_imports_in_file() helper so both the real sweep test and the vacuity-guard test share one code path"

patterns-established:
  - "Dataclass style: from __future__ import annotations, @dataclass(frozen=True) for immutable preset data, plain @dataclass for request/variant/trace objects"
  - "core/ import-boundary rule enforced by AST walk over core/**/*.py, checked against a FORBIDDEN module set"

requirements-completed: [PLAT-03]

# Metrics
duration: 15min
completed: 2026-07-04
---

# Phase 1 Plan 1: Core Library Skeleton Summary

**core/models.py with all five canonical dataclasses (including the locked GenerationTrace shape) plus the repo's first pytest scaffold and an AST-based import-boundary guard for core/**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-04T07:20:00Z
- **Completed:** 2026-07-04T07:36:50Z
- **Tasks:** 2
- **Files modified:** 7 (all created)

## Accomplishments
- Defined `MoodPreset`, `GenerationRequest`, `LoopVariant`, `TheoryExplanation`, `GenerationTrace` as pure-Python dataclasses in `core/models.py` — no music21 objects required to construct any of them
- `GenerationTrace` locked to exactly the five fields Phase 2/2.5 will populate: `seed`, `pattern_strategy`, `register_choices`, `voice_leading_steps`, `chord_tones_used`
- Established the repo's first pytest infrastructure (`pytest.ini`, `tests/__init__.py`, `tests/conftest.py`) scoped to `tests/` only, leaving room for a separate `tests-ui/` later
- Added an AST-based import-boundary guard proving `core/` has zero `streamlit`/`argparse` imports, with a non-vacuous self-check against a fixture file

## Task Commits

Each task was committed atomically, following the TDD RED/GREEN cycle:

1. **Task 1: Create core/models.py with the five canonical dataclasses**
   - `d993c7f` (test) — failing tests for the five dataclasses + pytest.ini scaffold
   - `34a915d` (feat) — core/models.py implementation, 5/5 tests passing
2. **Task 2: Add import-boundary guard test for core/**
   - `9579879` (test) — AST-walk sweep test + vacuity-guard fixture test, 2/2 passing

**Plan metadata:** committed separately after this summary (docs commit)

_Note: Task 1 followed a full RED (failing tests) -> GREEN (implementation) cycle. Task 2's artifact IS the test file itself (a checker plus its own tests), so RED/GREEN collapsed into a single correct-on-first-write commit; both the real sweep and the vacuity guard passed immediately since core/models.py was already clean._

## Files Created/Modified
- `core/__init__.py` - empty package marker for `core/`
- `core/models.py` - the five canonical dataclasses (GenerationRequest, TheoryExplanation, GenerationTrace, LoopVariant, MoodPreset)
- `pytest.ini` - `testpaths = tests`, scoping discovery away from the not-yet-existing `tests-ui/`
- `tests/__init__.py` - empty test package marker
- `tests/conftest.py` - `tolerance` fixture (1e-9) for later plans' float-comparison tests
- `tests/test_models.py` - 5 unit tests asserting dataclass shape, defaults, and frozen behavior
- `tests/test_import_boundary.py` - AST-walk import-boundary guard + non-vacuous fixture test

## Decisions Made
- Confirmed no `sys.path` bootstrap was needed in `tests/conftest.py`: running pytest from repo root with `pytest.ini` present already makes `core` importable via pytest's rootdir insertion, so `conftest.py` only carries the `tolerance` fixture anticipated by RESEARCH.md's Wave 0 gap list.
- Extracted the import-boundary AST-walk logic into a shared `_forbidden_imports_in_file(path) -> set[str]` helper so the real-world sweep test and the vacuity-guard test exercise identical logic (per the plan's Task 2 acceptance criteria and threat T-01-03 mitigation).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- No `.venv` exists inside this git worktree (it is gitignored and worktrees only share git history, not the filesystem outside the checkout). Used the main repo's `.venv` at `/Users/ebataeva/wp2/music-notation-codex/.venv/bin/python3` (music21 10.5.0, pytest 9.1.1 already installed there) to run all verification commands via absolute path — no files were written outside this worktree.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `core/models.py` is ready for Plan 01-02 (validators) and Plan 01-03/01-04 (preset registry) to import and build on.
- `tests/` scaffold (pytest.ini, conftest.py `tolerance` fixture) is ready for subsequent Phase 1 plans to add `test_validators.py` and `test_presets_registry.py` without any additional setup.
- No blockers identified.

---
*Phase: 01-core-library-skeleton-validators*
*Completed: 2026-07-04*

## Self-Check: PASSED

All created files verified present on disk; all task/summary commit hashes verified present in git log.
