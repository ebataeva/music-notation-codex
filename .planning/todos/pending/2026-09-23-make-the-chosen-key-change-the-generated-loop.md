---
created: 2026-09-23T17:12:18.067Z
title: Make the chosen key change the generated loop
area: engine
severity: major
files:
  - core/engine/loop_engine.py:590 (build_progression_score)
  - core/engine/loop_engine.py:490 (_register_map_chord)
  - app/services/generation.py:372 (key_tonic/key_mode -> preset)
---

## Problem

Changing Key tonic / Key mode in the UI does not change the generated loop at all. Same progression + same seed gives note-for-note identical takes in every key — the whole melody always starts from the same note.

Verified 2026-09-23 on branch worktree-ecstatic-heisenberg-728342: "Cm Ab Eb Bb", dark_trip_hop, seed=7 → first bar of every take is identical in C minor, A minor and E major (low: C2-Eb2-G2-C2). The key only changes:
- the printed key signature (KEY-01);
- the explanation's reference ("relative to A", "chromatic notes add color around the reference tonic A").

Cause: notes come only from the absolute chord symbols (build_progression_score / _register_map_chord); key_tonic/key_mode never reach the pitch choice. Reported by the user while reviewing quick task 260923-pge.

## Solution

TBD — first decide the intended behavior with the user:
- (a) treat the progression as relative to the key and transpose it (e.g. a "Cm Ab Eb Bb" in C minor becomes "Am F C G" in A minor);
- (b) keep the chords as typed, but let the key shape the line: anchor/start/emphasis on the tonic or a key-relevant chord tone;
- (c) warn when the progression does not fit the chosen key (the explainer already detects "chromatic notes around the reference tonic").

Whatever is chosen: write a failing test first (same progression + seed, different key → assert the intended difference), keep SPELL-01 (spell from the chord), keep LOOP-02 (takes distinct) and the loop-seam constraints.
