# music-notation-codex Brain

## Project identity

Local music-notation workflow for composing and exporting violin + cello duet material, cello ostinatos, looper-style sections, drum-machine MIDI, MusicXML for MuseScore, and MIDI for Ableton.

## Current direction

The project is moving from CLI scripts into a local web interface. The planned app should be a practical composition workspace, not a landing page. Its heart is a **loop coach for an electric cellist**: enter chords (text) + mood, get several playable cello loop variants with plain-language music-theory explanations and start/develop/end/transition guidance, hear the vibe, and export. It also acts as a **practice partner**: the user records her own playing and gets analysis + concrete suggestions on how to improve, plus on-demand music Q&A.

## Locked decisions

- Application language: English for all visible UI copy.
- Code comments: English only, and only where comments clarify non-obvious logic.
- Frontend/app framework: Streamlit for the first local web interface.
- Music engine: Python + music21 remains the core generation/export layer.
- Instruments: violin + cello duet as first-class arrangement mode.
- Performance workflow: looper-style slots/sections and drum-machine MIDI for Ableton.
- Exports: MusicXML for MuseScore, MIDI for Ableton.
- Primary input: chord progressions as text + key/mood (humming/voice melody input deferred to a later version).
- Performance feedback (v1): record the user's own electric-cello playing -> analyze via an external Audio Analysis MCP -> return plain-language suggestions and answer on-demand questions. App must stay usable for loop coaching when the MCP is unavailable.
- Out of scope: extracting chords from third-party audio tracks (MP3/Spotify/YouTube) — only the user's own playing is analyzed.
- Testing: UI/browser tests must live in a separate Playwright-based test framework under `tests-ui/`, isolated from the app code.
- Browser execution: Playwright drives Chrome/Chromium via ChromeDriver (ChromeDriver is a hard requirement, not just "compatible").
- Reports: UI test reports must be generated in Allure format.

## Existing artifacts

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/phase-01-web-interface/01-PLAN.md`
- `scripts/generate_cello_dark_ostinato.py`
- `scripts/harmony_advisor.py`

## Next implementation phase

Implement Phase 1 from `.planning/phases/phase-01-web-interface/01-PLAN.md`.
