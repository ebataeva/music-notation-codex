---
task: 260901-p4d
title: Pedalboard guide — Atmosphere → Aquarius → Twin Looper, tied to the loop seam
subsystem: app/pages
tags: [ui, hardware-guide, looper, pedalboard, loop-seam]
dependency-graph:
  requires: [260831-s8m]
  provides: [_render_pedalboard_guide]
  affects: [app/pages/loop_coach.py, tests-ui/test_loop_coach_happy_path.py]
tech-stack:
  added: []
  patterns:
    - "Hardware quick-setup guides live as collapsed ui.expansion panels in loop_coach with a data-testid, mirrored by a Playwright test — established by the Sheeran Looper+ guide (77e5a5b)."
key-files:
  created:
    - .claude/launch.json
  modified:
    - app/pages/loop_coach.py
    - tests-ui/test_loop_coach_happy_path.py
decisions:
  - "Power/polarity section dropped at the user's instruction — the board is already wired and working. Sources also disagreed on the Twin Looper's polarity, so asserting one would have been a fabricated hazard warning."
  - "The panel's payoff section is the loop seam, not a spec dump: both loopers splice at the punch-out point, and the two time-based pedals sit before them, so Atmosphere TRAIL and Aquarius F.BACK print their tails into that splice."
  - "Added .claude/launch.json so the app can be launched for browser verification without hand-rolling a server command."
metrics:
  duration: "~20 minutes"
  completed: 2026-09-01
---

# Quick Task 260901-p4d: Pedalboard guide for the real board

The user photographed the board this coach is actually played through and asked that the `pedal` branch account for it. Added a collapsed guide panel next to the existing Sheeran Looper+ one, following the same pattern.

## The Stack

Read off the photo, confirmed against vendor documentation:

| pedal | role | verified specs |
|---|---|---|
| JOYO Atmosphere | reverb | TRAIL on/off switch, DECAY / MIX / TONE |
| JOYO Aquarius R-07 | delay + looper | 8 delay modes, 5-minute looper, delay and looper usable simultaneously, 150 mA, DC 9 V centre-negative |
| VSN Twin Looper | stereo dual looper | 10 min recording, unlimited overdubs, undo/redo, 11 play types incl. reverse/stutter/bounce, stereo I/O with independent L/R level, 44.1 kHz / 24-bit, 105 dB dynamic range, in 2×1/4" 470 kΩ / out 2×1/4" 100 Ω, ~100 mA, 116×90×35 mm, 522 g, true bypass, full metal case |

## What Was Done

`_render_pedalboard_guide()` in `app/pages/loop_coach.py`, testid `pedalboard-guide`, with four sections:

1. **Signal chain** — cello → Atmosphere → Aquarius → Twin Looper LEFT IN → L/R OUT. States the consequence of the ordering plainly: both time-based pedals sit *before* the loopers, so whatever they are doing at punch-out is printed into the take and cannot be dialled back.
2. **Two loopers, one master** — the Aquarius carries its own 5-minute looper alongside the Twin Looper's 10 minutes. Drive one, leave the other on delay-only duty.
3. **Twin Looper controls** — LOOPER and FX footswitches, CHANGE forward/reverse, SPEED normal/fast, independent LEVEL L / LEVEL R.
4. **Closing the loop cleanly** (the point of the panel) — connects the hardware to quick task 260831-s8m. The generated loop now comes home, so the splice lands on a step the hand already knows; the two things that can still smear it are Atmosphere TRAIL left ON and Aquarius F.BACK left high while recording the foundation layer, because both keep sounding past the punch-out and get baked into the seam.

`test_pedalboard_guide` in `tests-ui/test_loop_coach_happy_path.py` mirrors the Sheeran test: collapsed by default, expands, asserts each section and both seam controls by name, checks the manual link target, and checks the expanded panel fits a 390 px viewport.

Added `.claude/launch.json` (`loop-coach`, `.venv/bin/python app/main.py`, port 8080) so the app can be launched for browser verification.

## Verification

- `.venv/bin/python -m pytest tests/ -q` — 193 passed, 0 failures.
- Launched the app and drove it in a real browser: the panel renders collapsed, expands with all four sections, both external links present, no console errors.
- End-to-end generation run in the browser (Example input → Generate): 3 variants produced, and all three coaching texts carry the seam sentence — "The repeat itself is the move G2->A2 — 2 semitones back to the opening note…", "G3->A3 — 2 semitones…" ×2. This also closes the manual browser check left outstanding from 260831-s8m.
- The pre-existing uncommitted diffs in `AGENTS.md`, `CONTEXT.md`, `README.md`, `scores/musicxml/*` and untracked `duet_card.png` remain untouched.

## Deviations from Plan

**1. Power section dropped mid-task.** The first draft included a power/polarity caution: the photo shows a daisy chain, and sources contradict each other on the Twin Looper's polarity (one lists 9 V AC positive-tip, another 9 V DC centre-negative). The user said the board is already wired and working, so the section was cut rather than shipped as a warning about a settled question.

**2. The fourth pedal.** A fourth gold pedal appears at the top-right of the photo with its panel mostly out of frame. The user identified the gold unit as the VSN Twin Looper, so the guide covers the three legible pedals and does not speculate about the partially visible one.

## Sources

- [VSN Twin Looper — Reverb listing](https://reverb.com/item/37122189-vsn-twin-looper)
- [VSN Twin Looper — Amazon listing with full specs](https://www.amazon.fr/VSN-guitare-%C3%A9lectrique-minutes-denregistrement/dp/B07YCB8GQD)
- [Rowin Twin Looper user manual — ManualsLib](https://www.manualslib.com/manual/1334821/Rowin-Twin-Looper.html)
- [JOYO R-07 Aquarius — official product page](https://www.joyoaudio.com/product/10.html)
- [JOYO R-07 Aquarius user manual](https://manuals.plus/joyo/r-07-aquarius-delay-looper-manual)
