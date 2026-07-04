---
phase: 01-core-library-skeleton-validators
plan: 03
subsystem: testing
tags: [music21, pytest, golden-file-regression, requirements-pin, sha1]

# Dependency graph
requires:
  - phase: 01-core-library-skeleton-validators (plan 01)
    provides: core/ dataclasses, validators, and initial pytest scaffold (tests/conftest.py, pytest.ini)
provides:
  - requirements.txt pinned to music21==10.5.0 + pytest (unpinned)
  - Golden regression baseline (tests/golden/baseline_hashes.json) capturing MIDI SHA1 + normalized-MusicXML SHA1 for all 7 script invocations, on the 10.5.0 pin, before any preset data migration
  - tests/test_golden_regression.py with a re-runnable capture_baseline() helper and two pytest tests (test_midi_outputs_match_baseline, test_musicxml_outputs_match_baseline_normalized)
affects: [01-04 (preset data migration must keep this test green), phase-2 (LoopEngine refactor consumers of scripts/*.py)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Golden-file regression via MIDI-hash-primary + normalized-MusicXML-secondary comparison (MIDI is deterministic; MusicXML ids/encoding-date are not)"

key-files:
  created:
    - tests/test_golden_regression.py
    - tests/golden/baseline_hashes.json
  modified:
    - requirements.txt

key-decisions:
  - "Golden baseline has 7 MIDI + 7 MusicXML entries (4 ostinato genres + 3 duet scripts), not 8+8 as the plan text stated — the plan's task description double-counted; 4+3=7 invocations is the accurate, achievable set for the 5 existing scripts"
  - "Copied the three duet CLI scripts (generate_sexy_duet_loop.py, generate_simple_sexy_duet_loop.py, generate_dorian_sexy_duet_loop.py) into this worktree — they existed in the main repo but only as untracked files, absent from this worktree's git history, and the plan requires running them"
  - "MIDI hashed as raw bytes (verified deterministic); MusicXML normalized via regex (strip <encoding-date> content and id=\"P...\"/id=\"I...\" attribute values) before hashing, per RESEARCH.md Pitfall 1"

requirements-completed: [PLAT-03]

# Metrics
duration: 20min
completed: 2026-07-04
---

# Phase 01 Plan 03: Bump music21 pin + capture golden regression baseline Summary

**requirements.txt pinned to music21==10.5.0/pytest, and a MIDI-SHA1 + normalized-MusicXML-SHA1 golden baseline captured for all 7 existing script invocations before any preset data migration.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-07-04T07:25:00Z (approx)
- **Completed:** 2026-07-04T07:45:52Z
- **Tasks:** 2 completed
- **Files modified:** 15 (requirements.txt, 3 new duet scripts, 2 test/baseline files, 10 regenerated score output files)

## Accomplishments
- `requirements.txt` now pins `music21==10.5.0` and `pytest` (was `music21>=9.1,<10`, unbumped despite the `.venv` already running 10.5.0)
- Golden regression baseline captured on the 10.5.0 pin, before any preset data moves to `core/presets/` — the exact "no-op relative to the 10.5.0 baseline" comparison point CONTEXT.md requires for Plan 04
- MIDI output confirmed byte-identical across repeated runs (live re-verification); MusicXML confirmed non-identical across runs due to volatile `id="P.../I..."` attributes and `<encoding-date>`, both handled by the normalization regex
- `tests/test_golden_regression.py` passes (2/2) and is ready to be Plan 04's pass/fail gate

## Task Commits

Each task was committed atomically:

1. **Task 1: Bump requirements.txt to music21==10.5.0 and verify clean install** - `4592108` (feat) — also includes the three missing duet scripts (Rule 3 blocking-issue fix, see Deviations)
2. **Task 2: Capture golden baseline (MIDI hash + normalized MusicXML) from all scripts on the 10.5.0 pin** - `141c8ac` (test)

## Files Created/Modified
- `requirements.txt` - pinned `music21==10.5.0` and `pytest` (was `music21>=9.1,<10`)
- `scripts/generate_sexy_duet_loop.py` - added (was untracked in main repo, missing from worktree; Rule 3)
- `scripts/generate_simple_sexy_duet_loop.py` - added (same reason)
- `scripts/generate_dorian_sexy_duet_loop.py` - added (same reason)
- `tests/test_golden_regression.py` - MIDI-hash-primary + normalized-MusicXML-secondary golden regression guard, with a documented `capture_baseline()` recapture routine
- `tests/golden/baseline_hashes.json` - captured SHA1 baseline (7 MIDI entries, 7 normalized-MusicXML entries)
- `scores/midi/*.mid`, `scores/musicxml/*.musicxml` - regenerated as the pre-migration reference state (4 ostinato genre variants re-run; 3 duet script outputs newly created in this worktree)

## Decisions Made
- Baseline uses 7+7 entries (not 8+8 as the plan's task text stated): the plan describes "4 invocations" for the ostinato script and "3 invocations" for the duet scripts — 4+3=7, and the actual `scores/` output confirmed exactly 7 distinct MIDI/MusicXML pairs are produced by the 5 scripts' invocations. A pre-existing `cello_dark_ostinato.mid`/`.musicxml` pair from the repo's very first commit (predating the `--genre` CLI flag) is a stale, orphaned artifact not reproduced by any current script invocation and was correctly excluded from the golden set.
- MIDI is the primary, fully-deterministic comparison; normalized MusicXML (regex-stripped `<encoding-date>` and `id="P.../I..."`) is secondary, per RESEARCH.md's live-verified findings — not raw-byte MusicXML hashing.
- `capture_baseline()` is a named, importable, documented helper (not a throwaway one-off script) so a future intentional data change can deliberately regenerate the baseline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Copied three duet scripts into the worktree**
- **Found during:** Task 2 read_first step
- **Issue:** `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, and `scripts/generate_dorian_sexy_duet_loop.py` exist in the main repository working tree but were never committed to git (shown as `??` untracked in `git status`) — as a result they did not exist in this git worktree, which is checked out from a commit. The plan's Task 2 explicitly requires running all three to capture the golden baseline.
- **Fix:** Read the three files from the main repo's working tree (not git history, since they were never committed there either) and wrote identical copies into this worktree.
- **Files modified:** `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, `scripts/generate_dorian_sexy_duet_loop.py`
- **Verification:** All three scripts run successfully and produce the expected MusicXML/MIDI output pairs; content verified byte-for-byte identical to the main repo's working-tree copies at copy time.
- **Committed in:** `4592108` (Task 1 commit)

**2. [Rule 1 - Bug] Corrected baseline entry count from stated "8+8" to actual "7+7"**
- **Found during:** Task 2 execution
- **Issue:** The plan's task action/acceptance criteria describe "4 invocations, 8 output files" for the ostinato script and "3 invocations, 6 output files" for the duet scripts, then states the combined total as "8 MIDI files and 8 MusicXML files" and "exactly 8 entries" in the baseline JSON. The correct arithmetic is 4+3=7 invocations, and 4 (ostinato, 2 files each = 8) + 3 (duets, 2 files each = 6) = 14 total files = 7 MIDI + 7 MusicXML pairs, not 8+8.
- **Fix:** Captured the accurate 7 MIDI + 7 MusicXML baseline (one entry per each of the 5 scripts' 7 actual invocations). Verified against the confirmed pre-existing stale `cello_dark_ostinato.mid`/`.musicxml` pair (from the repo's first commit, before the `--genre` flag existed) which is not reproduced by any current script and was correctly excluded.
- **Files modified:** `tests/golden/baseline_hashes.json`, `tests/test_golden_regression.py`
- **Verification:** `pytest tests/test_golden_regression.py -v` passes 2/2; `json.load` confirms 7 entries under both `"midi"` and `"musicxml_normalized"` (not 8, since 8 was the plan's arithmetic error, not an achievable/correct target).
- **Committed in:** `141c8ac` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were necessary to complete the plan's actual intent (capture a working golden baseline for all 5 existing scripts). No scope creep — no new functionality was added beyond what the plan already specified; the duet scripts already existed as designed, and the entry count was a correction of an internal arithmetic inconsistency in the plan text, not a design change.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `tests/test_golden_regression.py` is ready to serve as Plan 04's pass/fail gate for the preset-data migration into `core/presets/`
- `requirements.txt` bump to `music21==10.5.0` is committed and verified; Plan 04 and later phases can rely on this pin
- Known pre-existing note: `generate_simple_sexy_duet_loop.py`'s `cello_bars` contains pitch `"A1"` (MIDI 33), below the locked C2 (MIDI 36) floor `validate_pitch` will enforce — per RESEARCH.md, this is migrated verbatim and flagged for Phase 2 to resolve, not silently fixed here (validators are not yet wired into script generation this phase)
- No blockers for Plan 04

---
*Phase: 01-core-library-skeleton-validators*
*Completed: 2026-07-04*
## Self-Check: PASSED
