---
phase: quick-260920-pxe
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - core/export/exporter.py
  - tests/test_exporter.py
  - tests/test_golden_regression.py
autonomous: true
requirements: []

must_haves:
  truths:
    - "Running `.venv/bin/python -m pytest tests/ -q` modifies or creates nothing inside the repo working tree: `git status --short` is identical before and after the run, and `git diff --stat -- scores/ tests/golden/` is empty"
    - "Both golden regression tests pass against the unchanged, un-recaptured tests/golden/baseline_hashes.json"
    - "`ExportEngine()` with no argument and no MNC_SCORES_DIR in the environment still resolves base_dir to PROJECT_ROOT/scores, so the CLI scripts run by hand keep writing where they always did"
    - "`ExportEngine()` with MNC_SCORES_DIR set resolves base_dir to that directory; an explicit base_dir= argument still wins over the environment"
    - "capture_baseline() no longer reads or writes anything under scores/; it still writes only tests/golden/baseline_hashes.json (and is NOT executed by this task)"
  artifacts:
    - path: "core/export/exporter.py"
      provides: "MNC_SCORES_DIR environment override for the default base_dir, read per instance in __init__"
      contains: "MNC_SCORES_DIR"
    - path: "tests/test_golden_regression.py"
      provides: "run_all_scripts(output_dir) / compute_current_hashes(output_dir) driven by pytest tmp_path; capture_baseline() on a TemporaryDirectory"
      contains: "MNC_SCORES_DIR"
    - path: "tests/test_exporter.py"
      provides: "deterministic default-base_dir test plus env-override and explicit-arg-priority tests"
      contains: "MNC_SCORES_DIR"
  key_links:
    - from: "tests/test_golden_regression.py::run_all_scripts"
      to: "core/export/exporter.py::ExportEngine.__init__"
      via: "subprocess.run(..., env={**os.environ, 'MNC_SCORES_DIR': str(output_dir)}) through the four scripts' no-arg ExportEngine() calls"
    - from: "tests/test_golden_regression.py::compute_current_hashes"
      to: "output_dir/midi and output_dir/musicxml"
      via: "the same tmp_path the scripts were redirected into, replacing the module-level scores/ constants"
---

<objective>
Stop `tests/test_golden_regression.py` from rewriting the 14 git-tracked files under `scores/midi/` and `scores/musicxml/` on every pytest run. The golden BASELINE is `tests/golden/baseline_hashes.json`; the files under `scores/` are only a by-product of the 7 CLI script invocations, and music21 makes the MusicXML byte-different on each run (fresh `<encoding-date>`, `id="P..."`/`id="I..."` minted from object addresses), leaving a dirty tree that blocks `git checkout`/`git merge`.

Approach (minimal, as recommended in the task brief): give `ExportEngine` an `MNC_SCORES_DIR` environment override for its default `base_dir` (the four scripts call `ExportEngine()` with no args and have no output-dir flag, so an env variable is the only way to redirect all 7 invocations without touching the scripts), then have the golden test run the scripts with that variable pointed at pytest's `tmp_path` and hash from there.

Scope confirmation from planning: `tests/test_phase7_variants.py` was checked and does NOT write into the repo — it renders MIDI in memory via `streamToMidiFile(score).writestr()` and never touches `ExportEngine` or a `scores/` path. It is left alone. Only `tests/test_golden_regression.py` referenced the `scores/midi` / `scores/musicxml` module constants, so they can be deleted.

HARD CONSTRAINT carried from the brief: do NOT run `capture_baseline()`, do NOT regenerate or edit `tests/golden/baseline_hashes.json`, do NOT modify anything under `scores/`. A hash mismatch is a real regression to report, never something to "fix" by recapturing.

Purpose: keep the working tree clean after every test run so branch switches and merges stop being blocked by noise diffs.
Output: env-aware `ExportEngine.__init__`, a golden test that writes only to `tmp_path`, updated exporter tests.
</objective>

<execution_context>
@$HOME/.claude/gsd-core/workflows/execute-plan.md
@$HOME/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@core/export/exporter.py
@tests/test_exporter.py
@tests/test_golden_regression.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add MNC_SCORES_DIR environment override to ExportEngine's default base_dir</name>
  <files>core/export/exporter.py, tests/test_exporter.py</files>
  <precondition>`.venv/bin/python -m pytest --version` succeeds from the worktree root (project venv with pytest and music21 present).</precondition>
  <reversibility rating="reversible">The variable name MNC_SCORES_DIR is only consumed by ExportEngine and only set by the golden test; renaming or removing it later is a two-file change.</reversibility>
  <behavior>
    - Test 1 (existing `test_export_engine_defaults_base_dir_to_project_root_scores`, made deterministic): with `MNC_SCORES_DIR` removed from the environment via `monkeypatch.delenv("MNC_SCORES_DIR", raising=False)`, `ExportEngine().base_dir == Path(__file__).resolve().parents[1] / "scores"` (keep the independent parents[] computation and its comment).
    - Test 2 (new `test_export_engine_honours_scores_dir_env_override`): with `monkeypatch.setenv("MNC_SCORES_DIR", str(tmp_path))`, `ExportEngine().base_dir == tmp_path`.
    - Test 3 (new `test_export_engine_explicit_base_dir_beats_env_override`): with the same env set, `ExportEngine(base_dir=tmp_path / "explicit").base_dir == tmp_path / "explicit"`.
    - Test 4 (new `test_export_engine_ignores_empty_scores_dir_env`): with `monkeypatch.setenv("MNC_SCORES_DIR", "")`, `ExportEngine().base_dir` is the PROJECT_ROOT/scores default (empty string is treated as unset).
  </behavior>
  <action>
    RED first: write the four tests above in `tests/test_exporter.py` (keep the existing `ExportEngine` import-inside-test style and the `_make_minimal_score` helper untouched), run `tests/test_exporter.py`, and confirm tests 2-4 fail before touching the exporter.

    GREEN: in `core/export/exporter.py` add `import os` to the stdlib import block (above `from pathlib import Path`). Rewrite `ExportEngine.__init__(self, base_dir: Path | None = None)` so resolution order is explicit and uses an `is None` check rather than the current `or` idiom (a Path is always truthy, but an explicit test keeps intent obvious): (1) an explicit `base_dir` argument is used as-is; (2) otherwise, if `os.environ.get("MNC_SCORES_DIR")` is a non-empty string, use `Path(that_value)`; (3) otherwise `PROJECT_ROOT / "scores"`. The environment must be read inside `__init__` at construction time, never at module import, so `monkeypatch` in-process and a per-subprocess `env=` both take effect. Add one short English comment above the env lookup saying the hook exists for test isolation: the golden regression test uses it to redirect the CLI scripts' output out of the repo working tree. Leave `_safe_path`, `export_to_musicxml`, `export_to_midi`, `export`, `PROJECT_ROOT` and the module docstring unchanged — `_safe_path` still rejects separators/traversal in `output_name`, so an export can never escape whichever `base_dir` was selected.

    Do not touch the four scripts under `scripts/` and do not add any README/doc text (docs are out of scope for this quick task).
  </action>
  <verify>
    <automated>cd /Users/ebataeva/Brain/Projects/music-notation-codex/.claude/worktrees/vibrant-montalcini-d07a13 && .venv/bin/python -m pytest tests/test_exporter.py -q && OUT="$(mktemp -d)" && MNC_SCORES_DIR="$OUT" .venv/bin/python scripts/generate_dorian_sexy_duet_loop.py >/dev/null && test -f "$OUT/midi/dorian_sexy_violin_cello_loop.mid" && test -f "$OUT/musicxml/dorian_sexy_violin_cello_loop.musicxml" && [ -z "$(git status --short -- scores/)" ] && rm -rf "$OUT" && echo TASK1-OK</automated>
  </verify>
  <done>All exporter tests pass (7 total: 3 existing tmp_path tests + the 4 behaviours above). Running a real CLI script with MNC_SCORES_DIR set writes its .mid/.musicxml pair only into that directory and leaves `git status --short -- scores/` empty. Without the variable, `ExportEngine().base_dir` is still PROJECT_ROOT/scores.</done>
</task>

<task type="auto">
  <name>Task 2: Route the golden regression test through tmp_path so it never writes into scores/</name>
  <files>tests/test_golden_regression.py</files>
  <action>
    Edit `tests/test_golden_regression.py` only. Baseline stays frozen: never call `capture_baseline()` during this task and never edit `tests/golden/baseline_hashes.json` or anything under `scores/`.

    1. Imports: add `import os` and `import tempfile` to the stdlib group (alphabetical: hashlib, json, os, re, subprocess, sys, tempfile).
    2. Delete the two module-level constants that point at the repo's `scores/midi` and `scores/musicxml` directories (planning grep confirmed nothing else in the repo references them). Keep `PROJECT_ROOT`, `BASELINE_PATH`, `PYTHON`, `INVOCATIONS`, and both regexes as they are.
    3. `run_all_scripts(output_dir: Path) -> None`: build `env = {**os.environ, "MNC_SCORES_DIR": str(output_dir)}` and pass `env=env` to `subprocess.run`, keeping `check=True` and `cwd=PROJECT_ROOT` (the scripts still need the project root cwd for their imports). Update its docstring: it re-runs the 7 invocations and writes into `output_dir/midi` and `output_dir/musicxml`, never into the repo.
    4. `compute_current_hashes(output_dir: Path)`: derive `midi_dir = output_dir / "midi"` and `musicxml_dir = output_dir / "musicxml"` locally and build the per-file paths from those; the returned dict shape (`{"midi": {...}, "musicxml_normalized": {...}}` keyed by file name) must not change, because the committed baseline is keyed that way.
    5. `capture_baseline() -> None` keeps its no-arg signature so the documented one-liner still works, but now does its work inside `with tempfile.TemporaryDirectory() as tmp:` — `output_dir = Path(tmp)`, `run_all_scripts(output_dir)`, `hashes = compute_current_hashes(output_dir)` — and then writes `BASELINE_PATH` exactly as before (mkdir parents, `json.dumps(..., indent=2, sort_keys=True) + "\n"`). Keep its warning docstring about not using it to "fix" a failing test.
    6. Both test functions take the pytest `tmp_path` fixture and call `run_all_scripts(tmp_path)` then `compute_current_hashes(tmp_path)`; the assertions against `_load_baseline()` are unchanged.
    7. Module docstring: keep paragraphs 1-2 (the Phase 1 provenance and the MIDI-vs-normalized-MusicXML rationale are still accurate). Rewrite the recapture paragraph so it no longer claims hashes come from the current state of `scores/midi/` and `scores/musicxml/`: state that the scripts are re-run into a temporary directory by pointing `ExportEngine` at it through the `MNC_SCORES_DIR` environment variable, that hashes are computed from that directory, and that this module neither reads nor writes anything under `scores/` (the tracked files there are a by-product of running the scripts by hand, not the baseline). Also replace the stale first sentence of the two test docstrings ("Expected to PASS at the end of this plan: data hasn't moved yet, scripts are unchanged.") with a present-tense sentence saying the test runs every invocation into `tmp_path` and compares the result with the committed baseline; keep the rest of each docstring.

    If either golden test fails after the change with a hash mismatch, stop and report it as a regression in the SUMMARY — do not recapture, do not edit the baseline, do not mark the task complete.
  </action>
  <verify>
    <automated>cd /Users/ebataeva/Brain/Projects/music-notation-codex/.claude/worktrees/vibrant-montalcini-d07a13 && .venv/bin/python -c "import inspect, tests.test_golden_regression as m; assert not hasattr(m, 'MIDI_DIR') and not hasattr(m, 'MUSICXML_DIR'); assert 'output_dir' in inspect.signature(m.run_all_scripts).parameters; assert 'output_dir' in inspect.signature(m.compute_current_hashes).parameters" && BEFORE="$(git status --short)" && .venv/bin/python -m pytest tests/test_golden_regression.py -q && [ "$BEFORE" = "$(git status --short)" ] && .venv/bin/python -m pytest tests/ -q && [ "$BEFORE" = "$(git status --short)" ] && [ -z "$(git diff --stat -- scores/ tests/golden/)" ] && [ -z "$(git status --short -- scores/ tests/golden/)" ] && echo TASK2-OK</automated>
  </verify>
  <done>Both golden tests pass against the untouched baseline; the full suite (`pytest tests/ -q`, ~1144 tests) passes; `git status --short` is byte-identical before and after each run (the runs create and modify nothing in the tree); `git diff --stat -- scores/ tests/golden/` and `git status --short -- scores/ tests/golden/` are empty; the module no longer exposes the two repo-pointing directory constants.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| process environment → ExportEngine | A new input (MNC_SCORES_DIR) now selects where exports are written when no base_dir is passed |
| pytest process → script subprocesses | The test hands the scripts an environment it constructs; the scripts write wherever that environment says |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-pxe-01 | Tampering | core/export/exporter.py::ExportEngine.__init__ (MNC_SCORES_DIR) | low | accept | Local single-user desktop tool: whoever sets the environment already owns the filesystem, so the variable grants no new capability. It only selects base_dir; `_safe_path` still rejects separators and traversal in output_name, so an export cannot escape the selected base_dir. Empty value is treated as unset. |
| T-pxe-02 | Tampering | tests/test_golden_regression.py::run_all_scripts subprocess env | low | mitigate | Env is built as `{**os.environ, "MNC_SCORES_DIR": str(output_dir)}` where output_dir is pytest's tmp_path (outside the repo); Task 2's verify gate compares `git status --short` before and after the run so any write into the tree fails the task. |
| T-pxe-SC | Tampering | npm/pip/cargo installs | low | accept | No package-manager installs in this plan; no new dependencies (os, tempfile are stdlib). |
</threat_model>

<verification>
Run from the worktree root after Task 2's commit (the tree must be clean at that point, which is what the brief's acceptance checks assume):

1. `.venv/bin/python -m pytest tests/ -q` — all tests pass (expected ~1144).
2. Immediately afterwards `git status --short` prints nothing — no modified files under `scores/`, no stray output directories anywhere in the tree.
3. `git diff --stat -- scores/ tests/golden/` prints nothing.
4. `git log -1 --format=%H -- tests/golden/baseline_hashes.json scores/` is unchanged from before the task (neither the baseline nor the tracked score files were touched).
</verification>

<success_criteria>
- The golden regression test and the full suite are green with the baseline hashes exactly as committed before this task.
- A pytest run leaves `git status --short` unchanged; `scores/` and `tests/golden/` show no diff.
- `ExportEngine()` behaviour for humans running the scripts by hand is unchanged (default still PROJECT_ROOT/scores); the override is opt-in via MNC_SCORES_DIR and an explicit base_dir argument always wins.
- `tests/test_phase7_variants.py` untouched (confirmed read-only: in-memory MIDI via writestr()).
- No file under `scores/` and no `tests/golden/baseline_hashes.json` edit appears in the task's commits.
</success_criteria>

<output>
Create `.planning/quick/260920-pxe-stop-golden-regression-test-from-overwri/260920-pxe-SUMMARY.md` when done. If a golden hash mismatch appeared, the SUMMARY must report it as an open regression with the differing file names — not as something fixed.
</output>
