# Phase 3 Audit: TheoryExplainer

**Audited:** 2026-07-06
**Commit:** 5f787e8
**Auditor:** GLM-5.2

---

## Verdict: PASS with findings

Phase 3 meets all 4 ROADMAP success criteria and all 6 plan must_have truths. 113/113 tests green. Golden regression intact. Import boundary respected. However, 3 findings below warrant attention before or during Phase 4.

---

## ROADMAP Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | explain() returns 5-field TheoryExplanation for every preset | PASS | `test_explain_populates_all_fields_for_every_preset` — all 7 presets (4 solo + 3 duet) |
| 2 | why_it_works has no unexplained jargon (manual review ≥4 presets) | PASS | Manual CLI review of 5 presets + `test_explanation_avoids_unexplained_jargon_terms` |
| 3 | how_to_start/how_to_transition include cello-specific cues | PASS | `test_cello_and_looper_cues_are_present` — "bow", "pulse", "loop", "register", "dynamics" |
| 4 | why_it_works references concrete trace data (pedal tone, chord tone, register) | PASS | `test_explanation_contains_trace_anchor` — C2 confirmed; progression-driven anchor confirmed via manual probe |

---

## Plan must_haves Truths

| # | Truth | Status |
|---|-------|--------|
| 1 | All five fields populated for every preset, including duets with empty tuples | PASS |
| 2 | why_it_works references concrete GenerationTrace decision | PASS |
| 3 | Anchor selection branches first on trace.pattern_strategy | PASS |
| 4 | trace=None raises ValueError | PASS |
| 5 | English, deterministic, no Cyrillic | PASS |
| 6 | Text-only: golden MusicXML/MIDI unchanged | PASS |

---

## Findings

### FINDING-1: MEDIUM — Preset theory data unused (D-09 violation)

**What:** The explainer does not incorporate `preset.progressions`, `preset.modulations`, or `preset.mood_tips` text into the explanation output. All 4 solo presets have rich theory data (2 progressions, 2 modulations, 3 mood_tips each) that is being ignored.

**D-09 says:**
- `progressions` → basis of `why_it_works`
- `modulations` → `how_to_transition`
- `mood_tips` → `how_to_develop`

**Actual implementation:**
- `why_it_works` uses a generic template with the anchor + key/mode + tempo + feel — no progression text
- `how_to_develop` uses a hardcoded string: `"Keep the bow close to the string and let small dynamic changes create motion."` — same for every preset
- `how_to_transition` uses a hardcoded string: `"Move by repeating the anchor once, then shift the next loop entry to a nearby pitch."` — same for every preset
- `_first_or_fallback` is called only as a boolean truthiness check (`if _first_or_fallback(preset.progressions, ""):`), never to surface the actual text

**Impact:** Solo presets lose their specific harmonic guidance. A user asking "why does dark_trip_hop work?" gets a generic answer instead of the carefully-written progression explanation ("i - VI - v - i: C minor -> Ab -> G minor -> C minor..."). This is the core value proposition of the phase.

**Recommendation:** Surface the first progression as the basis of `why_it_works`, the first modulation in `how_to_transition`, and the first mood_tip in `how_to_develop` — with fallbacks for duet presets. Can be done as a quick task before Phase 4.

### FINDING-2: LOW — No integration test for progression_driven_register_mapped through explain()

**What:** `_select_anchor` is unit-tested for both strategies, but `explain()` is only tested with `preset_verbatim` traces (via `trace_for_preset()` which always sets `pattern_strategy="preset_verbatim"`).

**Impact:** Phase 2.5 produces `progression_driven_register_mapped` traces. Phase 4 will call `explain()` on them. The integration path is untested — a bug in how `explain()` handles pitch-class anchors (e.g., "A" without octave) in the full output could surface in Phase 4.

**Mitigating factor:** Manual probe confirmed `explain()` works correctly with a progression-driven trace — the output contains "the chord tone A placed in the mid register". But this is not captured as a regression test.

**Recommendation:** Add one test: `test_explain_with_progression_driven_trace` that constructs a `progression_driven_register_mapped` trace, calls `explain()`, and asserts the chord tone appears in `why_it_works`.

### FINDING-3: INFO — Cue templates don't use `feel` or `meter_signature`

**What:** D-08 says cue content should be "parameterized by preset characteristics (tempo, meter, mood/feel)". Current implementation uses only tempo band and register.

**Impact:** Minor. Cues are still cello-specific and practical. Meter and feel could add variety (e.g., 3/4 vs 4/4 pulse language), but the MVP success criteria are met without them.

**Recommendation:** Defer to a future enhancement — not blocking for Phase 4.

---

## Decisions Verified (D-01..D-11)

| Decision | Status | Notes |
|----------|--------|-------|
| D-01: All output English | PASS | `test_explanation_text_contains_no_cyrillic` |
| D-02: Russian prose translated | PASS | Done in quick task 260706-21y; goldens green |
| D-03: Faithful/literal translation | PASS | Jargon cleanup deferred per plan |
| D-04: why_it_works weaves 1-2 anchor sentences | PASS | Anchor present, not over-detailed |
| D-05: Anchor selection deterministic heuristic | PASS | `test_explain_is_deterministic_for_same_input` |
| D-06: trace=None → ValueError | PASS | `test_explain_requires_trace` |
| D-07: Cue types: bowing, looper, dynamics | PASS | All present in cue templates |
| D-08: Template-driven, parameterized | PARTIAL | Uses tempo + register; not meter/feel (FINDING-3) |
| D-09: Field mapping from preset data | FAIL | Theory data unused (FINDING-1) |
| D-10: CLI becomes thin wrapper with --seed | PASS | `--seed` added; prints all 5 fields |
| D-11: Duet presets explainable | PASS | `test_duet_presets_with_empty_theory_tuples_use_fallback_text` |

---

## Import Boundary & Blast Radius

- **Files modified:** `core/theory/__init__.py`, `core/theory/explainer.py`, `core/theory/cues.py`, `scripts/harmony_advisor.py`, `tests/test_theory_explainer.py` — all within plan scope ✅
- **No changes to:** `core/models.py`, `core/presets/`, `core/engine/`, score files ✅
- **Golden regression:** 113/113 tests pass, musicxml files unchanged ✅
- **Cue selection not keyed by preset name:** `test_cue_selection_is_not_keyed_by_preset_name` passes ✅

---

## Test Coverage Summary

| Test | What it covers |
|------|----------------|
| `test_explain_populates_all_fields_for_every_preset` | SC-1: all 7 presets, 5 fields |
| `test_duet_presets_with_empty_theory_tuples_use_fallback_text` | D-11: duet fallback |
| `test_explain_requires_trace` | D-06: trace=None raises |
| `test_explain_is_deterministic_for_same_input` | D-05: same input → same output |
| `test_preset_verbatim_anchor_uses_octave_bearing_pitch` | IN-01: preset_verbatim anchor |
| `test_progression_anchor_uses_pitch_class_with_register_choice` | IN-01: progression anchor |
| `test_unknown_pattern_strategy_raises_value_error` | Defensive: unknown strategy |
| `test_explanation_contains_trace_anchor` | SC-4: trace data in why_it_works |
| `test_cello_and_looper_cues_are_present` | SC-3: cello vocabulary |
| `test_explanation_text_contains_no_cyrillic` | D-01: English only |
| `test_explanation_avoids_unexplained_jargon_terms` | SC-2: no jargon |
| `test_cue_selection_is_not_keyed_by_preset_name` | D-08: property-based |

**Gap:** No `explain()` integration test with `progression_driven_register_mapped` trace (FINDING-2).

---

## Summary

Phase 3 is functionally complete and meets all ROADMAP success criteria. The implementation is clean, well-tested (12 tests), and respects the import boundary. The main finding (FINDING-1: D-09 preset theory data unused) is a quality gap — the carefully-written progression/modulation/mood_tip text in solo presets is being ignored in favor of generic hardcoded strings. This should be addressed before Phase 4, either as a quick task or as part of Phase 4's integration work.

---

*Audit completed: 2026-07-06*
