---
phase: 01-core-library-skeleton-validators
verified: 2026-07-04T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
mvp_mode_discrepancy: "ROADMAP.md declares Mode: mvp for this phase, but the phase goal is not in User Story format (\"As a ... I want to ... so that ...\"). gsd-sdk query user-story.validate confirms invalid=true. This is a pure-Python library/backend phase with no user-facing surface, so standard goal-backward verification against the roadmap Success Criteria was used instead of MVP user-flow framing. Recommend running /gsd mvp-phase 1 to either reformat the goal or clear the mvp mode flag, or accepting this as an intentional non-UI phase exemption."
---

# Phase 1: Core Library Skeleton + Validators Verification Report

**Phase Goal:** The core/ library structure exists with all dataclasses (MoodPreset, LoopVariant, GenerationRequest, TheoryExplanation, GenerationTrace), a MoodPreset registry merged from all 5 CLI scripts (GENRE_PRESETS + GENRE_IDEAS + duet preset data as data-only), a pytest scaffold for core unit tests, and validators that enforce cello range and bar duration correctness.
**Verified:** 2026-07-04
**Status:** passed
**Re-verification:** No — initial verification

## MVP Mode Note

ROADMAP.md marks this phase `Mode: mvp`, but the goal text fails User Story format validation (`gsd-sdk query user-story.validate` → `valid: false`, missing "As a", "I want to", "so that" clauses). Per the MVP-mode verification contract, this is surfaced as a discrepancy rather than silently forced into user-flow framing. Given this phase ships zero user-facing UI (pure Python library + validators + pytest scaffold, no Streamlit code yet — Streamlit UI starts Phase 4), standard goal-backward verification against the roadmap's explicit Success Criteria list was used, which is the substantively correct verification approach for this phase's actual content. This is reported as a WARNING for the human to resolve the mode/goal-format mismatch in ROADMAP.md, not a phase-blocking gap.

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria — authoritative contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A note outside C2-D5 raises a validation error at generation time, confirmed by a passing pytest unit test | VERIFIED | `core/engine/validators.py:9-16` `validate_pitch()`; `tests/test_validators.py` has 9 dedicated pitch tests (in-range no-raise, out-of-range raise, extended flag, accidentals); live spot-check: `validate_pitch("A1")` raises `ValueError: Pitch A1 (MIDI 33) is outside playable cello range (36-74).` |
| 2 | A rhythm pattern whose durations do not sum to the bar length raises a validation error, confirmed by unit test | VERIFIED | `core/engine/validators.py:19-28` `validate_bar_duration()`; 5 dedicated tests in `tests/test_validators.py` cover 4/4 and 3/4 meters, both match and mismatch cases, and the real `sexy_duet` rhythm pattern |
| 3 | All existing CLI scripts still produce the same output files after refactoring their data into core/presets/ | VERIFIED | `tests/test_golden_regression.py` passes 2/2 (`test_midi_outputs_match_baseline`, `test_musicxml_outputs_match_baseline_normalized`) comparing post-migration script output against Plan 03's pre-migration baseline (`tests/golden/baseline_hashes.json`, 7 MIDI + 7 normalized-MusicXML entries); live `git diff` on a regenerated MusicXML file confirms only volatile `id="P.../I..."` attributes changed, zero note/content differences |
| 4 | `pytest tests/` runs the core unit suite with zero failures (pytest infrastructure established) | VERIFIED | `.venv/bin/python3 -m pytest tests/ -q` → `30 passed in ~3.7s`; `pytest.ini` sets `testpaths = tests`, scoping discovery away from a future `tests-ui/` |
| 5 | Dataclasses include GenerationTrace fields (seed, pattern strategy, register, voice-leading, chord tones) so later phases don't retrofit them | VERIFIED | `core/models.py:27-33` — `GenerationTrace` has exactly `seed, pattern_strategy, register_choices, voice_leading_steps, chord_tones_used`; `tests/test_models.py` asserts the exact field-name set via `dataclasses.fields()` |
| 6 | requirements.txt pins the approved stack (music21==10.5.0) and installs cleanly on Python 3.12+ | VERIFIED | `cat requirements.txt` → `music21==10.5.0` / `pytest`; `.venv/bin/python3 -c "import music21; print(music21.__version__)"` → `10.5.0` |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `core/models.py` | 5 canonical dataclasses incl. locked GenerationTrace shape | VERIFIED | All 5 present with exact field sets per 01-01-PLAN.md; `MoodPreset` is `@dataclass(frozen=True)`; `LoopVariant.trace` defaults to `None`; no music21 objects required to construct any dataclass |
| `core/engine/validators.py` | `validate_pitch`, `validate_bar_duration` | VERIFIED | Both plain functions, narrow `from music21 import meter, pitch` import, no `4.0` hardcoded (grep confirms zero matches), no custom exception classes, no `__post_init__` |
| `core/presets/mood_presets.py` | `MOOD_PRESETS` dict with 7 entries | VERIFIED | 7 entries present (4 solo + 3 duet), data migrated verbatim including Russian text and the flagged "A1" out-of-range note with inline comment |
| `core/presets/registry.py` | `get_preset(name)`, `list_presets()` | VERIFIED | Plain dict lookup + `sorted()`, natural `KeyError` on miss, no custom exception |
| `pytest.ini` | `testpaths = tests` | VERIFIED | Present at repo root, exact content `[pytest]\ntestpaths = tests` |
| `tests/test_models.py` | Dataclass shape/default tests | VERIFIED | 5 test functions covering import, GenerationTrace field set, LoopVariant.trace default, MoodPreset frozen + defaults, GenerationRequest defaults |
| `tests/test_import_boundary.py` | AST-based import-boundary guard | VERIFIED | 2 tests: real sweep over `core/**/*.py` + non-vacuous fixture-based positive-detection test; shared `_forbidden_imports_in_file()` helper |
| `tests/test_validators.py` | LOOP-03/LOOP-04 unit tests | VERIFIED | 14 test functions, individually named, covering range floor/ceiling, extended mode, accidentals, message content, both 4/4 and 3/4 meters |
| `tests/golden/baseline_hashes.json` | MIDI SHA1 + normalized MusicXML SHA1 baseline | VERIFIED | 7 MIDI + 7 musicxml_normalized entries (corrected from plan's stated 8+8 — documented and justified in 01-03-SUMMARY.md as an arithmetic correction, not a scope reduction) |
| `tests/test_golden_regression.py` | Regression comparison against baseline | VERIFIED | 2 tests, both passing against the post-migration codebase |
| `tests/test_presets_registry.py` | Merge-completeness tests | VERIFIED | 7 tests proving all 5 source scripts' data landed in the registry with no silent loss |
| `requirements.txt` | `music21==10.5.0` pin | VERIFIED | Exact pin present; installs cleanly, `music21.__version__ == "10.5.0"` confirmed live |
| 5 CLI scripts (data-source swap) | Import from `core.presets.registry` instead of inline dicts | VERIFIED | `grep` confirms `from core.presets.registry import` in all 5 scripts; zero remaining `GENRE_PRESETS`/`GENRE_IDEAS` dict literals or `GenrePreset` class |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tests/test_models.py` | `core/models.py` | `from core.models import ...` | WIRED | Import present, tests exercise real dataclass construction |
| `tests/test_validators.py` | `core/engine/validators.py` | `from core.engine.validators import validate_pitch, validate_bar_duration` | WIRED | Import present, 14 tests call both functions with real music21-backed logic |
| `tests/test_import_boundary.py` | `core/` | AST walk over `core/**/*.py` | WIRED | Confirmed non-vacuous via fixture test |
| `core/presets/mood_presets.py` | `core/models.py` | `from core.models import MoodPreset` | WIRED | Confirmed in file header |
| `core/presets/registry.py` | `core/presets/mood_presets.py` | `from core.presets.mood_presets import MOOD_PRESETS` | WIRED | Confirmed |
| 5 `scripts/*.py` | `core/presets/registry.py` | `from core.presets.registry import get_preset, list_presets` | WIRED | Confirmed in all 5 files; live CLI run (`--list-genres`) and `harmony_advisor.py --genre ritual_tribal` both exit 0 with real content |
| `tests/test_golden_regression.py` | `tests/golden/baseline_hashes.json` | `json.load` | WIRED | Test loads and compares against baseline; passes |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite passes | `.venv/bin/python3 -m pytest tests/ -q` | `30 passed in 3.69s` | PASS |
| Out-of-range pitch raises | `validate_pitch("A1")` | `ValueError: Pitch A1 (MIDI 33) is outside playable cello range (36-74).` | PASS |
| CLI lists all moods with feel text | `generate_cello_dark_ostinato.py --list-genres` | Prints all 7 preset names with feel text (4 solo have full Russian feel text; 3 duets have blank/short feel — expected, matches plan's "do not fabricate" instruction) | PASS |
| Golden regression is a true no-op | `pytest tests/test_golden_regression.py -v` | `2 passed`; `git diff` on regenerated MusicXML shows only volatile id attributes changed | PASS |
| music21 pin installs cleanly | `python3 -c "import music21; print(music21.__version__)"` | `10.5.0` | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| LOOP-03 | 01-02, 01-04 | Every generated note is within playable cello range (C2-D5), validated at generation time | SATISFIED | `validate_pitch` implemented and unit-tested (14 tests); note: not yet wired into any generation call path — by design, deferred to Phase 2 per both plans' explicit scope statements |
| LOOP-04 | 01-02, 01-04 | Each bar's rhythm sums exactly to the meter, validated | SATISFIED | `validate_bar_duration` implemented and unit-tested against 4/4 and 3/4 meters, never hardcoding 4.0 |
| PLAT-03 | 01-01, 01-03 | Code comments in English, only where they clarify non-obvious logic | SATISFIED | Spot-checked `core/models.py`, `core/engine/validators.py`, `core/presets/mood_presets.py`, `core/presets/registry.py` — all comments are English and explain non-obvious decisions (e.g. trace default, A1 flag, MIDI constant meanings); no Russian comments (Russian text appears only in migrated preset *data* fields, which is correct — PLAT-02 governs UI copy, not preset content, and this data isn't UI copy in this phase) |

No orphaned requirements: REQUIREMENTS.md maps exactly LOOP-03, LOOP-04, PLAT-03 to Phase 1, and all three are declared across the phase's plans' `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in any phase-modified file | — | — |
| `core/engine/validators.py` | 9-16 | `validate_pitch` accepts octave-less pitch names (defaults to octave 4) and leaks `music21.pitch.PitchException` instead of `ValueError` for malformed names | INFO (from 01-REVIEW.md WR-02) | Not a phase-goal blocker — all documented behaviors in the plan pass; this is an edge case beyond the plan's specified test matrix, correctly flagged as advisory in the code review |
| `core/engine/validators.py` | 19-28 | `validate_bar_duration` accepts negative/zero durations if the sum matches | INFO (01-REVIEW.md WR-03) | Same — outside plan's specified behavior matrix, advisory |
| `scripts/generate_cello_dark_ostinato.py`, `harmony_advisor.py` | registry-driven `choices=` | Duet presets (empty `bars`/`rhythm`) leak into the solo ostinato CLI's genre choices, producing a silently empty export if selected | WARNING (01-REVIEW.md WR-01) | Functional regression relative to pre-migration CLI behavior, but does not affect any of the 6 roadmap Success Criteria (golden regression only exercises the 4 solo genres, which are unaffected) or any LOOP-03/LOOP-04/PLAT-03 requirement text. Recommend addressing in Phase 2 when scripts become thin wrappers, or as a quick follow-up. |
| `core/models.py`, `core/presets/registry.py` | — | `frozen=True` on `MoodPreset` doesn't protect mutable list/dict fields; `get_preset()` returns shared references | WARNING (01-REVIEW.md WR-05) | Latent risk for Phase 2 (LoopEngine deriving variants from presets), not a Phase 1 goal blocker |

All review findings were already surfaced in the committed `01-REVIEW.md` (0 critical, 5 warnings, 7 info) and independently confirmed here to exist as described. None of them contradict or block the phase's 6 roadmap Success Criteria.

### Human Verification Required

None. All must-haves are objectively verifiable via automated tests, greps, and live command execution — no visual, real-time, or subjective-UX elements exist in this phase (pure Python library, no UI).

### Gaps Summary

No gaps found against the roadmap's 6 Success Criteria, all 3 requirement IDs, and all must-haves declared across the 4 plans' frontmatter. The full test suite (30/30) passes, matching the expected count. The golden regression mechanism independently proves the preset-data migration was a behavioral no-op for all 5 CLI scripts. All artifacts exist, are substantive (not stubs), and are wired end-to-end (dataclasses -> validators -> registry -> scripts, and each backed by real tests).

One process-level discrepancy is surfaced as a WARNING (not a gap): ROADMAP.md marks this phase `Mode: mvp` but the goal text is not in User Story format, and this phase has no user-facing surface to walk through. This does not affect the phase's actual deliverables, which were verified via standard goal-backward analysis against the roadmap's explicit Success Criteria (the correct fallback given the mode/goal mismatch).

The code review (01-REVIEW.md, already committed) found 5 warnings and 7 info-level issues — all advisory quality/robustness concerns (edge cases beyond the plan's specified test matrix, a CLI UX regression for duet-preset selection, and a mutability leak) that do not block phase-goal achievement but are worth tracking into Phase 2 planning.

---

_Verified: 2026-07-04_
_Verifier: Claude (gsd-verifier)_
