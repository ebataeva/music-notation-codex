---
phase: 1
slug: core-library-skeleton-validators
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-04
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (installed into .venv in Wave 0 alongside music21==10.5.0) |
| **Config file** | none — Wave 0 installs (pyproject/pytest.ini decided by planner) |
| **Quick run command** | `.venv/bin/python -m pytest tests/ -q` |
| **Full suite command** | `.venv/bin/python -m pytest tests/ -q && for s in scripts/generate_*.py; do .venv/bin/python "$s" >/dev/null; done` |
| **Estimated runtime** | ~10–30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/python -m pytest tests/ -q`
- **After every plan wave:** Run the full suite command (unit tests + all 5 scripts execute cleanly)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01-01 | 1 | PLAT-03 | — | core/ dataclasses (incl. GenerationTrace) importable, serialization-friendly | unit | `.venv/bin/python -m pytest tests/test_models.py -q` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01-01 | 1 | PLAT-03 | — | core/ never imports streamlit/argparse (positive-detection boundary test) | unit | `.venv/bin/python -m pytest tests/test_import_boundary.py -q` | ❌ W0 | ⬜ pending |
| 01-02-01/02 | 01-02 | 1 | LOOP-03 | — | out-of-range pitch (e.g. B1/D#5+) raises ValueError with readable message | unit (TDD) | `.venv/bin/python -m pytest tests/test_validators.py -q -k pitch` | ❌ W0 | ⬜ pending |
| 01-02-01/02 | 01-02 | 1 | LOOP-04 | — | rhythm sum ≠ TimeSignature.barDuration.quarterLength raises ValueError | unit (TDD) | `.venv/bin/python -m pytest tests/test_validators.py -q -k bar_duration` | ❌ W0 | ⬜ pending |
| 01-03-01 | 01-03 | 2 | PLAT-03 | — | requirements.txt pins music21==10.5.0; installs cleanly | CLI | `.venv/bin/python -m pip install -r requirements.txt && .venv/bin/python -c "import music21; print(music21.__version__)"` | ✅ | ⬜ pending |
| 01-03-02 | 01-03 | 2 | (criterion 3) | — | golden baseline captured on 10.5.0 BEFORE data move (MIDI SHA1 primary) | CLI | golden-capture script per plan; hashes stored under tests/golden/ | ❌ W0 | ⬜ pending |
| 01-04-01 | 01-04 | 3 | LOOP-03/04 (data) | — | MOOD_PRESETS registry (7 entries) merged verbatim, A1 note flagged not fixed | unit | `.venv/bin/python -m pytest tests/ -q` | ❌ W0 | ⬜ pending |
| 01-04-02 | 01-04 | 3 | (criterion 3) | — | all 5 scripts byte-identical MIDI vs golden after data-source swap | CLI | golden-compare per plan + run all 5 scripts | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (repo-root import path for core/)
- [ ] `tests/test_validators.py` — stubs for LOOP-03 / LOOP-04
- [ ] pytest install into .venv + requirements.txt update (music21==10.5.0, pytest)
- [ ] Golden baseline capture: run all 5 scripts on music21 10.5.0 BEFORE any data move; store MIDI SHA1 hashes (MusicXML is non-deterministic — MIDI hash is the primary guard per RESEARCH.md)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Code comments are English-only and only where non-obvious | PLAT-03 | Style judgment, not assertable | Review diff of core/ files during code review |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (all 8 tasks across 4 plans — confirmed by plan-checker)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-04 (plan-checker VERIFICATION PASSED, Dimension 8 checks 8a–8d)
