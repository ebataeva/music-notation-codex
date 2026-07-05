---
phase: 2
slug: loopengine-exportengine
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-06
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> **Retro-filled 2026-07-06** by the Nyquist validation auditor per the v1
> interim milestone audit (`.planning/v1-MILESTONE-AUDIT.md`), which flagged
> Phase 2 as the only complete phase missing this artifact. Phase 2 was
> already implemented and verified (`02-VERIFICATION.md`, passed 12/12) —
> this file audits that existing coverage against the phase's 3 requirements
> and closes gaps found with new tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (config in `pytest.ini`) |
| **Config file** | `pytest.ini` |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_loop_engine.py tests/test_exporter.py tests/test_validation_phase2.py -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q` |
| **Estimated runtime** | ~4 seconds (full suite, 94 tests) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~4 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01/02-02/02-03 | 02-01, 02-02, 02-03 | LOOP-01 | — | `build_score`/`generate_variant` return a populated Score + GenerationTrace for a real MoodPreset, no errors | unit | `pytest tests/test_loop_engine.py -q` | ✅ | ✅ green |
| 02-01/02-02/02-03 | 02-01, 02-02, 02-03 | LOOP-01 (gap-fill) | — | End-to-end smoke: `generate_variant` produces a trace with `pattern_strategy`, `chord_tones_used`, `register_choices` all populated and length-matched to preset bars | unit | `pytest tests/test_validation_phase2.py -q -k produces_playable_loop` | ✅ | ✅ green |
| 02-02-01 | 02-02 | SAFE-02 (solo path) | — | `build_score`/`generate_variant` reject >64-bar preset with `ValueError` before Score is built | unit | `pytest tests/test_loop_engine.py -q -k 64_bars` | ✅ | ✅ green |
| 02-02-01 (gap-fill, was WR-03 in 02-REVIEW.md) | 02-02 | SAFE-02 (duet path) | WR-03 | `build_duet_score` rejects a >64-bar per-instrument request with `ValueError` before Score is built | unit | `pytest tests/test_validation_phase2.py -q -k duet_score_rejects` | ✅ | ✅ green |
| 02.5 carry-forward (gap-fill) | — | SAFE-02 (progression-build path) | — | `build_progression_score` rejects a >64-chord progression with `ValueError` before Score is built | unit | `pytest tests/test_validation_phase2.py -q -k progression_score_rejects` | ✅ | ✅ green |
| 02.5 carry-forward (gap-fill) | — | SAFE-02 (progression-variant path) | — | `generate_variant_from_progression` rejects a >64-chord progression with `ValueError` before Score is built | unit | `pytest tests/test_validation_phase2.py -q -k from_progression_rejects` | ✅ | ✅ green |
| 02-02-01 (gap-fill) | 02-02 | SAFE-07 (preset path) | — | `generate_variant` does not recursively invoke itself / spawn further variant-generation calls — proven via call-count instrumentation, not code reading | unit | `pytest tests/test_validation_phase2.py -q -k not_recursively_generate` | ✅ | ✅ green |
| 02-02-01 (gap-fill) | 02-02 | SAFE-07 (progression path) | — | `generate_variant_from_progression` is likewise flat/non-recursive | unit | `pytest tests/test_validation_phase2.py -q -k not_recursively_spawn` | ✅ | ✅ green |
| 02-01/02-03 | 02-01, 02-03 | Golden regression (scripts stay thin wrappers) | — | All 4 generator scripts produce byte-identical MIDI vs golden baseline | regression | `pytest tests/test_golden_regression.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Requirement → test evidence:**
- **LOOP-01** — `test_build_score_returns_music21_score_no_errors`, `test_build_score_has_expected_measure_count`, `test_generate_variant_pattern_strategy_is_non_empty_string`, `test_generate_variant_register_choices_one_per_bar`, `test_generate_variant_chord_tones_used_matches_bars` (`tests/test_loop_engine.py`); `test_generate_variant_produces_playable_loop_from_preset_no_errors` (`tests/test_validation_phase2.py`, gap-fill smoke covering the full LOOP-01 observable promise in one assertion chain)
- **SAFE-02** — solo path: `test_build_score_raises_value_error_for_out_of_range_pitch_not_excepted` (pitch, adjacent guard), `test_generate_variant_raises_for_more_than_64_bars_before_score_built` (`tests/test_loop_engine.py`); duet path (previously the WR-03 gap in `02-REVIEW.md`/`02-VERIFICATION.md`): `test_build_duet_score_rejects_more_than_64_bars_per_part`; progression paths (added when Phase 2.5 introduced `build_progression_score`/`generate_variant_from_progression` but never covered by a SAFE-02-specific test): `test_build_progression_score_rejects_more_than_64_chords`, `test_generate_variant_from_progression_rejects_more_than_64_chords` (all three gap-fill tests in `tests/test_validation_phase2.py`)
- **SAFE-07** — previously verified only by manual code reading in `02-VERIFICATION.md` ("read in full — no self-recursive... call path exists"), with zero automated regression coverage; gap-filled behaviorally via call-count instrumentation: `test_generate_variant_does_not_recursively_generate_further_variants`, `test_generate_variant_from_progression_does_not_recursively_spawn_variants` (`tests/test_validation_phase2.py`)

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. pytest + `pytest.ini` were already in place; no new framework, fixtures, or dependencies required for the gap-fill tests.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| Ear-check (does a preset-driven loop sound idiomatic on cello) | LOOP-01 (subjective quality) | Musical "vibe" is subjective — automated tests confirm the loop is generated without error and carries a populated trace, not aesthetic quality | Render a preset to audio via `ExportEngine`/`midi2audio`, listen for idiomatic voicing; out of scope for Phase 2 (Phase 2.5's UAT already exercises the progression-driven ear-check) |

---

## Validation Sign-Off

- [x] All tasks have automated verify (all 3 requirements — LOOP-01, SAFE-02, SAFE-07 — now have executed, passing tests)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none — existing infra sufficient)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

## Validation Audit 2026-07-06

| Metric | Count |
|--------|-------|
| Requirements audited | 3 (LOOP-01, SAFE-02, SAFE-07) |
| COVERED (pre-existing, no new test needed) | 1 (LOOP-01 core behavior already had solid coverage in `test_loop_engine.py`; added one smoke test to make the full observable promise explicit) |
| Gaps found | 3 |
| Gap 1 | SAFE-02 duet path (`build_duet_score`) had a real code guard (added post-verification, commit `01c45d8`, fixing `02-REVIEW.md` WR-03) but **no automated test** exercising it — `02-VERIFICATION.md`'s PARTIAL finding was about the missing guard, which is now fixed in code, but the verification artifact was never updated with a corresponding test |
| Gap 2 | SAFE-02 progression paths (`build_progression_score`, `generate_variant_from_progression`, added in Phase 2.5) had the guard in code but no requirement-labeled test asserting it specifically (existing Phase 2.5 tests cover leap/register/monophony behavior, not the bar-count ceiling) |
| Gap 3 | SAFE-07 had **zero automated coverage** — `02-VERIFICATION.md` verified it exclusively via manual code reading ("read in full — no self-recursive... call path exists"), which is not a regression-safe check; a future refactor could silently introduce recursive variant spawning with no test to catch it |
| Resolved | 3 (all closed by `tests/test_validation_phase2.py`, 6 new tests, all executed and passing; full suite 94/94 green) |
| Escalated | 0 |

**Note on the SAFE-01 (`MAX_NOTES=512`) guard:** at the time of this audit, a MAX_NOTES guard was being actively added to `loop_engine.py` by a concurrent workstream (per `v1-MILESTONE-AUDIT.md`'s SAFE-01 orphaned-requirement finding). This validation file and its gap-fill tests deliberately do not reference or depend on that guard — SAFE-01 belongs to Phase 1's traceability mapping, not Phase 2's declared requirements (LOOP-01, SAFE-02, SAFE-07), and its absence at audit time is not counted as a Phase 2 gap.

Full suite green: 94 passed, 1 warning (pre-existing D-07 legacy-note warning, expected, unrelated to this audit). No BLOCKER-level gaps — all 3 requirements now have executed, passing, requirement-labeled automated tests.

**Approval:** approved 2026-07-06 (Nyquist validation audit, retro-fill)
