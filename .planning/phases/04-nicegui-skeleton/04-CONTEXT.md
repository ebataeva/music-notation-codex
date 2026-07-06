# Phase 4: NiceGUI Skeleton + App State — Context

**Gathered:** 2026-07-06
**Status:** Ready for execution

<domain>
## Phase Boundary

Build the NiceGUI app skeleton: `app/main.py` entry point, `app/pages/loop_coach.py` primary page, `app/services/generation.py` orchestration service. The app accepts chord progression text + key/mood dropdowns, generates a cello loop via `generate_variant_from_progression()`, and displays the `TheoryExplanation` as text. No notation rendering or audio playback (Phase 5). No export buttons (Phase 6). State survives browser refresh via `app.storage`.

Tech stack: NiceGUI 3.14.0 — replaces the abandoned Streamlit approach. NiceGUI provides a real persistent DOM with stable element ids, enabling Phase 8 Playwright tests.
</domain>

<decisions>
## Implementation Decisions

### Architecture
- **D-01:** `app/` directory (new) replaces `apps/` (Streamlit prototype). `apps/ear_check_streamlit.py` stays as reference, not refactored.
- **D-02:** No music21 import in `app/` layer. The GenerationService calls `core/` functions; app layer only handles UI + serialization.
- **D-03:** LoopVariant serialization: store `midi_bytes`, `musicxml_path`, `midi_path`, and the serialized TheoryExplanation text in `app.storage`. Do NOT store live music21 Score objects (not JSON-serializable). The Score is rebuilt from bytes/paths when needed (Phase 5/6).

### UI Structure
- **D-04:** Single-page app (`app/main.py` + `app/pages/loop_coach.py`). No multi-page routing for v1.
- **D-05:** Stable element ids via `.props('id=...')` on every interactive element — the selector contract for Phase 8 Playwright tests. IDs: `chord-input`, `key-tonic-select`, `key-mode-select`, `mood-select`, `generate-btn`, `example-btn`, `theory-output`.
- **D-06:** `app.storage` (NiceGUI built-in per-client storage) holds the last generation result. On page refresh, the UI restores from storage.

### Input Widgets
- **D-07:** Chord progression: `ui.input` with placeholder "Am F C G". Key tonic: `ui.select` with all 12 tones. Key mode: `ui.select` with major/minor. Mood: `ui.select` from `list_presets()`.
- **D-08:** "Example input" button fills the form with "Am F C G" / A / minor / dark_trip_hop — a working demo for on-camera use.

### Generation Flow
- **D-09:** Generate button → parse chords via `parse_progression()` → `generate_variant_from_progression(chords, preset, seed)` → `explain(variant, preset)` → display 5 TheoryExplanation fields as text.
- **D-10:** Seed is optional (random by default). A "reproducible" checkbox + seed input can be added later; for now, random seed.
- **D-11:** SAFE-08: Generate button is disabled while generation is in flight (debounce). NiceGUI has no rerun model, so this targets double-clicks.

### Performance
- **D-12:** Generation typically completes in <1s (8 bars of cello). If it exceeds the budget, `run.cpu_bound` is available, but for v1 the sync path is sufficient.

### SAFE-05
- **D-13:** Explanation text truncated at 500 words per field in the UI layer (not in `explainer.py` — keep the core pure). Simple `text[:500]` truncation is sufficient for MVP.
</decisions>

<canonical_refs>
## Canonical References

### Core API (read-only consumers)
- `core/engine/loop_engine.py` — `generate_variant_from_progression(chords, preset, seed)` returns `LoopVariant` with `midi_bytes`, `musicxml_path`, `trace`
- `core/engine/progression.py` — `parse_progression(text)` returns `list[ParsedChord]`; raises `ValueError` on bad tokens
- `core/theory/explainer.py` — `explain(variant, preset)` returns `TheoryExplanation` (5 str fields)
- `core/presets/registry.py` — `list_presets()`, `get_preset(name)` for mood dropdown
- `core/models.py` — `LoopVariant`, `TheoryExplanation`, `MoodPreset`, `GenerationRequest` dataclasses

### Existing patterns
- `apps/ear_check_streamlit.py` — Streamlit prototype (reference for UI flow, not code reuse)
- `scripts/harmony_advisor.py` — CLI wrapper showing the explain() → print pattern

### Stack decisions
- CLAUDE.md — NiceGUI 3.14.0, FluidSynth, OSMD, midi2audio (locked stack)
- .planning/ROADMAP.md lines 112-131 — Phase 4 success criteria (9 criteria)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_variant_from_progression()` already produces `midi_bytes` and `musicxml_path` — the UI can serialize these
- `parse_progression()` already validates chord input with clear error messages — the UI can display these directly
- `explain()` already returns 5-field TheoryExplanation — the UI just renders each field

### Integration Points
- Phase 5 will add OSMD notation rendering into a DOM div on the same page
- Phase 6 will add download buttons using ExportEngine on the same page
- Phase 8 will use stable element ids from this phase for Playwright selectors
</code_context>

---

*Phase: 04-nicegui-skeleton*
*Context gathered: 2026-07-06*
