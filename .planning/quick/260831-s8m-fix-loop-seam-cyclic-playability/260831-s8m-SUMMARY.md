---
task: 260831-s8m
title: Close the loop seam — generated loops were unplayable at the repeat
subsystem: core/engine
tags: [bugfix, loop-generation, playability, voice-leading, invariants]
dependency-graph:
  requires: []
  provides: [_playable_candidates, _closing_pitch, _voice_leading_steps, cyclic_adjacencies, LOOP_SEAM_MARKER]
  affects: [core/theory/explainer.py, app/services/generation.py]
tech-stack:
  added: []
  patterns:
    - "For a cyclic artifact, verify invariants over cyclic adjacencies (zip(xs, xs[1:] + xs[:1])), never linear ones — the wrap-around pair is a real adjacency the user performs."
    - "Guarantee an invariant by construction (constrain the candidate set) rather than by post-hoc repair, and record the non-emptiness proof next to the filter."
key-files:
  created:
    - tests/test_loop_cyclic_playability.py
  modified:
    - core/engine/loop_engine.py
    - core/models.py
    - core/theory/explainer.py
decisions:
  - "The loop's final slot chooses which chord tone sounds, not just its octave — matching how the curated presets close. Restricting it to the round-robin tone makes a <=7 semitone seam unreachable (a B against a C2 anchor is a major seventh away in every octave)."
  - "The closing note is selected before the register-bias narrowing: the bias shapes the body of the loop, but on the closing note coming home outranks the octave preference."
  - "LOOP_SEAM_MARKER lives in core/models.py (the shared data contract) so the engine that writes it and the explainer that reads it share one literal without depending on each other."
  - "test_build_progression_score_does_not_monotonically_climb_to_ceiling was left untouched — it passed unmodified, so the anchor-relative rewrite the plan held in reserve was not needed."
metrics:
  duration: "~35 minutes"
  completed: 2026-08-31
---

# Quick Task 260831-s8m: Close the loop seam

Generated cello loops were formally correct and unplayable as loops. Every note sat in range, every bar summed to its meter, every chord tone was clean, the MusicXML validated, and all 187 tests passed — while 17% of loops asked the player to jump up to 22 semitones at the moment of repeat.

## The Defect

`core/engine/loop_engine.py` promised, in code and in its docstring, "avoiding leaps larger than an octave between consecutive notes", and delivered — for the *linear* note sequence. `previous_pitch` started as `None` in bar 1 and the last note was never compared against the first.

But the artifact is a **cycle**. `app/pages/loop_coach.py:262` renders `<audio ... loop>`, and the cellist repeats the figure live. The last-note → first-note pair is an adjacency the player physically performs on every pass, and neither the engine nor any test ever looked at it.

The existing guards (`tests/test_loop_engine.py:390`, `:440`) walk `zip(notes, notes[1:])` — n−1 adjacencies out of n. The n−1 → 0 pair was checked nowhere.

**Minimal counterexample** — one chord, one bar:

```
Am, dark_trip_hop, seed=1, bias=default  ->  A2 C3 E3 A2 C3 E3 A3 C4
max leap inside the bar: 7 semitones
on repeat: C4 -> A2 = 15 semitones
```

**Measured over 900 generations** (`Am F C G` × 3 biases × 300 seeds): seam > octave in 17% of loops, max 22 semitones.

**Reference standard, measured rather than invented** — the four hand-authored solo presets via `build_score`:

| preset | first | last | seam | max leap inside |
|---|---|---|---|---|
| dark_trip_hop | C2 | C2 | 0 | 14 |
| driving_cinematic | C2 | G2 | 7 | 14 |
| noir_slow_burn | A2 | A2 | 0 | 9 |
| ritual_tribal | D2 | D2 | 0 | 14 |

The human author's priorities are the exact inverse of the code's: 14-semitone leaps inside a bar are fine, the seam never is.

## What Was Done

**Task 1 — tessitura anchor and loop closure (`core/engine/loop_engine.py`)**

Added `MAX_MELODIC_LEAP_SEMITONES = 12` (replacing the magic literal) and `LOOP_TESSITURA_SEMITONES = 12`.

Extracted `_playable_candidates(pitch_class, previous_pitch, anchor_pitch)`, which applies the two loop constraints in order: the tessitura band around the loop's opening note, then the max-leap rule. The band is what makes the seam safe **by construction** — if every note is within ±12 of the anchor and the anchor is the first note, then `|last − first| ≤ 12` follows. The non-emptiness proof is recorded next to the filter: candidates of one pitch class sit 12 semitones apart across [36, 74]; for any anchor in that range the band-range intersection is ≥ 13 integers wide, and such a window holds exactly one member of every residue class mod 12.

Added `_closing_pitch(chord, previous_pitch, anchor_pitch)`: the loop's final slot picks whichever chord tone — in any playable octave — lands nearest the anchor, over candidates that already passed both filters, so closing the loop can never introduce an unplayable interval.

`_register_map_chord` now threads `anchor_pitch` and `close_last` and returns a 3-tuple; the first note chosen becomes the anchor, which preserves the rng draw order for that note. `build_progression_score` threads the anchor through the bar loop and marks the final bar.

**Task 2 — the pedagogical half (`core/models.py`, `core/theory/explainer.py`)**

`voice_leading_steps` was hardcoded to `None` with the comment "future refinement", so the coaching layer described every bar except the moment the player repeats. `_voice_leading_steps()` now emits one step per performed adjacency with the wrap entry suffixed `LOOP_SEAM_MARKER`.

`_loop_seam_clause()` in the explainer appends a sentence naming that move to `how_to_end`, and returns `""` when the trace carries no seam so preset-verbatim variants keep their original wording. It computes the interval through the explainer's existing `_semitone` helper plus a new `_absolute_semitone`, keeping the module music21-free.

**Task 3 — not needed.** The plan held a rewrite in reserve for `test_build_progression_score_does_not_monotonically_climb_to_ceiling`, whose absolute `min(midis) <= 43` floor was expected to conflict with anchoring. It passed unmodified, so it was left alone.

## Verification

- `.venv/bin/python -m pytest tests/ -q` — **193 passed**, 0 failures (187 pre-existing + 6 new).
- `.venv/bin/python -m pytest tests/test_golden_regression.py -q` — 2 passed, no baseline recapture. The preset-verbatim paths were never touched.
- Re-ran the 900-generation measurement: seam **max 22 → 2** semitones, **mean 2.0**, violation rate **17% → 0%**. Internal leaps unchanged at max 12 (the cap).
- Every counterexample from the plan closed:

  | case | seam before | after |
  |---|---|---|
  | `Am` seed=1 default | 15 | **0** (returns to A2 exactly) |
  | `Am F` seed=5 high | 24 | **0** |
  | `C G` seed=2 default | 23 | 2 |
  | `Am F C G` seed=0 high | 22 | 2 |

- Explainer output for `Am F C G`, seed=42: seam step `G2->A2 (loop)`, and `how_to_end` reads "… The repeat itself is the move G2->A2 — 2 semitones back to the opening note, so keep that return in the hand and the loop comes round without a jump."
- `git diff --stat` limited to `core/engine/loop_engine.py`, `core/models.py`, `core/theory/explainer.py` plus the new test. The pre-existing uncommitted diffs in `AGENTS.md`, `CONTEXT.md`, `README.md`, `scores/musicxml/*` and untracked `duet_card.png` are untouched.

## The Reusable Part

`tests/test_loop_cyclic_playability.py` carries `cyclic_adjacencies(items)`, returning `(i, items[i], items[(i+1) % len])`. The bug class it catches is **"invariant verified on the linear sequence while the artifact is cyclic"** — the seam leap was one instance; register continuity, enharmonic spelling, dynamics and string crossings are the same shape. Any future invariant about a looped artifact should run through it instead of `zip(xs, xs[1:])`.

The file also guards the reference: the four curated presets must keep closing within 7 semitones, so future preset authoring cannot quietly erode the standard the generated bound is calibrated against.

## Deviations from Plan

**1. Closing note selects the chord tone, not just the octave**
- **Found during:** Task 1 verification — the first implementation, which only chose the octave of the round-robin tone, still left 39 loops above the 7-semitone bar (worst 12).
- **Cause:** two distinct blockers. The register-bias filter discarded the nearest candidate (`A3->A2 = 12` when A2 was available but octave 2 fell outside the biased pool), and the round-robin tone was sometimes unreachable in principle (`B2->C2 = 11`: no B sits within 7 semitones of a C2 anchor in any octave).
- **Fix:** moved the closing selection ahead of the bias narrowing, and let it range over all of the final chord's tones. This is what the curated presets do — they close by choosing which tone ends the bar.
- **Effect:** the 7-semitone bound became reachable everywhere in the matrix; measured max is 2.

**2. Task 3 skipped** — the absolute-floor test passed unmodified, so it was not rewritten. Fewer changes than planned, not more.

## Commits

- `dfc71cf` — fix(quick-260831-s8m): close the loop seam in generated cello loops

## Self-Check: PASSED

- FOUND: `core/engine/loop_engine.py` contains `LOOP_TESSITURA_SEMITONES`, `_playable_candidates`, `_closing_pitch`
- FOUND: `core/models.py` contains `LOOP_SEAM_MARKER`
- FOUND: `core/theory/explainer.py` contains `_loop_seam_clause`
- FOUND: `tests/test_loop_cyclic_playability.py` contains `cyclic_adjacencies`
- FOUND: commit `dfc71cf`
- FOUND: 193 passed, 0 failures in the full suite
