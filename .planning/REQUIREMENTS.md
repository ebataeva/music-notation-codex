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
- [x] **LOOP-03**: Every generated note is within playable cello range (C2–D5) — validated at generation time
- [x] **LOOP-04**: Each bar's rhythm sums exactly to the meter — validated (no silent corruption)

### Theory

- [ ] **THEORY-01**: App explains, in plain non-jargon language, why each variant works (the music theory)
- [ ] **THEORY-02**: App gives per-variant guidance on how to start, develop, end, and make a transition for the loop

### Playback & Notation

- [ ] **PLAY-01**: User can hear a generated loop in the browser before playing it on the cello
- [ ] **NOTATE-01**: User can see the loop as readable notation (score) in the browser

### Export

- [ ] **EXPORT-01**: User can download the loop as MusicXML for MuseScore
- [ ] **EXPORT-02**: User can download the loop as MIDI for Ableton
- [ ] **EXPORT-03**: User can download the rendered audio (WAV/MP3) of the current loop
- [ ] **EXPORT-04**: User can download the notation as an image (PNG/SVG) for posts/sharing

### Trace & Transparency

- [ ] **TRACE-01**: Every generated variant carries a GenerationTrace (seed, pattern strategy, register choices, voice-leading steps, chord tones used)
- [ ] **TRACE-02**: Theory explanations reference the actual notes/decisions from the variant's GenerationTrace (not generic preset text)

### Feedback (Practice Partner)

- [ ] **FEEDBACK-01**: User can record her own cello playing inside the app
- [ ] **FEEDBACK-02**: App analyzes the recording via the Audio Analysis MCP and returns plain-language suggestions on how to improve
- [ ] **FEEDBACK-03**: User can ask on-demand questions about the current loop/recording and get music advice
- [ ] **FEEDBACK-04**: App stays fully usable for loop coaching when the Audio Analysis MCP is offline (graceful degradation)

### Platform

- [ ] **PLAT-01**: App runs locally from a single command and opens a web UI
- [ ] **PLAT-02**: All visible UI copy is written in English
- [x] **PLAT-03**: Code comments are in English and only where they clarify non-obvious logic

### Testing

- [ ] **TEST-01**: UI/browser tests live in a separate Playwright-based framework under `tests-ui/`, isolated from app code
- [ ] **TEST-02**: Playwright drives Chrome/Chromium via ChromeDriver
- [ ] **TEST-03**: UI test reports are generated in Allure format

### Specification Gaming Guards (SAFE)

Hard limits that prevent AI agents (and the app itself) from finding loopholes in the spec —
optimising for a metric while violating intent. Inspired by the 111-agent deep-research incident
(Anthropic, 2026-06-02): no token budget guard, no fetch limit enforcement, no StructuredOutput
enforcement → 111 agents, 1.2M tokens, zero output.

- [ ] **SAFE-01**: Max notes per loop — generation stops with an error if a single variant exceeds 512 notes (covers ~32 bars of 4/4 at 16th-note density; any real cello loop is well within this)
- [ ] **SAFE-02**: Max bars per loop — generation rejects requests for loops longer than 64 bars
- [ ] **SAFE-03**: MIDI render timeout — FluidSynth render is killed if it exceeds 30 seconds; user sees a clear error, not a hung browser
- [ ] **SAFE-04**: MCP call rate limit — no more than 5 MCP analysis calls per browser session; subsequent calls show "analysis quota reached" with a reset hint
- [ ] **SAFE-05**: Max explanation length — TheoryExplainer output is truncated at 500 words per explanation field; no wall-of-text loophole
- [ ] **SAFE-06**: MusicXML size guard — export is rejected if the generated MusicXML exceeds 10 MB; user sees "loop too large to export, try fewer bars"
- [ ] **SAFE-07**: Variant generation depth guard — variant generation is flat (one level): a variant does not recursively spawn sub-variants; enforced in LoopEngine, not in documentation
- [ ] **SAFE-08**: Streamlit rerun loop guard — session_state tracks consecutive unproductive reruns; after 10 reruns within 5 seconds with no state change, app shows an error and stops
- [ ] **SAFE-09**: GSD plan step budget — any GSD execution plan for a single phase is capped at 15 steps; if more steps are needed, the phase must be split
- [ ] **SAFE-10**: Hard numeric guards are enforced in code (assert / raise), not in comments or docs — comments can be ignored, code cannot

## v1.5 Requirements

Content-creation layer on top of the v1 loop coach (OnlyFans content, dev-blog/stream, reflective blog). Mapped to phases 10–12.

### Content Workflows

- [ ] **CONTENT-01**: Loop Library — save/load generated loops with metadata (name, mood, chords, date, notes) so loops survive browser sessions
- [ ] **CONTENT-02**: Content Pack — one click exports a bundle for a post: audio + notation image + MIDI + caption text (from the theory explanation)
- [ ] **CONTENT-03**: Transparency & Compare — view the GenerationTrace in the UI, compare two variants side by side (A/B), and export a markdown fragment ("this loop works because…") for a blog post

## v2 Requirements

Deferred to a future release. Tracked but not in the current roadmap.

### Content & Streaming

- **CONTENT-04**: Content calendar fields in the Loop Library (status: draft/posted, planned date)
- **STREAM-01**: Presentation mode for streaming (large notation, high-contrast theme, minimal chrome)

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
| LOOP-03 | Phase 1 | Complete |
| LOOP-04 | Phase 1 | Complete |
| PLAT-03 | Phase 1 | Complete |
| LOOP-01 | Phase 2 | Pending |
| INPUT-01 | Phase 2.5 | Pending |
| TRACE-01 | Phase 2.5 | Pending |
| THEORY-01 | Phase 3 | Pending |
| THEORY-02 | Phase 3 | Pending |
| TRACE-02 | Phase 3 | Pending |
| INPUT-02 | Phase 4 | Pending |
| INPUT-03 | Phase 4 | Pending |
| PLAT-01 | Phase 4 | Pending |
| PLAT-02 | Phase 4 | Pending |
| NOTATE-01 | Phase 5 | Pending |
| PLAY-01 | Phase 5 | Pending |
| EXPORT-01 | Phase 6 | Pending |
| EXPORT-02 | Phase 6 | Pending |
| EXPORT-03 | Phase 6 | Pending |
| EXPORT-04 | Phase 6 | Pending |
| LOOP-02 | Phase 7 | Pending |
| TEST-01 | Phase 8 | Pending |
| TEST-02 | Phase 8 | Pending |
| TEST-03 | Phase 8 | Pending |
| FEEDBACK-01 | Phase 9 | Pending |
| FEEDBACK-02 | Phase 9 | Pending |
| FEEDBACK-03 | Phase 9 | Pending |
| FEEDBACK-04 | Phase 9 | Pending |
| SAFE-01 | Phase 1 | Pending |
| SAFE-02 | Phase 2 | Pending |
| SAFE-03 | Phase 5 | Pending |
| SAFE-04 | Phase 9 | Pending |
| SAFE-05 | Phase 3 | Pending |
| SAFE-06 | Phase 6 | Pending |
| SAFE-07 | Phase 2 | Pending |
| SAFE-08 | Phase 4 | Pending |
| SAFE-09 | All phases | Pending |
| SAFE-10 | All phases | Pending |
| CONTENT-01 | Phase 10 | Pending |
| CONTENT-02 | Phase 11 | Pending |
| CONTENT-03 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 25 total
- v1.5 requirements: 3 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-07-04 — added TRACE/EXPORT-03/04 (v1), CONTENT (v1.5) requirements for the three content formats; INPUT-01 moved to new Phase 2.5*
