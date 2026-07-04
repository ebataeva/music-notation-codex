---
phase: 01-core-library-skeleton-validators
plan: 04
subsystem: data
tags: [music21, dataclass, registry-pattern, data-migration]

requires:
  - phase: 01-core-library-skeleton-validators
    provides: "core/models.py MoodPreset dataclass (Plan 01), tests/golden/baseline_hashes.json pre-move baseline (Plan 03)"
provides:
  - "core/presets/mood_presets.py: MOOD_PRESETS registry with 7 entries (4 solo moods + 3 duet presets)"
  - "core/presets/registry.py: get_preset(name)/list_presets() read-only lookup helpers"
  - "All 5 CLI scripts now source their preset data from core/presets/ instead of inline dict literals"
affects: [02-loop-engine, 03-theory-explainer]

tech-stack:
  added: []
  patterns:
    - "core/presets/ as single source of truth for mood/duet preset data (ARCHITECTURE.md Pattern 2)"
    - "Registry read-only lookup (get_preset/list_presets) with natural KeyError on miss, no custom exception type"
    - "sys.path bootstrap in scripts/*.py so scripts can import core/ without package installation"

key-files:
  created:
    - core/presets/__init__.py
    - core/presets/mood_presets.py
    - core/presets/registry.py
    - tests/test_presets_registry.py
  modified:
    - scripts/generate_cello_dark_ostinato.py
    - scripts/harmony_advisor.py
    - scripts/generate_sexy_duet_loop.py
    - scripts/generate_simple_sexy_duet_loop.py
    - scripts/generate_dorian_sexy_duet_loop.py

key-decisions:
  - "Duet presets store rhythm=[]/bars=[]/feel=\"\" for their non-duet schema fields since no solo-cello-only equivalent data exists in source scripts (no fabricated data)"
  - "The pre-existing out-of-range 'A1' note in simple_sexy_duet migrated verbatim with an inline flag comment, not silently fixed (threat T-01-08)"
  - "Added sys.path bootstrap (Rule 3 - blocking issue) to all 5 scripts so `from core...` imports resolve when scripts are run directly, since they are not installed as a package"

patterns-established:
  - "MOOD_PRESETS dict[str, MoodPreset] is the canonical data source; scripts are now thin consumers via core.presets.registry"

requirements-completed: [LOOP-03, LOOP-04]

duration: 35min
completed: 2026-07-04
---

# Phase 01 Plan 04: Merge preset data into core/presets/ Summary

**Merged GENRE_PRESETS + GENRE_IDEAS + 3 duet scripts' hardcoded data into a single MOOD_PRESETS registry (7 entries), then swapped all 5 CLI scripts to read from it — golden regression confirms byte-for-byte no-op.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-07-04
- **Tasks:** 2 completed
- **Files modified:** 4 created, 5 scripts modified

## Accomplishments
- `core/presets/mood_presets.py` and `core/presets/registry.py` created with all 7 `MoodPreset` entries (4 solo moods merged from two scripts' data, 3 standalone duet presets with per-instrument `duet_rhythm`/`duet_bars`)
- All 5 CLI scripts (`generate_cello_dark_ostinato.py`, `harmony_advisor.py`, and 3 duet scripts) now import preset data from `core/presets/registry.py` instead of defining it inline
- Golden regression test (Plan 03's baseline) passes 2/2 — MIDI hashes and normalized MusicXML hashes are identical to pre-move output, proving the migration is a byte-for-byte behavioral no-op (Roadmap Phase 1 success criterion 3)
- The pre-existing out-of-range "A1" (MIDI 33) note in `simple_sexy_duet` was migrated verbatim with an inline flag comment, not silently fixed

## Task Commits

Each task was committed atomically:

1. **Task 1: Build core/presets/mood_presets.py and registry.py — merge all 5 sources into 7 MoodPreset entries** - `e9f03b6` (feat)
2. **Task 2: Swap all 5 scripts' preset data source to core/presets/ and verify golden regression stays green** - `8674271` (feat)

## Files Created/Modified
- `core/presets/__init__.py` - empty package marker
- `core/presets/mood_presets.py` - MOOD_PRESETS dict with 7 MoodPreset entries, data migrated verbatim from all 5 source scripts
- `core/presets/registry.py` - get_preset(name)/list_presets() lookup helpers
- `tests/test_presets_registry.py` - 7 tests proving merge completeness and no silent data loss
- `scripts/generate_cello_dark_ostinato.py` - removed GenrePreset class + GENRE_PRESETS dict, now uses get_preset()/list_presets()
- `scripts/harmony_advisor.py` - removed GENRE_IDEAS dict, now reads preset.progressions/modulations/mood_tips
- `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, `scripts/generate_dorian_sexy_duet_loop.py` - replaced hardcoded rhythm/bars literals with registry lookups (`sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet` respectively); velocities and tempo remain literal script arguments (not part of MoodPreset's duet schema)

## Decisions Made
- Duet presets' non-duet schema fields (`rhythm`, `bars`, `feel`, `progressions`, `modulations`, `mood_tips`) are set to empty/placeholder values (`[]`/`""`) rather than fabricated data, since no `GENRE_IDEAS`-equivalent theory data exists for duets and no solo-only bar data exists for these scripts — matches the plan's explicit "do not invent" instruction
- `dorian_sexy_duet.feel` carries the script's own code comment text ("D Dorian vamp: Dm9 -> G9. The B natural keeps it warm instead of funeral-dark.") per plan instruction; the other two duet presets have empty `feel` since their scripts had no equivalent descriptive comment

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added sys.path bootstrap to all 5 scripts**
- **Found during:** Task 2 (script data-source swap)
- **Issue:** Running `python3 scripts/generate_cello_dark_ostinato.py` directly failed with `ModuleNotFoundError: No module named 'core'` because scripts are invoked as standalone files (not as an installed package or via `python -m`), so the project root was never on `sys.path`. This blocked all 5 scripts and the golden regression test (which invokes scripts via `subprocess.run([PYTHON, script_path, ...], cwd=PROJECT_ROOT)` — `cwd` does not affect `sys.path`).
- **Fix:** Added `PROJECT_ROOT = Path(__file__).resolve().parents[1]` followed by `sys.path.insert(0, str(PROJECT_ROOT))` before the `core` import in each of the 5 scripts, with `# noqa: E402` on the subsequently-non-top-of-file imports.
- **Files modified:** scripts/generate_cello_dark_ostinato.py, scripts/harmony_advisor.py, scripts/generate_sexy_duet_loop.py, scripts/generate_simple_sexy_duet_loop.py, scripts/generate_dorian_sexy_duet_loop.py
- **Verification:** All 5 scripts run standalone with exit 0; golden regression test (`tests/test_golden_regression.py`) passes 2/2 via the same subprocess invocation pattern used before this fix
- **Committed in:** 8674271 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for the scripts to function at all after the data-source swap; no scope creep — this only bridges the import path, no behavior or data changed.

## Issues Encountered
- `generate_cello_dark_ostinato.py --list-genres` now also lists the 3 duet presets (in addition to the 4 solo moods) since `list_presets()` returns all 7 `MOOD_PRESETS` keys. The plan's acceptance criteria only required "lists all 4 solo mood names with feel text," which is satisfied; the 2 duet presets with empty `feel` print with a blank feel string, and `dorian_sexy_duet` prints its comment text. This is a side effect of Task 2's explicit instruction to swap `GENRE_PRESETS.values()` for `[get_preset(n) for n in list_presets()]` and was not flagged as an issue by the plan. Not treated as a deviation since it follows the plan's action text exactly; noted here for visibility ahead of Phase 2 UI work, where `list_presets()` may need a solo/duet filter.

## Next Phase Readiness
- `core/presets/registry.py` is the stable read API Phase 2's `LoopEngine` and Phase 3's `TheoryExplainer` will consume
- All 30 tests in `tests/` pass (models, import boundary, validators, golden regression, presets registry)
- Golden baseline (`tests/golden/baseline_hashes.json`) remains valid — no recapture needed since this plan's move was verified as a no-op

---
*Phase: 01-core-library-skeleton-validators*
*Completed: 2026-07-04*

## Self-Check: PASSED

- FOUND: core/presets/__init__.py
- FOUND: core/presets/mood_presets.py
- FOUND: core/presets/registry.py
- FOUND: tests/test_presets_registry.py
- FOUND: .planning/phases/01-core-library-skeleton-validators/01-04-SUMMARY.md
- FOUND commit: e9f03b6
- FOUND commit: 8674271
- FOUND commit: 5f10dd4
