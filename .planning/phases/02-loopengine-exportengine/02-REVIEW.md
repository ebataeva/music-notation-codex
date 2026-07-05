---
phase: 02-loopengine-exportengine
reviewed: 2026-07-05T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - core/engine/loop_engine.py
  - core/engine/validators.py
  - core/export/__init__.py
  - core/export/exporter.py
  - core/presets/registry.py
  - scripts/generate_cello_dark_ostinato.py
  - scripts/generate_dorian_sexy_duet_loop.py
  - scripts/generate_sexy_duet_loop.py
  - scripts/generate_simple_sexy_duet_loop.py
  - tests/test_exporter.py
  - tests/test_loop_engine.py
  - tests/test_presets_registry.py
  - tests/test_validators.py
findings:
  critical: 0
  warning: 7
  info: 5
  total: 12
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-05
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed the LoopEngine/ExportEngine extraction: `core/engine/loop_engine.py`, `core/engine/validators.py`, `core/export/exporter.py`, `core/presets/registry.py`, 4 CLI scripts, and 4 test files. All 65 tests pass. Every edge-case finding below was verified empirically by executing the code, not just by reading it.

No critical (data-loss/crash-in-happy-path/security-boundary) defects found. The solo path (`build_score` / `generate_variant`) is well-guarded. The main weakness is that **the duet path (`build_duet_score`) received none of the hardening applied to the solo path**: no SAFE-02 bar-count guard, no None-check on duet fields (raw `TypeError` leak), and no cello/violin bar-count alignment check. Additionally, `validate_bar_duration` leaks a raw `Music21Exception` with a wildly misleading message for invalid meter strings — inconsistent with the WR-02 wrapping policy this phase itself established for pitches. `ExportEngine` accepts unsanitized `output_name`, allowing path escape from `base_dir` (verified: `../../escape` writes outside).

## Warnings

### WR-01: `ExportEngine` output_name allows path escape from base_dir

**File:** `core/export/exporter.py:25,31`
**Issue:** `output_name` is interpolated directly into the path: `self.base_dir / "musicxml" / f"{output_name}.musicxml"`. A value like `../../escape` resolves outside `base_dir` (verified empirically: `/tmp/x/scores` + `../../escape` → `/private/tmp/x/escape.musicxml`). `output_name` is user-controlled today via `--output-name` in `scripts/generate_cello_dark_ostinato.py:22`. For a local CLI this is low-impact (the user already owns the filesystem), but ExportEngine is the component that will be wired into the Streamlit UI in later phases, where this becomes a real write-anywhere primitive. Fix it now while the surface is one class.
**Fix:**
```python
def _safe_path(self, subdir: str, output_name: str, ext: str) -> Path:
    if Path(output_name).name != output_name or output_name in ("", ".", ".."):
        raise ValueError(f"output_name {output_name!r} must be a bare file name.")
    return self.base_dir / subdir / f"{output_name}{ext}"
```

### WR-02: `validate_bar_duration` leaks raw Music21Exception with misleading message for invalid meter

**File:** `core/engine/validators.py:37`
**Issue:** `meter.TimeSignature(meter_signature)` on an invalid string raises a raw `Music21Exception` whose message is actively misleading (verified): *"Cannot parse this file -- this error often comes up if the musicxml pickled file is out of date... Time Signature: not_a_meter"*. This is exactly the exception-leak class this phase fixed for pitches (the module wraps `PitchException` into `ValueError` at lines 18-21, and `tests/test_validators.py:86` enforces that policy) — but the same policy was not applied to the meter parameter of the *same validator module*.
**Fix:**
```python
from music21.exceptions21 import Music21Exception
try:
    ts = meter.TimeSignature(meter_signature)
except Music21Exception as exc:
    raise ValueError(f"Meter {meter_signature!r} is not a valid time signature: {exc}") from exc
```

### WR-03: SAFE-02 bar-count guard missing from `build_duet_score`

**File:** `core/engine/loop_engine.py:154-219`
**Issue:** `MAX_BARS` is enforced twice on the solo path (`build_score:51`, `generate_variant:100`) with comments declaring it a DoS guard (SAFE-02), but `build_duet_score` — which also constructs unbounded numbers of `stream.Measure` objects from `preset.duet_bars` — has no guard at all. The stated invariant ("reject oversized requests before any Score object is constructed") does not hold for the duet code path. Today duet data comes only from static presets, but the guard's whole premise is defense against future untrusted input, and the duet path is the one that will grow a public API (DUET-01).
**Fix:** At the top of `build_duet_score`, after resolving `cello_bars`/`violin_bars`:
```python
for part_name, bars in (("cello", cello_bars), ("violin", violin_bars)):
    if len(bars) > MAX_BARS:
        raise ValueError(f"{part_name} part: {len(bars)} bars exceeds the maximum of {MAX_BARS}.")
```

### WR-04: `build_duet_score` crashes with raw TypeError on solo presets

**File:** `core/engine/loop_engine.py:177-180`
**Issue:** `preset.duet_rhythm["cello"]` subscripts a field typed `dict | None` (`core/models.py:65-66`) with no None-check. Passing any solo preset (e.g. `get_preset("dark_trip_hop")`) raises `TypeError: 'NoneType' object is not subscriptable` (verified empirically) instead of a diagnosable `ValueError`. The function is a public module-level API — nothing prevents a caller from handing it a solo preset, and the registry offers no `list_duet_presets()` to steer them away.
**Fix:**
```python
if preset.duet_rhythm is None or preset.duet_bars is None:
    raise ValueError(f"Preset {preset.name!r} has no duet data; use build_score() for solo presets.")
```

### WR-05: No cello/violin measure-count alignment check in `build_duet_score`

**File:** `core/engine/loop_engine.py:185-215`
**Issue:** The two per-part loops iterate `cello_bars` and `violin_bars` independently. If the counts diverge (e.g. cello 8 bars, violin 7), the function silently produces a score whose parts have different lengths — misaligned playback and structurally suspect MusicXML — with no error. Per-bar rhythm lengths *are* strictly validated (`zip(..., strict=True)` in `add_measure`), so intra-bar mismatch fails loudly while inter-part mismatch passes silently. Inconsistent rigor on the same data structure.
**Fix:**
```python
if len(cello_bars) != len(violin_bars):
    raise ValueError(
        f"Duet parts have mismatched bar counts: cello={len(cello_bars)}, violin={len(violin_bars)}."
    )
```

### WR-06: `generate_variant` on a duet preset fails with misleading "Rhythm is empty" error

**File:** `core/engine/loop_engine.py:92-105`
**Issue:** Duet presets are legitimate registry entries with `bars=[]` / `rhythm=[]` (`core/presets/mood_presets.py:168-169`). Calling the public `generate_variant(get_preset("sexy_duet"))` passes the MAX_BARS guard (0 ≤ 64), then dies inside `build_score` with `ValueError: Rhythm is empty for meter 4/4.` (verified empirically) — an error that describes the internal data representation, not the caller's mistake. A user who picked a valid preset name from `list_presets()` gets no hint that they need a solo preset.
**Fix:** Guard at the top of `generate_variant` (and/or `build_score`):
```python
if not preset.bars:
    raise ValueError(
        f"Preset {preset.name!r} has no solo bars (duet-only preset); "
        f"choose one of: {', '.join(list_solo_presets())}."
    )
```

### WR-07: File handle leak in `export_to_midi` when write fails

**File:** `core/export/exporter.py:34-36`
**Issue:** `midi_file.open(...)` / `write()` / `close()` with no `try/finally` — if `write()` raises (disk full, encoding error in the MidiFile), `close()` is never called and the handle leaks until GC. The manual open/write/close dance is also unnecessary: music21 exports MIDI natively via `score.write("midi", fp=...)`, exactly as `export_to_musicxml` already does for MusicXML — and the project stack guide explicitly says "music21 already exports MIDI natively."
**Fix:**
```python
def export_to_midi(self, score: stream.Score, output_name: str) -> Path:
    midi_path = self.base_dir / "midi" / f"{output_name}.mid"
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("midi", fp=str(midi_path))
    return midi_path
```

## Info

### IN-01: Dead constants `MUSICXML_PATH` / `MIDI_PATH` in all three duet scripts

**File:** `scripts/generate_sexy_duet_loop.py:18-19`, `scripts/generate_simple_sexy_duet_loop.py:18-19`, `scripts/generate_dorian_sexy_duet_loop.py:18-19`
**Issue:** Both module-level constants are computed but never used — the actual paths come from `ExportEngine().export(...)` at line 26. Leftovers from the pre-extraction scripts; if `ExportEngine` layout ever changes, these constants will silently lie.
**Fix:** Delete both constants from all three scripts (keep `OUTPUT_NAME`).

### IN-02: Duet scripts hardcode tempo values that duplicate `preset.duet_tempo_bpm`

**File:** `scripts/generate_sexy_duet_loop.py:25`, `scripts/generate_simple_sexy_duet_loop.py:25`, `scripts/generate_dorian_sexy_duet_loop.py:25`
**Issue:** Each script passes a literal `tempo_bpm=` (76/64/88) to `build_duet_score`, while the presets already carry the same values in `duet_tempo_bpm` (`mood_presets.py:200,244,285`). Two sources of truth; editing the preset won't change script output. The scripts' print statements also hardcode the bpm a third time.
**Fix:** `build_duet_score(preset, tempo_bpm=preset.duet_tempo_bpm, ...)` — or have `build_duet_score` default to `preset.duet_tempo_bpm` when `tempo_bpm` is None.

### IN-03: `_classify_register` misparses multi-digit octaves

**File:** `core/engine/loop_engine.py:226`
**Issue:** The comprehension collects every digit character independently, so a hypothetical "C10" yields octaves `[1, 0]` → min 0 → "low register". Unreachable with current cello/violin data (max octave 6), but the function will silently misclassify if range constants ever widen.
**Fix:** Extract the trailing digit run instead: `int(re.search(r"(\d+)$", pitch_name).group(1))` per pitch, guarded for no-match.

### IN-04: Legacy pitch exception is scoped per-preset, not per-part

**File:** `core/engine/loop_engine.py:200-205`
**Issue:** In `build_duet_score`, the violin loop consults the same `_LEGACY_PITCH_EXCEPTIONS` set as the cello loop. The documented exception (D-07) is the *cello* "A1" of `simple_sexy_duet`, but an "A1" appearing in that preset's *violin* bars would also silently bypass validation. Harmless with current static data; widens the exception beyond its documented scope.
**Fix:** Key the exception map on `(preset_name, part)` or skip the legacy check entirely in the violin loop.

### IN-05: Tautological default-base-dir test

**File:** `tests/test_exporter.py:61-65`
**Issue:** `assert engine.base_dir == PROJECT_ROOT / "scores"` imports `PROJECT_ROOT` from the module under test, so the assertion restates the implementation and can only fail if the default expression itself changes shape — it would not catch the very bug the source comment warns about (`parents[2]` vs `parents[1]` miscount). Gives false confidence in path correctness.
**Fix:** Assert against an independently computed root: `assert engine.base_dir == Path(__file__).resolve().parents[1] / "scores"`.

---

_Reviewed: 2026-07-05_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
