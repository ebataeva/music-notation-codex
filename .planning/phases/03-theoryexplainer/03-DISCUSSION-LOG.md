# Phase 3: TheoryExplainer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-05
**Phase:** 03-theoryexplainer
**Areas discussed:** Explanation language, Trace grounding depth, Cello-specific cues, harmony_advisor CLI, Duet presets

---

## Explanation language

| Option | Description | Selected |
|--------|-------------|----------|
| English now (Recommended) | Explanation templates in English, Russian preset texts translated in this phase; matches locked "UI copy in English" | ✓ |
| Russian in v1 | Keep Russian, translate later; conflicts with locked decision at Phase 4 display time | |
| Bilingual | Store both languages; double content maintenance | |

**User's choice:** English now
**Notes:** User also requested using jdocmunch for doc reads during the session (Brain rule). Index does not cover `.planning/` — noted for later re-index.

### Sub-question: Russian source texts in presets

| Option | Description | Selected |
|--------|-------------|----------|
| Translate presets (Recommended) | Translate fields directly in core/presets — one language everywhere; goldens unaffected | ✓ |
| Keep Russian + English in explainer | Two theory sources; drift risk | |

### Sub-question: translation style

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite (Recommended) | Plain-language rework with jargon explained inline | |
| Literal translation | Faithful translation; jargon review becomes a separate pass | ✓ |

**Notes:** User explicitly rejected the rewrite recommendation — meaning preservation valued over immediate jargon cleanup.

### Sub-question: feel strings

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, everything (Recommended) | All preset text fields translated in one pass | ✓ |
| Theory fields only | feel stays Russian until UI phase | |

### Sub-question: jargon criterion gap

| Option | Description | Selected |
|--------|-------------|----------|
| Explanations in templates (Recommended) | Explainer templates gloss terms in parentheses on first use | |
| Review pass after | Assemble texts as-is, clean jargon in a separate pass driven by user's manual review | ✓ |
| Jargon acceptable | Soften the criterion (would require ROADMAP edit) | |

---

## Trace grounding depth (TRACE-02)

| Option | Description | Selected |
|--------|-------------|----------|
| 1–2 anchor sentences (Recommended) | Readable paragraph: preset theory + 1–2 sentences with real trace data; full breakdown is Phase 12 | ✓ |
| Per-bar breakdown | Richer but long; duplicates Phase 12 | |
| Separate field | Would change the Phase-1-locked 5-field dataclass | |

### Sub-question: anchor selection

| Option | Description | Selected |
|--------|-------------|----------|
| "Most salient" heuristic (Recommended) | Repeated low note → pedal tone; else first chord's tones + register; branch per IN-01; deterministic | ✓ |
| Fixed formula | Always first bar tones + register; predictable but can miss the interesting feature | |

### Sub-question: trace=None

| Option | Description | Selected |
|--------|-------------|----------|
| Clear error (Recommended) | explain() raises ValueError; TRACE-02 guaranteed by contract | ✓ |
| Degrade to preset text | Softer but silently violates TRACE-02 | |

---

## Cello-specific cues

| Option | Description | Selected |
|--------|-------------|----------|
| Bowing & articulation | legato/détaché, pizzicato, tremolo, accents | ✓ |
| Strings & positions | Which string/position, tied to trace register | |
| Looper workflow | Layer order, entering/exiting the loop, transitions via loop pedal | ✓ |
| Dynamics & effects | Volume arcs, reverb/distortion between sections | ✓ |

**User's choice:** Bowing/articulation + Looper workflow + Dynamics/effects (multi-select; strings/positions explicitly not selected)

### Sub-question: content source

| Option | Description | Selected |
|--------|-------------|----------|
| Templates + parameters (Recommended) | Shared cue library parameterized by preset/trace; new presets get guidance for free | ✓ |
| Hand-written per preset | 28 texts; every new preset needs manual work | |
| Hybrid | Templates + per-preset additions | |

### Sub-question: field mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Classic (Recommended) | progressions→why_it_works; modulations→how_to_transition; mood_tips→how_to_develop; start/end→new templates | ✓ |
| Free mixing | No fixed mapping; planner decides | |

---

## harmony_advisor CLI

| Option | Description | Selected |
|--------|-------------|----------|
| Generates + explains (Recommended) | CLI generates a variant via LoopEngine (--seed) and prints full TheoryExplanation with trace anchors; manual-review tool for criterion #2 | ✓ |
| Preset theory only | "Map of options" without generation/trace | |
| Both modes | Flag switches between quick reference and full explanation | |

---

## Duet presets

| Option | Description | Selected |
|--------|-------------|----------|
| Via duet cello part (Recommended) | Variant built from cello part of duet_bars via Phase 2's internal duet path; all 7 presets explainable | ✓ |
| Solo presets only in CLI | Duet presets covered only by unit test with hand-built variant | |
| Narrow the criterion | Restrict criterion #1 to solo presets (ROADMAP edit) | |

**Notes:** Fact confirmed during discussion: all 3 duet presets have 0 solo bars (`solo_bars=0, rhythm=0, duet=True`).

---

## Claude's Discretion

- Where English template/cue content lives (explainer.py vs separate data module in core/theory/)
- Explanation test strategy (offered as a gray area; user did not select it)
- API shape: explain(variant, preset) vs explain(variant) + lookup; class vs module functions (offered as a gray area; user did not select it)

## Deferred Ideas

- Goal-conditioned performance feedback ("we play to the advisor, it evaluates and advises toward what we want to achieve") — core capability exists as Phase 9 (FEEDBACK-01..04); the goal-conditioning nuance is broader than current requirements — surfaced by user via free-text during the final gate; noted for Phase 9 planning.
