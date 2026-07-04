# Phase 2: LoopEngine + ExportEngine - Pattern Map

**Mapped:** 2026-07-04
**Files analyzed:** 11 (4 CLI scripts as extraction source; 1 modified validator; 2 new core modules; 4+ new/extended test files)
**Analogs found:** 11 / 11 (extraction phase — every new file has a brownfield analog in `scripts/`; the two genuinely new pieces, the legacy-exception mechanism and the seed field, extend an existing shape rather than copy one)

**Note on analog source:** Same situation as Phase 1 — `core/engine/` and `core/export/` are new subtrees, so the analogs are the 4 CLI scripts being gutted, plus Phase 1's own `core/presets/registry.py` and `core/engine/validators.py` for "simple function, no custom exception" style, plus `01-PATTERNS.md` for dataclass/import conventions already locked in.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `core/engine/loop_engine.py` | service (engine) | transform (preset -> music21 Score) | `scripts/generate_cello_dark_ostinato.py` `build_cello_ostinato()` (lines 18-44) + 3 duet scripts' `build_score()` (two-part path) | exact — direct extraction |
| `core/export/exporter.py` | service (file I/O) | file-I/O | `scripts/generate_cello_dark_ostinato.py` `export_score()` (lines 47-60) | exact — direct extraction |
| `core/engine/validators.py` (modified) | utility | request-response (validate-or-raise) | itself (Phase 1 version) + `.planning/research/PITFALLS.md` reference fix recipes for WR-02/WR-03 | exact — hardening in place |
| `scripts/generate_cello_dark_ostinato.py` (thin wrapper) | controller (CLI) | request-response (argparse -> core call -> print) | itself pre-refactor (keep `parse_args`/`main` shape, strip `build_cello_ostinato`/`export_score` bodies) | exact — modify in place |
| `scripts/generate_sexy_duet_loop.py` (thin wrapper) | controller (CLI) | request-response | itself pre-refactor + the ostinato script's post-refactor wrapper shape (no argparse today — WR-01 discretion: leave args-free per D-11 scope, just delegate) | exact — modify in place |
| `scripts/generate_simple_sexy_duet_loop.py` (thin wrapper) | controller (CLI) | request-response | same as `generate_sexy_duet_loop.py` | exact — modify in place |
| `scripts/generate_dorian_sexy_duet_loop.py` (thin wrapper) | controller (CLI) | request-response | same as `generate_sexy_duet_loop.py` | exact — modify in place |
| `tests/test_loop_engine.py` (new) | test | transform (assert Score shape + trace) | `tests/test_validators.py` (assert-raises / assert-no-raise style) + `tests/test_presets_registry.py` (assert-equality-on-dataclass-field style) | role-match |
| `tests/test_exporter.py` (new) | test | file-I/O | `tests/test_golden_regression.py` (path construction + `mkdir(parents=True, exist_ok=True)` conventions) | role-match |
| `tests/test_validators.py` (extended) | test | request-response | itself (Phase 1 version) — add cases for WR-02 (octave-less names, `PitchException` wrap) and WR-03 (non-positive rhythm sum) | exact — extend in place |
| `tests/test_golden_regression.py` | test | file-I/O (unchanged contract) | itself — no structural change expected, but MUST stay green after refactor; verifies WR-04 side effect (no `~/.music21rc` rewrite) doesn't break the harness | exact — regression guard only |

## Pattern Assignments

### `core/engine/loop_engine.py` (service, transform)

**Analog:** `scripts/generate_cello_dark_ostinato.py` lines 1-44 (solo path) + `scripts/generate_sexy_duet_loop.py` lines 20-68 (two-part path, internal only per D-13)

**Imports pattern** (`scripts/generate_cello_dark_ostinato.py` lines 1-15, minus the argparse/CLI-only pieces which stay in `scripts/`):
```python
from __future__ import annotations

from music21 import clef, duration, instrument, key, meter, note, stream, tempo

from core.models import MoodPreset
from core.engine.validators import validate_bar_duration, validate_pitch
```
Note: `argparse`, `sys`, `PROJECT_ROOT`/`sys.path.insert` bootstrap, and `environment` all stay OUT of `core/` — those are CLI/script concerns (import-boundary rule, `.planning/research/ARCHITECTURE.md` line 122: "No music21 import may appear in `app/`... core/ is a pure Python library"). `core/` needs no `sys.path` bootstrap since it is imported as a real package, not run as `__main__`.

**Core solo-build pattern to extract** (`scripts/generate_cello_dark_ostinato.py` lines 18-44, `build_cello_ostinato`):
```python
def build_cello_ostinato(preset: MoodPreset) -> stream.Score:
    score = stream.Score(id=f"cello_{preset.name}")
    cello_part = stream.Part(id="cello")

    cello_part.append(instrument.Violoncello())
    cello_part.append(clef.BassClef())

    cello_part.append(tempo.MetronomeMark(number=preset.tempo_bpm))
    cello_part.append(key.Key(preset.key_tonic, preset.key_mode))
    cello_part.append(meter.TimeSignature(preset.meter_signature))

    for measure_number, pitches in enumerate(preset.bars, start=1):
        measure = stream.Measure(number=measure_number)
        for pitch_name, quarter_length in zip(pitches, preset.rhythm, strict=True):
            cello_note = note.Note(pitch_name)
            cello_note.duration = duration.Duration(quarterLength=quarter_length)
            cello_note.volume.velocity = preset.velocity
            measure.append(cello_note)
        cello_part.append(measure)

    score.insert(0, cello_part)
    return score
```
**Rename per D-05/ARCHITECTURE.md:** becomes `build_score(preset: MoodPreset, ...) -> stream.Score` (low-level API). `zip(strict=True)` for bars/rhythm pairing is a locked convention (01-CONTEXT.md / 01-PATTERNS.md) — preserve verbatim.

**D-06 validator wiring — insert BEFORE building each note/measure** (this is new logic, not present in the source script, since Phase 1 validators were never called from generation code):
```python
# Inside the per-bar loop, before constructing note.Note(pitch_name):
if not preset.is_legacy_exception(pitch_name):   # name illustrative — see D-07 below
    validate_pitch(pitch_name)
validate_bar_duration(preset.rhythm, preset.meter_signature)
```
Call `validate_bar_duration` once per preset (rhythm/meter don't vary per-bar in current presets) or once per bar if the per-preset exception mechanism needs bar-level granularity — planner's call per D-07 naming discretion.

**D-07 legacy exception handling — no existing analog; new mechanism.** The only concrete data point is `simple_sexy_duet.duet_bars["cello"][1] == ["A1", "E2", "G2", "C#3"]` (confirmed in `tests/test_presets_registry.py` line 40, and flagged verbatim in 01-PATTERNS.md line 193 with the comment: `# NOTE: "A1" (MIDI 33) is below the C2 validator floor — pre-existing in source script, migrated verbatim, not yet validated at generation time (Phase 2 concern).`). Phase 2 is exactly that concern landing. Recommended shape (Claude's discretion per CONTEXT.md D-07, naming not locked):
```python
# Per-preset set/list of (pitch_name) or (bar_index, pitch_name) tuples known to
# violate validate_pitch's range but which must survive byte-identically.
# Example candidate field on MoodPreset (if planner chooses to extend the dataclass)
# or a small module-level dict keyed by preset.name in loop_engine.py itself
# (avoids touching the frozen MoodPreset shape locked in Phase 1).
_LEGACY_PITCH_EXCEPTIONS: dict[str, set[str]] = {
    "simple_sexy_duet": {"A1"},
}
```
Emit a warning (not raise) when skipping — e.g. `warnings.warn(...)` or append to a trace field — and record it so it's visible, per D-07 "warning recorded in the trace."

**Two-part duet build pattern (internal-only path, D-13)** — extracted from `scripts/generate_sexy_duet_loop.py` lines 20-68 (identical shape repeated in `generate_simple_sexy_duet_loop.py` and `generate_dorian_sexy_duet_loop.py`, differing only in tempo/velocity/preset name):
```python
def make_note(pitch_name: str, quarter_length: float, velocity: int) -> note.Note:
    n = note.Note(pitch_name)
    n.duration = duration.Duration(quarterLength=quarter_length)
    n.volume.velocity = velocity
    return n


def add_measure(part: stream.Part, number: int, pitches: list[str], rhythm: list[float], velocity: int) -> None:
    measure = stream.Measure(number=number)
    for pitch_name, quarter_length in zip(pitches, rhythm, strict=True):
        measure.append(make_note(pitch_name, quarter_length, velocity))
    part.append(measure)


def build_duet_score(preset: MoodPreset, tempo_bpm: int, cello_velocity: int, violin_velocity: int) -> stream.Score:
    score = stream.Score(id=f"duet_{preset.name}")

    violin = stream.Part(id="violin")
    violin.append(instrument.Violin())
    violin.append(clef.TrebleClef())

    cello = stream.Part(id="cello")
    cello.append(instrument.Violoncello())
    cello.append(clef.BassClef())

    for part in (violin, cello):
        part.append(tempo.MetronomeMark(number=tempo_bpm))
        part.append(key.Key(preset.key_tonic, preset.key_mode))
        part.append(meter.TimeSignature(preset.meter_signature))

    cello_rhythm = preset.duet_rhythm["cello"]
    violin_rhythm = preset.duet_rhythm["violin"]
    cello_bars = preset.duet_bars["cello"]
    violin_bars = preset.duet_bars["violin"]

    for measure_number, pitches in enumerate(cello_bars, start=1):
        add_measure(cello, measure_number, pitches, cello_rhythm, velocity=cello_velocity)
    for measure_number, pitches in enumerate(violin_bars, start=1):
        add_measure(violin, measure_number, pitches, violin_rhythm, velocity=violin_velocity)

    score.insert(0, violin)
    score.insert(0, cello)
    return score
```
**Byte-identity note:** each duet script currently hardcodes its own `tempo`/`key`/`velocity` values inline (`76`/`"D"`,`"minor"`/`82`,`70` for sexy_duet; `64`/`68`,`58` for simple_sexy_duet; `88`/`74`,`62` for dorian_sexy_duet — key/mode identical `"D","minor"` in all three source scripts, `preset.duet_tempo_bpm` already exists on `MoodPreset` per Phase 1's dataclass, per `tests/test_presets_registry.py` line 61 asserting `duet_tempo_bpm is not None`). Read tempo from `preset.duet_tempo_bpm` and velocities from the wrapper call site (or store on preset if planner prefers) — must reproduce the exact existing numbers or the golden hash breaks.

**D-01/D-02/D-03 seed plumbing (new, no analog)** — engine should accept a seed parameter and construct a `random.Random(seed)` instance, generating one via a fresh `random.Random()`/`os.urandom`-seeded call if none given, and always writing the resolved value into `trace.seed`. No existing code in the repo uses `random` anywhere — this is genuinely new plumbing, not an extraction. Suggested shape:
```python
import random

def _resolve_seed(seed: int | None) -> tuple[int, random.Random]:
    if seed is None:
        seed = random.Random().getrandbits(32)
    return seed, random.Random(seed)
```

**D-04 trace population (new, no analog)** — `GenerationTrace` fields must be computed from the actual preset notes per-bar as the score is built, not left as placeholders:
```python
# Inside the per-bar build loop, accumulate real data instead of nulls:
register_choices: list[str] = []   # e.g. one label per bar: "low register" / "mid register"
chord_tones_used: list[list[str]] = []  # e.g. append(list(pitches)) per bar
# pattern_strategy = "preset_verbatim" (or planner's chosen literal, per D-04/discretion)
```

---

### `core/export/exporter.py` (service, file-I/O)

**Analog:** `scripts/generate_cello_dark_ostinato.py` lines 47-60 (`export_score`), identical logic repeated in all 3 duet scripts' `export_score()` (lines 71-80 / 69-77 / 68-76 respectively — only path variable names differ, body is byte-for-byte the same pattern).

**Core file-I/O pattern to extract:**
```python
def export_score(score: stream.Score, output_name: str) -> tuple[Path, Path]:
    musicxml_path = PROJECT_ROOT / "scores" / "musicxml" / f"{output_name}.musicxml"
    midi_path = PROJECT_ROOT / "scores" / "midi" / f"{output_name}.mid"
    musicxml_path.parent.mkdir(parents=True, exist_ok=True)
    midi_path.parent.mkdir(parents=True, exist_ok=True)

    score.write("musicxml", fp=str(musicxml_path))

    midi_file = midi.translate.streamToMidiFile(score)
    midi_file.open(str(midi_path), "wb")
    midi_file.write()
    midi_file.close()
    return musicxml_path, midi_path
```
**D-08 base-directory parameterization (new twist on old pattern):** `PROJECT_ROOT / "scores"` was a hardcoded module constant in every script (`scripts/generate_sexy_duet_loop.py` line 9: `PROJECT_ROOT = Path(__file__).resolve().parents[1]`). ExportEngine must accept a configurable base directory, defaulting to the same `scores/` at project root so wrapper output is unchanged:
```python
class ExportEngine:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (PROJECT_ROOT / "scores")
        # PROJECT_ROOT here must be core/export/exporter.py's own parents[2]
        # (core/export/exporter.py -> core/export -> core -> project root),
        # NOT parents[1] as in scripts/ (different file depth).

    def export(self, score: stream.Score, output_name: str) -> tuple[Path, Path]:
        musicxml_path = self.base_dir / "musicxml" / f"{output_name}.musicxml"
        midi_path = self.base_dir / "midi" / f"{output_name}.mid"
        ...
```
**ARCHITECTURE.md naming guidance** (`.planning/research/ARCHITECTURE.md` line 469): `export_score()` → `ExportEngine.export_to_musicxml()` + `ExportEngine.export_to_midi()` as two separate methods is the suggested granularity; alternatively keep a single combined `export()` returning both paths (matches D-09's "Export returns paths of written files" — either shape satisfies it). Since D-05/discretion leaves class-vs-function open, and ROADMAP wording uses class style, prefer a class here too for consistency with LoopEngine.

**D-09 note:** `LoopVariant.svg_bytes`/`.midi_bytes` stay `None` this phase — ExportEngine only writes to disk and returns `Path` objects, it does not read bytes back into memory yet (`core/models.py` lines 43-44 already have these fields present and nullable from Phase 1, no dataclass change needed).

**D-10:** no overwrite-guard logic needed — `mkdir(parents=True, exist_ok=True)` + unconditional `.write()` is the existing behavior and stays as-is.

---

### `core/engine/validators.py` (modified, WR-02/WR-03 hardening)

**Analog:** itself, current Phase 1 state (already read in full above) — this is in-place hardening, not extraction from `scripts/`.

**Current state** (`core/engine/validators.py` lines 1-29, unchanged signature surface, only internal robustness added):
```python
from music21 import meter, pitch

CELLO_MIN_MIDI = 36
CELLO_MAX_MIDI_DEFAULT = 74
CELLO_MAX_MIDI_EXTENDED = 84


def validate_pitch(pitch_name: str, extended: bool = False) -> None:
    p = pitch.Pitch(pitch_name)
    max_midi = CELLO_MAX_MIDI_EXTENDED if extended else CELLO_MAX_MIDI_DEFAULT
    if not (CELLO_MIN_MIDI <= p.midi <= max_midi):
        raise ValueError(
            f"Pitch {pitch_name} (MIDI {p.midi}) is outside playable cello range "
            f"({CELLO_MIN_MIDI}-{max_midi})."
        )


def validate_bar_duration(
    rhythm: list[float], meter_signature: str, tolerance: float = 1e-9
) -> None:
    ts = meter.TimeSignature(meter_signature)
    expected_ql = ts.barDuration.quarterLength
    actual_ql = sum(rhythm)
    if abs(actual_ql - expected_ql) > tolerance:
        raise ValueError(
            f"Bar duration {actual_ql} != {expected_ql} for meter {meter_signature}."
        )
```

**WR-02 fix (octave-less pitch names + `PitchException` wrap):** `pitch.Pitch("C")` (no octave) does not raise in music21 by default — it silently defaults to octave 4 (or `None`) rather than failing, and malformed strings raise music21's own `PitchException`, not `ValueError`, breaking the documented "validators raise `ValueError`" contract established in 01-PATTERNS.md line 261 ("all raised errors are `ValueError`... no custom exception classes exist anywhere in the codebase"). Reference fix shape (per D-14/`.planning/research/PITFALLS.md`, and matching the existing bare `raise ValueError(...)` style — no new exception classes):
```python
from music21.pitch import PitchException

def validate_pitch(pitch_name: str, extended: bool = False) -> None:
    if pitch_name[-1].isalpha() or not any(ch.isdigit() for ch in pitch_name):
        # no octave digit present at all -> reject before construction
        raise ValueError(f"Pitch {pitch_name!r} must include an octave (e.g. 'C3'), not just a pitch class.")
    try:
        p = pitch.Pitch(pitch_name)
    except PitchException as exc:
        raise ValueError(f"Pitch {pitch_name!r} is not a valid pitch name: {exc}") from exc
    max_midi = CELLO_MAX_MIDI_EXTENDED if extended else CELLO_MAX_MIDI_DEFAULT
    if not (CELLO_MIN_MIDI <= p.midi <= max_midi):
        raise ValueError(
            f"Pitch {pitch_name} (MIDI {p.midi}) is outside playable cello range "
            f"({CELLO_MIN_MIDI}-{max_midi})."
        )
```
(Exact octave-detection check is planner/implementer's call — the important contract is: no bare `PitchException` escapes, and octave-less names like `"C"` or `"Bb"` are rejected with `ValueError` rather than silently accepted at a default octave.)

**WR-03 fix (non-positive rhythm durations):** current `validate_bar_duration` only checks the *sum* of the rhythm list against the meter's expected quarterLength — it never checks that individual entries are positive, so `[5.0, -1.0]` in `4/4` passes (`sum == 4.0`) despite containing a nonsensical negative duration. Add a per-element guard before the sum check:
```python
def validate_bar_duration(
    rhythm: list[float], meter_signature: str, tolerance: float = 1e-9
) -> None:
    for quarter_length in rhythm:
        if quarter_length <= 0:
            raise ValueError(f"Rhythm value {quarter_length} must be positive.")
    ts = meter.TimeSignature(meter_signature)
    expected_ql = ts.barDuration.quarterLength
    actual_ql = sum(rhythm)
    if abs(actual_ql - expected_ql) > tolerance:
        raise ValueError(
            f"Bar duration {actual_ql} != {expected_ql} for meter {meter_signature}."
        )
```

**Verification obligation (D-14):** both fixes are stated in CONTEXT.md as "verified not to affect golden output files" — i.e. no existing preset data in `core/presets/mood_presets.py` trips either new check (the one known exception, `simple_sexy_duet`'s `"A1"`, is a *pitch-range* violation handled by D-07's engine-level skip mechanism, not a validator change — WR-02/03 are about malformed input shapes, not legitimate low notes). Confirm `tests/test_golden_regression.py` still passes after the validator edit as the acceptance gate.

---

### `scripts/generate_cello_dark_ostinato.py` (thin wrapper)

**Analog:** itself, pre-refactor (already read above, lines 1-91).

**Target shape** (imports/build/export bodies removed, delegate to core; argparse/`main()` shape preserved per D-12 "thin wrapper = parse_args() + core calls + printing results"):
```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from music21 import environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_score  # noqa: E402
from core.export.exporter import ExportEngine  # noqa: E402
from core.presets.registry import get_preset, list_presets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cello ostinato MusicXML and MIDI files.")
    parser.add_argument("--genre", choices=sorted(list_presets()), default="dark_trip_hop")
    parser.add_argument("--output-name", default=None, help="File name without extension.")
    parser.add_argument("--list-genres", action="store_true")
    parser.add_argument("--seed", type=int, default=None)  # D-03
    return parser.parse_args()


def main() -> None:
    environment.Environment()["warnings"] = 0  # WR-04 fix — see Shared Patterns below
    args = parse_args()

    if args.list_genres:
        for preset in [get_preset(n) for n in list_presets()]:
            print(f"{preset.name}: {preset.feel}")
        return

    preset = get_preset(args.genre)
    output_name = args.output_name or f"cello_{preset.name}_ostinato"
    score = build_score(preset)  # seed threading depends on planner's chosen API shape (D-05 discretion)
    musicxml_path, midi_path = ExportEngine().export(score, output_name)
    print(f"Genre: {preset.name} - {preset.feel}")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
```
**WR-01 fix location:** `choices=sorted(list_presets())` today lists ALL 7 presets including the 3 duet-only ones (`sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet`), which have no `.bars`/`.rhythm` (only `.duet_bars`/`.duet_rhythm`) — passing one of those to `--genre` silently produces an empty/broken export. Registry needs a way to filter to solo-capable presets only, e.g. a new `list_solo_presets()` in `core/presets/registry.py` (analog: existing `list_presets()`, `core/presets/registry.py` lines 17-18) filtering on `preset.bars` being non-empty, then the CLI's `choices=sorted(list_solo_presets())`.

---

### `scripts/generate_sexy_duet_loop.py` / `generate_simple_sexy_duet_loop.py` / `generate_dorian_sexy_duet_loop.py` (thin wrappers)

**Analog:** each script itself, pre-refactor (already read above) — all three share byte-identical structure, differing only in preset name / tempo / velocity constants.

**Target shape** (using `generate_sexy_duet_loop.py` as the template — the other two are the same minus the literal constants):
```python
from __future__ import annotations

import sys
from pathlib import Path

from music21 import environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.loop_engine import build_duet_score  # noqa: E402  (internal-only path, D-13)
from core.export.exporter import ExportEngine  # noqa: E402
from core.presets.registry import get_preset  # noqa: E402

OUTPUT_NAME = "sexy_d_minor_violin_cello_loop"


def main() -> None:
    environment.Environment()["warnings"] = 0  # WR-04 fix
    preset = get_preset("sexy_duet")
    score = build_duet_score(preset, tempo_bpm=preset.duet_tempo_bpm, cello_velocity=82, violin_velocity=70)
    musicxml_path, midi_path = ExportEngine().export(score, OUTPUT_NAME)
    print("Sexy duet loop: D minor, 76 bpm, 8 bars, violin + cello")
    print(f"MusicXML: {musicxml_path}")
    print(f"MIDI: {midi_path}")


if __name__ == "__main__":
    main()
```
**Byte-identity risk flag:** velocities (82/70, 68/58, 74/62) and the printed summary strings are NOT stored on `MoodPreset` today — they are hardcoded in each script's `main()`/`build_score()`. Planner must decide whether to (a) keep them as literals in the thin wrapper (simplest, matches "thin wrapper = parse_args + core calls + printing" from D-12, since printing the summary is a wrapper concern) or (b) push them into `MoodPreset`/preset data (bigger blast radius, touches Phase 1 locked shape). Keeping velocities as wrapper-level call arguments to `build_duet_score(...)` is the minimal-risk choice and keeps `core/engine/loop_engine.py`'s duet path config-driven from the call site rather than requiring new preset fields.

---

## Shared Patterns

### Import-boundary rule (core/ vs scripts/)
**Source:** `.planning/research/ARCHITECTURE.md` line 122, enforced by `tests/test_import_boundary.py` (already passing in Phase 1, FORBIDDEN = `{"streamlit", "argparse"}`)
**Apply to:** `core/engine/loop_engine.py`, `core/export/exporter.py` — neither may import `argparse` or `streamlit`; `sys.path.insert` bootstrap and `PROJECT_ROOT` constants stay in `scripts/` only. `core/export/exporter.py` needs its own `Path`-based project-root resolution relative to its own file depth (`parents[2]`, not `parents[1]` as in `scripts/`).
```python
FORBIDDEN = {"streamlit", "argparse"}
```

### WR-04 fix: `environment.Environment()` instead of `environment.UserSettings()`
**Source:** all 4 scripts currently call `environment.UserSettings()["warnings"] = 0` (`scripts/generate_cello_dark_ostinato.py` line 72; identical call in the 3 duet scripts' `main()`, e.g. `scripts/generate_sexy_duet_loop.py` line 84) — `UserSettings()` persists to the user's `~/.music21rc` on every call (confirmed side effect flagged in `tests/test_golden_regression.py` module docstring and CONTEXT.md's Specific Ideas: "rewrites `~/.music21rc` 14 times per pytest session").
**Apply to:** all 4 thin wrappers' `main()` — one-line swap:
```python
environment.Environment()["warnings"] = 0  # in-memory only, no disk write
```
Verify this actually suppresses the same warnings `UserSettings()` did (test acceptance: golden suite still green, and no `~/.music21rc` mtime change during a pytest run).

### `zip(..., strict=True)` for bars/rhythm pairing
**Source:** identical across `core/engine/validators.py`'s callers-to-be and all 4 scripts, e.g. `scripts/generate_cello_dark_ostinato.py` line 35, `scripts/generate_sexy_duet_loop.py` line 29
**Apply to:** `core/engine/loop_engine.py`'s `build_score()` and `build_duet_score()` — locked convention, carried over verbatim per 01-PATTERNS.md and CONTEXT.md's "Established Patterns" section.

### Simple functions, no custom exceptions
**Source:** `core/presets/registry.py` (Phase 1, module docstring lines 1-5: "Kept intentionally simple... no custom exception type, no try/except") + `core/engine/validators.py` (bare `ValueError` raises)
**Apply to:** `core/engine/loop_engine.py`, `core/export/exporter.py` — propagate `KeyError` from `get_preset()` misses and `ValueError` from validator failures naturally; do not wrap in a new `LoopEngineError`/`ExportError` type. D-07's legacy-exception mechanism is a data-driven skip, not a new exception type.

### Path handling / project root
**Source:** identical across all 4 scripts, e.g. `scripts/generate_cello_dark_ostinato.py` line 9: `PROJECT_ROOT = Path(__file__).resolve().parents[1]`
**Apply to:** `core/export/exporter.py`'s `ExportEngine.__init__` default `base_dir` — same `scores/` relative-to-project-root convention, computed from `core/export/exporter.py`'s own location (`parents[2]`) since it now lives two directories deeper than the scripts did.

### Test structure (pytest, function-based, no classes)
**Source:** `tests/test_validators.py` (15 flat `test_*` functions, no test classes, `pytest.raises(ValueError)` context managers) and `tests/test_presets_registry.py` (same flat style, direct dict/dataclass field assertions)
**Apply to:** `tests/test_loop_engine.py`, `tests/test_exporter.py` — keep flat function style, no `unittest.TestCase`, no custom test base classes. Use `tmp_path` fixture (pytest built-in) for `ExportEngine` base-dir tests rather than writing into the real `scores/` directory during unit tests (golden regression already covers the real path).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Seed-resolution logic (`_resolve_seed` or equivalent, inside `loop_engine.py`) | utility | transform | No `random` usage exists anywhere in the current codebase (confirmed: `grep -r "import random" scripts/ core/` returns nothing) — D-01/D-02 plumbing is genuinely new, follow CONTEXT.md's decision text directly rather than a codebase pattern |
| D-07 legacy-pitch-exception mechanism | utility | transform | No per-preset exception/allowlist concept exists yet; only data point is the known `simple_sexy_duet` `"A1"` note flagged in 01-PATTERNS.md — naming and storage shape (module dict vs. new dataclass field) is Claude's discretion per CONTEXT.md |
| `list_solo_presets()` (WR-01 fix, likely lands in `core/presets/registry.py`) | service (CRUD) | CRUD | `list_presets()` (Phase 1) has no solo/duet filter concept; new filtering logic needed, though the surrounding module (`registry.py`) itself is an exact-match analog for style |

## Metadata

**Analog search scope:** `scripts/` (4 generator scripts), `core/engine/`, `core/presets/`, `tests/` (all existing test files), `.planning/phases/01-core-library-skeleton-validators/` (prior phase outputs), `.planning/research/ARCHITECTURE.md` (naming/structure guidance only, not a code analog).
**Files scanned:** 11 (4 scripts read in full, `core/models.py`, `core/engine/validators.py`, `core/presets/registry.py` read in full, `tests/conftest.py`/`test_validators.py`/`test_models.py`/`test_presets_registry.py`/`test_import_boundary.py`/`test_golden_regression.py` read in full, `01-PATTERNS.md` read in full, `ARCHITECTURE.md` lines 100-155 targeted-read for extraction/structure guidance).
**Pattern extraction date:** 2026-07-04
