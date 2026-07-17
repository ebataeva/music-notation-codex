# music-notation-codex Brain

## Project identity

Local music-notation workflow for composing and exporting cello ostinatos, duet material, looper-style sections, MusicXML for MuseScore, and MIDI for Ableton. Now a **loop coach web app** built on NiceGUI.

## Current direction

A **loop coach for an electric cellist**: enter chords (text) + mood, get several playable cello loop variants with plain-language music-theory explanations and start/develop/end/transition guidance, hear the vibe, and export. Also acts as a **practice partner**: the user records her own playing and gets analysis + concrete suggestions on how to improve, plus on-demand music Q&A.

## Locked decisions

- Application language: English for all visible UI copy.
- Code comments: English only, and only where comments clarify non-obvious logic.
- Frontend/app framework: **NiceGUI 3.14.0** (changed from Streamlit 2026-07-05; real persistent DOM, stable element ids, async-native, Playwright-friendly).
- Music engine: Python + music21 remains the core generation/export layer.
- Exports: MusicXML for MuseScore, MIDI for Ableton, WAV audio, SVG notation image.
- Primary input: chord progressions as text + key/mood (humming/voice input deferred to v2).
- Performance feedback (v1): record the user's own electric-cello playing → analyze via Audio Analysis MCP → return plain-language suggestions. App must degrade gracefully when MCP unavailable.
- Out of scope: extracting chords from third-party audio tracks; mobile app; hosting/deployment.
- Testing: UI/browser tests in separate Playwright-based framework under `tests-ui/`, ChromeDriver, Allure reports.

## Branch & approval workflow (recorded 2026-07-17)

The main product per roadmap stays the **local NiceGUI app** (Streamlit rejected for the main UI 2026-07-05, locked). Streamlit's only role now is **per-branch cloud showcases for testing/approval**:

1. Feature work happens in feature branches, never directly in `main`:
   - `style-harmony-policy` — style-aware harmony policy + explainer rewrite (pushed, 10 commits ahead of main)
   - `codex/violin-cello-showcase` — builds on style-harmony-policy, explainer fixes (local only, not pushed yet)
   - `blog-theory-explainer`, `cloud-audio-fallback` — parallel branches
2. Each feature branch gets a lightweight **Streamlit entrypoint** (`apps/*_streamlit.py`, commits "Add ... Streamlit entrypoint") pushed to GitHub; Streamlit Cloud picks it up so the user can hear/test the result in the browser.
3. User tests the Streamlit demo and gives approval.
4. **Approval is the trigger to merge the branch into `main`** — it does not mean work already continues in main. As of 2026-07-17 nothing from these branches is merged yet; `main` is far behind (phases 8–9 work also lives only in branches).

Helper scripts: `deploy.sh` / `git-push.mk` commit and push `apps/ear_check_streamlit.py` to `origin/style-harmony-policy`.

## Current status (2026-07-06)

**Progress: 80% (8 of 10 v1 phases complete)**

### Completed phases

| Phase | What was built | Commit |
|-------|----------------|--------|
| 1. Core Library + Validators | dataclasses (GenerationTrace, MoodPreset, LoopVariant, TheoryExplanation), validate_pitch (C2–D5), validate_bar_duration, MoodPreset registry (all 5 scripts merged), pytest scaffold | early commits |
| 2. LoopEngine + ExportEngine | refactor CLI → core/engine/loop_engine.py; generate_variant() + ExportEngine; seed policy + trace population | early commits |
| 2.5. Progression-Driven Generation | parse_progression("Am F C G") via pychord → chord tones → cello register mapping → validated bars; 8 review fixes (slash-chord cache corruption CR-01, register ratchet WR-01, etc.) | review branch |
| 3. TheoryExplainer | explain(variant, preset) → 5-field TheoryExplanation grounded in GenerationTrace; cue_pair_for property-based (tempo/register); CLI refactored; audit found D-09 violation (preset theory data unused) → fixed; 118 tests | `5f787e8`, `50fa945` |
| 4. NiceGUI Skeleton | app/main.py (NiceGUI, localhost:8080); app/pages/loop_coach.py (chord input, key/mood dropdowns, Generate button, theory text output, app.storage state persistence); app/services/generation.py (GenerationService orchestrator); stable element ids for Phase 8; SAFE-08 debounce, SAFE-05 truncation | `762d5cc` |
| 5. Notation + Playback | OSMD 1.9.0 (CDN) renders MusicXML as SVG in real DOM div (no iframe); FluidSynth CLI renders MIDI→WAV (subprocess, 30s timeout SAFE-03); ui.audio data-URL playback | `762d5cc` |
| 6. Export Panel | 4 download buttons: MusicXML, MIDI, WAV audio, SVG notation image; all from same generated variant | `762d5cc` |
| 7. 3-Variant Generation | `register_bias` field on GenerationTrace ("low"/"default"/"high"); `generate_variants()` batch function; `generate_loop_variants()` service; `loop_coach.py` rewritten with 3 side-by-side `ui.card` variant cards; explainer varies `why_it_works`/`how_to_start` per register_bias; 11 new tests; 129 total | `1c09c2f` |

### Key architecture

```
app/                    # NiceGUI UI layer (no music21 imports)
├── main.py             # Entry point: python app/main.py → localhost:8080
├── pages/
│   └── loop_coach.py   # Primary page: input → generate → theory + notation + audio + export
└── services/
    └── generation.py   # GenerationService: orchestrates core/ → JSON-serializable dict

core/                   # Pure Python library (no NiceGUI imports)
├── engine/
│   ├── loop_engine.py  # generate_variant(), generate_variant_from_progression(), generate_variants()
│   ├── progression.py  # parse_progression("Am F C G") → list[ParsedChord]
│   └── validators.py   # validate_pitch (C2–D5), validate_bar_duration
├── theory/
│   ├── explainer.py    # explain(variant, preset) → TheoryExplanation; register_bias-aware
│   └── cues.py         # Property-based cue helpers (tempo band, register)
├── export/
│   └── exporter.py     # ExportEngine: MusicXML + MIDI file export
├── presets/
│   ├── mood_presets.py # MOOD_PRESETS registry (4 solo + 3 duet)
│   └── registry.py     # get_preset(), list_presets(), list_solo_presets()
└── models.py           # LoopVariant, TheoryExplanation, GenerationTrace, MoodPreset

scripts/                # Thin CLI wrappers (backwards compat)
tests/                  # 129 pytest tests (golden regression, theory, validators, 3-variant)
```

### Tech stack (verified working)

- Python 3.14.5, music21 10.5.0, pychord 0.2.8
- NiceGUI 3.14.0 (installed in .venv)
- FluidSynth 2.5.5 (brew) + VintageDreamsWaves-v2.sf2 soundfont
- OSMD 1.9.0 (CDN) for notation rendering
- midi2audio, soundfile, numpy
- pytest 9.1.1 (129 tests passing)

### GenerationService output (verified)

```
generate_loop_variants("Am F C G", "dark_trip_hop", seed=42, include_audio=False, count=3) →
  3 variants, each with:
  - register_bias: "low" / "default" / "high" (distinct octave pools)
  - seed: 42 / 1042 / 2042 (base + i*1000)
  - MusicXML string: ~10.9 KB each
  - MIDI bytes (b64): ~500 chars each
  - TheoryExplanation: 5 fields, varies per register_bias (warmth/depth vs brightness/tension)
```

### Remaining phases

- **Phase 8**: UI Test Framework — Playwright + ChromeDriver + allure-pytest, tests-ui/ isolated (TEST-01/02/03)
- **Phase 9**: MCP Gateway + Recorder + Feedback — record playing, MCP analysis, Q&A, graceful degradation (FEEDBACK-01/02/03/04)
- **Phases 10-12 (v1.5)**: Loop Library, Content Pack Export, Transparency & Compare

### Blockers for remaining phases

- **Phase 9**: Audio Analysis MCP server status (already built vs to-build?) must be confirmed
- **Phase 9**: FEEDBACK-03 (on-demand Q&A) requires an LLM not in v1 stack — narrow requirement or add LLM integration

### Key commits (this session)

- `5f787e8` — Phase 3: TheoryExplainer (explainer.py, cues.py, 12 tests)
- `11b55af` — Phase 3 audit (PASS with 3 findings)
- `50fa945` — Phase 3 audit fixes (D-09 preset theory data surfaced, integration test added, 118 tests)
- `762d5cc` — Phases 4/5/6: NiceGUI app + OSMD notation + FluidSynth audio + export panel
- `1c09c2f` — Phase 7: 3-Variant Generation (register_bias, generate_variants, 3 side-by-side cards, 129 tests)

## How to run

```bash
cd /Users/ebataeva/Brain/Projects/music-notation-codex
source .venv/bin/activate
python app/main.py
# Opens http://localhost:8080
```

## How to test

```bash
cd /Users/ebataeva/Brain/Projects/music-notation-codex
.venv/bin/python -m pytest tests/ -q
# 129 passed
```

---

*Last updated: 2026-07-17 — recorded branch & Streamlit-showcase approval workflow*
