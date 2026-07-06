# Phase 3: TheoryExplainer - Research

**Researched:** 2026-07-06
**Domain:** Template-driven plain-language text generation grounded in a structured trace object (no new external dependencies — pure Python)
**Confidence:** HIGH

## Summary

Phase 3 has no framework-discovery risk: it introduces zero new external packages. The
entire job is designing a maintainable, testable **template/strategy layer** inside
`core/theory/explainer.py` that (1) converts existing preset prose (`progressions`,
`modulations`, `mood_tips`) into `TheoryExplanation` fields, (2) generates two brand-new
fields (`how_to_start`, `how_to_end`) from a small cello/looper cue-template library
parameterized by preset characteristics, and (3) weaves 1-2 deterministic "anchor"
sentences from the variant's real `GenerationTrace` into `why_it_works`. All of this is
plain dataclasses/functions/dict-lookups — consistent with the codebase's established
"no exception hierarchies, no frameworks" convention (`01-PATTERNS.md`).

The two genuine design risks are (a) avoiding an unmaintainable if/elif chain across 7
presets as more moods are added, and (b) making the trace-anchor heuristic (D-05)
reproducible and unit-testable given that `chord_tones_used` has **two different shapes**
depending on `pattern_strategy` (the IN-01 contract in `core/models.py`). Both are solved
with a dict-keyed strategy table + small pure functions — no new library needed.

**Primary recommendation:** Build `explainer.py` as a set of small pure functions
(`explain(variant, preset) -> TheoryExplanation`) backed by a **cue-template registry**
(a plain dict or list of dataclasses keyed by tempo-band/meter/mood-word, not by preset
name), plus a `_select_anchor(trace) -> str` helper that branches once on
`trace.pattern_strategy` and is 100% unit-testable in isolation from text generation.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Preset prose → TheoryExplanation field mapping (D-09) | Core library (`core/theory/`) | — | Pure data transform; no I/O, no UI |
| Trace-anchor selection (D-05) | Core library (`core/theory/`) | Core models (`core/models.py` — trace shape contract) | Must read `GenerationTrace` per the IN-01 docstring; stays a pure function so Phase 12 can reuse the trace without re-deriving anchors |
| Cello/looper cue templates (D-07/D-08) | Core library (`core/theory/`) | Core presets (`core/presets/` — supplies tempo/meter/feel as template parameters) | Templates are data-driven off preset fields already defined in `MoodPreset`; no new tier needed |
| CLI presentation (D-10) | Scripts (`scripts/harmony_advisor.py`, thin wrapper) | Core engine (`core/engine/loop_engine.py` — variant generation) | CLI only orchestrates: generate variant → call explainer → print; no theory logic in the script itself (matches ARCHITECTURE.md's extraction rule) |
| Duet-preset explanation input (D-11) | Core engine (internal duet build path) | Core theory (`explainer.py` consumes the resulting variant/trace like any other) | Explainer does not need duet-specific code — it only needs a `LoopVariant` with a populated trace, regardless of how that variant was built |
| Length guard (SAFE-05) | Core library (`core/theory/`) | — | Must be enforced in code (truncation), not documentation, per SAFE-10 |

**Note:** No Streamlit/NiceGUI/browser tier is touched in this phase (Phase 4 is UI). No
new "explainer service" tier is warranted — `explain()` is a direct library call, matching
Phase 2's `generate_variant()` precedent (module-level function, not a class).

## Standard Stack

### Core
This phase requires **no new packages**. All work is plain Python 3.12+ standard library
(`dataclasses`, `textwrap`, `random` — already a transitive need via trace data) plus the
already-installed project stack.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| (stdlib only) | Python 3.12+ | dataclasses, string formatting, list/dict lookups | Matches project convention: `core/` has zero framework dependencies beyond music21/pychord, and this phase touches neither |

### Supporting
None. `music21` and `pychord` are not imported by `explainer.py` — `GenerationTrace` and
`MoodPreset` already expose everything needed as plain strings/tuples (verified by reading
`core/models.py` and `core/presets/mood_presets.py` directly).

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain f-string/`.format()` templates | Python `string.Template` or Jinja2 | Jinja2 is a new dependency for a project explicitly avoiding framework creep (`CLAUDE.md`: "keep it simple"); `string.Template` adds no value over f-strings for this phase's fixed, small template set. Reject both — no gettext-style i18n need exists (D-01 locks English-only) |
| Dict-keyed strategy table for cue templates | `if/elif` chain on preset name | Explicitly the anti-pattern this phase must avoid (research prompt item 1) — an if/elif chain does not scale as new moods are added and duplicates logic per preset |
| Dict-keyed strategy table for cue templates | Class hierarchy (`CueStrategy` ABC + subclasses per mood) | Overkill for a project with zero OOP elsewhere in `core/` (Phase 1 pattern: module-level functions, not classes) — rejected per Claude's Discretion note in CONTEXT.md ("class vs module-level functions (Phase 1 style)") |

**Installation:** None required — this phase adds zero lines to `requirements.txt`.

**Version verification:** N/A — no packages to verify.

## Package Legitimacy Audit

**Not applicable.** This phase installs zero external packages. No `pip install` / registry
lookups are required. Confirmed by reading `core/models.py`, `core/presets/mood_presets.py`,
`core/presets/registry.py`, `core/engine/loop_engine.py`, and `scripts/harmony_advisor.py` —
none import anything beyond the project's existing pinned stack (`music21`, `pychord`), and
`explainer.py` itself needs neither.

**Packages removed due to slopcheck [SLOP] verdict:** none (N/A — no packages proposed)
**Packages flagged as suspicious [SUS]:** none (N/A — no packages proposed)

## Architecture Patterns

### System Architecture Diagram

```
                    ┌────────────────────────────┐
                    │  scripts/harmony_advisor.py │   (D-10: thin wrapper)
                    │  --genre X [--seed N]        │
                    └──────────────┬───────────────┘
                                   │ 1. get_preset(genre)
                                   ▼
                    ┌────────────────────────────┐
                    │  core/presets/registry.py   │
                    └──────────────┬───────────────┘
                                   │ MoodPreset
                                   ▼
                    ┌────────────────────────────┐
                    │ core/engine/loop_engine.py  │
                    │  generate_variant(preset)   │   (solo presets)
                    │  OR internal duet build     │   (D-11: 3 duet presets,
                    │  path -> variant w/ trace   │    0 solo bars)
                    └──────────────┬───────────────┘
                                   │ LoopVariant (trace ALWAYS populated,
                                   │ Phase 2 D-01/D-02 seed policy)
                                   ▼
                    ┌─────────────────────────────────────────┐
                    │      core/theory/explainer.py            │
                    │                                          │
                    │  explain(variant, preset)                │
                    │    -> TheoryExplanation                  │
                    │                                          │
                    │  ┌──────────────────────────────────┐    │
                    │  │ 1. trace is None?  -> ValueError  │    │  (D-06)
                    │  └──────────────────────────────────┘    │
                    │  ┌──────────────────────────────────┐    │
                    │  │ 2. _select_anchor(trace)          │    │  (D-04/D-05)
                    │  │    branch on pattern_strategy:    │    │
                    │  │    - preset_verbatim: repeated    │    │
                    │  │      lowest note -> pedal tone;   │    │
                    │  │      else chord_tones + register  │    │
                    │  │    - progression_driven_...:      │    │
                    │  │      pitch classes + register_    │    │
                    │  │      choices (parallel list)      │    │
                    │  └──────────────────────────────────┘    │
                    │  ┌──────────────────────────────────┐    │
                    │  │ 3. why_it_works = preset.         │    │  (D-09)
                    │  │    progressions[0] + anchor(s)    │    │
                    │  │ 4. how_to_develop = mood_tips[0]  │    │
                    │  │ 5. how_to_transition = modula-    │    │
                    │  │    tions[0]                       │    │
                    │  │ 6. how_to_start/how_to_end =       │    │  (D-07/D-08)
                    │  │    CUE_TEMPLATES lookup keyed by   │    │
                    │  │    (tempo band, meter, feel words) │    │
                    │  └──────────────────────────────────┘    │
                    │  ┌──────────────────────────────────┐    │
                    │  │ 7. SAFE-05: truncate any field     │    │
                    │  │    exceeding 500 words             │    │
                    │  └──────────────────────────────────┘    │
                    └──────────────────┬───────────────────────┘
                                       │ TheoryExplanation (5 str fields)
                                       ▼
                    ┌────────────────────────────┐
                    │  scripts/harmony_advisor.py  │
                    │  prints all 5 fields +       │
                    │  trace anchor sentence(s)    │
                    └────────────────────────────┘
```

### Recommended Project Structure
```
core/
├── theory/
│   ├── __init__.py
│   ├── explainer.py        # explain(variant, preset) -> TheoryExplanation; _select_anchor()
│   └── cues.py             # CUE_TEMPLATES data + lookup helper (Claude's Discretion: separate
│                            # data module vs inline in explainer.py — recommend separate file,
│                            # mirrors core/presets/mood_presets.py + registry.py split already
│                            # established in this codebase)
tests/
└── test_explainer.py        # new — mirrors existing tests/test_*.py flat structure
```

### Pattern 1: Dict-keyed strategy table for cue templates (not if/elif)

**What:** A module-level dict (or list of small dataclasses) keyed by a small set of
discrete preset characteristics — e.g. `tempo_band` (slow/medium/fast, derived from
`tempo_bpm`), presence of specific words in `feel` (e.g. "dark", "ritual", "cinematic")
— mapping to template strings with `{}` placeholders filled from preset/trace data.

**When to use:** Every place D-08 requires "template-driven, not 28 hand-written texts."

**Example (illustrative, not prescriptive of exact wording):**
```python
# core/theory/cues.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CueTemplate:
    condition: str          # e.g. "slow", "fast", "default" — matched by a small pure function
    how_to_start: str
    how_to_end: str

# Keyed by tempo band, NOT by preset name -- new presets get guidance for free
# because they fall into an existing band without new code (D-08's core requirement).
TEMPO_BAND_CUES: dict[str, CueTemplate] = {
    "slow": CueTemplate(
        condition="slow",
        how_to_start=(
            "Start the loop pedal on the lowest note alone, played legato and let it "
            "ring before you record the layer — a slow tempo gives you room to settle "
            "the bow before the loop starts repeating."
        ),
        how_to_end=(
            "Fade the top layer's volume down first, then let the low note ring out "
            "and stop the loop on the downbeat — a slow ending reads as a held breath, "
            "not an abrupt cut."
        ),
    ),
    "fast": CueTemplate(
        condition="fast",
        how_to_start=(
            "Record the pulse layer first using short détaché strokes so the loop "
            "locks in tight before you add anything on top."
        ),
        how_to_end=(
            "Cut the loop cleanly on beat 1 rather than letting it trail — a fast "
            "groove needs a hard stop to read as an ending, not a dropout."
        ),
    ),
    "default": CueTemplate(
        condition="default",
        how_to_start="Start with the lowest voice alone, looped once before adding layers.",
        how_to_end="Bring the texture back down to the single low voice before stopping the loop.",
    ),
}

def tempo_band(tempo_bpm: int) -> str:
    if tempo_bpm < 70:
        return "slow"
    if tempo_bpm > 95:
        return "fast"
    return "default"
```
This pattern is idiomatic to the existing codebase (mirrors `_classify_register()` in
`core/engine/loop_engine.py`, which is exactly this "cheap discrete-bucket classifier"
pattern already used for `register_choices`).

### Pattern 2: Trace-anchor selection as an isolated, pure, testable function

**What:** `_select_anchor(trace: GenerationTrace) -> str` takes only a `GenerationTrace`
and returns a plain sentence fragment. It never touches `MoodPreset` or randomness — same
trace in, same string out, always. This directly satisfies D-05's "same seed → same text"
requirement, because the trace itself already contains everything derived from the seed
(the seed's randomness happened upstream in `loop_engine.py`; by the time `explain()` runs,
all inputs are frozen data).

**When to use:** For every `why_it_works` call (D-04/TRACE-02).

**Example (branch structure only — exact wording is a discretion call for the planner/executor):**
```python
def _select_anchor(trace: GenerationTrace) -> str:
    if trace is None:
        raise ValueError("TheoryExplanation requires a populated GenerationTrace (TRACE-02); got None.")

    if trace.pattern_strategy == "preset_verbatim":
        # chord_tones_used[i] is octave-bearing concrete pitches, e.g. ["C2", "C2", "G2", ...]
        lowest_per_bar = [min(bar, key=_octave_of) for bar in trace.chord_tones_used]
        if len(set(lowest_per_bar)) == 1:
            pedal = lowest_per_bar[0]
            return f"The repeated low {pedal} acts as a pedal tone anchoring the harmony above it."
        first_bar_tones = trace.chord_tones_used[0]
        register = trace.register_choices[0]
        return f"The line opens on {', '.join(first_bar_tones)} in the {register}."

    if trace.pattern_strategy == "progression_driven_register_mapped":
        # chord_tones_used[i] is octave-LESS pitch classes; register lives in register_choices
        first_bar_pitch_classes = trace.chord_tones_used[0]
        register = trace.register_choices[0]
        return f"The first bar draws on {', '.join(first_bar_pitch_classes)} placed in the {register}."

    # Defensive: IN-01 documents exactly these two strategies today. A third strategy
    # value would silently produce wrong anchors if not handled -- fail loudly instead.
    raise ValueError(f"Unknown pattern_strategy {trace.pattern_strategy!r}; cannot select an anchor.")
```
**Testability:** This function needs no `MoodPreset`, no music21, no randomness object —
just a `GenerationTrace` literal constructed in a test. Both IN-01 shapes can be
unit-tested directly by constructing two literal `GenerationTrace` instances (one per
strategy) without calling `generate_variant()` at all, which is faster and decouples the
anchor-selection test from LoopEngine's own test suite.

### Pattern 3: Field-mapping table matches D-09 exactly, expressed as a table not prose

**What:** Keep the D-09 mapping explicit and centralized as a single small function or
comment block, so a future reader can verify field provenance without re-deriving it from
scattered code:

| MoodPreset field | TheoryExplanation field | Notes |
|---|---|---|
| `progressions[0]` (+ anchor sentence(s)) | `why_it_works` | D-04/D-09 |
| `modulations[0]` | `how_to_transition` | D-09 |
| `mood_tips[0]` | `how_to_develop` | D-09 |
| (new template, keyed by tempo/meter/feel) | `how_to_start` | D-07/D-08/D-09 |
| (new template, keyed by tempo/meter/feel) | `how_to_end` | D-07/D-08/D-09 |

**Duet presets (D-11):** all 3 duet presets have `progressions=(), modulations=(),
mood_tips=()` (confirmed empty tuples in `core/presets/mood_presets.py`, lines 173-175,
214-216, 259-261 — inherited from "no GENRE_IDEAS-equivalent theory data source" per the
module's own docstring at line 159-160). **This means `why_it_works`/`how_to_transition`/
`how_to_develop` cannot follow the same `preset.progressions[0]` lookup for duet presets —
it will `IndexError` on an empty tuple.** The explainer must handle this case explicitly:
either (a) fall back to trace-anchor-only text for `why_it_works` when `progressions` is
empty, with a plain sentence acknowledging the duet context, or (b) raise a clear
`ValueError` if the phase's scope truly requires prose. Given D-11 explicitly commits
"Explanations therefore work for all 7 presets (criterion #1)," **option (a) is required**
— the planner must design a graceful empty-tuple fallback, not assume `progressions[0]`
always exists. This is the single most important pitfall this research surfaces (see
Common Pitfalls below).

### Anti-Patterns to Avoid
- **If/elif chain keyed by preset name:** Explicitly rejected by D-08 and the research
  prompt. Any code with `if preset.name == "dark_trip_hop": ... elif preset.name ==
  "ritual_tribal": ...` for cue text is the anti-pattern this phase exists to avoid.
- **Assuming `chord_tones_used[i]` is always octave-bearing:** IN-01 is explicit that this
  is FALSE for `progression_driven_register_mapped`. Code that does
  `pitch.Pitch(chord_tones_used[0][0]).octave` without checking `pattern_strategy` first
  will crash (`progression_driven_register_mapped` tones are octave-less pitch classes
  like `"A"`, not `"A2"`).
- **Hand-written text per preset (28 texts):** D-08 explicitly rules this out — it does
  not scale and new presets get zero guidance until manually authored.
- **Silent `trace=None` degradation:** D-06 requires a loud `ValueError`, matching
  Phase 1's validator convention (no silent fallback to preset-only text).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| String templating with placeholders | A custom mini-template engine | Python f-strings / `.format()` | Templates here are small, fixed, and known at write-time — no user-supplied template strings exist, so no injection/escaping concern justifies a library |
| Word-count truncation (SAFE-05) | Regex-based sentence-boundary truncation | `str.split()` + `" ".join(words[:500])` | The requirement is a hard word-count cap, not "truncate at a sentence boundary" — simplest correct implementation wins; no NLP library needed |
| Detecting "does this text still contain Cyrillic" (test strategy, Claude's Discretion) | A language-detection library (langdetect, langid) | `re.search(r'[а-яА-ЯёЁ]', text)` or `str.isascii()` on the field | The check is binary (any Cyrillic char present, yes/no), not language classification — a full detection library is unjustified overhead for a 5-field dataclass check |

**Key insight:** Every "don't hand-roll" temptation in this phase points toward reaching
for a library that solves a more general problem than what's actually needed. The
project's existing convention (plain functions, no exception hierarchies, no frameworks)
is the correct fit for a fixed, small, well-understood template set — reaching for Jinja2,
a template-engine, or an NLP library would violate `CLAUDE.md`'s "keep it simple" directive
and Claude's Discretion note about staying idiomatic to the existing style.

## Common Pitfalls

### Pitfall 1: Empty-tuple `progressions`/`modulations`/`mood_tips` for duet presets crashes naive field mapping
**What goes wrong:** Code that does `preset.progressions[0]` unconditionally raises
`IndexError` for `sexy_duet`, `simple_sexy_duet`, `dorian_sexy_duet` (all three have empty
tuples — confirmed by direct inspection of `mood_presets.py`).
**Why it happens:** The 4 solo presets all have non-empty `progressions`/`modulations`/
`mood_tips` (2-3 items each), so a planner/executor working from the 4 solo presets first
may not hit this until testing against duet presets, if at all.
**How to avoid:** Explicitly branch on `not preset.progressions` (etc.) in the field-mapping
code and substitute a trace-anchor-only sentence or an explicit generic sentence
acknowledging the duet source ("This duet line leans on the cello part's own
register/pedal-tone anchor below.") for the empty case. Write a unit test that calls
`explain()` against all 3 duet presets specifically (not just the 4 solo ones) to catch
regressions.
**Warning signs:** Any test suite that only exercises `dark_trip_hop`/`ritual_tribal`/
`noir_slow_burn`/`driving_cinematic` will pass while `sexy_duet` etc. crash at CLI runtime
— this is exactly the coverage gap D-11 calls out ("Explanations therefore work for all 7
presets") as a phase success criterion.

### Pitfall 2: IN-01 shape confusion breaks anchor selection silently (wrong text, not a crash)
**What goes wrong:** If anchor-selection code assumes `chord_tones_used` is always
concrete octave-bearing pitches (as it is for `preset_verbatim`), the
`progression_driven_register_mapped` strategy's pitch-class-only tones (e.g. `"A"`
instead of `"A2"`) either crash on `pitch.Pitch(x).octave` calls or, worse, silently
produce a confusing sentence like "the repeated low A" when no octave/register
information was actually available in that list at all — the register lives in the
*separate* `register_choices` list for this strategy.
**Why it happens:** Both strategies use the same dataclass field name
(`chord_tones_used`), so it's easy to write code that "just works" against whichever
strategy was tested first and quietly produces wrong (not crashing) output against the
other.
**How to avoid:** Branch explicitly on `trace.pattern_strategy` as the *first* line of
`_select_anchor()` (see Pattern 2 above) — never infer the shape from the data itself.
Write one unit test per strategy using literal `GenerationTrace` construction (not real
generation) so both shapes are exercised independently and deterministically.
**Warning signs:** A test suite that only constructs traces via `generate_variant()` (solo
path) will never exercise the `progression_driven_register_mapped` branch of the anchor
selector at all.

### Pitfall 3: `voice_leading_steps` is always `None` — don't reference it
**What goes wrong:** A template or anchor sentence that assumes `voice_leading_steps` has
data (e.g. "the line moves by a smooth half-step") will crash or degrade to `None`/empty
text, because both current strategies leave this field `None` (confirmed in
`loop_engine.py` — both `generate_variant()` and `generate_variant_from_progression()`
explicitly set `voice_leading_steps=None` with an inline comment marking it a future
concern).
**Why it happens:** The field exists in the dataclass and looks like it should be usable;
without re-reading `loop_engine.py` directly it's easy to assume it's populated.
**How to avoid:** Constrain all anchor/cue text to only reference `chord_tones_used` and
`register_choices`, matching the explicit constraint already noted in CONTEXT.md.
**Warning signs:** Any explanation text mentioning "voice leading," "smooth motion between
notes," or similar phrasing not backed by actual trace data.

### Pitfall 4: SAFE-05 truncation must be enforced in the explainer, not assumed elsewhere
**What goes wrong:** No other layer (LoopEngine, CLI, future UI) currently enforces a
word-count cap on explanation text; if `explainer.py` doesn't enforce SAFE-05 itself, the
requirement silently goes unmet — and it's an explicit SAFE guard requiring code
enforcement (SAFE-10: "Hard numeric guards are enforced in code... comments can be
ignored, code cannot").
**Why it happens:** SAFE-05 is easy to treat as "obviously satisfied" because templates are
short by construction — but the guard is a REQUIREMENT with its own roadmap traceability
row, not just a design intention, and must be independently testable (e.g. a test that
constructs an artificially long preset/trace combination and asserts the output field is
capped at 500 words).
**How to avoid:** Add an explicit truncation step at the end of `explain()` (or a small
`_enforce_word_limit(text: str) -> str` helper) applied to all 5 fields, with a dedicated
unit test.
**Warning signs:** SAFE-05 has no corresponding test in the plan.

### Pitfall 5: Tone/register mismatch between translated preset prose and new template prose
**What goes wrong:** The already-completed translation (D-02, done 2026-07-06) was
explicitly **faithful/literal**, not a rewrite — so `progressions`/`modulations`/
`mood_tips` may retain source-language sentence structure or more "textbook" theory
phrasing (e.g. "Works because the low tonic holds the hypnotic pull, VI adds dark warmth")
alongside this phase's brand-new, more casual, cello-practice-oriented template text (e.g.
"Start the loop pedal on the lowest note alone"). A cellist reading both back to back may
notice an abrupt register shift in tone.
**Why it happens:** The two text sources were authored at different times, by different
processes (literal translation vs. new template authorship this phase), for different
original purposes (a print-CLI's "harmonic development options" vs. this phase's
practice-guidance framing).
**How to avoid:** This is explicitly NOT this phase's job to fix (D-03: jargon cleanup is
a separate review pass after the user's manual review). However, the CLI wrapper (D-10)
should be structured so the user's manual review (success criterion #2, ≥4 presets) can
easily *see* this tone mismatch when reading full output side-by-side — i.e., print all 5
fields together per preset, not just the new fields, so the review surfaces the seam.
Document this explicitly as an item to flag during that checkpoint, not silently paper
over it with extra editorializing in the new templates.
**Warning signs:** If planner writes new template text that tries to "match" the more
literary tone of the translated preset prose (rather than staying in a distinct,
consistently practical/cello-practice register), the review checkpoint may not surface the
seam at all — losing the signal D-03 depends on.

## Code Examples

### Field-mapping happy path (solo preset, e.g. `dark_trip_hop`)
```python
# Illustrative -- exact wording/logic is for the planner/executor to finalize.
def explain(variant: LoopVariant, preset: MoodPreset) -> TheoryExplanation:
    if variant.trace is None:
        raise ValueError(
            f"Cannot explain variant {variant.id!r}: no GenerationTrace present (TRACE-02 "
            "requires trace-grounded explanations)."
        )

    anchor = _select_anchor(variant.trace)
    why_it_works = _first_or_fallback(preset.progressions, anchor)
    how_to_transition = _first_or_fallback(preset.modulations, _default_transition_cue(preset))
    how_to_develop = _first_or_fallback(preset.mood_tips, _default_develop_cue(preset))
    how_to_start, how_to_end = _cue_pair_for(preset)

    return TheoryExplanation(
        why_it_works=_enforce_word_limit(f"{why_it_works} {anchor}"),
        how_to_start=_enforce_word_limit(how_to_start),
        how_to_develop=_enforce_word_limit(how_to_develop),
        how_to_end=_enforce_word_limit(how_to_end),
        how_to_transition=_enforce_word_limit(how_to_transition),
    )
```

### Duet-preset empty-tuple guard (Pitfall 1)
```python
def _first_or_fallback(items: tuple[str, ...], fallback: str) -> str:
    """D-11: duet presets have empty progressions/modulations/mood_tips tuples --
    fall back to a generic, still-honest sentence rather than IndexError."""
    return items[0] if items else fallback
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `scripts/harmony_advisor.py` prints `GENRE_IDEAS` dict values via `print_section()` | `core/theory/explainer.py` returns structured `TheoryExplanation` dataclass; CLI is a thin printer | This phase (Phase 3) | Enables Phase 4 (UI) to consume the same structured data without any script refactor; enables Phase 12 to reuse trace data |
| Theory text hand-written per genre (4 GENRE_IDEAS entries, no duet coverage) | Trace-grounded + template-driven, covering all 7 presets including 3 duets | This phase | Directly satisfies success criterion #1 (all 7 presets) which the old script could not do (duets had no `GENRE_IDEAS` entry at all) |

**Deprecated/outdated:**
- `harmony_advisor.py`'s `print_section()`/`main()` structure: superseded per
  ARCHITECTURE.md ("`main()`/`print_section()` deleted from the script" — though CONTEXT.md
  D-10 clarifies the CLI itself is kept as a thin wrapper generating + printing, so
  `print_section` as a *pure printing helper* may still have a role; the *data-holding*
  logic (`GENRE_IDEAS` dict, `print_section` iterating over raw preset lists) is what's
  superseded, not necessarily every line of the CLI).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The planner should key cue templates by discrete bands (tempo_band, meter, feel-keyword) rather than any other discretization scheme | Architecture Patterns, Pattern 1 | Low — this is offered as one valid idiomatic approach (mirrors existing `_classify_register()` pattern), not the only correct one; CONTEXT.md leaves "where template content lives" and exact strategy shape to Claude's Discretion |
| A2 | Exact English phrasing shown in Code Examples / Pattern 1 and Pattern 2 is illustrative only | Architecture Patterns | Low — explicitly labeled as illustrative; the planner/executor must write final copy meeting the "no unexplained jargon" criterion, ideally validated against a cellist's actual vocabulary during the D-10 CLI review checkpoint |
| A3 | `IndexError` (not a different exception) is what naive `preset.progressions[0]` raises on an empty tuple, and this must be guarded explicitly for duet presets | Common Pitfalls, Pitfall 1 | Low — verified directly by reading `core/presets/mood_presets.py` (empty tuples for exactly the 3 duet preset names) and Python tuple-indexing semantics; this is a direct code-reading fact, not training-data speculation, so it is effectively VERIFIED despite the ASSUMED tag (kept here only because it foreshadows an execution-time behavior, not a pre-run test) |

**If this table is empty:** N/A — table is populated above; all three entries are low-risk
clarifications rather than compliance/security/performance claims requiring user
confirmation.

## Open Questions

1. **Exact word-count enforcement granularity for SAFE-05**
   - What we know: SAFE-05 requires each explanation field truncated at 500 words; "per
     explanation field" is explicit in REQUIREMENTS.md.
   - What's unclear: Whether truncation should happen inside `explain()` (guaranteeing the
     dataclass invariant always holds) or as a separate validator function callable
     independently (matching the `validate_pitch`/`validate_bar_duration` pattern from
     Phase 1).
   - Recommendation: Follow the Phase 1 precedent — a small dedicated function (e.g.
     `_enforce_word_limit` or a `core/theory/validators.py` mirroring
     `core/engine/validators.py`) called at the end of `explain()`, unit-tested
     independently with a deliberately-long fixture string. This keeps the same
     "explicit validator function, plain ValueError-free enforcement (truncation, not
     rejection)" shape already established.

2. **API shape: `explain(variant, preset)` vs `explain(variant)` + internal registry lookup**
   - What we know: CONTEXT.md explicitly defers this to Claude's Discretion. `LoopVariant`
     carries `preset_name: str` but not the `MoodPreset` object itself.
   - What's unclear: Whether the explainer should re-look-up the preset via
     `get_preset(variant.preset_name)` internally (fewer call-site arguments, but couples
     `explainer.py` to `core.presets.registry`) or require the caller to pass both
     (explicit, no coupling, matches how `harmony_advisor.py`'s CLI already has the preset
     in hand from its own `get_preset()` call).
   - Recommendation: Prefer `explain(variant: LoopVariant, preset: MoodPreset)` (explicit
     two-argument form). It avoids a second registry dependency inside `core/theory/` and
     matches the CLI's natural flow (D-10: CLI already calls `get_preset()` before
     `generate_variant()`), so no extra lookup is needed at the call site either.

## Environment Availability

Skipped — this phase has no external dependencies beyond the already-installed Python
3.12+ interpreter and the existing pinned stack (`music21`, `pychord`), neither of which
`explainer.py` itself imports. No new CLI tools, services, or runtimes are introduced.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (config in `pytest.ini`, already installed in `.venv`) |
| Config file | `pytest.ini` |
| Quick run command | `.venv/bin/python3 -m pytest tests/test_explainer.py -q` |
| Full suite command | `.venv/bin/python3 -m pytest tests/ -q` |
| Current full-suite baseline | 101 passed, 1 warning (pre-existing D-07 legacy-note warning), ~4.15s — verified by running the suite during this research session |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| THEORY-01 | `explain()` returns non-empty `why_it_works` for all 7 presets; text contains no unexplained jargon markers (heuristic: no bare theory terms like "pedal tone"/"modulation" without an inline plain-language gloss — assertable via a small allow-list of terms requiring a companion explanation phrase) | unit | `pytest tests/test_explainer.py -k why_it_works -q` | ❌ Wave 0 |
| THEORY-01 | Manual jargon review of ≥4 presets via refactored CLI (success criterion #2) | manual | `python3 scripts/harmony_advisor.py --genre <name> [--seed N]` for ≥4 presets | ❌ Wave 0 (CLI refactor) |
| THEORY-02 | `explain()` returns non-empty `how_to_start`/`how_to_develop`/`how_to_end`/`how_to_transition` for all 7 presets (incl. 3 duet presets with empty source tuples — Pitfall 1) | unit | `pytest tests/test_explainer.py -k "all_five_fields or all_seven_presets" -q` | ❌ Wave 0 |
| TRACE-02 | `why_it_works` contains the actual anchor text derived from a given `GenerationTrace` (not generic boilerplate) — assert anchor substring appears in output for both `preset_verbatim` and `progression_driven_register_mapped` literal trace fixtures | unit | `pytest tests/test_explainer.py -k anchor -q` | ❌ Wave 0 |
| TRACE-02 | `trace=None` raises plain `ValueError` (D-06) | unit | `pytest tests/test_explainer.py -k trace_none -q` | ❌ Wave 0 |
| TRACE-02 | Same seed -> same `why_it_works` text (D-05 determinism) — generate the same preset+seed twice via `generate_variant()`, assert identical `explain()` output | unit | `pytest tests/test_explainer.py -k reproducib -q` | ❌ Wave 0 |
| SAFE-05 | Any explanation field is truncated at 500 words even when template/preset input would exceed it | unit | `pytest tests/test_explainer.py -k word_limit -q` | ❌ Wave 0 |
| D-02 verification | Golden regression suite stays green after preset text translation (confirms text-only changes didn't touch MusicXML/MIDI) | regression | `pytest tests/test_golden_regression.py -q` | ✅ (pre-existing; already green per STATE.md) |

### Sampling Rate
- **Per task commit:** `.venv/bin/python3 -m pytest tests/test_explainer.py -q`
- **Per wave merge:** `.venv/bin/python3 -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`; plus the manual CLI jargon
  review (success criterion #2) signed off separately, since it cannot be automated
  (subjective language-clarity judgment, same category as Phase 2.5's "ear-check").

### Wave 0 Gaps
- [ ] `tests/test_explainer.py` — new test file; no existing coverage for `core/theory/`
      (the directory doesn't exist yet)
- [ ] `core/theory/__init__.py`, `core/theory/explainer.py`, `core/theory/cues.py` (or
      equivalent) — module scaffolding
- [ ] No new pytest fixtures needed beyond what `tests/conftest.py` already provides
      (`tolerance` fixture is unrelated to this phase; literal `GenerationTrace`/
      `MoodPreset` construction can happen inline per test, matching the style already used
      in `tests/test_loop_engine.py`)

*(Framework itself needs no install — pytest is already present and configured.)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local single-user desktop tool; no auth surface in this phase |
| V3 Session Management | no | No session state introduced by this phase (pure function, no persistence) |
| V4 Access Control | no | No access boundaries in this phase |
| V5 Input Validation | yes | `trace=None` -> `ValueError` (D-06); SAFE-05 word-count truncation is itself an output-bounding control, not input validation per se, but follows the same "enforce in code" principle (SAFE-10) |
| V6 Cryptography | no | No secrets, no crypto surface |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unbounded text length (wall-of-text) from a pathological trace/preset combination | Denial of Service (resource/UX) | SAFE-05: hard 500-word cap enforced in code on every `TheoryExplanation` field, independent of input size |
| `IndexError` from empty preset tuples (duet presets) surfacing as an unhandled crash to the CLI/future UI | Denial of Service (availability) | Explicit `_first_or_fallback()`-style guard (Pitfall 1) rather than raw `tuple[0]` indexing; covered by a dedicated unit test against all 3 duet presets |
| `AttributeError`/`IndexError` from mis-branching on `pattern_strategy` (IN-01 shape confusion) crashing at explanation time | Denial of Service (availability) / Tampering (wrong data surfaced with high confidence) | Explicit strategy branch with a final `else: raise ValueError(f"Unknown pattern_strategy...")` (Pattern 2) rather than duck-typing the trace shape |

This phase has no network/file/credential attack surface — the ASVS categories that do
apply are output-bounding (SAFE-05) and input-contract enforcement (D-06), both already
covered by the codebase's existing "plain ValueError, no silent degradation" convention.

## Sources

### Primary (HIGH confidence)
- Direct code inspection (this session, 2026-07-06): `core/models.py`, `core/presets/mood_presets.py`, `core/presets/registry.py`, `core/engine/loop_engine.py`, `core/engine/progression.py`, `scripts/harmony_advisor.py`, `.planning/config.json`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/research/ARCHITECTURE.md`, `.planning/phases/03-theoryexplainer/03-CONTEXT.md`, `.planning/phases/01-core-library-skeleton-validators/01-VALIDATION.md`, `.planning/phases/01-core-library-skeleton-validators/01-PATTERNS.md`, `.planning/phases/02.5-progression-driven-generation/02.5-VALIDATION.md`
- Direct command execution (this session): `.venv/bin/python -m pytest tests/ -q` — confirmed 101 passed, 1 warning, ~4.15s baseline

### Secondary (MEDIUM confidence)
- [Beginner's Guide to Pedal Point & Pedal Tones](https://littleredpiano.com/pedal-in-music/) — cross-checked plain-language pedal-tone phrasing against Wikipedia's definition; consistent
- [Pedal tone - Wikipedia](https://en.wikipedia.org/wiki/Pedal_tone) — confirms "sustained note while harmony changes above it" as the core, jargon-free definition
- [Live looping - Wikipedia](https://en.wikipedia.org/wiki/Live_looping) — confirms "layering," "overdub," "clear/undo" as standard, correctly-used looper-pedal vocabulary (matches D-07's requested cue types)
- [The Complete Guide to Loop Pedals for Beginners - BOSS Articles](https://articles.boss.info/the-complete-guide-to-loop-pedals-for-beginners/) — corroborates overdub/layering terminology from a manufacturer's own beginner guide

### Tertiary (LOW confidence)
- None — all WebSearch findings above were cross-verified across ≥2 independent sources (Wikipedia + at least one guitar/looper-industry guide) before inclusion.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages, entirely verified by direct code inspection (no external claim to hedge)
- Architecture: HIGH — directly derived from locked CONTEXT.md decisions (D-04 through D-11) plus direct reading of `core/models.py`'s IN-01 docstring and `loop_engine.py`'s actual trace-population code
- Pitfalls: HIGH — Pitfalls 1-4 are derived from direct inspection of actual data (empty tuples, `voice_leading_steps=None`, SAFE-05's explicit roadmap requirement) rather than speculation; Pitfall 5 (tone mismatch) is a reasoned inference flagged appropriately as a review-process risk, not a code-verifiable fact

**Research date:** 2026-07-06
**Valid until:** No expiration risk — this phase introduces no new external dependencies whose APIs could drift; research is valid as long as `core/models.py`'s `GenerationTrace`/`TheoryExplanation` shapes and `core/presets/mood_presets.py`'s data remain unchanged (i.e., valid indefinitely unless Phase 1/2/2.5 locked decisions are revisited).
