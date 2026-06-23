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

## Research findings (2026-06-22)

Full detail in `.planning/research/` (STACK / FEATURES / ARCHITECTURE / PITFALLS / SUMMARY). Highlights:

### Recommended stack (with versions)
- Python 3.12+; music21 10.5.0 (bump existing pin); Streamlit 1.58.0.
- Chord-text parsing: **pychord 0.2.8** (more robust than `music21.harmony.ChordSymbol` for "Am F C G").
- In-browser playback: **FluidSynth** (`brew install fluidsynth`) + **midi2audio 0.1.1** → MIDI rendered to WAV → `st.audio()`. No pure-Python alternative; system dependency.
- Notation in browser: **OSMD 1.9.x** (pinned CDN) via `st.components.v1.html()`; base64-encode MusicXML before passing to JS.
- Recording: native **`st.audio_input()`** — must override default sample rate 16000 → 44100/48000 Hz.
- MCP client: **`mcp` Python SDK >=1.9,<2**, stdio transport; async↔sync bridge via background daemon event-loop thread + `asyncio.run_coroutine_threadsafe`, session cached in `session_state`.
- Tests: **`allure-pytest`** (pip) + pytest-playwright — NOT `allure-playwright` (npm/JS-only; wrong toolchain = empty reports).

### Riskiest integrations (in order)
FluidSynth playback pipeline > `st.audio_input` recording > async↔sync MCP bridge > OSMD CDN rendering.

### Must-do-early guards (cheap now, expensive to retrofit)
- `validate_pitch()` — cello range C2 (MIDI 36) to D5 (MIDI 74), up to C6 for electric/advanced; raise at generation time.
- `validate_bar_duration()` — `sum(rhythm) == TimeSignature.barDuration.quarterLength`; do NOT hardcode 4.0 (silent MusicXML corruption otherwise).
- **session_state architecture from the first widget** — every Streamlit rerun clobbers locals; store all generated loops/recordings in `st.session_state`; capture audio bytes in an `on_change` callback.
- Audio Analysis MCP wrapped in try/except from line one, explicit `timeout=30`, "MCP offline" banner — graceful degradation is a hard rule, not a nice-to-have.
- Playwright-on-Streamlit: wait on the `"Running..."` indicator appearing then detaching after each interaction; never `wait_for_timeout()`; poll `/_stcore/health`.

### Architecture
Three layers enforced at import level: `core/` (pure Python, imports music21 never streamlit) → `app/` (Streamlit UI + services, no music21 in pages) → `tests-ui/` (isolated black-box Playwright, imports nothing from core/app). Merge the two scripts' parallel dicts `GENRE_PRESETS` + `GENRE_IDEAS` into one `MoodPreset` dataclass so theory travels with generation params.

### Suggested build order (12 phases, fine granularity)
1. Core skeleton + validators · 2. LoopEngine + ExportEngine · 3. TheoryExplainer (template-driven) · 4. Streamlit skeleton + session_state · 5. Notation + playback (FluidSynth + OSMD; riskiest) · 6. Export panel · 7. 3-variant generation · 8. tests-ui (Playwright + Allure) · 9. MCP gateway + recorder · 10. Violin duet · 11. Drum machine · 12. Looper slots.

### Open questions to resolve before the named phase
- **Audio Analysis MCP server: already built or to-build?** If to-build, Phase 9 expands to implementing it (librosa internally). Validate transport (stdio vs HTTP/SSE) + tool schema first.
- FluidSynth + SF2 soundfont present on this macOS machine? Validate before Phase 5.
- OSMD renders the actual generated MusicXML correctly? Validate early in Phase 5 (fallback: MuseScore CLI).
- LLM vs template-driven theory explanations for v1? Recommendation: template-driven; LLM is a v2 upgrade that expands Phase 3.

## Existing artifacts

- `.planning/PROJECT.md` — full project context (current source of truth)
- `.planning/config.json` — GSD workflow config (YOLO, fine granularity, parallel, research/plan-check/verifier on)
- `.planning/research/` — STACK, FEATURES, ARCHITECTURE, PITFALLS, SUMMARY
- `.planning/REQUIREMENTS.md` — 21 v1 requirements, fully mapped to phases (traceability populated)
- `.planning/ROADMAP.md` — APPROVED 9-phase v1 roadmap (the plan)
- `.planning/STATE.md` — project memory
- `CLAUDE.md` — generated project guide
- `scripts/generate_cello_dark_ostinato.py`, `scripts/harmony_advisor.py` — existing engine to refactor into `core/`

## Approved roadmap (v1 — 9 phases)

Plan file: `.planning/ROADMAP.md`. Core-first; v2 items (violin duet, drum machine, looper slots, humming input, LLM explanations) are deferred and tracked in REQUIREMENTS.md.

1. **Core library skeleton + validators** — dataclasses, MoodPreset registry, `validate_pitch` (C2–D5) + `validate_bar_duration`. Pure Python, no Streamlit. (LOOP-03, LOOP-04, PLAT-03)
2. **LoopEngine + ExportEngine** — refactor CLI scripts into pure `core/`; single-variant generation + file export. (LOOP-01)
3. **TheoryExplainer** — template-driven "why it works" + start/develop/end/transition guidance. (THEORY-01, THEORY-02)
4. **Streamlit skeleton + session_state** — one-command launch; chord/key/mood input; text output; session_state architecture. (INPUT-01/02/03, PLAT-01/02)
5. **Notation + playback** — OSMD score in browser + FluidSynth audio. Highest-risk phase. (NOTATE-01, PLAY-01)
6. **Export panel** — MusicXML + MIDI download buttons. (EXPORT-01, EXPORT-02)
7. **3-variant generation** — three distinct loops per request, side by side. (LOOP-02)
8. **UI test framework** — Playwright + ChromeDriver + allure-pytest, isolated from app. (TEST-01/02/03)
9. **MCP gateway + recorder + feedback** — record playing, MCP analysis, on-demand Q&A, graceful offline degradation. (FEEDBACK-01/02/03/04)

Pre-phase checks: validate FluidSynth + SF2 soundfont before Phase 5; confirm whether the Audio Analysis MCP server is already built or must be built before Phase 9.

## Next step

`/gsd-plan-phase 1` — write the detailed plan for Phase 1 (core library skeleton + validators). No per-phase plans exist yet; they are written one phase at a time.
