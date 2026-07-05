# music-notation-codex Brain

## Project identity

Local music-notation workflow for composing and exporting violin + cello duet material, cello ostinatos, looper-style sections, drum-machine MIDI, MusicXML for MuseScore, and MIDI for Ableton.

## Current direction

The project is moving from CLI scripts into a local web interface. The planned app should be a practical composition workspace, not a landing page. Its heart is a **loop coach for an electric cellist**: enter chords (text) + mood, get several playable cello loop variants with plain-language music-theory explanations and start/develop/end/transition guidance, hear the vibe, and export. It also acts as a **practice partner**: the user records her own playing and gets analysis + concrete suggestions on how to improve, plus on-demand music Q&A.

## Locked decisions

- Application language: English for all visible UI copy.
- Code comments: English only, and only where comments clarify non-obvious logic.
- Frontend/app framework: **NiceGUI 3.14.0** for the local web interface (changed from Streamlit 2026-07-05, before any UI code existed — Streamlit's rerun model, sandboxed component iframes, and unstable DOM made reliable Playwright UI tests impossible, conflicting with the locked Playwright+Allure testing decision; NiceGUI gives a real persistent DOM with stable element ids and is async-native, which also removes the sync↔async MCP bridge from Phase 9). Note: Streamlit-specific advice in the 2026-06-22 research findings below (st.audio_input, session_state, st.components, "Running..." indicator waits) is superseded.
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

## Approved roadmap (v1 — 13 phases after 2026-07-04 review)

Plan file: `.planning/ROADMAP.md`. Core-first; v2 items (violin duet, drum machine, looper slots, humming input, LLM explanations, content calendar, presentation mode) are deferred and tracked in REQUIREMENTS.md.

1. **Core library skeleton + validators** — dataclasses incl. GenerationTrace fields, MoodPreset registry (all 5 scripts, duet data as data-only), pytest scaffold, `validate_pitch` (C2–D5) + `validate_bar_duration`, music21 pin → 10.5.0. (LOOP-03, LOOP-04, PLAT-03)
2. **LoopEngine + ExportEngine** — refactor CLI scripts into pure `core/`; single-variant generation + file export; explicit seed policy; trace population. (LOOP-01)
2.5. **Progression-driven generation** — pychord parse "Am F C G" → chord tones → cello register mapping → preset rhythm strategies → validated bars. The hardest musical-algorithm work; previously hidden inside Phase 2. (INPUT-01, TRACE-01)
3. **TheoryExplainer** — template-driven "why it works" grounded in the variant's GenerationTrace + lifecycle guidance. (THEORY-01, THEORY-02, TRACE-02)
4. **Streamlit skeleton + session_state** — one-command launch; chord/key/mood input; ≤3 s generation budget; example-input button; explicit LoopVariant serialization decision. (INPUT-02/03, PLAT-01/02)
5. **Notation + playback** — OSMD score in browser + FluidSynth audio. Highest-risk phase. (NOTATE-01, PLAY-01)
6. **Export panel** — MusicXML + MIDI + audio (WAV/MP3) + notation image (PNG/SVG). (EXPORT-01/02/03/04)
7. **3-variant generation** — three distinct loops per request, side by side. (LOOP-02)
8. **UI test framework** — Playwright + ChromeDriver + allure-pytest, isolated from app. Also "stream insurance" against live regressions. (TEST-01/02/03)
9. **MCP gateway + recorder + feedback** — record playing, MCP analysis, on-demand Q&A, graceful offline degradation. BLOCKING pre-phase decisions: MCP server built-or-build; FEEDBACK-03 needs an LLM not in the v1 stack. (FEEDBACK-01/02/03/04)
10. **Loop Library (v1.5)** — persist loops with metadata + seed; survive browser sessions. Foundation for all three content workflows. (CONTENT-01)
11. **Content Pack Export (v1.5)** — one click: audio + notation image + MIDI + caption from theory explanation. (CONTENT-02)
12. **Transparency & Compare (v1.5)** — GenerationTrace view, A/B variant compare, markdown post-fragment export. (CONTENT-03)

Pre-phase checks: validate FluidSynth + SF2 soundfont before Phase 5; resolve both Phase 9 blocking decisions before Phase 9 planning.

## Review findings applied (2026-07-04)

Full review delivered in-session by Claude Fable 5; changes committed to ROADMAP/REQUIREMENTS:
- **Biggest blind spot:** generation from an arbitrary chord progression (the core value) was implied but never scoped — now explicit Phase 2.5.
- **Contradiction:** FEEDBACK-03 (Q&A) needs an LLM while THEORY-03 (LLM explanations) is deferred to v2 — recorded as a Phase 9 blocking pre-phase decision.
- **Content-format strategy:** all three blog formats (OnlyFans content, dev-stream, reflective blog) reduce to two shared primitives — Loop Library (persistence) + GenerationTrace (transparency) — plus thin export features. Trace fields go into Phase 1 dataclasses (cheap now, expensive to retrofit); trace-grounded explanations also close research Pitfall 7 (ungrounded theory text).
- Housekeeping: pytest scaffold added to Phase 1; requirements.txt pin (music21>=9.1,<10) contradicts approved stack (10.5.0) — fixed in Phase 1 scope; roadmap now acknowledges all 5 scripts (3 duet generators added after roadmap creation).

## Review findings applied (2026-07-05, Phase 02.5)

Code review of the progression-driven generation path found 8 issues (1 Critical, 3 Warnings, 4 Info); all 8 fixed and merged to main (branch `gsd-reviewfix/02.5-15234`, report in `.planning/phases/02.5-progression-driven-generation/02.5-REVIEW-FIX.md`):
- **CR-01 (critical):** slash-chord input (`C/G`) permanently corrupted pychord's process-global quality cache, silently breaking every later chord in the Streamlit session — slash tokens now rejected up front in `parse_progression` (also resolves WR-03's confusing `Cmaj7/G` error).
- **WR-01:** register mapping ratcheted every line to the top of the cello range within ~2 bars — max-leap now constrains instead of short-circuiting, low-register bias for root/fifth works again (32-bar loop now spans MIDI 36–60).
- **WR-02:** duet-only presets through the progression path leaked internal "Rhythm is empty" — now an actionable duet-only message listing solo presets.
- **Info:** trace field semantics documented per strategy; flat-key respelling (Gm renders Bb, not A#); fifth detected by interval (power chords); regression tests for flats/slash/leap/register added (88 tests green).

## Next step

Phase 1 GSD planning artifacts (CONTEXT/RESEARCH/PATTERNS/PLAN) are being produced via /gsd-plan-phase 1. After that: `/gsd-execute-phase 1`.
