<!-- GSD:project-start source:PROJECT.md -->
## Project

**music-notation-codex**

A local web app that acts as a **loop coach and practice partner for an electric cellist**. You enter a chord progression (as text) plus a mood/key, and it returns several playable loop ideas as cello notation — each one explained with the music theory behind *why* it works, plus guidance on how to start, develop, end, and transition the loop. You can hear the vibe in the browser before playing it live, and export to MusicXML/MIDI. It also lets you **record your own playing and get analysis + concrete suggestions on how to improve** (via an Audio Analysis MCP), and ask on-demand questions about your music. It grows to add a violin layer (duet) and a drum machine.

**Core Value:** Turn a chord progression into several playable electric-cello loop ideas, each explained by the music theory behind why it works — so playing stops being boring and the "vibe" becomes reachable.

### Constraints

- **Tech stack**: Streamlit UI + Python/`music21` engine — local Python-first project, keep it simple and runnable from one command.
- **Language**: All visible UI copy in English; code comments in English and only where they clarify non-obvious logic — locked project decision.
- **Testing**: UI/browser tests live in a *separate* Playwright-based framework under `tests-ui/`, driving Chrome/Chromium via ChromeDriver — locked decision (keeps app code clean, enables real browser regression).
- **Reporting**: UI test reports generated in Allure format — locked decision.
- **Platform**: Local desktop tool; no hosting/deployment in scope.
- **Dependency**: Performance feedback relies on an external Audio Analysis MCP server — the app must degrade gracefully (stay usable for loop coaching) when the MCP is unavailable.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Runtime | music21 v10 requires 3.12+; macOS ships 3.x; existing .venv already in place |
| music21 | 10.5.0 | Music object model, MusicXML export, MIDI export, harmony analysis | Already used in project; the authoritative Python music theory library with ChordSymbol, RomanNumeral, stream, export; no real alternative for MusicXML round-trip |
| Streamlit | 1.58.0 | UI framework | Locked project decision; single-command local dev; no frontend code; good enough for one-user local tool |
| pychord | 0.2.8 | Parse chord names from raw text ("Am F C G") → note lists | Simpler and more reliable than music21.harmony.ChordSymbol for plain-text chord name input; handles "Am", "F#m7", "Gsus4" etc. via `Chord("Am").components()`; complements music21 (use pychord to parse, music21 for the rest) |
### Audio Playback (MIDI → In-Browser Audio)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FluidSynth | system (brew) | SoundFont-based MIDI synthesizer | The only mature, free, local MIDI renderer; well-established on macOS via `brew install fluidsynth`; required by midi2audio and pyfluidsynth |
| midi2audio | 0.1.1 | Python wrapper: MIDI file → WAV via FluidSynth | Thin, simple, works; accepted pattern in the Streamlit community (andfanilo/streamlit-midi-to-wav); returns WAV bytes passable to `st.audio()` |
| GeneralUser GS / FluidR3 Mono | .sf2 soundfont | Instrument voices for MIDI rendering | Free, redistributable, good cello/strings patch; place at `~/.fluidsynth/default_sound_font.sf2` as midi2audio convention |
| st.audio() | (Streamlit built-in) | Play WAV bytes in browser | Native Streamlit; accepts `bytes` or file-like; no custom component needed |
### Audio Recording (User's Cello → Browser Microphone)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| st.audio_input | Streamlit 1.58.0 (built-in) | Capture mic input in browser; returns WAV UploadedFile | Native API, no third-party component; added in Streamlit ~1.31; sample rate configurable (use 44100 or 48000 for instrument capture, not the 16000 Hz speech default); returns WAV bytes directly |
### Notation Rendering (MusicXML → Visible Score in Browser)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenSheetMusicDisplay (OSMD) | 1.9.x (CDN) | Render MusicXML as SVG notation in browser | Dominant open-source MusicXML renderer; based on VexFlow; outputs clean SVG; loaded via CDN inside `st.components.v1.html()` — no npm/build step; pass MusicXML string from Python to JS |
| st.components.v1.html | Streamlit built-in | Inject arbitrary HTML+JS iframe into Streamlit page | Standard way to embed custom JS libraries in Streamlit; OSMD is loaded inside the iframe |
### MCP Integration (Audio Analysis MCP Server)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| mcp (Python SDK) | >=1.9,<2 | Client to connect to and call tools on an Audio Analysis MCP server | Official Anthropic/MCP SDK; stable v1.x line; `stdio_client` + `ClientSession` covers the full pattern; v2 alpha exists but pin <2 until stable (targeted 2026-07-27) |
| asyncio / run_coroutine_threadsafe | stdlib | Bridge between Streamlit's sync context and MCP's async client | Streamlit runs sync; MCP SDK is async; standard solution is a background event loop thread + `asyncio.run_coroutine_threadsafe()` |
### Audio Analysis (on Recorded WAV from User)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| librosa | 0.11.0 | Pitch, tempo, beat, onset, intonation analysis of WAV audio | Used inside the Audio Analysis MCP server (not in the Streamlit app directly); the standard Python audio analysis library; `librosa.yin()` for pitch, `librosa.beat.beat_track()` for tempo |
## Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pychord | 0.2.8 | Parse "Am F C G" text → chord note lists | Chord text input parsing; feed results into music21 stream construction |
| pretty-midi | 0.2.11 | MIDI manipulation utilities | Only if you need to inspect or post-process MIDI at note level outside music21; music21 handles MusicXML/MIDI export natively so this may not be needed |
| soundfile | 0.12.x | Read/write WAV/FLAC; required by librosa | Always needed alongside librosa |
| numpy | 1.26+ / 2.x | Array math; required by librosa, midi2audio, soundfile | Transitive dependency; pin >=1.26 for Python 3.12 compat |
## Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| Playwright + pytest-playwright | UI/browser test framework | Locked project decision; lives in `tests-ui/`, drives Chromium |
| allure-pytest | Allure test reporting | Locked project decision; generates HTML reports from Playwright runs |
| uv | Fast dependency management | Optional but strongly recommended; music21 v10 itself migrated to uv; `uv run streamlit run app.py` replaces managing .venv manually |
## Installation
# System dependency: FluidSynth (macOS)
# Download a free soundfont and place it where midi2audio expects it
# Option A: GeneralUser GS (good strings/cello patch)
# Download from https://schristiancollins.com/generaluser.php
# cp GeneralUser_GS.sf2 ~/.fluidsynth/default_sound_font.sf2
# Option B: FluidR3 Mono (smaller, included with many distros)
# cp FluidR3_GM.sf2 ~/.fluidsynth/default_sound_font.sf2
# Python packages
# Dev / test
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pychord (chord text parsing) | music21.harmony.ChordSymbol | Use ChordSymbol when you need Roman numeral analysis or already have music21 objects — but its text-parsing of "Am" vs "A-m" has gotchas; pychord handles common lead-sheet strings more robustly |
| FluidSynth + midi2audio → st.audio() | Tone.js / MIDI.js in browser | Use in-browser MIDI playback only if you want zero system dependencies; requires a custom Streamlit component and more JS complexity; not worth it for a single-user local tool |
| st.audio_input() | streamlit-mic-recorder (third-party) | streamlit-mic-recorder adds speech-to-text hooks and more callback control; use it only if st.audio_input falls short in practice (unlikely for cello recording) |
| OSMD via st.components.v1.html() | music21 + MuseScore CLI → PNG/PDF | MuseScore approach is reliable but requires MuseScore installed and a subprocess call; OSMD renders inline without an extra app; use MuseScore if you want print-quality PDFs |
| mcp Python SDK (official) | httpx + raw JSON-RPC | Only if the Audio Analysis MCP server uses SSE/HTTP transport exclusively; the official SDK handles all transports |
| librosa (inside MCP server) | aubio, essentia | aubio is C-based, harder to install; essentia is heavy (ML); librosa is pure Python + numpy, easiest to ship in a local MCP server |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pyfluidsynth (direct Python bindings) | C binding; harder install; lower-level API; midi2audio wraps it cleanly | midi2audio |
| music21 + MuseScore for in-browser rendering | Requires MuseScore installed + subprocess call; outputs PNG/SVG file, not interactive; slower for preview | OSMD via st.components.v1.html() |
| streamlit-audio-recorder (stefanrmmr) | Unmaintained React component; no updates since 2022; fragile with current Streamlit versions | st.audio_input() (native) |
| MCP SDK v2 (alpha) | Not stable; breaking changes expected; stable release targeted 2026-07-27 | mcp>=1.9,<2 |
| humming/voice pitch input via crepe/pyin | High complexity, out of scope per PROJECT.md; no need when chord text input is the workflow | Text chord input |
| pretty-midi as primary MIDI export | music21 already exports MIDI natively; pretty-midi adds a dependency without benefit here | music21.midi.translate |
## Risky Pieces — Explicit Guidance
### 1. In-Streamlit Audio Recording (HIGH RISK if not handled correctly)
- **Default sample rate is 16000 Hz** — good for speech, bad for cello. Always set `sample_rate=44100` or `sample_rate=48000` explicitly.
- **Browser microphone permission**: local app on `localhost` will trigger browser permission prompt; first run requires user to allow it. Document this.
- **File size limit**: the recorded WAV is subject to `server.maxUploadSize` (default 200 MB — fine for a few minutes of cello).
- **Returns a WAV UploadedFile** (BytesIO subclass) — pass it directly to librosa or write to a temp file.
- **Streamlit re-runs on widget change**: wrap analysis logic in `st.session_state` guards to avoid re-running analysis on every UI interaction.
### 2. MIDI/Audio Playback (MEDIUM RISK)
- FluidSynth must be installed on the host machine (`brew install fluidsynth`). Document this as a system prerequisite.
- The soundfont file must be present at `~/.fluidsynth/default_sound_font.sf2` (or pass path explicitly to midi2audio). Automating this via a setup script is worthwhile.
- **midi2audio renders to a file, not memory**: call `FluidSynth().midi_to_audio(midi_path, wav_path)`, then read WAV bytes and pass to `st.audio(wav_bytes)`. Keep temp files in a `tempfile.TemporaryDirectory`.
- If cello-specific instrument patch sounds wrong (General MIDI cello = program 42), verify soundfont has it; most good SF2 files do.
### 3. MCP Integration (MEDIUM RISK)
- MCP Python SDK is async; Streamlit is synchronous. The bridge pattern:
- The app **must degrade gracefully** when the MCP server is not running (per PROJECT.md). Wrap all MCP calls in try/except and show a disabled UI state.
- Use `StdioServerParameters` to spawn the MCP server as a subprocess; the server script path should be configurable (env var or config file), not hardcoded.
### 4. OSMD Notation Rendering (LOW-MEDIUM RISK)
- MusicXML is passed as a string from Python into JavaScript via `st.components.v1.html()`. Escape or base64-encode the string to avoid HTML injection issues.
- OSMD loads from CDN by default — the app requires internet on first render. For fully offline use, vendor the OSMD JS file locally.
- `st.components.v1.html()` runs in a sandboxed iframe; OSMD renders inside it and cannot communicate back to Python without a bidirectional custom component. For read-only score display this is fine.
- OSMD version: pin the CDN URL to a specific OSMD version tag (e.g. `@1.9.0`) not `@latest` to avoid surprise breakage.
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| music21==10.5.0 | Python 3.12, 3.13 | Do not use 9.x; 10.x is current and has better MIDI/MusicXML support |
| librosa==0.11.0 | numpy>=1.26, soundfile>=0.12 | Released March 2025; current stable |
| mcp>=1.9,<2 | Python 3.10+ | Pin <2 until MCP v2 stable (2026-07-27) |
| streamlit==1.58.0 | Python 3.9–3.13 | Current stable (May 2026) |
| pychord==0.2.8 | Python 3.8+ | Released Jan 2026; current stable |
| midi2audio==0.1.1 | FluidSynth (system) | Requires `fluidsynth` binary on PATH |
## Sources
- music21 releases: https://github.com/cuthbertLab/music21/releases — v10.5.0 confirmed latest (June 2024)
- music21 harmony docs: https://music21.org/music21docs/moduleReference/moduleHarmony.html — ChordSymbol notation verified
- pychord PyPI: https://pypi.org/project/pychord/0.2.8/ — v0.2.8, Jan 2026
- librosa 0.11.0 release: https://librosa.org/doc/0.11.0/ — March 2025
- Streamlit 2026 release notes: https://docs.streamlit.io/develop/quick-reference/release-notes/2026 — v1.58.0 confirmed
- st.audio_input docs: https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input — sample rate options verified
- midi2audio GitHub: https://github.com/bzamecnik/midi2audio — pattern for MIDI→WAV via FluidSynth
- streamlit-midi-to-wav reference app: https://github.com/andfanilo/streamlit-midi-to-wav — community-validated FluidSynth+Streamlit pattern
- OSMD: https://opensheetmusicdisplay.org/ and https://github.com/opensheetmusicdisplay/opensheetmusicdisplay — v1.9.0 confirmed
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk — v1.9.4 current stable, v2 alpha; client pattern verified
- MCP SDK version pin: https://pypi.org/project/mcp/ — >=1.9,<2 recommended
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

## Knowledge base
Personal wiki at ~/Brain/. Read ~/Brain/CLAUDE.md for global rules (jCodemunch mandatory, token economy, specification gaming protection).
