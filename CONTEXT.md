# Project Context — music-notation-codex

**Last updated:** 2026-09-24 15:27 CEST
**Branch:** `codex/theory-dictionary`
**Last commit:** `806c2a9 — docs(daily): record the SPELL-01 fix and the three follow-up tasks`
**Progress:** Restart with a new planner (Addy Agent Skills) replacing GSD — pending the user's decision on new vs same repo

---

## Active Task

**Restart the project from scratch with a new planner instead of GSD.** The Addy Osmani `agent-skills` pack (25 skills) was installed on 2026-09-24. No repository changes were made: GSD and `.planning/` are intact.

Planner process to follow, in order:

1. `interview-me` — determine what goes into the first version.
2. `spec-driven-development` — agree on requirements and scope (capability map first for a large project).
3. `planning-and-task-breakdown` — plan with acceptance criteria.
4. `incremental-implementation` + `test-driven-development` — one working slice at a time.

**Blocked on:** the user has not yet decided whether to restart in a new empty repository or in the current one.

## Key Decisions

### Planner (2026-09-24)

- Chosen: Addy Osmani `agent-skills` as the main process. OpenSpec is optional and compatible (`spec-driven-development` says not to create a duplicate `SPEC.md` when OpenSpec is already in use).
- Install locations (verified): `~/.agents/skills` (canonical, 25/25), Codex plugin `agent-skills@agent-skills` 0.6.10, symlinks into Claude Code and Hermes Agent, `~/.agents/references` (7 checklists restored manually — upstream issue #361).
- Trap: `npm install -g openspec` installs a dead 0.0.0 placeholder (2019); the real package is `@fission-ai/openspec`. Spec Kit installs via `uvx --from git+https://github.com/github/spec-kit.git specify init .`.
- GSD not removed.

### Historical (completed, committed) — retained

1. Research outputs transposable patterns (scale degrees), not fixed notes.
2. Cadences: flat list with comments, not binary preferred/avoided.
3. Classical harmony rules are reference, not final preset policy.
4. Duet presets have filled theory tuples.

## Open Questions

1. **Blocking:** new empty repo vs current repo for the restart.
2. Fate of `.planning/` and GSD (archive / remove / keep).
3. Install OpenSpec (`@fission-ai/openspec`) as the durable spec layer? (optional)
4. Clean up the 21 duplicate Addy symlinks in `~/.hermes/skills`? (low urgency — `hermes skills list` dedupes by name)
5. Addy pack in the Ekko profile dir? (requires `metadata.keywords` frontmatter adaptation)

Historical future-work items (recorded, not active): "Expand advice by case" button; audio effects integration; classical formulas usage.

## Next Steps

1. Ask the user: new repo or current repo (blocking).
2. Then `interview-me` → `spec-driven-development` → `planning-and-task-breakdown`.
3. Do not remove GSD until the restart actually starts.

## Relevant Files

### Planner / state

- `handoffs/context-handoff-20260924-151959.md` — full handoff of this decision + install inventory
- `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/config.json` — GSD (not removed)
- `AGENTS.md` — project rules (CONTEXT.md is the resume file)

### App logic (unchanged)

- `core/theory/explainer.py`, `core/theory/harmony.py`, `core/engine/loop_engine.py`
- `core/presets/mood_presets.py`, `core/presets/style_policy.py`, `core/presets/effects_policy.py`
- `app/services/generation.py`, `app/pages/loop_coach.py`, `app/pages/theory_dictionary.py`, `app/components/notation.py`

### Tests

- `tests/` (Python), `tests-ui/` (Playwright)

### Docs

- `daily/2026-09-23.md` (latest), `daily/2026-09-20.md`, `daily/2026-09-21.md`
- `CLAUDE.md` — detailed project context

## Git State

- Branch `codex/theory-dictionary`, HEAD `806c2a9`, tracking `origin/codex/theory-dictionary` (the branch is already on origin).
- `main` at `6743c64`; HEAD is 49 commits ahead, `main` is an ancestor — branch not merged into `main`.
- Uncommitted: `daily/2026-09-20.md`, `daily/2026-09-21.md` (modified); `daily/2026-09-23.md`, `duet_card.png`, `handoffs/context-handoff-20260924-151959.md` (untracked).
- Extra worktree: `.claude/worktrees/ecstatic-heisenberg-728342` on branch `worktree-ecstatic-heisenberg-728342` at `09a8ee8`.
- Recent work: SPELL-01 series (`0efeeec`, `0cb626f`, `4c8fac9`, `2dbd60a`) — note spelling from chord / line of fifths; `260920-pxe` (`8801797`) — golden regression no longer rewrites `scores/`.

## How to Resume

1. Read this CONTEXT.md, then `handoffs/context-handoff-20260924-151959.md`.
2. Use jCodemunch for code and jDocMunch for documents; refresh a stale index before relying on it.
3. New edits go through the Addy planner (interview → spec → plan → incremental + TDD), not GSD.
4. Ask the user the blocking question before making any code changes.
