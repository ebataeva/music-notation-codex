---
task: 260714-v3b
title: Fix explainer crash — duet presets have dict-typed texture_idiom
subsystem: core/presets
tags: [bugfix, yaml-parsing, style-policy, duet-presets]
dependency-graph:
  requires: []
  provides: [_normalize_texture_idiom]
  affects: [core/theory/explainer.py]
tech-stack:
  added: []
  patterns: ["normalize untyped/loosely-typed external data (YAML) at the load boundary rather than adding isinstance checks at every consumer"]
key-files:
  created: []
  modified:
    - core/presets/style_policy.py
    - tests/test_style_policy.py
    - tests/test_theory_explainer.py
decisions:
  - "Reconstruct original prose from the misparsed dict via f\"{key}: {value}\" join, rather than modifying the YAML source files (avoids risk to other consumers of research/*.yaml)."
metrics:
  duration: "~15 minutes"
  completed: 2026-07-14
---

# Quick Task 260714-v3b: Fix explainer crash — duet presets have dict-typed texture_idiom Summary

Normalized `StylePolicy.texture_idiom` to always be a `str` at the YAML-load boundary, fixing an `AttributeError: 'dict' object has no attribute 'split'` crash in `core/theory/explainer.py::_style_context_clause` for the `sexy_duet` and `dorian_sexy_duet` presets.

## What Was Done

**Task 1: Normalize texture_idiom to string at YAML-load boundary**

Added `_normalize_texture_idiom(raw: Any) -> str` in `core/presets/style_policy.py`, placed above `_parse_style_policy`:
- `str` input → returned unchanged (no-op for the common case)
- `dict` input → reconstructed via `". ".join(f"{key}: {value}" for key, value in raw.items())`, recovering the mid-sentence colon that PyYAML misparsed as a mapping separator
- falsy/`None` → `""`
- anything else → `str(raw)`

`_parse_style_policy` now calls `texture_idiom=_normalize_texture_idiom(data.get("texture_idiom", ""))` instead of using the raw YAML value directly.

Root cause: `research/sexy_duet.yaml` and `research/dorian_sexy_duet.yaml` have `texture_idiom` prose containing a literal colon mid-sentence ("Duet texture: bass foundation..."). As an indented plain scalar without `|`/`>` block indicators or quoting, PyYAML's `safe_load` parsed the colon as a mapping separator, turning the field into a single-key dict instead of a string. `simple_sexy_duet.yaml` and `dark_trip_hop.yaml` have no colon in their prose and were already parsing correctly as `str` — confirmed unaffected by the fix.

Added `test_texture_idiom_is_always_a_string_even_when_yaml_has_colon()` to `tests/test_style_policy.py`, asserting:
- `sexy_duet` and `dorian_sexy_duet` texture_idiom are `str` and match/contain the expected reconstructed prose
- `simple_sexy_duet` and `dark_trip_hop` texture_idiom remain unchanged plain strings (regression guard)
- every preset in `list_presets_with_policy()` has `isinstance(policy.texture_idiom, str) is True`

Also extended the existing `test_get_style_policy_returns_policy_for_each_preset` loop with `assert isinstance(policy.texture_idiom, str)`.

**Task 2: Confirm explainer and full suite are green**

No production code changes were planned for this task, but running `tests/test_theory_explainer.py` revealed one additional failure unrelated to texture_idiom typing: `test_duet_presets_use_style_policy_data` asserted `"Aeolian" in explanation.why_it_works.lower()` — comparing a capitalized literal against a fully-lowercased string, which can never match. This is a pre-existing test bug, proven unrelated to the texture_idiom fix (confirmed by inspecting the assertion logic, not the production code path). Per Rule 1 (auto-fix bug), corrected the literal to `"aeolian"` to match the `.lower()` comparison already used elsewhere in the same test file (see line 363 for the same pattern).

## Verification

- `.venv/bin/pytest tests/test_style_policy.py -q` — 39 passed (10 in this file + others when combined with explainer file), 0 failures.
- `.venv/bin/pytest tests/test_theory_explainer.py -q` — 29 passed, 0 failures (previously 1 failed after texture_idiom fix, due to the unrelated case-sensitivity bug).
- `.venv/bin/pytest tests/ -q` — 184 passed, 0 failures, 1 unrelated pre-existing warning (`UserWarning: Skipping validate_pitch for legacy out-of-range note 'A1'`, not caused by this task).
- `StylePolicy.texture_idiom` confirmed `str` for every preset in `list_presets_with_policy()`.
- `app/services/generation.py` and `scores/musicxml/*.musicxml` untouched — confirmed via `git diff --stat` showing only `core/presets/style_policy.py`, `tests/test_style_policy.py`, and `tests/test_theory_explainer.py` changed by this plan's commits.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed case-sensitivity bug in `test_duet_presets_use_style_policy_data`**
- **Found during:** Task 2 verification run of `tests/test_theory_explainer.py`
- **Issue:** `assert "Aeolian" in explanation.why_it_works.lower()` compared a capitalized literal against a fully-lowercased string — structurally impossible to pass regardless of the texture_idiom fix.
- **Fix:** Changed the expected literal to lowercase `"aeolian"` to match the existing `.lower()` comparison pattern used elsewhere in the file.
- **Files modified:** `tests/test_theory_explainer.py`
- **Commit:** 9b29371

## Commits

- `40d307e` — fix(quick-260714-v3b): normalize texture_idiom to str at YAML-load boundary
- `9b29371` — fix(quick-260714-v3b): fix case-sensitivity bug in duet style-policy test

## Self-Check: PASSED

- FOUND: core/presets/style_policy.py contains `_normalize_texture_idiom`
- FOUND: tests/test_style_policy.py contains `test_texture_idiom_is_always_a_string_even_when_yaml_has_colon`
- FOUND: commit 40d307e
- FOUND: commit 9b29371
- FOUND: 184 passed in full test suite run, 0 failures
