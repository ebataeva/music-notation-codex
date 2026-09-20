---
phase: quick-260920-pxe
plan: 01
subsystem: export
status: complete
tags: [test-isolation, golden-regression, exporter, working-tree-hygiene]
requires: []
provides:
  - "MNC_SCORES_DIR environment override for ExportEngine.base_dir"
  - "golden regression test that writes only into pytest tmp_path"
affects:
  - "any future test or tool that needs to redirect CLI script output out of the repo"
tech-stack:
  added: []
  patterns:
    - "env-var test-isolation hook read at construction time, never at import"
key-files:
  created: []
  modified:
    - core/export/exporter.py
    - tests/test_exporter.py
    - tests/test_golden_regression.py
decisions:
  - "MNC_SCORES_DIR is read inside ExportEngine.__init__ (not at module import) so monkeypatch in-process and per-subprocess env= both take effect"
  - "Empty MNC_SCORES_DIR is treated as unset rather than as 'write to cwd'"
  - "Explicit base_dir= argument always wins over the environment; resolution uses an explicit `is None` check instead of the old `or` idiom"
  - "Baseline stays frozen: capture_baseline() was NOT executed and tests/golden/baseline_hashes.json was NOT edited"
metrics:
  duration: ~12 min
  completed: 2026-09-20
actuals:
  tokens: 2600
  tasks: 2
  commits: 3
---

# Quick Task 260920-pxe: Stop Golden Regression Test From Overwriting scores/ Summary

Gave `ExportEngine` an `MNC_SCORES_DIR` environment override and pointed the golden
regression test at pytest's `tmp_path`, so a full test run no longer rewrites the 14
git-tracked files under `scores/midi/` and `scores/musicxml/`.

## What Was Built

**Task 1 — `MNC_SCORES_DIR` override (TDD, commits `08f99de` RED → `c158336` GREEN)**

`ExportEngine.__init__` now resolves `base_dir` in an explicit order: the `base_dir=`
argument if given, else a non-empty `MNC_SCORES_DIR`, else `PROJECT_ROOT / "scores"`.
The `or` idiom was replaced with an `is None` check so intent is readable. The
environment is read at construction time, never at module import — that is what makes
both `monkeypatch` (in-process) and `env=` (per-subprocess) work. `_safe_path`,
`export_to_musicxml`, `export_to_midi`, `export` and `PROJECT_ROOT` are unchanged, so an
export still cannot escape whichever `base_dir` was selected.

Four behaviours are covered in `tests/test_exporter.py`: the default path (with the env
var explicitly deleted, so the test is deterministic), the env override, explicit-arg
priority over the env, and empty-string-means-unset.

**Task 2 — golden test writes only to `tmp_path` (commit `8801797`)**

`run_all_scripts(output_dir)` builds `{**os.environ, "MNC_SCORES_DIR": str(output_dir)}`
and passes it to `subprocess.run`, keeping `check=True` and `cwd=PROJECT_ROOT` (the
scripts still need the project root for their imports). `compute_current_hashes(output_dir)`
derives `midi_dir` / `musicxml_dir` locally; the returned dict shape is unchanged, because
the committed baseline is keyed that way. The two module-level constants that pointed at
`scores/midi` and `scores/musicxml` are gone. `capture_baseline()` keeps its no-arg
signature (the documented one-liner still works) but now does its work inside a
`tempfile.TemporaryDirectory`. Both tests take the `tmp_path` fixture. The module
docstring's recapture paragraph no longer claims hashes come from the current state of
`scores/`.

## Acceptance Gate — Actual Output

Run from the worktree root after the Task 2 commit, with the tree clean:

1. `.venv/bin/python -m pytest tests/ -q` → **`1147 passed, 14 warnings in 7.98s`**.
   1147, not the expected ~1144, because this task added exactly 3 new exporter tests
   (1144 + 3 = 1147).
2. `git status --short` immediately after → only two pre-existing untracked entries:
   ```
   ?? .gsd/
   ?? .planning/quick/260920-pxe-stop-golden-regression-test-from-overwri/
   ```
   Nothing under `scores/`, no stray generated directories. This output is byte-identical
   to the status captured immediately *before* the run.
3. `git diff --stat -- scores/ tests/golden/` → **empty**.
4. `git log -1 --format=%H -- tests/golden/baseline_hashes.json scores/` →
   `0e55f8c595633ea85e61c2aea3ddb64470ca0b2a`, identical to the value recorded before the
   task started. Neither the baseline nor any tracked score file was touched.

`git diff --name-only HEAD~3 HEAD` lists exactly three files — `core/export/exporter.py`,
`tests/test_exporter.py`, `tests/test_golden_regression.py`. No path under `scores/` or
`tests/golden/` appears in any of the task commits.

## Golden Hash Result

**No regression.** Both golden tests passed against the unchanged, un-recaptured
`tests/golden/baseline_hashes.json` on the first run after the change
(`2 passed in 3.64s`). `capture_baseline()` was never executed and the baseline file was
never opened for writing.

## Deviations from Plan

**1. [Rule 3 - Blocking] The worktree has no `.venv`**

- **Found during:** setup, before Task 1
- **Issue:** `.venv/` is gitignored, so it exists only in the main checkout at
  `/Users/ebataeva/Brain/Projects/music-notation-codex/.venv` and not in this worktree.
  Every command in the plan is written as `.venv/bin/python`, which fails with
  `no such file or directory` here.
- **Fix:** ran every command with the absolute interpreter path
  `/Users/ebataeva/Brain/Projects/music-notation-codex/.venv/bin/python` from the worktree
  root. Verified the interpreter resolves project imports to the *worktree* copy
  (`core.export.exporter.__file__` points into the worktree), and that there are no `.pth`
  files in site-packages redirecting to the main checkout, so the tests genuinely exercise
  the code under change.
- **Rejected alternative:** a `.venv` symlink inside the worktree was tried first and
  backed out — `.gitignore` has `.venv/` with a trailing slash, which matches directories
  but not symlinks, so the symlink showed up as `?? .venv` and would have polluted the
  `git status` acceptance gate.
- **Files modified:** none.

**2. [Observation, not a fix] Only test 2 of the four was genuinely RED**

- **Found during:** Task 1 RED step
- **Issue:** the plan expected tests 2-4 to fail before the exporter change. In fact only
  `test_export_engine_honours_scores_dir_env_override` failed
  (`1 failed, 6 passed`). Tests 3 and 4 passed pre-change by construction: with the env
  never read, an explicit `base_dir` trivially wins and an empty value is trivially
  ignored.
- **Assessment:** this is expected, not a defect in the tests. Both are regression guards
  against a plausible naive implementation — one that reads the env *before* honouring the
  explicit argument, or that uses `os.environ.get("MNC_SCORES_DIR", default)` without the
  empty-string check. They are worth keeping; they simply cannot be RED until the feature
  exists.
- **Files modified:** none.

## Must-Haves Verification

| Truth | Status |
|-------|--------|
| A pytest run modifies/creates nothing in the tree; `git status --short` identical before and after; `git diff --stat -- scores/ tests/golden/` empty | Verified — gates 1-3 above |
| Both golden tests pass against the un-recaptured baseline | Verified — `2 passed in 3.64s` |
| `ExportEngine()` with no arg and no env still resolves to `PROJECT_ROOT/scores` | Verified — `test_export_engine_defaults_base_dir_to_project_root_scores` |
| `ExportEngine()` with env set resolves to it; explicit arg still wins | Verified — tests 2 and 3 |
| `capture_baseline()` no longer reads/writes under `scores/`; writes only the baseline; NOT executed | Verified by inspection — its only write target is `BASELINE_PATH`; it was not run |

## Scope Notes

- `tests/test_phase7_variants.py` left untouched, as planned — it renders MIDI in memory
  via `streamToMidiFile(score).writestr()` and never touches `ExportEngine` or a `scores/`
  path.
- The four scripts under `scripts/` were not modified; they pick up the redirect purely
  through their existing no-arg `ExportEngine()` calls.
- No README or doc text added (out of scope for this quick task).
- No new dependencies — `os` and `tempfile` are stdlib.

## Known Stubs

None.

## Threat Flags

None. The plan's threat register anticipated both surfaces: `T-pxe-01` (the env var grants
no new capability on a local single-user tool, and `_safe_path` still constrains
`output_name`) and `T-pxe-02` (the subprocess env is mitigated by the before/after
`git status` gate, which passed).

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `08f99de` | test | RED: four `MNC_SCORES_DIR` behaviours in `tests/test_exporter.py` |
| `c158336` | feat | GREEN: `ExportEngine` honours `MNC_SCORES_DIR` |
| `8801797` | fix | golden regression scripts run into `tmp_path`, not `scores/` |

No REFACTOR commit — the GREEN implementation needed no cleanup.

## TDD Gate Compliance

Task 1 followed RED → GREEN with a `test(...)` commit preceding the `feat(...)` commit.
Task 2 was not marked `tdd="true"` in the plan; it is verified by the before/after
`git status` comparison in its own verify gate rather than by a new failing test.

## Self-Check: PASSED

- `core/export/exporter.py` — FOUND
- `tests/test_exporter.py` — FOUND
- `tests/test_golden_regression.py` — FOUND
- Commit `08f99de` — FOUND
- Commit `c158336` — FOUND
- Commit `8801797` — FOUND
