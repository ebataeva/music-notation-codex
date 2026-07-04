# Roadmap: music-notation-codex

**Created:** 2026-06-22
**Milestone:** v1 — Loop Coach MVP (+ v1.5 content layer, phases 10–12)
**Granularity:** fine
**Mode:** mvp
**Total phases:** 13
**Requirements covered:** v1 25/25, v1.5 3/3

---

## Phases

- [x] **Phase 1: Core Library Skeleton + Validators** - Pure-Python data structures, dataclasses (incl. GenerationTrace fields), pytest scaffold, and guards (range + bar duration) (completed 2026-07-04)
- [ ] **Phase 2: LoopEngine + ExportEngine** - Refactor CLI scripts into testable core engine; single-variant generation + file export; seed policy + trace population
- [ ] **Phase 2.5: Progression-Driven Generation** - Parse arbitrary chord text ("Am F C G") and generate validated cello bars from it (pychord → chord tones → cello register mapping → preset rhythm strategies)
- [ ] **Phase 3: TheoryExplainer** - Template-driven plain-language explanations grounded in the variant's GenerationTrace, plus loop lifecycle guidance
- [ ] **Phase 4: Streamlit Skeleton + Session State** - Interactive UI with chord/key/mood input; text output only; session_state architecture
- [ ] **Phase 5: Notation + Playback** - In-browser score rendering (OSMD) and audio playback (FluidSynth pipeline)
- [ ] **Phase 6: Export Panel** - MusicXML, MIDI, audio (WAV/MP3), and notation image (PNG/SVG) downloads wired to ExportEngine
- [ ] **Phase 7: 3-Variant Generation** - Generate and display 3 distinct cello loop variants per request
- [ ] **Phase 8: UI Test Framework** - Playwright + ChromeDriver + allure-pytest; loop coach happy-path coverage
- [ ] **Phase 9: MCP Gateway + Recorder + Feedback** - Audio recording, MCP analysis, Q&A, graceful degradation
- [ ] **Phase 10 (v1.5): Loop Library** - Persist generated loops with metadata; loops survive browser sessions
- [ ] **Phase 11 (v1.5): Content Pack Export** - One-click post bundle: audio + notation image + MIDI + caption text
- [ ] **Phase 12 (v1.5): Transparency & Compare** - GenerationTrace view in UI, A/B variant comparison, markdown fragment export for blog posts

---

## Phase Details

### Phase 1: Core Library Skeleton + Validators

**Goal:** The core/ library structure exists with all dataclasses (MoodPreset, LoopVariant, GenerationRequest, TheoryExplanation, GenerationTrace), a MoodPreset registry merged from all 5 CLI scripts (GENRE_PRESETS + GENRE_IDEAS + duet preset data as data-only), a pytest scaffold for core unit tests, and validators that enforce cello range and bar duration correctness.
**Mode:** mvp
**Depends on:** Nothing (brownfield refactor from scripts/)
**Requirements:** LOOP-03, LOOP-04, PLAT-03
**Success Criteria** (what must be TRUE):

  1. A note outside C2-D5 raises a validation error at generation time (confirmed by a passing pytest unit test)
  2. A rhythm pattern whose durations do not sum to the bar length raises a validation error (confirmed by unit test)
  3. All existing CLI scripts still produce the same output files after refactoring their data into core/presets/
  4. `pytest tests/` runs the core unit suite with zero failures (pytest infrastructure established)
  5. Dataclasses include GenerationTrace fields (seed, pattern strategy, register, voice-leading, chord tones) so later phases don't retrofit them
  6. requirements.txt pins the approved stack (music21==10.5.0) and installs cleanly on Python 3.12+

**Plans:** 4/4 plans complete
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — core/models.py (5 dataclasses) + pytest scaffold + import-boundary guard
- [x] 01-02-PLAN.md — validate_pitch + validate_bar_duration (TDD, LOOP-03/LOOP-04)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03-PLAN.md — requirements.txt bump to music21==10.5.0 + golden baseline capture

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-04-PLAN.md — MoodPreset registry merge (7 entries) + script data-source swap + golden regression verify

### Phase 2: LoopEngine + ExportEngine

**Goal:** The generation logic from generate_cello_dark_ostinato.py lives in core/engine/loop_engine.py and core/export/exporter.py; the script becomes a thin wrapper; a single cello loop variant can be generated and exported entirely from pure-Python code, with an explicit seed policy and a populated GenerationTrace.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** LOOP-01
**Success Criteria** (what must be TRUE):

  1. Calling LoopEngine.build_score() with a MoodPreset returns a music21 Score object with no errors
  2. Calling ExportEngine.export_to_musicxml() and export_to_midi() writes valid files to scores/musicxml/ and scores/midi/
  3. The existing scripts/generate_cello_dark_ostinato.py runs via its thin wrapper and produces identical output to before the refactor
  4. Generation accepts an explicit seed; the same seed reproduces an identical variant (reproducibility for caching, tests, and blog posts)
  5. Every generated variant carries a populated GenerationTrace (strategy, register, chord tones used)

**Plans:** TBD

### Phase 2.5: Progression-Driven Generation

**Goal:** The engine generates a playable, validated cello loop from an arbitrary user chord progression ("Am F C G") plus key/mood — not just from hardcoded preset bars. This is the hardest musical-algorithm work in the project: pychord parsing → chord tones → mapping into the cello register → applying the preset's rhythm/pattern strategies → range- and duration-validated bars.
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** INPUT-01, TRACE-01
**Success Criteria** (what must be TRUE):

  1. A progression string like "Am F C G" parses into chord objects; an unrecognized token produces a clear, human-readable error naming the bad token
  2. LoopEngine.build_score() with an arbitrary parsed progression + mood returns a Score whose bars pass validate_pitch and validate_bar_duration
  3. Generated bars use chord tones of the user's progression (verified by unit test), voiced in idiomatic cello register (monophonic, C2–D5)
  4. The GenerationTrace records which chord tones, register choices, and pattern strategy were used per bar

**Plans:** TBD

### Phase 3: TheoryExplainer

**Goal:** The harmony text from harmony_advisor.py lives in core/theory/explainer.py as structured TheoryExplanation dataclasses; given a LoopVariant and MoodPreset, the explainer returns plain-language "why it works" + start/develop/end/transition guidance, grounded in the variant's GenerationTrace.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** THEORY-01, THEORY-02, TRACE-02
**Success Criteria** (what must be TRUE):

  1. TheoryExplainer.explain() returns a TheoryExplanation with all five fields populated (why_it_works, how_to_start, how_to_develop, how_to_end, how_to_transition) for every supported mood preset
  2. The why_it_works text contains no unexplained jargon — verified by manual review of at least 4 presets
  3. The how_to_start and how_to_transition fields include practical cello-specific cues (not generic piano/guitar language)
  4. The why_it_works text references at least one concrete note/decision from the variant's GenerationTrace (e.g. the actual pedal tone or chromatic step used), not only generic preset language

**Plans:** TBD

### Phase 4: Streamlit Skeleton + Session State

**Goal:** The Streamlit app launches with one command, shows chord/key/mood input widgets, generates a loop on submit, and displays the theory explanation as text — with all results stored in session_state so reruns do not lose data.
**Mode:** mvp
**Depends on:** Phase 2.5, Phase 3
**Requirements:** INPUT-02, INPUT-03, PLAT-01, PLAT-02
**Success Criteria** (what must be TRUE):

  1. Running `streamlit run app/main.py` opens the app in the browser with no errors
  2. User can type a chord progression (e.g. "Am F C G"), choose a key and mood from dropdowns, and click Generate
  3. After clicking Generate, the theory explanation text appears on the page without a traceback
  4. Refreshing the browser or clicking Generate again does not erase the previous result (session_state preserved)
  5. All visible UI labels and button text are in English
  6. Generation completes in ≤3 s from click to visible result (stream-friendly speed budget)
  7. An "Example input" button fills the form with a working demo progression in one click (for on-camera demos)
  8. LoopVariant storage in session_state follows an explicit serialization decision (bytes/paths vs live music21 Score) — no silent pickle failures on rerun

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

**Goal:** The user can download the current loop as MusicXML (MuseScore), MIDI (Ableton), rendered audio (WAV/MP3 — the same render used for in-browser playback), and a notation image (PNG/SVG) directly from the browser via download buttons.
**Mode:** mvp
**Depends on:** Phase 5
**Requirements:** EXPORT-01, EXPORT-02, EXPORT-03, EXPORT-04
**Success Criteria** (what must be TRUE):

  1. Clicking "Download MusicXML" triggers a file download that MuseScore can open without errors
  2. Clicking "Download MIDI" triggers a file download that Ableton can import without errors
  3. Clicking "Download audio" saves the WAV/MP3 render of the current loop (playable in any player)
  4. Clicking "Download notation image" saves a PNG/SVG of the score suitable for a post
  5. Downloaded files contain the same loop variant the user generated and heard in the browser

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
**Pre-phase decisions (BLOCKING before planning):**

  1. Does the Audio Analysis MCP server already exist, or must it be built in this phase? (validate transport + tool schema)
  2. FEEDBACK-03 (on-demand Q&A) requires an LLM, which is not in the v1 stack — either narrow FEEDBACK-03 to template/analysis-grounded answers, or add an explicit LLM integration to this phase's scope

**Requirements:** FEEDBACK-01, FEEDBACK-02, FEEDBACK-03, FEEDBACK-04
**Success Criteria** (what must be TRUE):

  1. The recorder page allows the user to record audio via st.audio_input and save it as a WAV file
  2. When the Audio Analysis MCP is online, the app displays at least one concrete plain-language suggestion after analysis
  3. When the user types a question about the recording or loop, the app returns a music-relevant answer (MCP online)
  4. When the Audio Analysis MCP is offline, the recorder page shows a dismissable warning banner and the loop coach page functions normally with no error or traceback

**Plans:** TBD
**UI hint**: yes

### Phase 10 (v1.5): Loop Library

**Goal:** Generated loops can be saved with metadata (name, mood, chords, seed, date, free-text notes) and reloaded in a later session — loops stop dying with the browser tab. This is the shared foundation for all three content workflows (posting, streaming, reflective analysis).
**Mode:** mvp
**Depends on:** Phase 7
**Requirements:** CONTENT-01
**Success Criteria** (what must be TRUE):

  1. Clicking "Save to library" persists the current variant (score + trace + metadata) to local storage on disk
  2. After fully restarting the app, the library page lists saved loops and any of them can be reopened with notation, playback, and explanation intact
  3. A saved loop can be regenerated identically from its stored seed + request parameters

**Plans:** TBD
**UI hint**: yes

### Phase 11 (v1.5): Content Pack Export

**Goal:** One click exports a ready-to-post bundle for a loop: rendered audio + notation image + MIDI + caption text derived from the theory explanation ("why this works" doubles as post copy).
**Mode:** mvp
**Depends on:** Phase 6, Phase 10
**Requirements:** CONTENT-02
**Success Criteria** (what must be TRUE):

  1. Clicking "Export content pack" produces a folder/zip containing audio (WAV/MP3), notation image (PNG/SVG), MIDI, and a caption .md/.txt
  2. The caption text is the variant's actual theory explanation (edited-friendly plain text), not a placeholder
  3. The pack is generated for any loop in the library, not only the current session's loop

**Plans:** TBD
**UI hint**: yes

### Phase 12 (v1.5): Transparency & Compare

**Goal:** The app can show its "internals" for the reflective blog: the GenerationTrace is visible per variant, two variants can be compared side by side (A/B) at the theory level, and a markdown fragment ("this loop works because… / this one is weaker because…") can be exported for a post.
**Mode:** mvp
**Depends on:** Phase 7, Phase 10
**Requirements:** CONTENT-03
**Success Criteria** (what must be TRUE):

  1. Each variant card has a "Why these notes?" view exposing the GenerationTrace in readable form (seed, strategy, register, chord tones, voice-leading steps)
  2. An A/B compare view shows two variants' notation + traces side by side with their differences highlighted at theory level
  3. "Export post fragment" produces a markdown snippet combining notation image reference, trace summary, and explanation text

**Plans:** TBD
**UI hint**: yes

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Library Skeleton + Validators | 4/4 | Complete    | 2026-07-04 |
| 2. LoopEngine + ExportEngine | 0/0 | Not started | - |
| 2.5. Progression-Driven Generation | 0/0 | Not started | - |
| 3. TheoryExplainer | 0/0 | Not started | - |
| 4. Streamlit Skeleton + Session State | 0/0 | Not started | - |
| 5. Notation + Playback | 0/0 | Not started | - |
| 6. Export Panel | 0/0 | Not started | - |
| 7. 3-Variant Generation | 0/0 | Not started | - |
| 8. UI Test Framework | 0/0 | Not started | - |
| 9. MCP Gateway + Recorder + Feedback | 0/0 | Not started | - |
| 10. Loop Library (v1.5) | 0/0 | Not started | - |
| 11. Content Pack Export (v1.5) | 0/0 | Not started | - |
| 12. Transparency & Compare (v1.5) | 0/0 | Not started | - |

---

*Roadmap created: 2026-06-22*
*Last updated: 2026-07-04 — review findings applied: Phase 2.5 (progression-driven generation) inserted; trace/seed/pytest/speed-budget criteria added to phases 1–4; EXPORT-03/04 added to Phase 6; Phase 9 pre-phase decisions recorded; v1.5 content phases 10–12 added*
