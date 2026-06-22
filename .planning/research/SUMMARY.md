# Research Summary: music-notation-codex

**Synthesized:** 2026-06-22
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md
**Overall confidence:** MEDIUM-HIGH (core stack/features/architecture HIGH; in-Streamlit audio I/O and Audio Analysis MCP MEDIUM)

## Executive Summary

Brownfield local Streamlit app wrapping two working CLI scripts (`generate_cello_dark_ostinato.py`, `harmony_advisor.py`) into an interactive loop coach + practice partner for a solo electric cellist. Build strategy: extract existing music logic into a pure-Python `core/` library first (no Streamlit), then add the Streamlit `app/` layer. The core value — "chord text → mood-shaped cello loop with plain-language theory explanation" — is already ~60% present in the scripts; the work is structuring, wiring, and presenting it.

The four highest-risk integrations, each with a known mitigation: (1) in-Streamlit MIDI playback via FluidSynth (system dep + soundfont + MIDI→WAV temp-file pipeline); (2) `st.audio_input` recording (set sample rate to 44100/48000 Hz explicitly; capture bytes in an `on_change` callback into `session_state`); (3) OSMD notation rendering in `st.components.v1.html()` (base64-encode MusicXML before passing to JS; pin CDN version); (4) async↔sync MCP bridge (background daemon event-loop thread + `asyncio.run_coroutine_threadsafe`, session cached in `session_state`, every call wrapped in try/except with graceful degradation).

Hard architectural rule: the app must stay fully functional as a loop coach when the Audio Analysis MCP is offline. The MCP is a strictly additive layer enhancing only the recorder page.

## Recommended Stack (with versions)

| Component | Choice | Why |
|-----------|--------|-----|
| Runtime | Python 3.12+ | music21 v10 requires it; existing `.venv` in place |
| Music model | music21 10.5.0 | MusicXML/MIDI export, harmony analysis; already used (bump the pin) |
| UI | Streamlit 1.58.0 | Locked decision; single-command local dev |
| Chord parsing | pychord 0.2.8 | Parses lead-sheet strings ("Am F C G") more robustly than `music21.harmony.ChordSymbol` |
| Playback | FluidSynth (`brew install fluidsynth`) + midi2audio 0.1.1 | MIDI → WAV → `st.audio()`; community-validated; no pure-Python alternative |
| Notation | OSMD 1.9.x (pinned CDN) via `st.components.v1.html()` | MusicXML → SVG; no npm/build step |
| Recording | native `st.audio_input()` | Built in since Streamlit ~1.31; set sample_rate to 44100/48000 |
| MCP client | `mcp` Python SDK >=1.9,<2 | Pin `<2` until v2 stable; stdio transport |
| Tests | pytest-playwright + **allure-pytest** (pip) | NOT `allure-playwright` (npm/JS-only) — wrong toolchain gives empty reports |

Riskiest integrations in order: FluidSynth pipeline > st.audio_input recording > async↔sync MCP bridge > OSMD CDN rendering.

## Features

**Table stakes (P1):**
- Chord-text input + key/mood selector
- Generate 3 distinct loop variants per request
- Plain-language theory explanation per variant ("why it works") — the core value
- Start / Develop / End / Transition guidance per variant — most-cited live-looper pain, no competitor addresses it
- In-browser playback (MIDI → WAV via FluidSynth → `st.audio()`)
- MusicXML + MIDI download (MuseScore / Ableton)
- Graceful degradation when Audio Analysis MCP is offline

**Differentiators (P2):**
- Record own playing + Audio Analysis MCP feedback in the context of the current loop
- On-demand music Q&A scoped to the current session
- Side-by-side variant comparison
- More mood presets beyond the existing 4

**Defer (v2+):** looper-style regenerable slots; violin duet; drum machine; LLM-generated (vs template) theory explanations.

**Market gap:** no competitor covers cello-idiomatic patterns + "why it works" explanation + loop lifecycle guidance together (Hooktheory = theory but piano/guitar; ChordChord = generation but no explanation; Yousician = feedback but no loop context).

## Architecture

Three layers, enforced at import level:
- `core/` — pure Python; imports `music21`, never `streamlit`
- `app/` — Streamlit UI + services; never calls `music21` directly in pages
- `tests-ui/` — isolated Playwright black-box tests; imports nothing from `core/`/`app/`

Key components: `LoopEngine` (preset+progression+variant → music21 Score), `TheoryExplainer` (template-driven plain-language explanation + lifecycle guidance), `AnalysisMCPGateway` (wraps MCP SDK; 30s health-check cache; returns `None` on failure; never called from UI directly), `GenerationService` / `FeedbackService` (orchestration), `notation_player` component, `tests-ui/` (Page Object Model + Allure).

Key data models: `GenerationRequest`, `LoopVariant` (score + explanation + rendered bytes + file paths — the session_state unit), `TheoryExplanation` (why_it_works / how_to_start / how_to_develop / how_to_end / how_to_transition), `MoodPreset` (merges `GENRE_PRESETS` + `GENRE_IDEAS` from the two scripts), `RecordingSession`.

## Critical Pitfalls (must-do-early)

1. **Streamlit rerun clobbers state** — store ALL results in `st.session_state` from the first widget; capture `st.audio_input` bytes in `on_change`. HIGH recovery cost if retrofitted.
2. **Pitches outside cello range** — `validate_pitch()` in Phase 1, range C2 (MIDI 36)–D5 (MIDI 74), up to C6 for electric/advanced; raise at generation time.
3. **Bar duration mismatch** — `validate_bar_duration()`: `sum(rhythm) == TimeSignature.barDuration.quarterLength` (do NOT hardcode 4.0); silent MusicXML corruption otherwise.
4. **MCP unavailable crashes app** — wrap every MCP call in try/except from line one; explicit `timeout=30`; "MCP offline" banner, never a traceback.
5. **Wrong Allure toolchain** — `allure-pytest` (pip), NOT `allure-playwright` (npm).
6. **Flaky Playwright on Streamlit** — wait on the `"Running..."` indicator appearing then detaching after each interaction; never `wait_for_timeout()`; poll `/_stcore/health`.
7. **st.audio_input defaults to 16000 Hz** — set 44100/48000; test on Chrome/Chromium (Firefox has a confirmed playback bug).
8. **Theory explanations jargon-heavy/wrong** — anchor system prompt to the user persona, ground in actual generated notes, human-review the first 10.

## Suggested Build Order (12 phases — fine granularity)

1. Core library skeleton + validators (`validate_pitch`, `validate_bar_duration`, dataclasses, merged `MoodPreset`)
2. LoopEngine + ExportEngine (pure music21; CLI scripts become thin wrappers)
3. TheoryExplainer (template-driven; structured + validated text)
4. Streamlit skeleton + GenerationService + **session_state architecture** (text I/O only)
5. NotationRenderer + PlaybackEngine (FluidSynth + OSMD) — riskiest table-stakes phase
6. Export panel (MusicXML + MIDI download buttons)
7. Variant generation (3 distinct loops per request)
8. `tests-ui/` framework (Playwright + ChromeDriver + allure-pytest; "Running..." wait pattern)
9. AnalysisMCPGateway + FeedbackService + recorder page (st.audio_input + MCP + graceful degradation)
10. Violin duet mode
11. Drum machine
12. Looper slots / section management

Ordering logic: pure-Python core (1–3) is unit-testable before any UI; session_state established (4) before results exist to lose; playback (5) before recorder (9); tests (8) before the complex MCP/duet/drums phases.

## Open Questions (resolve before the named phase)

- **Audio Analysis MCP server: already built or to-build?** Largest open question. If to-build, Phase 9 scope expands to include implementing the MCP server (would use `librosa` internally). Validate transport (stdio vs HTTP/SSE) and tool schema before Phase 9.
- **FluidSynth + soundfont on this macOS machine?** Validate before Phase 5 (`brew install fluidsynth` + an SF2 soundfont). Fallback: browser-side JS synth or MuseScore CLI.
- **OSMD vs MuseScore/LilyPond for notation?** OSMD is the no-system-dep recommendation; validate it renders the actual generated MusicXML early in Phase 5.
- **LLM vs template-driven theory explanations for v1?** Recommendation: template-driven (lower complexity, faster to validate). LLM is a P3/v2 upgrade; choosing it expands Phase 3.

---
*Research completed: 2026-06-22. Ready for roadmap: yes.*
