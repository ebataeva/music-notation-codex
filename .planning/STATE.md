---
gsd_state_version: 1.0
milestone: v1
milestone_name: Loop Coach MVP
status: phase_complete
last_updated: "2026-09-16T07:03:38.000Z"
last_activity: 2026-09-16 -- Quick task 260916-bta implemented Prompt 2; 1115 Python tests and 7 Playwright tests passed; uncommitted
progress:
  total_phases: 10
  completed_phases: 9
  total_plans: 12
  completed_plans: 12
  percent: 90
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-22)

**Core value:** Turn a chord progression into several playable electric-cello loop ideas, each explained by the music theory behind why it works.
**Current focus:** Phase 9 — recorder feedback complete; next up Phase 10 (Loop Library)

## Current Position

Phase: 09 (recorder-feedback) — COMPLETE (implemented and smoke-tested 2026-07-06)
Plan: 1 of 1
Status: Phase 09 implemented; next up Phase 10 (Loop Library)
Last activity: 2026-09-23 - Completed quick task 260923-pge: distinct takes and take-specific explanations

Progress: [█████████░] 90%

## Performance Metrics

**Velocity:**

- Total plans completed: 12
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 02 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Brownfield refactor — CLI scripts become thin wrappers over core/ library before any Streamlit work begins
- Roadmap: must-do-early guards (validate_pitch, validate_bar_duration, session_state arch, MCP degradation) anchored in earliest phases
- Roadmap: duet, drums, looper slots are v2 — excluded from this roadmap
- Review 2026-07-04: GenerationTrace fields designed into Phase 1 dataclasses (transparency for reflective blog + grounded explanations)
- Review 2026-07-04: progression-driven generation split out as Phase 2.5 — the hardest musical-algorithm work, previously hidden in Phase 2
- Review 2026-07-04: content layer = phases 10–12 (Loop Library, Content Pack, Transparency & Compare); content calendar and presentation mode deferred to v2

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 5: FluidSynth + soundfont availability on this macOS machine must be validated before Phase 5 starts (`brew install fluidsynth`)
- Phase 10: decide storage shape for saved loops (browser storage vs local app persistence) before implementation

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260706-21y | Fix v1 audit tech-debt tails: SAFE-01 max-notes guard, English preset/CLI copy (PLAT-02), MoodPreset deep-immutability (WR-05) | 2026-07-06 | 77594d2 | [260706-21y-fix-v1-audit-tech-debt-tails-safe-01-max](./quick/260706-21y-fix-v1-audit-tech-debt-tails-safe-01-max/) |
| 260714-v3b | Fix explainer crash: duet presets have dict texture_idiom, explainer expects string | 2026-07-14 | 9b29371 | [260714-v3b-fix-explainer-crash-duet-presets-have-di](./quick/260714-v3b-fix-explainer-crash-duet-presets-have-di/) |
| 260916-bta | Prompt 2: concise Theory cards, 19 contextual dictionary articles with notation/audio, and transition guidance; 1115 Python and 7 Playwright tests passed | 2026-09-16 | bb9c822 | Approved plan in conversation; executed inline without new documentation |
| 260831-s8m | Close the loop seam: tessitura anchor + closing-tone selection so generated loops come home instead of jumping up to 22 semitones at the repeat | 2026-08-31 | dfc71cf | [260831-s8m-fix-loop-seam-cyclic-playability](./quick/260831-s8m-fix-loop-seam-cyclic-playability/) |
| 260920-0xn | Merge pedal into codex/theory-dictionary: seam, READ-01, KEY-01 single path, advisor, pedalboard; played_pitches in the trace; short per-take cards; 1144 Python and 10 Playwright tests passed | 2026-09-20 | b50b321 | [260920-0xn-merge-pedal-into-codex-theory-dictionary](./quick/260920-0xn-merge-pedal-into-codex-theory-dictionary/) |
| 260920-pxe | Stop the golden regression test overwriting scores/: MNC_SCORES_DIR override on ExportEngine, test runs the 7 CLI invocations into tmp_path; baseline untouched; 1147 Python tests passed and the tree stays clean | 2026-09-20 | 8801797 | [260920-pxe-stop-golden-regression-test-from-overwri](./quick/260920-pxe-stop-golden-regression-test-from-overwri/) |
| 260923-pge | Port cd5de99: distinct takes (engine re-draw) and take-specific explanations with Bb-style flats | 2026-09-23 | b205330 | [260923-pge-port-cd5de99-distinct-why-it-works-expla](./quick/260923-pge-port-cd5de99-distinct-why-it-works-expla/) |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v2 | DUET-01 Violin duet mode | Deferred | Roadmap creation |
| v2 | DRUM-01 Drum machine | Deferred | Roadmap creation |
| v2 | SLOT-01 Looper slots | Deferred | Roadmap creation |
| v2 | INPUT-04 Humming/voice input | Deferred | Roadmap creation |
| v2 | THEORY-03 LLM-generated explanations | Deferred | Roadmap creation |

## Session Continuity

Last session: 2026-09-20T00:00:00.000Z
Stopped at: Completed quick task 260920-pxe (golden regression test no longer writes into scores/)
Resume file: None
