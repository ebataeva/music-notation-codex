---
phase: quick-260715-3fo
plan: 01
subsystem: ui
tags: [nicegui, osmd, fluidsynth, run.io_bound, ui.download]

# Dependency graph
requires:
  - phase: none
    provides: n/a (hotfix on existing Loop Coach page)
provides:
  - OSMD script loaded once during page build (not after Generate click) so notation reliably renders
  - Async do_generate using nicegui.run.io_bound so the event loop stays responsive during FluidSynth rendering
  - ui.download calls fixed to the installed NiceGUI 3.14.0 positional signature (no content= kwarg)
affects: [loop-coach-ui, export-flows, notation-rendering]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "OSMD/other page-scoped body scripts must be loaded via ui.add_body_html during initial page build, never inside a function invoked from a later click handler (add_body_html is a silent no-op after page delivery)"
    - "Long-running synchronous work (e.g. FluidSynth subprocess rendering) inside an async NiceGUI event handler is awaited via nicegui.run.io_bound(fn, **kwargs) to avoid blocking the event loop"

key-files:
  created: []
  modified:
    - app/pages/loop_coach.py
    - tests/test_loop_coach_audio.py

key-decisions:
  - "Extracted _load_osmd_script() as a standalone module function called once near the top of create_loop_coach_page(), rather than inlining the script tags at the call site, so the fix is independently testable"

patterns-established:
  - "_FakeUi test double extended with add_body_html/button/download/row/run_javascript fakes plus _FakeButton/_FakeRow/_FakeContainer helpers for unit-testing NiceGUI render helpers without a real browser context"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-07-15
---

# Phase quick-260715-3fo: Hotfix Loop Coach UI (OSMD/generation/download) Summary

**Fixed three production-breaking bugs in the Loop Coach page: OSMD notation never rendered (script tag added after page delivery), Generate froze the UI for 1-3 minutes (sync FluidSynth call on the event loop), and every export button crashed (`ui.download(content=...)` doesn't match the installed NiceGUI 3.14.0 signature).**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-15T05:41:00Z
- **Completed:** 2026-07-15T05:53:27Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- Notation now renders reliably: OSMD `<script>` tags load once during `create_loop_coach_page()` build, before any click handler can run, closing the "add_body_html after page delivery is a silent no-op" failure mode.
- Generate no longer freezes the browser: `do_generate` is now `async def` and awaits `run.io_bound(generate_loop_variants, ...)`, keeping the NiceGUI event loop responsive during the 1-3 minute FluidSynth render.
- All three export buttons (MusicXML, MIDI, WAV) call `ui.download` with bytes as the first positional argument, matching the installed NiceGUI 3.14.0 API (`ui.download(src, filename=None, media_type='')`) — no more `TypeError` from the nonexistent `content=` kwarg.
- Locked all three fixes in with regression tests using the existing hand-rolled `_FakeUi` monkeypatch pattern.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix OSMD load timing, async generation, and ui.download calls** - `9871988` (fix)
2. **Task 2: Add regression tests for OSMD timing and ui.download contract** - `787fd1a` (test)

**Plan metadata:** committed separately by the orchestrator (SUMMARY.md, STATE.md)

## Files Created/Modified
- `app/pages/loop_coach.py` - Extracted `_load_osmd_script()` called once during page build; `do_generate` is now `async def` awaiting `run.io_bound(generate_loop_variants, ...)`; all three `ui.download` calls pass bytes positionally (no `content=` kwarg)
- `tests/test_loop_coach_audio.py` - Extended `_FakeUi` with `add_body_html`/`button`/`download`/`row`/`run_javascript` fakes plus `_FakeButton`/`_FakeRow`/`_FakeContainer` helpers; added 3 regression tests for OSMD script-load timing and the `ui.download` positional-bytes contract

## Decisions Made
- Kept `_load_osmd_script()` as a standalone function (not inlined at the call site) so the OSMD-load timing fix is independently unit-testable via monkeypatch, matching the plan's `must_haves.artifacts` requirement.

## Deviations from Plan

None - plan executed exactly as written. All three fixes (OSMD timing, async generation, ui.download positional args) and both tasks matched the plan's task breakdown precisely; no additional bugs, missing functionality, or blocking issues were discovered during execution.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Loop Coach page's three core interactive flows (see notation, generate without freezing, download files) are restored on `hotfix/loop-coach-notation-audio`.
- Full `tests/` suite green: 187 passed, 0 failures (baseline 184 + 3 new regression tests).
- Storage-restore path and duet rehearsal-loop audio rendering verified unchanged (existing tests for `_render_variant_audio` still pass; `_render_variant_cards` regression test confirms no `add_body_html` calls leak out of it).
- Ready for the hotfix branch to be merged/PR'd; no blockers.

---
*Phase: quick-260715-3fo*
*Completed: 2026-07-15*

## Self-Check: PASSED

- FOUND: app/pages/loop_coach.py
- FOUND: tests/test_loop_coach_audio.py
- FOUND: commit 9871988
- FOUND: commit 787fd1a
