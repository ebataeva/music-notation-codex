# music-notation-codex Brain

## Project identity

Local music-notation workflow for composing and exporting violin + cello duet material, cello ostinatos, looper-style sections, drum-machine MIDI, MusicXML for MuseScore, and MIDI for Ableton.

## Current direction

The project is moving from CLI scripts into a local web interface. The planned app should be a practical composition workspace, not a landing page.

## Locked decisions

- Application language: English for all visible UI copy.
- Code comments: English only, and only where comments clarify non-obvious logic.
- Frontend/app framework: Streamlit for the first local web interface.
- Music engine: Python + music21 remains the core generation/export layer.
- Instruments: violin + cello duet as first-class arrangement mode.
- Performance workflow: looper-style slots/sections and drum-machine MIDI for Ableton.
- Exports: MusicXML for MuseScore, MIDI for Ableton.
- Testing: UI/browser tests must live in a separate Playwright-based test framework under `tests-ui/`.
- Browser execution: Playwright should run against Chromium/Chrome with ChromeDriver-compatible browser execution expectations.
- Reports: UI test reports must be generated in Allure format.

## Existing artifacts

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/phases/phase-01-web-interface/01-PLAN.md`
- `scripts/generate_cello_dark_ostinato.py`
- `scripts/harmony_advisor.py`

## Next implementation phase

Implement Phase 1 from `.planning/phases/phase-01-web-interface/01-PLAN.md`.
