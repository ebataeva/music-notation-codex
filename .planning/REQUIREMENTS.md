# Requirements: music-notation-codex

**Defined:** 2026-06-22
**Core Value:** Turn a chord progression into several playable electric-cello loop ideas, each explained by the music theory behind why it works.

## v1 Requirements

Requirements for the initial release. Each maps to roadmap phases.

### Input

- [ ] **INPUT-01**: User can enter a chord progression as text (e.g. `Am F C G`)
- [ ] **INPUT-02**: User can choose a key (tonic + mode) for generation
- [ ] **INPUT-03**: User can pick a mood/vibe preset (e.g. noir, ritual, trip-hop, cinematic)

### Loop Generation

- [ ] **LOOP-01**: App generates a playable cello loop from the chord progression + mood
- [ ] **LOOP-02**: App generates 3 distinct loop variants for the same input
- [ ] **LOOP-03**: Every generated note is within playable cello range (C2–D5) — validated at generation time
- [ ] **LOOP-04**: Each bar's rhythm sums exactly to the meter — validated (no silent corruption)

### Theory

- [ ] **THEORY-01**: App explains, in plain non-jargon language, why each variant works (the music theory)
- [ ] **THEORY-02**: App gives per-variant guidance on how to start, develop, end, and make a transition for the loop

### Playback & Notation

- [ ] **PLAY-01**: User can hear a generated loop in the browser before playing it on the cello
- [ ] **NOTATE-01**: User can see the loop as readable notation (score) in the browser

### Export

- [ ] **EXPORT-01**: User can download the loop as MusicXML for MuseScore
- [ ] **EXPORT-02**: User can download the loop as MIDI for Ableton

### Feedback (Practice Partner)

- [ ] **FEEDBACK-01**: User can record her own cello playing inside the app
- [ ] **FEEDBACK-02**: App analyzes the recording via the Audio Analysis MCP and returns plain-language suggestions on how to improve
- [ ] **FEEDBACK-03**: User can ask on-demand questions about the current loop/recording and get music advice
- [ ] **FEEDBACK-04**: App stays fully usable for loop coaching when the Audio Analysis MCP is offline (graceful degradation)

### Platform

- [ ] **PLAT-01**: App runs locally from a single command and opens a web UI
- [ ] **PLAT-02**: All visible UI copy is written in English
- [ ] **PLAT-03**: Code comments are in English and only where they clarify non-obvious logic

### Testing

- [ ] **TEST-01**: UI/browser tests live in a separate Playwright-based framework under `tests-ui/`, isolated from app code
- [ ] **TEST-02**: Playwright drives Chrome/Chromium via ChromeDriver
- [ ] **TEST-03**: UI test reports are generated in Allure format

## v2 Requirements

Deferred to a future release. Tracked but not in the current roadmap.

### Arrangement

- **DUET-01**: Violin layer / duet mode (cello + violin), two-staff export
- **DRUM-01**: Drum-machine pattern generation, Ableton-compatible MIDI
- **SLOT-01**: Looper-style slots/sections that can be regenerated independently

### Input & Theory

- **INPUT-04**: Hum/voice a melody into the mic and have it recognized (pitch detection)
- **THEORY-03**: LLM-generated dynamic per-chord theory explanations (vs template-driven)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Extracting chords from third-party audio tracks (MP3/Spotify/YouTube) | High complexity; chords are found online or known by ear. Only the user's own playing is analyzed. |
| Mobile app | Personal local desktop tool; web-first |
| Hosting / deployment | Runs locally only |
| Live audio effects / DAW replacement | Ableton and MuseScore handle performance and final editing downstream |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOOP-03 | Phase 1 | Pending |
| LOOP-04 | Phase 1 | Pending |
| PLAT-03 | Phase 1 | Pending |
| LOOP-01 | Phase 2 | Pending |
| THEORY-01 | Phase 3 | Pending |
| THEORY-02 | Phase 3 | Pending |
| INPUT-01 | Phase 4 | Pending |
| INPUT-02 | Phase 4 | Pending |
| INPUT-03 | Phase 4 | Pending |
| PLAT-01 | Phase 4 | Pending |
| PLAT-02 | Phase 4 | Pending |
| NOTATE-01 | Phase 5 | Pending |
| PLAY-01 | Phase 5 | Pending |
| EXPORT-01 | Phase 6 | Pending |
| EXPORT-02 | Phase 6 | Pending |
| LOOP-02 | Phase 7 | Pending |
| TEST-01 | Phase 8 | Pending |
| TEST-02 | Phase 8 | Pending |
| TEST-03 | Phase 8 | Pending |
| FEEDBACK-01 | Phase 9 | Pending |
| FEEDBACK-02 | Phase 9 | Pending |
| FEEDBACK-03 | Phase 9 | Pending |
| FEEDBACK-04 | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-06-22 after roadmap creation — traceability table populated*
