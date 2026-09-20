# Project Context — music-notation-codex

**Last updated:** 2026-09-16 20:39
**Branch:** `hotfix/loop-coach-notation-audio`
**Last commit:** `0002e10 — chore: add showcase push helpers (deploy.sh, git-push.mk); update .deepseek state`
**Progress:** Theory correctness audit complete; fixes remain uncommitted

---

## Active Task

**Prompt 2 — concise Theory cards, contextual Theory Dictionary, and transition guidance — implemented 2026-09-16, uncommitted.** The user approved the plan in the conversation; implementation used GSD quick task `260916-bta` inline. The earlier Theory musical correctness audit remains completed and was not restarted.

Read [the audit handoff](handoffs/context-handoff-20260916-030200.md) for the earlier audit state and [today's daily entry](daily/2026-09-16.md) for both the audit evidence and the complete Prompt 2 implementation record, including verification, fixes, and UI examples.

### Current Status

- Prompt 2 adds concise text and term IDs while preserving the five existing `TheoryExplanation` fields and detailed solo analysis.
- Solo generation uses the UI reference key. Authored duet explanations use the actual fixed score; the musical material is unchanged.
- `/theory` provides 19 articles with lazy cached notation and audio from one Score, contextual links in new tabs, and distinct transition examples. Standalone examples default to C.
- Verification after implementation: **1115 Python tests passed; 7 Playwright tests passed**. Coverage includes all 12 tonics and seven presets, MusicXML/MIDI pitch and timing agreement, audible fallback synthesis, visible OSMD scores, and continued loop playback while the dictionary opens in another tab. The 14 warnings are occurrences of the existing legacy A1-range warning.
- Main new files: `core/theory/{summaries,dictionary,transitions}.py`, `app/services/theory_dictionary.py`, `app/pages/theory_dictionary.py`, `app/components/notation.py`, `tests/test_theory_dictionary.py`, and `tests-ui/test_theory_dictionary.py`.
- FluidSynth subprocess errors now activate the existing fallback synthesizer. Both dictionary and loop audio containers have explicit widths.

Historical audit results, retained:

- Fixed three error groups: chord quality/degree/spelling errors; unsupported mode/cadence claims from preset policy; and advice tied to the original key.
- Modified: `core/theory/explainer.py`, `tests/test_theory_explainer.py`.
- New, untracked: `core/theory/harmony.py`, `tests/test_theory_musical_correctness.py`.
- Verification: **776 passed**, one legacy A1-range warning; `git diff --check` passed.
- Coverage includes six independent patterns in all 12 tonics across all seven presets, plus counterexamples and generated-score checks.
- The separate duet showcase bypass was outside the audit and is addressed by Prompt 2. Parser spelling limitations and source policy prose remain outside these fixes.
- No commit, push, or deployment. Do not repeat the completed audit by default.

---

## Key Decisions

1. **Research outputs transposable patterns (scale degrees), not fixed notes**
   - User question: "Why is the key hardcoded in stage 1?"
   - Decision: Research should output i, bVI, bVII, V (degrees), not C, Ab, Bb (notes)
   - Tonics from `mood_presets.py` are just instantiation of patterns, don't require research

2. **Cadences: flat list with comments, not binary preferred/avoided**
   - User question: "Why cadences: preferred/avoided? Better to keep and write a comment!"
   - Decision: Remove binary division. Keep flat list of cadential gestures with "why it works" comment

3. **Classical harmony rules are reference, not final preset policy**
   - Old harmony PDF/longreads are useful baseline theory vocabulary
   - Should not be mechanically applied to trip-hop/noir/ritual/cinematic presets
   - Modern genre research takes precedence

4. **Duet presets now have filled theory tuples**
   - sexy_duet: i-bVI-iv-V7, harmonic minor leading tone
   - simple_sexy_duet: simple i-V7 alternation, intimate
   - dorian_sexy_duet: Dorian i9-IV9 vamp, natural 6th warmth

---

## Open Questions

1. **UI idea: "Expand advice by case" button** (future work)
   - NiceGUI button that expands detailed advice for specific case
   - Not implementing now, just recorded

2. **Audio effects integration** (future work)
   - Research completed: characteristic effects per preset (reverb, delay, saturation, filters)
   - Not yet integrated into app — needs decision on how/where to surface

3. **Classical formulas usage** (future work)
   - Reference created: T35, T64, D7, SII6, K64, etc.
   - Not yet used in explainer — needs decision on when to cite classical rules vs modern patterns

---

## Next Steps

1. Review the completed Prompt 2 UI and continue according to the newest user request. The linked handoff describes the earlier audit; today's daily and this file also record the completed Prompt 2 implementation.
2. Prompt 4, parser work, commit, push, and deployment have not been authorized for this stage.
3. Preserve all earlier uncommitted audit and unrelated changes. Do not restart the completed audit or extend scope solely because a handoff lists an unresolved item.

---

## Relevant Files

### Core Logic
- `core/presets/mood_presets.py` — preset registry (7 presets: 4 solo + 3 duet)
- `core/presets/style_policy.py` — **NEW** harmonic language policy per preset
- `core/presets/effects_policy.py` — **NEW** audio effects policy per preset
- `core/theory/explainer.py` — evidence-grounded explanations with optional style suggestions
- `core/theory/harmony.py` — pitch spelling, chord quality, Roman numerals, collection compatibility
- `core/theory/classical_formulas.py` — **NEW** classical harmony formulas reference
- `core/engine/loop_engine.py` — loop generation engine

### Research Data
- `research/*.yaml` — research results (7 preset YAMLs + effects + classical formulas)
- `pravila_po_garmonii.pdf` — classical harmony reference (Russian)

### Tests
- `tests/test_theory_explainer.py` — explainer contracts updated for evidence-grounded output
- `tests/test_theory_musical_correctness.py` — independent musical corpus, all tonics/presets, counterexamples, and integration checks
- `tests/test_style_policy.py` — **NEW** style policy tests (9 tests)
- `tests/test_effects_policy.py` — **NEW** effects policy tests (5 tests)
- `tests/test_classical_formulas.py` — **NEW** classical formulas tests (8 tests)

### Documentation
- `daily/2026-09-16.md` — current audit results and before/after examples
- `handoffs/context-handoff-20260916-030200.md` — current new-chat handoff
- `daily/2026-07-09.md` — earlier style-policy research history
- `Brain/music-notation-codex.md` — project wiki (architecture, status)
- `.planning/STATE.md` — GSD state (progress, phases)
- `.planning/ROADMAP.md` — GSD roadmap (phases, success criteria)

---

## Git State

- Branch: `hotfix/loop-coach-notation-audio`.
- HEAD: `0002e10` — chore: add showcase push helpers (deploy.sh, git-push.mk); update .deepseek state.
- Both the earlier audit and Prompt 2 implementation remain uncommitted.
- Prompt 2 updates this existing CONTEXT.md and `.planning/STATE.md`. At the user's subsequent request, its full record was appended to the existing `daily/2026-09-16.md`; no new summary, README, or handoff documents were created.
- Pre-existing unrelated changes include AGENTS.md, Brain/meta-orchestrator.md, README.md, seven scores/musicxml files, and untracked duet_card.png. CONTEXT.md already had changes before this audit; earlier project decisions and open questions are retained above.
- The historical style-harmony-policy branch snapshot previously in this file is superseded by this live checkout state.

---

## How to Resume

1. Read this CONTEXT.md and CLAUDE.md through MCP first, then the linked handoff.
2. Use jCodemunch for code and jDocMunch for documents; refresh a stale index before relying on it.
3. Follow the existing GSD workflow for any new edits. The completed audit used the GSD debug entry point.
4. Review only the pending Theory/test changes for the next step; avoid restarting the whole investigation.
5. Test results above distinguish the earlier audit from Prompt 2 verification. Rerun appropriate tests after new implementation changes, not merely to transfer context.
