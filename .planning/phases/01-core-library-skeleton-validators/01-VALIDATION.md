---
phase: 1
slug: core-library-skeleton-validators
status: draft
nyquist_compliant: false
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

*To be filled by the planner per task. Anchors from ROADMAP success criteria:*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | LOOP-03 | — | out-of-range pitch raises ValueError | unit | `.venv/bin/python -m pytest tests/ -q -k pitch` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | LOOP-04 | — | bad bar-duration sum raises ValueError | unit | `.venv/bin/python -m pytest tests/ -q -k bar_duration` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PLAT-03 | — | N/A | manual | — | — | ⬜ pending |

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
