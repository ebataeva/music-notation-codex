<!-- GSD:project-start source:PROJECT.md -->
## Project

**music-notation-codex**

A local web app that acts as a **loop coach and practice partner for an electric cellist**. You enter a chord progression (as text) plus a mood/key, and it returns several playable loop ideas as cello notation — each one explained with the music theory behind *why* it works, plus guidance on how to start, develop, end, and transition the loop. You can hear the vibe in the browser before playing it live, and export to MusicXML/MIDI. It also lets you **record your own playing and get analysis + concrete suggestions on how to improve** (via an Audio Analysis MCP), and ask on-demand questions about your music. It grows to add a violin layer (duet) and a drum machine.

**Core Value:** Turn a chord progression into several playable electric-cello loop ideas, each explained by the music theory behind why it works — so playing stops being boring and the "vibe" becomes reachable.

### Constraints

- **Tech stack**: NiceGUI UI + Python/`music21` engine — local Python-first project, keep it simple and runnable from one command. (Changed from Streamlit 2026-07-05: Streamlit's rerun model, sandboxed component iframes, and unstable DOM made reliable Playwright UI tests impossible; NiceGUI gives a real persistent DOM with stable element ids.)
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
| NiceGUI | 3.14.0 | UI framework | Replaced Streamlit 2026-07-05; single-command local dev (`python app.py`); real persistent DOM with stable element ids → testable with Playwright; async-native (no sync/async bridge needed for MCP); FastAPI under the hood |
| pychord | 0.2.8 | Parse chord names from raw text ("Am F C G") → note lists | Simpler and more reliable than music21.harmony.ChordSymbol for plain-text chord name input; handles "Am", "F#m7", "Gsus4" etc. via `Chord("Am").components()`; complements music21 (use pychord to parse, music21 for the rest) |
### Audio Playback (MIDI → In-Browser Audio)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FluidSynth | system (brew) | SoundFont-based MIDI synthesizer | The only mature, free, local MIDI renderer; well-established on macOS via `brew install fluidsynth`; required by midi2audio and pyfluidsynth |
| midi2audio | 0.1.1 | Python wrapper: MIDI file → WAV via FluidSynth | Thin, simple, works; returns a WAV file whose bytes/path feed straight into `ui.audio()` |
| GeneralUser GS / FluidR3 Mono | .sf2 soundfont | Instrument voices for MIDI rendering | Free, redistributable, good cello/strings patch; place at `~/.fluidsynth/default_sound_font.sf2` as midi2audio convention |
| ui.audio() | (NiceGUI built-in) | Play WAV in browser | Native NiceGUI element; serve the rendered WAV via `app.add_media_files()` or a data URL; no custom component needed |
### Audio Recording (User's Cello → Browser Microphone)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| MediaRecorder JS + NiceGUI event | small custom component | Capture mic input in browser; send recorded blob to Python | NiceGUI has no built-in mic widget; standard pattern is ~30 lines of JS (`navigator.mediaDevices.getUserMedia` + `MediaRecorder`) wired to Python via `ui.run_javascript` / element events; request 44100 or 48000 Hz for instrument capture, not a speech default |
### Notation Rendering (MusicXML → Visible Score in Browser)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenSheetMusicDisplay (OSMD) | 1.9.x (CDN) | Render MusicXML as SVG notation in browser | Dominant open-source MusicXML renderer; based on VexFlow; outputs clean SVG; script loaded once via `ui.add_body_html()` — no npm/build step; pass MusicXML string from Python to JS |
| ui.add_body_html / ui.html / ui.run_javascript | NiceGUI built-ins | Load the OSMD CDN script and render into a real DOM element | No sandboxed iframe (unlike Streamlit): OSMD renders into a normal div in the page DOM, directly reachable by Playwright selectors |
### MCP Integration (Audio Analysis MCP Server)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| mcp (Python SDK) | >=1.9,<2 | Client to connect to and call tools on an Audio Analysis MCP server | Official Anthropic/MCP SDK; stable v1.x line; `stdio_client` + `ClientSession` covers the full pattern; v2 alpha exists but pin <2 until stable (targeted 2026-07-27) |
| (no bridge needed) | — | NiceGUI is async-native | Event handlers can be `async def` and `await` MCP SDK calls directly on the app's event loop — the background-thread + `run_coroutine_threadsafe` bridge that Streamlit required is obsolete |
### Audio Analysis (on Recorded WAV from User)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| librosa | 0.11.0 | Pitch, tempo, beat, onset, intonation analysis of WAV audio | Used inside the Audio Analysis MCP server (not in the UI app directly); the standard Python audio analysis library; `librosa.yin()` for pitch, `librosa.beat.beat_track()` for tempo |
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
| uv | Fast dependency management | Optional but strongly recommended; music21 v10 itself migrated to uv; `uv run python app.py` replaces managing .venv manually |
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
| FluidSynth + midi2audio → ui.audio() | Tone.js / MIDI.js in browser | Use in-browser MIDI playback only if you want zero system dependencies; more JS complexity; not worth it for a single-user local tool |
| NiceGUI | Streamlit | Rejected 2026-07-05: rerun model, sandboxed component iframes, and unstable DOM make reliable Playwright UI tests impossible — a locked testing requirement of this project |
| NiceGUI | FastAPI + htmx / Reflex | FastAPI+htmx gives max DOM control at the cost of much more hand-written frontend; Reflex drags in a node toolchain — both overkill for a single-user local tool |
| OSMD via ui.add_body_html + ui.html | music21 + MuseScore CLI → PNG/PDF | MuseScore approach is reliable but requires MuseScore installed and a subprocess call; OSMD renders inline without an extra app; use MuseScore if you want print-quality PDFs |
| mcp Python SDK (official) | httpx + raw JSON-RPC | Only if the Audio Analysis MCP server uses SSE/HTTP transport exclusively; the official SDK handles all transports |
| librosa (inside MCP server) | aubio, essentia | aubio is C-based, harder to install; essentia is heavy (ML); librosa is pure Python + numpy, easiest to ship in a local MCP server |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pyfluidsynth (direct Python bindings) | C binding; harder install; lower-level API; midi2audio wraps it cleanly | midi2audio |
| music21 + MuseScore for in-browser rendering | Requires MuseScore installed + subprocess call; outputs PNG/SVG file, not interactive; slower for preview | OSMD via ui.add_body_html + ui.html |
| Streamlit (and its widget ecosystem: st.audio_input, streamlit-mic-recorder, etc.) | Rejected 2026-07-05 for untestable UI: full-page reruns, sandboxed iframes, no stable selectors | NiceGUI 3.14.0 |
| MCP SDK v2 (alpha) | Not stable; breaking changes expected; stable release targeted 2026-07-27 | mcp>=1.9,<2 |
| humming/voice pitch input via crepe/pyin | High complexity, out of scope per PROJECT.md; no need when chord text input is the workflow | Text chord input |
| pretty-midi as primary MIDI export | music21 already exports MIDI natively; pretty-midi adds a dependency without benefit here | music21.midi.translate |
## Risky Pieces — Explicit Guidance
### 1. In-Browser Audio Recording (HIGH RISK if not handled correctly)
- **No built-in mic widget in NiceGUI** — write a small custom component: `navigator.mediaDevices.getUserMedia` + `MediaRecorder` in JS, blob posted back to Python via an element event or endpoint. Keep it in one module so tests can mock it.
- **Request 44100 or 48000 Hz** in `getUserMedia` audio constraints — speech defaults are too low for cello.
- **Browser microphone permission**: local app on `localhost` will trigger browser permission prompt; first run requires user to allow it. Document this.
- **Recorded blob arrives as webm/ogg by default** — either set a WAV-capable mimeType where supported or transcode server-side (ffmpeg/soundfile) before handing to librosa.
- **No rerun model in NiceGUI** — state lives in normal Python objects per client; no session-state guards needed, but keep long analysis off the event loop (`run.cpu_bound` / `run.io_bound`).
### 2. MIDI/Audio Playback (MEDIUM RISK)
- FluidSynth must be installed on the host machine (`brew install fluidsynth`). Document this as a system prerequisite.
- The soundfont file must be present at `~/.fluidsynth/default_sound_font.sf2` (or pass path explicitly to midi2audio). Automating this via a setup script is worthwhile.
- **midi2audio renders to a file, not memory**: call `FluidSynth().midi_to_audio(midi_path, wav_path)`, then serve the WAV to `ui.audio()` (via `app.add_media_files()` or a data URL). Keep temp files in a `tempfile.TemporaryDirectory`.
- If cello-specific instrument patch sounds wrong (General MIDI cello = program 42), verify soundfont has it; most good SF2 files do.
### 3. MCP Integration (MEDIUM RISK)
- MCP Python SDK is async; NiceGUI is async-native — call MCP directly from `async def` handlers, no background-loop bridge.
- The app **must degrade gracefully** when the MCP server is not running (per PROJECT.md). Wrap all MCP calls in try/except and show a disabled UI state.
- Use `StdioServerParameters` to spawn the MCP server as a subprocess; the server script path should be configurable (env var or config file), not hardcoded.
### 4. OSMD Notation Rendering (LOW-MEDIUM RISK)
- MusicXML is passed as a string from Python into JavaScript (`ui.run_javascript` or an element prop). Base64-encode the string to avoid HTML/JS injection and quoting issues.
- OSMD loads from CDN by default — the app requires internet on first render. For fully offline use, vendor the OSMD JS file locally via `app.add_static_files()`.
- No iframe: OSMD renders into a real div in the page DOM (`ui.html`/`ui.element`), so Playwright selectors reach the rendered SVG directly — a key reason for the NiceGUI switch.
- OSMD version: pin the CDN URL to a specific OSMD version tag (e.g. `@1.9.0`) not `@latest` to avoid surprise breakage.
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| music21==10.5.0 | Python 3.12, 3.13 | Do not use 9.x; 10.x is current and has better MIDI/MusicXML support |
| librosa==0.11.0 | numpy>=1.26, soundfile>=0.12 | Released March 2025; current stable |
| mcp>=1.9,<2 | Python 3.10+ | Pin <2 until MCP v2 stable (2026-07-27) |
| nicegui==3.14.0 | Python 3.9+ | Current stable (June 2026) |
| pychord==0.2.8 | Python 3.8+ | Released Jan 2026; current stable |
| midi2audio==0.1.1 | FluidSynth (system) | Requires `fluidsynth` binary on PATH |
## Sources
- music21 releases: https://github.com/cuthbertLab/music21/releases — v10.5.0 confirmed latest (June 2024)
- music21 harmony docs: https://music21.org/music21docs/moduleReference/moduleHarmony.html — ChordSymbol notation verified
- pychord PyPI: https://pypi.org/project/pychord/0.2.8/ — v0.2.8, Jan 2026
- librosa 0.11.0 release: https://librosa.org/doc/0.11.0/ — March 2025
- NiceGUI releases: https://github.com/zauberzeug/nicegui/releases — v3.14.0 confirmed (2026-06-30)
- NiceGUI testing docs: https://nicegui.io/documentation/section_testing — `user` fixture (fast, in-loop) + `Screen` fixture (real browser); complements the project's Playwright framework
- midi2audio GitHub: https://github.com/bzamecnik/midi2audio — pattern for MIDI→WAV via FluidSynth
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

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec
