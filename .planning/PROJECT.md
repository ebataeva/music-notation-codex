# music-notation-codex

## What This Is

A local web app that acts as a **loop coach and practice partner for an electric cellist**. You enter a chord progression (as text) plus a mood/key, and it returns several playable loop ideas as cello notation — each one explained with the music theory behind *why* it works, plus guidance on how to start, develop, end, and transition the loop. You can hear the vibe in the browser before playing it live, and export to MusicXML/MIDI. It also lets you **record your own playing and get analysis + concrete suggestions on how to improve** (via an Audio Analysis MCP), and ask on-demand questions about your music. It grows to add a violin layer (duet) and a drum machine.

## Core Value

Turn a chord progression into several playable electric-cello loop ideas, each explained by the music theory behind why it works — so playing stops being boring and the "vibe" becomes reachable.

## Requirements

### Validated

<!-- Inferred from the existing CLI scripts — the generation/export engine already works. -->

- ✓ Generates 8-bar cello ostinato patterns across mood presets (noir, ritual, trip-hop, cinematic) — existing (`scripts/generate_cello_dark_ostinato.py`)
- ✓ Exports playable material to MusicXML (MuseScore) and MIDI (Ableton) — existing
- ✓ Provides text-based harmony, modulation, and mood advice per genre — existing (`scripts/harmony_advisor.py`)

### Active

<!-- New scope being built toward. Hypotheses until shipped. -->

- [ ] Local web UI (Streamlit) that drives the whole workflow interactively from one command
- [ ] Enter a chord progression as text (e.g. `Am F C G`) plus key/mood as the starting point
- [ ] Generate several distinct loop variants for the same input
- [ ] Explain each variant in plain language: the music theory of *why* it works
- [ ] Guidance on how to start, develop, end, and make a transition for a loop
- [ ] In-browser playback to hear the vibe before playing it on the cello
- [ ] Record the user's own cello playing and get analysis + concrete suggestions on how to improve (via Audio Analysis MCP)
- [ ] Ask on-demand questions and get music advice about a loop or a recording
- [ ] Violin layer / duet mode (cello + violin)
- [ ] Drum-machine pattern generation compatible with Ableton
- [ ] Looper-style slots/sections that can be regenerated independently
- [ ] Export MusicXML and MIDI from the UI

### Out of Scope

- Audio analysis of *third-party* tracks (extracting chords from someone else's MP3/Spotify/YouTube file) — not needed; chords are found online or known by ear, and full-track transcription is high-complexity. (Note: analysis of the user's *own* playing for feedback IS in scope, via the Audio Analysis MCP.)
- Humming/voice melody input — deferred to a later version; pitch detection adds significant complexity, and chord-text input covers the main workflow first
- Mobile app — this is a personal local tool, web-first on the desktop
- Live audio effects / DAW replacement — Ableton and MuseScore handle performance and final editing downstream

## Context

- Brownfield: the project starts from two working CLI scripts (`generate_cello_dark_ostinato.py`, `harmony_advisor.py`) built on Python + `music21`, producing files in `scores/musicxml/` and `scores/midi/`.
- The user plays **electric cello** live, finds playing straight from chords boring, and is a beginner-to-intermediate in music theory — the app must *explain*, not just generate.
- Real pain points driving this: theory feels opaque, breaking songs into loops and making covers is hard, transitions and timing are hard, and "vibey/sexy" loops "just don't work out."
- Runs locally on macOS; existing `.venv` and `requirements.txt` already in place.
- The performance-feedback feature depends on an external **Audio Analysis MCP** server (to be connected). The user records playing → the MCP analyzes it → the app turns the analysis into plain-language suggestions and answers on-demand questions.

## Constraints

- **Tech stack**: Streamlit UI + Python/`music21` engine — local Python-first project, keep it simple and runnable from one command.
- **Language**: All visible UI copy in English; code comments in English and only where they clarify non-obvious logic — locked project decision.
- **Testing**: UI/browser tests live in a *separate* Playwright-based framework under `tests-ui/`, driving Chrome/Chromium via ChromeDriver — locked decision (keeps app code clean, enables real browser regression).
- **Reporting**: UI test reports generated in Allure format — locked decision.
- **Platform**: Local desktop tool; no hosting/deployment in scope.
- **Dependency**: Performance feedback relies on an external Audio Analysis MCP server — the app must degrade gracefully (stay usable for loop coaching) when the MCP is unavailable.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start from chord-text input; defer humming/voice input | Reliable and simple; covers the main workflow without pitch-detection complexity | — Pending |
| Core value is the cello loop coach with theory; violin duet + drums layer on after | Keeps the heart tight so the project doesn't sprawl, even though v1 scope includes duet + drums | — Pending |
| Streamlit for the first web interface | Local Python-first project; fastest path to an interactive workspace | — Pending |
| No audio analysis of third-party songs | High complexity, not required by the actual workflow | — Pending |
| Use an external Audio Analysis MCP for performance feedback (record → analyze → improve) in v1 | The user wants to record her own playing and ask how to improve; an MCP provides analysis without building DSP from scratch | — Pending |
| Separate Playwright + ChromeDriver test framework, Allure reports | Keep app code clean; real-browser regression with shareable reports | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-04 after Phase 1 completion (core library skeleton + validators: LOOP-03, LOOP-04, PLAT-03 verified)*
