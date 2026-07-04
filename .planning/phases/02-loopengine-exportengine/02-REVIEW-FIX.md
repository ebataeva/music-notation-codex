---
phase: 02-loopengine-exportengine
fixed_at: 2026-07-05T00:00:00Z
review_path: .planning/phases/02-loopengine-exportengine/02-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-07-05
**Source review:** .planning/phases/02-loopengine-exportengine/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (all Warnings; fix_scope=critical_warning excludes the 5 Info findings)
- Fixed: 7
- Skipped: 0

The full test suite (65 tests) was run after every individual fix and stayed green throughout. The golden regression remained byte-identical: after WR-07 the tracked `scores/midi/*.mid` files were confirmed unmodified by the regenerated output (native `score.write("midi")` produces identical bytes). Known IN-04 musicxml churn was discarded via `git checkout -- scores/` before every commit; no scores/ changes were committed.

## Fixed Issues

### WR-01: `ExportEngine` output_name allows path escape from base_dir

**Files modified:** `core/export/exporter.py`
**Commit:** 5060fb1
**Applied fix:** Added `_safe_path(subdir, output_name, ext)` helper that rejects any `output_name` containing path separators or traversal components (`Path(output_name).name != output_name` or `"" | "." | ".."`) with a ValueError; both `export_to_musicxml` and `export_to_midi` now build their paths through it.

### WR-02: `validate_bar_duration` leaks raw Music21Exception for invalid meter

**Files modified:** `core/engine/validators.py`
**Commit:** 2861c28
**Applied fix:** Wrapped `meter.TimeSignature(meter_signature)` in try/except `Music21Exception`, re-raising as `ValueError(f"Meter {meter_signature!r} is not a valid time signature: ...")` with exception chaining — matching the module's existing PitchException-wrapping policy. Verified empirically: `validate_bar_duration([4.0], "not_a_meter")` now raises ValueError.

### WR-03: SAFE-02 bar-count guard missing from `build_duet_score`

**Files modified:** `core/engine/loop_engine.py`
**Commit:** 01c45d8
**Applied fix:** Moved duet field resolution and `validate_bar_duration` calls above Score construction (honoring the SAFE-02 invariant "reject before any Score object is constructed") and added a per-part `MAX_BARS` guard for cello and violin bars. Verified empirically: a 320-bar duet raises `ValueError: cello part: 320 bars exceeds the maximum of 64.`

### WR-04: `build_duet_score` crashes with raw TypeError on solo presets

**Files modified:** `core/engine/loop_engine.py`
**Commit:** eaaa05d
**Applied fix:** Added a None-check on `preset.duet_rhythm` / `preset.duet_bars` before subscripting, raising `ValueError: Preset {name!r} has no duet data; use build_score() for solo presets.` Verified empirically with `get_preset("dark_trip_hop")`.

### WR-05: No cello/violin measure-count alignment check in `build_duet_score`

**Files modified:** `core/engine/loop_engine.py`
**Commit:** 931d05a
**Applied fix:** Added an inter-part bar-count check before Score construction, raising `ValueError: Duet parts have mismatched bar counts: cello={n}, violin={m}.` Verified empirically with an 8-vs-7-bar mutated preset.

### WR-06: `generate_variant` on a duet preset fails with misleading "Rhythm is empty" error

**Files modified:** `core/engine/loop_engine.py`
**Commit:** b805478
**Applied fix:** Added a guard at the top of `generate_variant` for empty `preset.bars`, raising an actionable ValueError that lists `list_solo_presets()` (imported from `core.presets.registry` — no circular import; verified). Empirical output: `Preset 'sexy_duet' has no solo bars (duet-only preset); choose one of: dark_trip_hop, driving_cinematic, noir_slow_burn, ritual_tribal.`

### WR-07: File handle leak in `export_to_midi` when write fails

**Files modified:** `core/export/exporter.py`
**Commit:** f1c4392
**Applied fix:** Replaced the manual `streamToMidiFile` + `open`/`write`/`close` dance with native `score.write("midi", fp=str(midi_path))`, mirroring `export_to_musicxml`; removed the now-unused `from music21 import midi` import. Byte-identity confirmed: regenerated `scores/midi/*.mid` files showed no diff against tracked versions.

## Skipped Issues

None — all in-scope findings were fixed. Info findings IN-01 through IN-05 were out of scope (fix_scope=critical_warning).

---

_Fixed: 2026-07-05_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
