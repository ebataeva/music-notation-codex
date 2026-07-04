---
phase: 01-core-library-skeleton-validators
reviewed: 2026-07-04T08:02:38Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - core/__init__.py
  - core/engine/__init__.py
  - core/engine/validators.py
  - core/models.py
  - core/presets/__init__.py
  - core/presets/mood_presets.py
  - core/presets/registry.py
  - scripts/generate_cello_dark_ostinato.py
  - scripts/generate_dorian_sexy_duet_loop.py
  - scripts/generate_sexy_duet_loop.py
  - scripts/generate_simple_sexy_duet_loop.py
  - scripts/harmony_advisor.py
  - tests/__init__.py
  - tests/conftest.py
  - tests/golden/baseline_hashes.json
  - tests/test_golden_regression.py
  - tests/test_import_boundary.py
  - tests/test_models.py
  - tests/test_presets_registry.py
  - tests/test_validators.py
findings:
  critical: 0
  warning: 5
  info: 7
  total: 12
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-07-04T08:02:38Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Reviewed the Phase 1 core-library skeleton: dataclass models, cello validators, the merged `MOOD_PRESETS` registry (4 solo + 3 duet presets), the 5 migrated CLI scripts, and the test suite (golden regression, import boundary, models, registry, validators).

Data integrity of the preset migration checks out: every preset's per-bar note counts match its rhythm length (verified against `zip(strict=True)` in the scripts), all rhythm rows sum to 4.0 quarter lengths, and the documented out-of-range `A1` is preserved verbatim with an explanatory comment. No secrets, no injection vectors, no unsafe subprocess usage (`subprocess.run` with static list args, no `shell=True`).

Five warnings were found, all empirically verified where possible:
1. The preset merge introduced a behavioral regression — the solo ostinato CLI now accepts duet preset names and silently exports empty score files (confirmed: 0 measures, no exception).
2. `validate_pitch` silently accepts octave-less pitch names (music21 defaults them to MIDI 60, always "in range") and leaks `PitchException` instead of the documented `ValueError` contract for malformed input.
3. `validate_bar_duration` accepts negative/zero durations as long as the sum matches.
4. All 4 generator scripts persistently rewrite the user's global music21 preferences file on every run (confirmed in music21 source: `UserSettings.__setitem__` calls `self._environment.write()`), and the golden tests trigger this 14 times per test session.
5. `frozen=True` on `MoodPreset` is an illusion of immutability — the registry hands out aliases to module-global mutable lists/dicts.

No critical (security/data-loss/crash) issues found.

## Warnings

### WR-01: Duet presets leak into solo CLI genre choices, producing silently empty exports

**File:** `scripts/generate_cello_dark_ostinato.py:65`, `scripts/harmony_advisor.py:26` (root cause: `core/presets/registry.py:17-18` exposes all 7 presets)
**Issue:** Before the merge, the ostinato script's `GENRE_PRESETS` had only the 4 solo moods. Now `parse_args()` builds `choices` from `list_presets()`, which includes `sexy_duet`, `simple_sexy_duet`, and `dorian_sexy_duet` — presets whose `rhythm=[]` and `bars=[]`. Running `--genre sexy_duet` builds a score with **0 measures and no error** (verified empirically) and exports empty `cello_sexy_duet_ostinato.musicxml`/`.mid` files. Similarly, `harmony_advisor.py --genre sexy_duet` prints three section headers with no content (`progressions`/`modulations`/`mood_tips` are all empty). `--list-genres` also prints duets with a blank `feel` ("sexy_duet: "). This is a functional regression introduced by the data move that the golden tests cannot catch (they only exercise the 4 solo genres).
**Fix:** Filter the CLI choices to presets that actually have solo data, e.g. in `generate_cello_dark_ostinato.py`:
```python
def solo_genres() -> list[str]:
    return sorted(n for n in list_presets() if get_preset(n).bars)

parser.add_argument("--genre", choices=solo_genres(), default="dark_trip_hop")
```
and the mirror filter (`preset.progressions`) in `harmony_advisor.py`. Alternatively add a guard in `build_cello_ostinato` that raises `ValueError` when `preset.bars` is empty.

### WR-02: `validate_pitch` silently accepts octave-less names and leaks music21 exceptions for malformed input

**File:** `core/engine/validators.py:9-16`
**Issue:** Two input-validation gaps:
1. `pitch.Pitch("C").midi == 60` with `octave=None` (verified). An octave-less pitch name (a likely data-entry mistake in preset bars, e.g. `"Eb"` instead of `"Eb3"`) is silently treated as octave 4 and passes validation — masking exactly the class of data bug this validator exists to catch.
2. Malformed names raise `music21.pitch.PitchException` (`Pitch("H2")` → "Cannot make a step out of 'H'", verified), not the `ValueError` contract that in-range violations use. Callers writing `except ValueError` will miss malformed-input failures.
**Fix:**
```python
def validate_pitch(pitch_name: str, extended: bool = False) -> None:
    try:
        p = pitch.Pitch(pitch_name)
    except Exception as exc:
        raise ValueError(f"Invalid pitch name {pitch_name!r}: {exc}") from exc
    if p.octave is None:
        raise ValueError(f"Pitch {pitch_name!r} has no octave; use explicit octave (e.g. 'C3').")
    max_midi = CELLO_MAX_MIDI_EXTENDED if extended else CELLO_MAX_MIDI_DEFAULT
    ...
```

### WR-03: `validate_bar_duration` accepts negative and zero durations

**File:** `core/engine/validators.py:19-28`
**Issue:** Only the sum is checked. `validate_bar_duration([5.0, -1.0], "4/4")` and `validate_bar_duration([4.0, 0.0, 0.0], "4/4")` both pass, though negative/zero quarter lengths are nonsense that will corrupt downstream `duration.Duration` construction in Phase 2's generation path. An empty rhythm list also produces the confusing message "Bar duration 0 != 4.0" rather than naming the real problem.
**Fix:**
```python
if not rhythm:
    raise ValueError(f"Rhythm is empty for meter {meter_signature}.")
if any(ql <= 0 for ql in rhythm):
    raise ValueError(f"Rhythm contains non-positive duration(s): {rhythm}")
```

### WR-04: Every generator script persistently rewrites the user's global music21 preferences file

**File:** `scripts/generate_cello_dark_ostinato.py:72`, `scripts/generate_sexy_duet_loop.py:84`, `scripts/generate_simple_sexy_duet_loop.py:81`, `scripts/generate_dorian_sexy_duet_loop.py:80`
**Issue:** `environment.UserSettings()["warnings"] = 0` is not an in-memory session setting. Verified in music21 source: `UserSettings.__setitem__` ends with `self._environment.write()` — it **writes the user's global preferences file (`~/.music21rc`) to disk on every script run**, permanently disabling music21 warnings for all projects on the machine. The golden regression tests amplify this: `run_all_scripts()` executes 7 subprocess invocations and is called by both tests, so a single `pytest` session rewrites the user's global config 14 times as a hidden side effect.
**Fix:** Use the in-memory session environment instead:
```python
environment.Environment()["warnings"] = 0
```
(`Environment.__setitem__` does not call `write()`; the change lives only for the process.)

### WR-05: `frozen=True` on `MoodPreset` gives false immutability; registry hands out aliases to shared global data

**File:** `core/models.py:51-67`, `core/presets/registry.py:13-14`
**Issue:** `MoodPreset` is frozen, but all its collection fields (`rhythm`, `bars`, `progressions`, `duet_rhythm`, `duet_bars`, ...) are mutable `list`/`dict` objects. `get_preset()` returns the shared instance, so any caller doing `preset.bars[0][0] = "X9"` or `preset.rhythm.append(0.5)` silently corrupts the module-global `MOOD_PRESETS` registry for the rest of the process — exactly the failure mode Phase 2's LoopEngine (which will derive variants from presets) is likely to hit. As a secondary effect, `frozen=True` + default `eq=True` makes the class nominally hashable, but hashing any instance raises `TypeError: unhashable type: 'list'` at runtime.
**Fix:** Either switch collection fields to immutable types (`tuple[float, ...]`, `tuple[tuple[str, ...], ...]`) or make the registry return defensive copies:
```python
import copy

def get_preset(name: str) -> MoodPreset:
    return copy.deepcopy(MOOD_PRESETS[name])
```
The tuple approach is stronger and keeps `frozen=True` honest.

## Info

### IN-01: Misleading comment about duet preset `rhythm`/`bars`

**File:** `core/presets/mood_presets.py:159-160`
**Issue:** The comment says "rhythm/bars/tempo_bpm mirror the duet_* fields for schema consistency", but `rhythm=[]` and `bars=[]` for all three duet presets — they do not mirror `duet_rhythm`/`duet_bars`; only `tempo_bpm` mirrors `duet_tempo_bpm`. Also inconsistent: `dorian_sexy_duet` has a non-empty `feel` while the other two duets have `feel=""`.
**Fix:** Correct the comment to say rhythm/bars are intentionally empty for duet presets (only tempo mirrors), and either fill or empty `feel` consistently across the three duets.

### IN-02: Unused `tolerance` fixture

**File:** `tests/conftest.py:4-7`
**Issue:** The fixture is not consumed by any test in the suite (the validator tests rely on the function's own default tolerance). Dead code shipped "for later plans".
**Fix:** Remove it until a test actually needs it, or wire it into `test_validators.py`.

### IN-03: `make_note`/`add_measure`/`export_score` triplicated verbatim across duet scripts

**File:** `scripts/generate_sexy_duet_loop.py:20-31,71-80`, `scripts/generate_simple_sexy_duet_loop.py:20-31,69-77`, `scripts/generate_dorian_sexy_duet_loop.py:20-31,68-76`
**Issue:** Three identical copies of the same helpers. A bug fix in one (e.g. the MIDI export sequence) must be repeated in all three. Phase 2's LoopEngine is the planned home for this logic, but until then the duplication is a maintenance hazard.
**Fix:** Extract a shared `scripts/_duet_common.py` (or fold into `core/engine` in Phase 2) and import the helpers.

### IN-04: Golden tests run all 7 script invocations twice per session and write into the repo tree

**File:** `tests/test_golden_regression.py:118-139`
**Issue:** Both tests call `run_all_scripts()` independently → 14 subprocess runs per `pytest` session for identical output. The scripts also write directly into `scores/midi/` and `scores/musicxml/` in the working tree; the MusicXML bytes differ on every run (memory-address ids, encoding-date), so if these artifacts ever get tracked, every test run dirties git status.
**Fix:** Regenerate once via a module-scoped fixture:
```python
@pytest.fixture(scope="module")
def regenerated_scores():
    run_all_scripts()
```
and consider redirecting script output to a temp dir (env var override) in tests.

### IN-05: `validate_bar_duration` tolerance of 1e-9 will falsely reject triplet rhythms written as rounded floats

**File:** `core/engine/validators.py:20`
**Issue:** A triplet quarter-length is 1/3, unrepresentable in decimal floats; `[0.3333, 0.3333, 0.3333, ...]` accumulates ~1e-4 error, far above the 1e-9 tolerance, and even exact binary floats `1/3` behave subtly. music21 itself uses `Fraction` for these durations. Not a live bug (no triplet presets exist yet), but a known trap for Phase 2 rhythm strategies.
**Fix:** Document that rhythm values must be exact quarter lengths (accept `Fraction`), or loosen tolerance to something like 1e-6 with a comment explaining why.

### IN-06: `dorian_sexy_duet` labeled `key_mode="minor"` though the material is D Dorian

**File:** `core/presets/mood_presets.py:250`, mirrored in `scripts/generate_dorian_sexy_duet_loop.py:47`
**Issue:** Migrated verbatim from the source script (which also uses `key.Key("D", "minor")`), so consistent with the golden baseline — but semantically wrong: the `feel` text and the B-naturals in the bars are Dorian. When Phase 2/3 starts driving theory explanations from `key_mode`, this metadata will produce wrong analysis. music21 supports `key.Key("D", "dorian")`.
**Fix:** Leave verbatim for now (golden guard), but record it as a deliberate correction for the Phase 2 recapture: change `key_mode` to `"dorian"` and re-baseline.

### IN-07: `--output-name` is used unsanitized in output paths

**File:** `scripts/generate_cello_dark_ostinato.py:48-49,66`
**Issue:** `--output-name ../../whatever` writes `.musicxml`/`.mid` files outside `scores/`. Low risk for a single-user local CLI, but trivially cheap to close.
**Fix:** Reject names containing path separators: `if Path(output_name).name != output_name: parser.error(...)`.

---

_Reviewed: 2026-07-04T08:02:38Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
