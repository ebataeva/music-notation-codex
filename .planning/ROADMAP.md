# Roadmap: music-notation-codex

**Created:** 2026-06-22
**Milestone:** v1 — Loop Coach MVP
**Granularity:** fine
**Mode:** mvp
**Total phases:** 9
**Requirements covered:** 21/21

---

## Phases

- [ ] **Phase 1: Core Library Skeleton + Validators** - Pure-Python data structures, dataclasses, and guards (range + bar duration)
- [ ] **Phase 2: LoopEngine + ExportEngine** - Refactor CLI scripts into testable core engine; single-variant generation + file export
- [ ] **Phase 3: TheoryExplainer** - Template-driven plain-language explanations and loop lifecycle guidance
- [ ] **Phase 4: Streamlit Skeleton + Session State** - Interactive UI with chord/key/mood input; text output only; session_state architecture
- [ ] **Phase 5: Notation + Playback** - In-browser score rendering (OSMD) and audio playback (FluidSynth pipeline)
- [ ] **Phase 6: Export Panel** - MusicXML and MIDI download buttons wired to ExportEngine
- [ ] **Phase 7: 3-Variant Generation** - Generate and display 3 distinct cello loop variants per request
- [ ] **Phase 8: UI Test Framework** - Playwright + ChromeDriver + allure-pytest; loop coach happy-path coverage
- [ ] **Phase 9: MCP Gateway + Recorder + Feedback** - Audio recording, MCP analysis, Q&A, graceful degradation

---

## Phase Details

### Phase 1: Core Library Skeleton + Validators
**Goal:** The core/ library structure exists with all dataclasses, MoodPreset registry (merged from both CLI scripts), and validators that enforce cello range and bar duration correctness.
**Mode:** mvp
**Depends on:** Nothing (brownfield refactor from scripts/)
**Requirements:** LOOP-03, LOOP-04, PLAT-03
**Success Criteria** (what must be TRUE):
  1. A note outside C2-D5 raises a validation error at generation time (confirmed by a passing pytest unit test)
  2. A rhythm pattern whose durations do not sum to the bar length raises a validation error (confirmed by unit test)
  3. All existing CLI scripts still produce the same output files after refactoring their data into core/presets/
**Plans:** TBD

### Phase 2: LoopEngine + ExportEngine
**Goal:** The generation logic from generate_cello_dark_ostinato.py lives in core/engine/loop_engine.py and core/export/exporter.py; the script becomes a thin wrapper; a single cello loop variant can be generated and exported entirely from pure-Python code.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** LOOP-01
**Success Criteria** (what must be TRUE):
  1. Calling LoopEngine.build_score() with a MoodPreset and chord progression returns a music21 Score object with no errors
  2. Calling ExportEngine.export_to_musicxml() and export_to_midi() writes valid files to scores/musicxml/ and scores/midi/
  3. The existing scripts/generate_cello_dark_ostinato.py runs via its thin wrapper and produces identical output to before the refactor
**Plans:** TBD

### Phase 3: TheoryExplainer
**Goal:** The harmony text from harmony_advisor.py lives in core/theory/explainer.py as structured TheoryExplanation dataclasses; given a LoopVariant and MoodPreset, the explainer returns plain-language "why it works" + start/develop/end/transition guidance.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** THEORY-01, THEORY-02
**Success Criteria** (what must be TRUE):
  1. TheoryExplainer.explain() returns a TheoryExplanation with all five fields populated (why_it_works, how_to_start, how_to_develop, how_to_end, how_to_transition) for every supported mood preset
  2. The why_it_works text contains no unexplained jargon — verified by manual review of at least 4 presets
  3. The how_to_start and how_to_transition fields include practical cello-specific cues (not generic piano/guitar language)
**Plans:** TBD

### Phase 4: Streamlit Skeleton + Session State
**Goal:** The Streamlit app launches with one command, shows chord/key/mood input widgets, generates a loop on submit, and displays the theory explanation as text — with all results stored in session_state so reruns do not lose data.
**Mode:** mvp
**Depends on:** Phase 2, Phase 3
**Requirements:** INPUT-01, INPUT-02, INPUT-03, PLAT-01, PLAT-02
**Success Criteria** (what must be TRUE):
  1. Running `streamlit run app/main.py` opens the app in the browser with no errors
  2. User can type a chord progression (e.g. "Am F C G"), choose a key and mood from dropdowns, and click Generate
  3. After clicking Generate, the theory explanation text appears on the page without a traceback
  4. Refreshing the browser or clicking Generate again does not erase the previous result (session_state preserved)
  5. All visible UI labels and button text are in English
**Plans:** TBD
**UI hint**: yes

### Phase 5: Notation + Playback
**Goal:** After generation, the user can see the cello loop as readable notation rendered in the browser and hear it play back via an audio widget — without leaving the Streamlit app.
**Mode:** mvp
**Depends on:** Phase 4
**Requirements:** NOTATE-01, PLAY-01
**Success Criteria** (what must be TRUE):
  1. The generated loop appears as a readable musical score (OSMD SVG) on the loop coach page
  2. The user can press Play and hear the loop audio in the browser (FluidSynth MIDI-to-WAV pipeline)
  3. The notation and audio reflect the same loop that was generated (no mismatch between score and sound)
**Plans:** TBD
**UI hint**: yes

### Phase 6: Export Panel
**Goal:** The user can download the current loop as a MusicXML file (for MuseScore) and as a MIDI file (for Ableton) directly from the browser via download buttons.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** EXPORT-01, EXPORT-02
**Success Criteria** (what must be TRUE):
  1. Clicking "Download MusicXML" triggers a file download that MuseScore can open without errors
  2. Clicking "Download MIDI" triggers a file download that Ableton can import without errors
  3. Downloaded files contain the same loop variant the user generated and heard in the browser
**Plans:** TBD
**UI hint**: yes

### Phase 7: 3-Variant Generation
**Goal:** A single Generate request produces 3 distinct cello loop variants for the same chord progression and mood; each variant has its own notation, playback, theory explanation, and export — displayed side by side.
**Mode:** mvp
**Depends on:** Phase 6
**Requirements:** LOOP-02
**Success Criteria** (what must be TRUE):
  1. After clicking Generate, 3 variant cards appear on the page (Variant 1, Variant 2, Variant 3)
  2. The 3 variants are audibly different from each other (different rhythm, register, or voice-leading strategy)
  3. Each variant has its own notation, Play button, theory explanation, and Download buttons
  4. Generating again for the same input produces 3 new distinct variants (not identical to the previous run)
**Plans:** TBD
**UI hint**: yes

### Phase 8: UI Test Framework
**Goal:** A Playwright-based test suite in tests-ui/ runs against the live Streamlit app, covers the loop coach happy path, and produces Allure HTML reports — without importing any app or core code.
**Mode:** mvp
**Depends on:** Phase 7
**Requirements:** TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. Running `pytest tests-ui/` against a running Streamlit server executes at least one test end-to-end with no import errors
  2. The test for the loop coach happy path (enter chords → generate → see 3 variants) passes on Chrome/Chromium via ChromeDriver
  3. Running `allure generate` on the test output produces an HTML report showing pass/fail results
  4. tests-ui/ contains zero imports from core/ or app/ (import boundary enforced)
**Plans:** TBD

### Phase 9: MCP Gateway + Recorder + Feedback
**Goal:** The user can record her own cello playing in the browser, receive plain-language analysis and improvement suggestions via the Audio Analysis MCP, and ask on-demand questions — while the loop coach remains fully functional even when the MCP is offline.
**Mode:** mvp
**Depends on:** Phase 8
**Requirements:** FEEDBACK-01, FEEDBACK-02, FEEDBACK-03, FEEDBACK-04
**Success Criteria** (what must be TRUE):
  1. The recorder page allows the user to record audio via st.audio_input and save it as a WAV file
  2. When the Audio Analysis MCP is online, the app displays at least one concrete plain-language suggestion after analysis
  3. When the user types a question about the recording or loop, the app returns a music-relevant answer (MCP online)
  4. When the Audio Analysis MCP is offline, the recorder page shows a dismissable warning banner and the loop coach page functions normally with no error or traceback
**Plans:** TBD
**UI hint**: yes

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Library Skeleton + Validators | 0/0 | Not started | - |
| 2. LoopEngine + ExportEngine | 0/0 | Not started | - |
| 3. TheoryExplainer | 0/0 | Not started | - |
| 4. Streamlit Skeleton + Session State | 0/0 | Not started | - |
| 5. Notation + Playback | 0/0 | Not started | - |
| 6. Export Panel | 0/0 | Not started | - |
| 7. 3-Variant Generation | 0/0 | Not started | - |
| 8. UI Test Framework | 0/0 | Not started | - |
| 9. MCP Gateway + Recorder + Feedback | 0/0 | Not started | - |

---

*Roadmap created: 2026-06-22*
*Last updated: 2026-06-22 after initial creation*
