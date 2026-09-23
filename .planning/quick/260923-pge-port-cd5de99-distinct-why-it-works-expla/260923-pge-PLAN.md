---
quick_id: 260923-pge
type: quick
---

# Port cd5de99: distinct explanation per generated take

Scope decided after investigation (cd5de99's `realized_pitches` already exists as `GenerationTrace.played_pitches`):

1. LOOP-02 (engine): takes low/default/high must never play identical notes — test first, then re-draw a colliding take from neighbouring seeds in its own block; trace.seed records the seed actually used.
2. VAR-01 (explainer): lead why_it_works / how_to_develop / how_to_end / how_to_transition (long text and cards) with clauses built from `played_pitches`; print flats as `b` (SPELL-01, written octave kept) — test first.
