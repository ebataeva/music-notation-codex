# Phase 3: TheoryExplainer - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

The harmony text from `scripts/harmony_advisor.py` moves into `core/theory/explainer.py` as structured `TheoryExplanation` output. Given a `LoopVariant` and `MoodPreset`, the explainer returns plain-language "why it works" plus start/develop/end/transition guidance, grounded in the variant's `GenerationTrace` (TRACE-02). All explanation text is English. No UI (Phase 4), no LLM-generated explanations (THEORY-03 → v2), duet generation as a public feature stays v2 — duet data is used only as a note source for explanations.

</domain>

<decisions>
## Implementation Decisions

### Language & translation
- **D-01:** All explanation output is English, starting THIS phase — matches the locked "All visible UI copy in English" constraint; Phase 4 receives display-ready text with no rework.
- **D-02:** The Russian preset texts (`progressions`, `modulations`, `mood_tips`, **and `feel`**) are translated to English directly in `core/presets/mood_presets.py` — one language across the whole library. This does not affect MusicXML/MIDI goldens (text fields never enter notation files) — must be confirmed by the golden regression suite staying green.
- **D-03:** Translation is **faithful/literal** (not a rewrite). Jargon cleanup happens as a SEPARATE review pass AFTER the user's manual review (success criterion #2: review of ≥4 presets) — the phase plan must include this review checkpoint.

### Trace grounding (TRACE-02)
- **D-04:** `why_it_works` weaves in 1–2 anchor sentences with real trace data (actual pedal tone, chord tones, register). Full trace breakdown is Phase 12's job — do not duplicate it here.
- **D-05:** Anchor selection uses a deterministic "most salient" heuristic: repeated lowest note present → name the pedal tone; otherwise → first bar's chord tones + chosen register. Branch on `pattern_strategy` per IN-01 (`preset_verbatim`: octave-bearing pitches in `chord_tones_used`; `progression_driven_register_mapped`: pitch classes + `register_choices` recorded separately). Same seed → same text (reproducible).
- **D-06:** `trace=None` → clear `ValueError` (Phase 1 validator style, no custom exception types). No silent degradation to preset-only text — TRACE-02 is guaranteed by contract.
- **Constraint:** `voice_leading_steps` is currently always `None` in both strategies — anchors can only use `chord_tones_used` / `register_choices`.

### Cello-specific cues (success criterion #3)
- **D-07:** Cue types to include: bowing/articulation (legato/détaché, pizzicato, tremolo, accents), looper workflow (layer order, entering/exiting the loop, section transitions via loop pedal), dynamics/effects (volume arcs, reverb/distortion changes between sections). Strings/positions cues were explicitly NOT selected.
- **D-08:** Cue content comes from a shared template library parameterized by preset characteristics (tempo, meter, mood/feel) and trace data — template-driven per the phase goal, not 28 hand-written texts. New presets get guidance for free.
- **D-09:** Preset-data → field mapping (locked): `progressions` → basis of `why_it_works`; `modulations` → `how_to_transition`; `mood_tips` → `how_to_develop`; `how_to_start` and `how_to_end` → new templates (looper + bowing + dynamics cues).

### harmony_advisor CLI
- **D-10:** The CLI becomes a thin wrapper that GENERATES a variant via LoopEngine (optional `--seed`) and prints the full `TheoryExplanation` with trace anchors — the ready-made tool for the user's manual review of ≥4 presets (criterion #2) before any UI exists.
- **D-11:** Duet presets (`sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet` — all confirmed to have 0 solo bars): the variant is built from the cello part of `duet_bars` via Phase 2's internal duet build path (Phase 2 D-13). Explanations therefore work for all 7 presets (criterion #1). Duet generation as a public feature remains v2 (DUET-01).

### Claude's Discretion
- Where the English template/cue content lives: inside `explainer.py` vs a separate data module under `core/theory/`.
- Explanation test strategy (all 5 fields non-empty, anchor actually present in text, no Cyrillic after translation, etc.).
- API shape: `explain(variant, preset)` vs `explain(variant)` + registry lookup; class vs module-level functions (Phase 1 style).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & prior decisions
- `.planning/research/ARCHITECTURE.md` — §TheoryExplainer (`core/theory/explainer.py` responsibilities; GENRE_IDEAS as the explainer's "seed"; `main()`/`print_section()` deleted from the script), Pattern 2 (MoodPreset carries theory data alongside generation data)
- `.planning/phases/02-loopengine-exportengine/02-CONTEXT.md` — D-04 (trace populated honestly for every strategy), D-05 (`generate_variant()` → LoopVariant is what Phase 3 consumes), D-11 (harmony_advisor deferred to Phase 3), D-13 (internal duet build path, not public API)
- `.planning/phases/02.5-progression-driven-generation/02.5-01-SUMMARY.md` — progression-driven strategy outputs
- `.planning/phases/02.5-progression-driven-generation/02.5-REVIEW-FIX.md` — IN-01 fix (chord_tones_used shape depends on strategy)

### Source material (brownfield)
- `core/models.py` — `TheoryExplanation` (5 str fields, locked in Phase 1), `GenerationTrace` with the IN-01 docstring (consumers must branch on `pattern_strategy`)
- `core/presets/mood_presets.py` — the Russian text fields to translate (D-02)
- `scripts/harmony_advisor.py` — the CLI to refactor into a thin wrapper (D-10)

### Regression guard
- `tests/test_golden_regression.py` + `tests/golden/baseline_hashes.json` — must stay green after preset text translation (D-02 verification)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/presets/registry.py` (`get_preset`, `list_presets`): preset source for the explainer and CLI
- `core/engine/loop_engine.py` `generate_variant()`: returns LoopVariant with an always-populated trace (Phase 2 seed policy D-01/D-02) — the CLI's generation entry point
- Internal duet build path in `core/engine/loop_engine.py` (Phase 2 D-13): note source for duet-preset explanations (D-11)
- `tests/` pytest scaffold + golden hashes: extend with explainer unit tests; golden suite guards the preset translation

### Established Patterns
- Module-level functions + plain `ValueError`, no custom exception types (01-PATTERNS.md) — D-06 follows this
- Branch on `pattern_strategy` per IN-01 docstring in `core/models.py` — never assume one `chord_tones_used` shape

### Integration Points
- Phase 4 calls `explain()` on Generate and displays the five fields as text
- Phase 12 (Transparency & Compare) reads the same GenerationTrace for the full breakdown — Phase 3 keeps anchors light (D-04)

</code_context>

<specifics>
## Specific Ideas

- Success criterion #2 (manual jargon review of ≥4 presets) is executed via the refactored CLI: `python3 scripts/harmony_advisor.py --genre X [--seed N]` prints the full explanation for review — no UI needed.
- Confirmed by script during discussion: all 3 duet presets have `solo_bars=0, rhythm=0, duet=True`; the 4 solo presets have 8 solo bars each.

</specifics>

<deferred>
## Deferred Ideas

- **Goal-conditioned performance feedback** ("we play TO the advisor — it evaluates our playing and gives advice depending on what we want to achieve"): recording + analysis + suggestions already exist as Phase 9 (FEEDBACK-01..04), but tying advice to the user's stated goal is broader than the current requirements — factor this in when planning Phase 9.
- Jargon rewrite of translated texts — a separate review pass after the user's manual review (a checkpoint within this phase, deliberately NOT part of the initial literal translation pass).

</deferred>

---

*Phase: 03-theoryexplainer*
*Context gathered: 2026-07-05*
