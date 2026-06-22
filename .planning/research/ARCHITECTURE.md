# Architecture Research

**Domain:** Local Python/Streamlit music-generation and practice-coaching app (loop coach for electric cellist)
**Researched:** 2026-06-22
**Confidence:** HIGH — based on direct code inspection of existing scripts, official Streamlit and music21 docs, and Audio Analysis MCP integration patterns.

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                           │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                    Streamlit UI  (app/)                       │   │
│  │  pages/loop_coach.py  pages/recorder.py  pages/duet.py       │   │
│  │  components/notation_player.py   components/export_panel.py  │   │
│  └──────────────┬────────────────────────┬────────────────────--─┘   │
└─────────────────┼────────────────────────┼────────────────────────---┘
                  │ calls (Python)          │ calls (Python)
┌─────────────────┼────────────────────────┼────────────────────────---┐
│                 │    APPLICATION LAYER    │                           │
│  ┌──────────────▼──────────┐  ┌──────────▼──────────────────────┐   │
│  │   GenerationService     │  │      FeedbackService            │   │
│  │  (orchestrates engine)  │  │   (orchestrates MCP + theory)   │   │
│  └──────────────┬──────────┘  └──────────┬──────────────────────┘   │
│                 │                         │                          │
│  ┌──────────────▼──────────┐  ┌──────────▼──────────────────────┐   │
│  │    TheoryExplainer      │  │     AnalysisMCPGateway          │   │
│  │  (why-it-works text,    │  │  (wraps MCP client; degrades   │   │
│  │   start/develop/end/    │  │   gracefully when offline)     │   │
│  │   transition guidance)  │  └─────────────────────────────────┘   │
│  └─────────────────────────┘                                        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │ calls (Python)
┌─────────────────▼───────────────────────────────────────────────────┐
│                         CORE ENGINE LAYER                            │
│                                                                      │
│  ┌───────────────────────┐   ┌──────────────────────────────────┐   │
│  │  LoopEngine           │   │  ExportEngine                    │   │
│  │  (music21 generation, │   │  (MusicXML + MIDI write)         │   │
│  │   ostinato builder,   │   │                                  │   │
│  │   variant generator,  │   └──────────────────────────────────┘   │
│  │   voice-leading)      │                                          │
│  └───────────────────────┘   ┌──────────────────────────────────┐   │
│                               │  NotationRenderer                │   │
│  ┌───────────────────────┐   │  (score → SVG/PNG for browser)   │   │
│  │  PresetRegistry       │   └──────────────────────────────────┘   │
│  │  (mood presets,       │                                          │
│  │   GENRE_PRESETS dict, │   ┌──────────────────────────────────┐   │
│  │   future DrumPresets) │   │  PlaybackEngine                  │   │
│  └───────────────────────┘   │  (score → MIDI → browser audio   │   │
│                               │   via midi.js or similar)        │   │
└──────────────────────────────┴──────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         DATA / STORAGE LAYER                         │
│                                                                      │
│  scores/musicxml/   scores/midi/   session state (st.session_state)  │
│  recordings/ (tmp WAV/MP3 for MCP)                                   │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DEPENDENCY                              │
│                                                                      │
│  Audio Analysis MCP Server  (optional; localhost or remote process)  │
│  Accessed only through AnalysisMCPGateway — never by UI directly     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     TEST FRAMEWORK (isolated)                        │
│                                                                      │
│  tests-ui/  Playwright + ChromeDriver  Allure reports                │
│  (never imports app code; drives the Streamlit HTTP server as a      │
│   black box; runs against `streamlit run app/main.py`)               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

### What each component owns — and does not own

| Component | Owns | Does NOT own |
|-----------|------|--------------|
| **Streamlit UI** (`app/`) | Widget state, routing between pages, rendering notation+audio, displaying text explanations | Music logic, file I/O, MCP calls |
| **GenerationService** (`app/services/generation.py`) | Orchestrating a full loop-generation request: call LoopEngine, call TheoryExplainer, call ExportEngine | music21 internals, UI state |
| **FeedbackService** (`app/services/feedback.py`) | Orchestrating a recording session: save WAV, call AnalysisMCPGateway, format suggestions as text | Recording UI, MCP protocol details |
| **LoopEngine** (`core/engine/loop_engine.py`) | Building music21 Score objects from GenrePreset + ChordProgression + VariantConfig; voice-leading; ostinato patterns | File I/O, explanations, UI |
| **PresetRegistry** (`core/presets/`) | Storing and querying GenrePreset objects; resolving mood aliases | Generation logic |
| **TheoryExplainer** (`core/theory/explainer.py`) | Generating "why it works" paragraphs + start/develop/end/transition guidance from a LoopVariant | Score generation, UI rendering |
| **ExportEngine** (`core/export/exporter.py`) | Writing MusicXML and MIDI files to disk; returning file paths | Score creation, UI download links |
| **NotationRenderer** (`core/render/notation_renderer.py`) | Converting a music21 Score to SVG/PNG for embedding in Streamlit | Playback, export |
| **PlaybackEngine** (`core/render/playback_engine.py`) | Converting a music21 Score or MIDI bytes to in-browser audio (MIDI.js embed or similar) | Notation rendering, export |
| **AnalysisMCPGateway** (`core/mcp/gateway.py`) | All communication with the Audio Analysis MCP server; health-check; returning None when offline | Recording UI, suggestion formatting |

---

## Refactoring the Existing CLI Scripts

### Current state

`generate_cello_dark_ostinato.py` already has clean separation in principle:
- `GENRE_PRESETS` dict — pure data → move to `core/presets/`
- `build_cello_ostinato(preset)` — pure music21 logic → move to `core/engine/loop_engine.py`
- `export_score(score, output_name)` — file I/O → move to `core/export/exporter.py`
- `main()` / `parse_args()` — CLI shell → thin wrapper remains in `scripts/` or is deleted

`harmony_advisor.py`:
- `GENRE_IDEAS` dict — pure data → move to `core/presets/` alongside `GENRE_PRESETS`
- The explanation strings in `GENRE_IDEAS` are the seed of `TheoryExplainer`; they become structured data (keyed by genre and dimension: progressions / modulations / mood) rather than print strings
- `main()` / `print_section()` → delete; the Streamlit page calls TheoryExplainer directly

The duet scripts (`generate_simple_sexy_duet_loop.py`, etc.) already show a two-part Score pattern — that becomes a second code path inside LoopEngine parameterised by `InstrumentSet` (cello-only vs. cello+violin).

### Extraction rule

No Streamlit import may appear below the `app/` layer. No music21 import may appear in `app/`. The boundary is enforced at the import level: `core/` is a pure Python library; `app/` is the Streamlit consumer.

---

## Recommended Project Structure

```
music-notation-codex/
├── app/                          # Streamlit UI — only layer that imports streamlit
│   ├── main.py                   # Entry point: streamlit run app/main.py
│   ├── pages/
│   │   ├── loop_coach.py         # Primary page: chord input → variants
│   │   ├── recorder.py           # Record → analyze → improve
│   │   └── duet.py               # Violin duet mode (later phase)
│   ├── components/
│   │   ├── notation_player.py    # Renders SVG notation + audio playback widget
│   │   └── export_panel.py       # Download MusicXML / MIDI buttons
│   └── services/
│       ├── generation.py         # GenerationService
│       └── feedback.py           # FeedbackService
│
├── core/                         # Pure Python library — no streamlit, no argparse
│   ├── engine/
│   │   └── loop_engine.py        # build_score(), generate_variants()
│   ├── presets/
│   │   ├── genre_presets.py      # GENRE_PRESETS (moved from scripts)
│   │   └── theory_data.py        # GENRE_IDEAS (moved from harmony_advisor)
│   ├── theory/
│   │   └── explainer.py          # TheoryExplainer: produces plain-language text
│   ├── export/
│   │   └── exporter.py           # export_to_musicxml(), export_to_midi()
│   ├── render/
│   │   ├── notation_renderer.py  # score_to_svg()
│   │   └── playback_engine.py    # score_to_midi_bytes() for browser
│   └── mcp/
│       └── gateway.py            # AnalysisMCPGateway (with graceful degradation)
│
├── scripts/                      # Thin CLI wrappers — kept for backwards compat
│   ├── generate_cello_dark_ostinato.py   # now calls core.engine + core.export
│   └── harmony_advisor.py                # now calls core.theory.explainer
│
├── tests-ui/                     # Playwright test framework (isolated)
│   ├── conftest.py               # browser fixture, base URL config
│   ├── tests/
│   │   ├── test_loop_coach.py
│   │   ├── test_recorder.py
│   │   └── test_export.py
│   ├── pages/                    # Page Object Models
│   │   ├── loop_coach_page.py
│   │   └── recorder_page.py
│   └── allure-results/           # Generated reports
│
├── scores/
│   ├── musicxml/
│   └── midi/
│
├── recordings/                   # Temporary WAV/MP3 uploads for MCP analysis
│
├── .planning/
│   ├── PROJECT.md
│   └── research/
│       └── ARCHITECTURE.md       # this file
│
├── requirements.txt              # app + core dependencies
├── requirements-test.txt         # playwright, allure-pytest (separate)
└── .venv/
```

### Structure rationale

- **`core/` as a library:** Zero Streamlit dependency. Can be tested with plain pytest, imported by CLI scripts, and later wrapped in a REST API if needed without touching any UI code.
- **`app/services/` layer:** Prevents Streamlit pages from calling music21 directly. Services translate between UI data types (strings, dicts) and domain objects (GenrePreset, LoopVariant).
- **`tests-ui/` fully isolated:** Has its own `requirements-test.txt`, its own `conftest.py`, never imports from `core/` or `app/`. Drives the running Streamlit server over HTTP as a black box. This means tests don't break when internal APIs change — only when the UI contract changes.
- **`recordings/` separate from `scores/`:** Recordings are ephemeral user uploads (deleted after MCP analysis); scores are generated artifacts kept for export.

---

## Data Models

These are the canonical data shapes. All layers communicate through these types.

### GenerationRequest

```python
@dataclass
class GenerationRequest:
    chord_progression: str          # "Am F C G" — raw text from user
    key_tonic: str                  # "A"
    key_mode: str                   # "minor"
    mood: str                       # "dark_trip_hop" | "ritual_tribal" | ...
    num_variants: int = 3           # how many distinct loop ideas to return
    bars: int = 8
    instrument_set: str = "cello"   # "cello" | "cello+violin"
```

### LoopVariant

```python
@dataclass
class LoopVariant:
    id: str                         # uuid or slug, stable within a session
    preset_name: str                # source mood/genre
    score: music21.stream.Score     # the actual music object
    label: str                      # e.g. "Variant 2 — pedal-tone drive"
    musicxml_path: Path | None      # set after export; None if not yet exported
    midi_path: Path | None
    svg_bytes: bytes | None         # set after render; None if not yet rendered
    midi_bytes: bytes | None        # for browser playback
    theory_explanation: TheoryExplanation | None
```

### TheoryExplanation

```python
@dataclass
class TheoryExplanation:
    why_it_works: str               # plain-language paragraph
    how_to_start: str               # practical cue: "Start on the open C string..."
    how_to_develop: str             # "Add a chromatic passing note on beat 3..."
    how_to_end: str                 # "Land on the root and let it ring..."
    how_to_transition: str          # "Drop the top voice down a half-step..."
```

### MoodPreset

```python
@dataclass(frozen=True)
class MoodPreset:
    name: str
    tempo_bpm: int
    key_tonic: str
    key_mode: str
    meter_signature: str
    velocity: int
    rhythm: list[float]
    bars: list[list[str]]
    feel: str
    progressions: list[str]         # from GENRE_IDEAS — merged here
    modulations: list[str]
    mood_tips: list[str]
```

Note: the current codebase has `GenrePreset` (in `generate_cello_dark_ostinato.py`) and `GENRE_IDEAS` (in `harmony_advisor.py`) as two separate structures keyed by the same genre name. Refactoring merges them into `MoodPreset` so theory data travels with generation data.

### RecordingSession

```python
@dataclass
class RecordingSession:
    id: str                         # uuid
    recording_path: Path            # temporary WAV on disk
    loop_variant_id: str | None     # which variant the user was practicing
    mcp_raw_response: dict | None   # raw JSON from MCP (None if offline)
    suggestions: list[str]          # formatted plain-language feedback
    questions_asked: list[str]      # on-demand questions the user typed
    answers: list[str]              # MCP answers to those questions
    created_at: datetime
```

---

## Data Flow

### Primary flow: chord progression → loop variants

```
User types "Am F C G" + selects mood "dark_trip_hop"
    ↓
app/pages/loop_coach.py  (Streamlit widget callback)
    ↓  GenerationRequest dataclass
app/services/generation.py  GenerationService.generate()
    ↓  MoodPreset  (looked up from PresetRegistry)
    ↓  calls core/engine/loop_engine.py  LoopEngine.build_variants()
    ↓  returns list[music21.stream.Score]
    ↓  calls core/theory/explainer.py  TheoryExplainer.explain()
    ↓  returns list[TheoryExplanation]
    ↓  calls core/render/notation_renderer.py  → list[svg_bytes]
    ↓  calls core/render/playback_engine.py  → list[midi_bytes]
    ↓  assembles list[LoopVariant]
    ↓
app/pages/loop_coach.py  stores to st.session_state["variants"]
    ↓
app/components/notation_player.py  renders each LoopVariant card:
    - SVG notation via st.image()
    - audio playback via st.audio(midi_bytes)
    - theory explanation text via st.expander()
```

### Export flow: variant → files on disk

```
User clicks "Export MusicXML / MIDI"
    ↓
app/components/export_panel.py
    ↓  LoopVariant (has music21 Score)
app/services/generation.py  GenerationService.export()
    ↓
core/export/exporter.py  export_to_musicxml() + export_to_midi()
    ↓  returns (Path, Path)
    ↓
st.download_button(data=open(path, "rb").read(), ...)
```

### Recording + MCP analysis flow

```
User records playing (st.audio_input or file upload)
    ↓
app/pages/recorder.py  saves WAV to recordings/<session_id>.wav
    ↓  RecordingSession dataclass
app/services/feedback.py  FeedbackService.analyze()
    ↓
core/mcp/gateway.py  AnalysisMCPGateway.analyze(wav_path)
    │
    ├─ MCP online → sends WAV, receives JSON analysis
    │   ↓  mcp_raw_response
    │   FeedbackService formats suggestions as list[str]
    │   ↓
    │   app/pages/recorder.py  displays suggestions + Q&A widget
    │
    └─ MCP offline → returns None
        ↓
        FeedbackService returns degraded_response:
        {suggestions: [], offline: True}
        ↓
        app/pages/recorder.py  shows "Analysis unavailable — MCP offline.
        Loop coaching features still work normally."
```

### On-demand theory question flow

```
User types question in text_input on any page
    ↓
app/services/feedback.py  FeedbackService.ask(question, loop_variant_id)
    ↓
core/mcp/gateway.py  AnalysisMCPGateway.ask(question, context)
    │
    ├─ MCP online → returns answer string
    └─ MCP offline → returns "MCP offline — question queued, try again later."
```

---

## Graceful Degradation for Audio Analysis MCP

The MCP is an optional enhancement, not a core dependency. The app must be fully functional without it.

### Gateway contract

```python
class AnalysisMCPGateway:
    def is_available(self) -> bool:
        """Health-check. Cached for 30 seconds to avoid hammering."""

    def analyze(self, wav_path: Path) -> dict | None:
        """Returns JSON analysis dict, or None if offline."""

    def ask(self, question: str, context: dict) -> str | None:
        """Returns answer string, or None if offline."""
```

### Degradation matrix

| MCP status | Loop generation | Theory explanations | Notation/playback | Recording analysis | Q&A |
|------------|-----------------|--------------------|--------------------|-------------------|-----|
| Online | Full | Full | Full | Full | Full |
| Offline | Full | Full | Full | "MCP offline" message | "MCP offline" message |
| Slow / timeout | Full | Full | Full | Shows spinner → falls back after 10 s | Falls back immediately |

### Implementation notes

- `AnalysisMCPGateway.is_available()` is called once at session start and cached in `st.session_state["mcp_available"]`; re-checked on each recorder page load.
- FeedbackService always checks `gateway.is_available()` before calling. It never raises — it returns a typed result that includes an `offline: bool` flag.
- The recorder page renders a dismissable warning banner (not an error, not a page block) when MCP is offline.
- The loop coach page has zero dependency on MCP; it never calls FeedbackService.

---

## Architectural Patterns

### Pattern 1: Services as thin orchestrators

**What:** `app/services/` classes do no music logic. They translate UI inputs into domain calls, sequence calls across `core/` modules, and return assembled result objects.
**When to use:** Every time a Streamlit page needs more than one `core/` call.
**Trade-offs:** Adds a layer; worth it because it keeps pages readable and makes the logic testable without Streamlit.

### Pattern 2: MoodPreset as the single source of truth

**What:** All generation parameters — tempo, rhythm, notes, feel text, theory advice — live in one `MoodPreset` dataclass. LoopEngine and TheoryExplainer both read from it.
**When to use:** Any time generation and explanation diverge (they are currently in two separate dicts in two separate scripts), this pattern prevents them from getting out of sync.
**Trade-offs:** Slightly larger preset objects, but eliminates dual-maintenance.

### Pattern 3: Variant as the unit of work

**What:** Once generated, a `LoopVariant` carries everything about one loop idea: the score, the explanation, the rendered bytes, the file paths. It is stored in `st.session_state` and passed between components.
**When to use:** All UI components and export actions operate on `LoopVariant`, not on raw music21 objects.
**Trade-offs:** LoopVariant can become large in memory (SVG bytes + MIDI bytes); keep to ≤ 5 variants per session.

### Pattern 4: Page Object Model in tests-ui/

**What:** `tests-ui/pages/` contains one class per Streamlit page, encapsulating locators and user-action methods. Test functions call page methods, not raw Playwright selectors.
**When to use:** Every UI test. Keeps test code stable when Streamlit widget IDs change.
**Trade-offs:** More upfront code per page; saves maintenance cost as the app grows.

---

## Anti-Patterns

### Anti-Pattern 1: Music logic in Streamlit pages

**What people do:** Call `music21` directly inside `app/pages/loop_coach.py` because it's fast to prototype.
**Why it's wrong:** Pages become untestable; logic gets duplicated across pages; adding duet mode or drums requires touching page code.
**Do this instead:** All music21 calls go in `core/engine/loop_engine.py`. Pages call `GenerationService`.

### Anti-Pattern 2: Calling MCP directly from the UI

**What people do:** `import mcp_client; mcp_client.analyze(wav)` inside the recorder page.
**Why it's wrong:** The page becomes broken when MCP is offline. Error handling is scattered. Adding retry logic or caching is messy.
**Do this instead:** All MCP calls go through `AnalysisMCPGateway`. The page only checks `result.offline`.

### Anti-Pattern 3: Storing music21 Score in st.session_state naively

**What people do:** `st.session_state["score"] = music21_score` directly.
**Why it's wrong:** music21 Score objects are not pickle-serializable in all configurations; Streamlit's session state serialization can fail or silently produce corrupt state on rerun.
**Do this instead:** Store `LoopVariant` objects, and within them keep the Score only if confirmed serializable; otherwise store the bytes (SVG, MIDI) and re-generate on demand from the preset + request.

### Anti-Pattern 4: tests-ui importing core or app modules

**What people do:** `from core.engine import LoopEngine` inside a Playwright test to set up test state.
**Why it's wrong:** Tests become coupled to internal implementation. The test framework loses its role as a black-box browser tester.
**Do this instead:** Tests set state only through the browser UI — fill in text fields, click buttons. If specific state is hard to reach via UI, add a hidden dev-mode URL parameter or fixture endpoint, not an import.

---

## Build Order (honoring dependencies)

This is the dependency graph expressed as a recommended phase sequence. Each phase's output is a prerequisite for the next.

```
Phase 1: Core library skeleton
    Extract GENRE_PRESETS + GENRE_IDEAS into core/presets/
    Define all dataclasses (GenerationRequest, LoopVariant, MoodPreset, etc.)
    No music21 calls yet — just data structures and interfaces.
    ↓
Phase 2: LoopEngine + ExportEngine (pure music21, no UI)
    Refactor build_cello_ostinato() → LoopEngine.build_score()
    Refactor export_score() → ExportEngine.export_to_musicxml() + export_to_midi()
    Thin CLI wrappers in scripts/ call these.
    Unit-testable with plain pytest.
    ↓
Phase 3: TheoryExplainer (pure text, no music21)
    Refactor GENRE_IDEAS print logic → TheoryExplainer.explain(preset, variant)
    Returns TheoryExplanation dataclass.
    Unit-testable with plain pytest.
    ↓
Phase 4: Streamlit skeleton + GenerationService
    app/main.py + app/pages/loop_coach.py (text I/O only, no notation yet)
    GenerationService wires Phase 2 + 3 outputs into one call.
    First interactive loop: type chords → see text explanation.
    ↓
Phase 5: NotationRenderer + PlaybackEngine
    score_to_svg() using music21's built-in SVG export or lilypond
    score_to_midi_bytes() for st.audio()
    loop_coach.py shows notation + audio player.
    ↓
Phase 6: Export panel + MusicXML/MIDI download
    app/components/export_panel.py
    st.download_button() backed by ExportEngine.
    ↓
Phase 7: Variant generation (multiple distinct loops per request)
    LoopEngine.generate_variants(request, n=3)
    Ostinato variation strategies: rhythmic displacement, register shift, voice-leading inversion.
    ↓
Phase 8: tests-ui/ framework setup
    Playwright + ChromeDriver installation, conftest.py, Allure wiring.
    First tests: loop coach happy path (enter chords → see 3 variants).
    Can run in parallel with Phase 7 work.
    ↓
Phase 9: AnalysisMCPGateway + FeedbackService + recorder page
    Gateway with health-check and offline fallback.
    Recorder page: file upload → WAV save → analyze() → display suggestions.
    Q&A widget.
    ↓
Phase 10: Violin duet mode
    InstrumentSet abstraction in LoopEngine.
    Merge logic from generate_simple_sexy_duet_loop.py.
    app/pages/duet.py.
    ↓
Phase 11: Drum machine
    DrumPreset data model.
    LoopEngine drum pattern builder (rhythm-only, GM MIDI channel 10).
    Drum track added to MIDI export.
    ↓
Phase 12: Looper slots / section management
    Named sections (Intro / Verse / Bridge) each with independent variant.
    Regenerate individual slot without resetting others.
    st.session_state slot management.
```

**Ordering rationale:**
- Phases 1–3 establish a testable pure-Python core; Streamlit is not involved at all.
- Phase 4 adds Streamlit only after the core is stable.
- Phase 5 (playback) must precede Phase 9 (recording) because the recorder page shows the variant the user practiced — it needs notation/playback already working.
- Phase 7 (variant generation) is placed after basic single-variant UI (Phase 5–6) to keep the first interactive loop simple.
- Phase 8 (tests-ui setup) is placed after the UI exists but before the more complex features, so regression coverage is in place during the harder phases.
- Phases 10–12 are strictly post-core: duet adds a second instrument to an existing engine; drums add a new preset type; looper slots add session management on top of everything else.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Audio Analysis MCP server | `AnalysisMCPGateway` wraps MCP client SDK; health-check cached 30 s; all calls return `None` on failure | Never called from UI directly; FeedbackService only |
| MuseScore (user's local app) | File-based: app writes MusicXML to `scores/musicxml/`; user opens manually | No programmatic integration needed |
| Ableton Live (user's DAW) | File-based: app writes MIDI to `scores/midi/`; user drags manually | No programmatic integration needed |

### Internal Boundaries

| Boundary | Communication | Direction | Notes |
|----------|---------------|-----------|-------|
| app/pages → app/services | Python function call with dataclass args | UI → Service | Services are not Streamlit-aware; return plain dataclasses |
| app/services → core/* | Python function call | Service → Core | Core modules never import from app/ |
| core/engine → core/presets | Import + lookup | Engine reads presets | PresetRegistry is stateless; no callbacks |
| core/theory → core/presets | Import + read | Explainer reads preset data | Same preset object used for generation and explanation |
| core/mcp/gateway → MCP server | HTTP or stdio MCP protocol | Gateway → MCP | Async preferred; sync fallback acceptable for v1 |
| tests-ui/ → Streamlit app | HTTP (Playwright browser) | Tests drive running server | tests-ui/ has zero Python imports from core/ or app/ |

---

## Scaling Considerations

This is a single-user local desktop tool. Scaling is not a goal. However, a few practical limits apply:

| Concern | At 1 user (target) | If shared locally (2-3 users) |
|---------|-------------------|-------------------------------|
| Generation speed | music21 Score build: ~0.5 s per variant; 3 variants: ~1.5 s — acceptable | Add async generation with st.spinner; no architecture change needed |
| Memory (session state) | 3 LoopVariant objects with SVG+MIDI bytes: ~5–15 MB — fine | Clear old sessions; add explicit "Clear session" button |
| MCP latency | 2–5 s analysis round-trip — acceptable with spinner | No change needed |
| File accumulation | scores/ and recordings/ grow unbounded | Add periodic cleanup of recordings/ (they are ephemeral) |

---

## Sources

- Direct code inspection: `scripts/generate_cello_dark_ostinato.py`, `scripts/harmony_advisor.py`, `scripts/generate_simple_sexy_duet_loop.py` (2026-06-22)
- Project requirements: `.planning/PROJECT.md` (2026-06-22)
- Streamlit session state and multi-page architecture: https://docs.streamlit.io/develop/concepts/architecture/session-state
- music21 Score serialization behavior: https://web.mit.edu/music21/doc/usersGuide/usersGuide_04_stream2.html
- Playwright Page Object Model pattern: https://playwright.dev/python/docs/pom
- Audio Analysis MCP integration pattern: inferred from MCP client SDK conventions (graceful degradation via health-check gateway is a standard pattern for optional service dependencies)

---

*Architecture research for: music-notation-codex (local Streamlit loop coach for electric cellist)*
*Researched: 2026-06-22*
*Confidence: HIGH for core architecture (based on direct code inspection); MEDIUM for MCP gateway details (MCP client API specifics depend on the concrete MCP server chosen)*
