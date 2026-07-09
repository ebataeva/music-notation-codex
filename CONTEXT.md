# Project Context — music-notation-codex

**Last updated:** 2026-07-09 14:50
**Branch:** `style-harmony-policy`
**Last commit:** `54d03c2` — docs(daily): update 2026-07-09 with full research report
**Progress:** 90% (9/10 phases v1 complete)

---

## Active Task

**Style-aware harmony policy implementation** — replace generic TheoryExplainer output with note-specific, preset-aware harmonic explanations grounded in modern genre research.

### Current Status

✅ **Completed:**
- Research: 7 parallel agents researched harmonic language for all presets (in transposable scale degrees, not fixed notes)
- Policy modules: `core/presets/style_policy.py`, `effects_policy.py`, `classical_formulas.py`
- Duet presets: filled empty progressions/modulations/mood_tips tuples
- Tests: 164 tests passing (22 new tests for policy modules)

⏳ **Next: Stage 4 — Rewrite `core/theory/explainer.py`**
- Remove generic phrases ("keeps the loop identity clear", "changing one harmonic parameter")
- Read policy from `style_policy.py` — generate note-specific text based on core_degrees, cadences, chromatic_approaches
- Optionally use `classical_formulas` for explanations
- Add snapshot tests for specific presets

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

1. **Rewrite `core/theory/explainer.py`** (Stage 4)
   - Remove generic phrases
   - Read from `style_policy.py`
   - Generate note-specific explanations
   - Add snapshot tests

2. **Test the rewritten explainer**
   - Run `pytest tests/test_theory_explainer.py -v`
   - Verify output is note-specific, not generic
   - Check all 7 presets produce distinct explanations

3. **Optional: Integrate effects policy**
   - Surface characteristic effects in UI or export
   - Decision needed: where/how

4. **Optional: Use classical formulas in explanations**
   - Cite T35, D7, etc. when relevant
   - Decision needed: when to use classical vs modern language

---

## Relevant Files

### Core Logic
- `core/presets/mood_presets.py` — preset registry (7 presets: 4 solo + 3 duet)
- `core/presets/style_policy.py` — **NEW** harmonic language policy per preset
- `core/presets/effects_policy.py` — **NEW** audio effects policy per preset
- `core/theory/explainer.py` — **TO REWRITE** theory explanation generator
- `core/theory/classical_formulas.py` — **NEW** classical harmony formulas reference
- `core/engine/loop_engine.py` — loop generation engine

### Research Data
- `research/*.yaml` — research results (7 preset YAMLs + effects + classical formulas)
- `pravila_po_garmonii.pdf` — classical harmony reference (Russian)

### Tests
- `tests/test_theory_explainer.py` — explainer tests (19 tests)
- `tests/test_style_policy.py` — **NEW** style policy tests (9 tests)
- `tests/test_effects_policy.py` — **NEW** effects policy tests (5 tests)
- `tests/test_classical_formulas.py` — **NEW** classical formulas tests (8 tests)

### Documentation
- `daily/2026-07-09.md` — today's session log (all user questions preserved)
- `Brain/music-notation-codex.md` — project wiki (architecture, status)
- `.planning/STATE.md` — GSD state (progress, phases)
- `.planning/ROADMAP.md` — GSD roadmap (phases, success criteria)

---

## Git State

```
Branch: style-harmony-policy (tracks origin/style-harmony-policy)
Recent commits:
  54d03c2 docs(daily): update 2026-07-09 with full research report
  ddfba48 feat(style-harmony-policy): fill duet presets
  9984411 feat(style-harmony-policy): add research YAML, policy modules
  fcc44c0 docs(daily): log Streamlit fallback cello synth
  cae35d6 docs(harmony): add style-aware harmony research plan

Untracked:
  ?? Brain/meta-orchestrator.md (generic router prompt, keep local)

Dirty:
   M .deepseek/state/subagents.v1.json (don't touch — not our mutation)
```

---

## How to Resume

**New session should:**
1. Read this `CONTEXT.md` (you're here)
2. Read `daily/2026-07-09.md` for detailed session history
3. Check current branch: `git branch --show-current`
4. Run tests: `.venv/bin/python -m pytest tests/ -q`
5. Continue with Stage 4: rewrite `core/theory/explainer.py`

**Key context:**
- All research is done (7 presets, effects, classical formulas)
- Policy modules are ready (`style_policy.py`, `effects_policy.py`, `classical_formulas.py`)
- Duet presets have filled theory tuples
- 164 tests passing
- Next: rewrite explainer to use new policy modules
