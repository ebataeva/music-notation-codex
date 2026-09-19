---
task: 260920-0xn
title: Merge pedal into codex/theory-dictionary
status: complete
subsystem: core/theory, app/pages, app/services
tags: [merge, theory, loop-seam, read-01, key-01, short-cards]
dependency-graph:
  requires: [260831-s8m, 260901-p4d, 260916-bta]
  provides: [merge/pedal-into-theory, GenerationTrace.played_pitches, _render_theory_section]
  affects: [core/theory/explainer.py, app/pages/loop_coach.py, app/services/generation.py, core/models.py, core/engine/loop_engine.py]
tech-stack:
  added: []
  patterns:
    - "Per-take sentences (melodic shape, loop seam) are computed once in explain() and injected into both the long text and the short card sections, so cards differ without touching summaries.py."
    - "The chord inventory separates what was supplied from what each bar sounds; READ-01 keeps a bar to a few notes, so tests assert played notes are a subset of chord tones, not equal to them."
key-files:
  created:
    - .planning/quick/260920-0xn-merge-pedal-into-codex-theory-dictionary/260920-0xn-PLAN.md
  modified:
    - core/theory/explainer.py
    - app/pages/loop_coach.py
    - app/services/generation.py
    - core/models.py
    - core/engine/loop_engine.py
    - tests/test_theory_musical_correctness.py
    - tests/test_models.py
    - .planning/STATE.md
decisions:
  - "pedal is merged on top of Codex, not the other way round: pedal's explainer changes are additive functions, Codex's are a rewrite."
  - "KEY-01 keeps Codex's path (preset replaced once with the player's key); pedal's key kwargs are no longer passed from generation.py. The engine still accepts them for direct callers."
  - "READ-01 wins over 'every chord tone sounds in its bar': the loop must read at sight. The explanation now says what was supplied and what each bar sounds; Codex's 12 agreement tests assert subset, not equality."
  - "Cards show the short sections only. The 'not an inferred cadence' hedge stays in the long text; on the card, how_to_end is the return plus the seam, two sentences."
  - "Notation uses Codex's shared component (app/components/notation.py); pedal's inline OSMD block is dropped, its w-full lesson is kept as a comment."
metrics:
  duration: "~1.5 hours including the audit-driven decisions"
  completed: 2026-09-20
---

# Quick Task 260920-0xn: merge pedal into codex/theory-dictionary

Branch `merge/pedal-into-theory` from `codex/theory-dictionary` (`bbe0a8c`), merge commit `b50b321` bringing in `pedal` (`ee30c7f`). Conflicts in four files, resolved by hand; nothing was pushed and nothing touched `main`.

## What changed beyond the mechanical merge

- **`core/theory/explainer.py`**: Codex version as base. Added back `_absolute_semitone` (now parses music21 flats such as `D-3`), `_melodic_shape_clause` and `_loop_seam_clause`, both shortened to one or two sentences. The shape sentence leads `why_it_works`; the seam sentence ends `how_to_end`; both are also injected into `short_sections`, and the card's `how_to_end` keeps only the return sentence plus the seam. `_chord_inventory` now takes the played notes and says what each bar sounds.
- **`core/models.py` / `core/engine/loop_engine.py`**: `GenerationTrace.played_pitches`, one list of octave-bearing names per bar, recorded next to `chord_tones_used`.
- **`app/services/generation.py`**: one KEY-01 path; both theory import blocks kept.
- **`app/pages/loop_coach.py`**: Codex base (key selectors, short sections, dictionary links, shared notation component) plus pedal's Sheeran and pedalboard guides, the progression advisor, and the card order: notation and audio first, "Why it works" open, the rest folded under "How to play it". New `_render_theory_section` renders each section with its `theory-{i}-{key}` test id and `term-{i}-{key}-{id}` links, so Codex's Playwright tests keep working inside pedal's layout.
- **`tests/test_theory_musical_correctness.py`**: the 12 `test_parsed_input_score_and_explanation_agree` cases assert played notes ⊆ chord tones, ≤ 4 notes per bar, the trace matches the score, and the explanation names both the supplied tones and what the bar sounds. `tests/test_models.py` lists the new trace field.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | 1144 passed (pedal 216 + Codex 1115 + 2 new trace/inventory assertions, no test deleted or skipped) |
| Golden regression | green, baseline not recaptured; the run's MusicXML id/date noise reverted before committing |
| `.venv/bin/python -m pytest tests-ui/ -q` | 10 passed (pedal's guides, real notation width, three cards; Codex's dictionary routing, card link, authored duet) |
| Browser, `Am F C G` in A minor, dark_trip_hop | three cards; SVG width 283 px each; three audio players; card sections 16–34 words, 2 sentences; first sentence per take (`A2->C2`, `A3->C3`, `A4->C4`); seam `G2->A2` named in How to end; dictionary links under Why it works; Suggest progression shows 7 cards |

## Known limits

- The three takes are register transpositions of one seed, so their first sentences differ only by octave names. Different shapes per take would need the engine to vary the line, not just the register.
- Duet presets still ignore the entered progression (open question for the user).
- Shared spelling bug from before the merge: A7 in D minor prints Db instead of C#.
