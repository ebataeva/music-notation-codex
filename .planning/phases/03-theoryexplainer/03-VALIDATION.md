---
phase: 3
slug: theoryexplainer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing scaffold in `tests/`) |
| **Config file** | none — suite discovered from `tests/` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_theory_explainer.py -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds (current full suite: 101 tests in ~4.3s) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command (explainer unit tests)
- **After every plan wave:** Run the full suite command (includes golden regression)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

> Filled in by the planner — one row per task, mapped to THEORY-01, THEORY-02, TRACE-02 and the 4 ROADMAP success criteria. The map below lists the requirement-level contracts every plan must satisfy; task IDs are assigned at planning time.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | THEORY-01 | — | explain() returns TheoryExplanation with all 5 fields non-empty for all 7 presets (incl. 3 duet presets with empty theory tuples — fallback path) | unit | `.venv/bin/python -m pytest tests/test_theory_explainer.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | THEORY-02 | — | why_it_works / how_to_start / how_to_transition contain cello/looper cue vocabulary, no Cyrillic, no unexplained jargon terms from the banned list | unit | `.venv/bin/python -m pytest tests/test_theory_explainer.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | TRACE-02 | — | why_it_works contains ≥1 concrete anchor from GenerationTrace (actual pedal tone or chord tones + register); trace=None raises ValueError; same seed → identical text (deterministic); anchor selector branches on pattern_strategy per IN-01 | unit | `.venv/bin/python -m pytest tests/test_theory_explainer.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | Regression | — | golden MusicXML/MIDI hashes unchanged (explainer is text-only; must not touch notation output) | golden | `.venv/bin/python -m pytest tests/test_golden_regression.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_theory_explainer.py` — stubs for THEORY-01, THEORY-02, TRACE-02: all-fields-populated across all 7 presets, anchor-presence check, trace=None ValueError, determinism (same seed → same text), duet empty-tuple fallback, no-Cyrillic guard
- [ ] Two literal `GenerationTrace` fixtures (one `preset_verbatim` shape, one `progression_driven_register_mapped` shape) so the anchor selector is testable as a pure function without calling `generate_variant()`

---

## Success Criteria Mapping (ROADMAP Phase 3)

1. **All 5 fields populated for every supported preset** → THEORY-01 unit tests over all 7 presets, including duet fallback
2. **No unexplained jargon (manual review ≥4 presets)** → human checkpoint via refactored `scripts/harmony_advisor.py` CLI (D-10); automated pre-check: banned-jargon term list assertion
3. **Cello-specific cues in how_to_start/how_to_transition** → unit assertion on cue vocabulary (bowing/looper/dynamics terms per D-07)
4. **why_it_works references concrete trace data** → TRACE-02 anchor-presence test with literal trace fixtures (IN-01 branch coverage for both strategies)
