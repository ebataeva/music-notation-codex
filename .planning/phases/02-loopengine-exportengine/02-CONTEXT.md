# Phase 2: LoopEngine + ExportEngine - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning

<domain>
## Phase Boundary

The generation logic from the CLI generator scripts moves into `core/engine/loop_engine.py` and `core/export/exporter.py`; the scripts become thin wrappers (argparse + core call + print). A single cello loop variant can be generated and exported entirely from pure-Python code, with an explicit seed policy and a fully populated GenerationTrace. Scripts keep producing byte-identical output (golden regression from Phase 1 stays green). No progression parsing (Phase 2.5), no theory explanations (Phase 3), no Streamlit (Phase 4+).

</domain>

<decisions>
## Implementation Decisions

### Seed policy
- **D-01:** RNG plumbing is introduced NOW: the engine accepts a seed, constructs `random.Random(seed)`, and passes it to generation strategies — even though the current preset-verbatim strategy is deterministic and won't use it. Phase 2.5 starts consuming the RNG without any interface change.
- **D-02:** When no seed is given, the engine generates a random seed itself and ALWAYS records it in GenerationTrace. `trace.seed` is never None — every result is reproducible post-hoc (blog, debugging, caching).
- **D-03:** The CLI wrapper gets an optional `--seed` flag; default behavior unchanged (golden tests unaffected).
- **D-04:** GenerationTrace is populated honestly and fully even for the deterministic strategy: `pattern_strategy` set to a "preset_verbatim"-style identifier; `register_choices` and `chord_tones_used` computed per-bar from the actual preset notes. TheoryExplainer (Phase 3) gets real data from day one.

### Engine API
- **D-05:** Two API levels: a low-level `build_score(preset, ...)` → `music21 Score` (matches success criterion 1) and a high-level `generate_variant(...)` → `LoopVariant` with populated trace. Phases 3/4/7 consume LoopVariant; the low level stays independently testable.
- **D-06:** Phase 1 validators (`validate_pitch`, `validate_bar_duration`) are called INSIDE the engine during score assembly — LOOP-03/LOOP-04 "validated at generation time" holds automatically for every caller.
- **D-07:** Legacy note A1 in the dark_trip_hop preset (below C2, must survive for byte-identity): per-preset exception mechanism — the engine skips known legacy deviations with a warning recorded in the trace; output stays byte-identical; new generation (Phase 2.5) validates strictly with no exceptions.

### Export policy
- **D-08:** ExportEngine takes a configurable base directory (default: `scores/` at project root) with `musicxml/` and `midi/` subdirectories. Wrappers pass the default → identical output; Phase 6 (Export Panel) can point it at temp dirs.
- **D-09:** Export returns paths of written files. `svg_bytes`/`midi_bytes` fields on LoopVariant stay None until Phases 5–6 where they're actually needed.
- **D-10:** Existing files are silently overwritten (current behavior; single-user local tool; results reproducible by seed).

### Wrapper scope + review fixes
- **D-11:** ALL FOUR generator scripts become thin wrappers in this phase: `generate_cello_dark_ostinato.py` plus the three duet generators. `harmony_advisor.py` waits for Phase 3 (TheoryExplainer).
- **D-12:** Thin wrapper = `parse_args()` + core calls + printing results. No music21 logic remains in `scripts/`.
- **D-13:** Two-part (cello+violin) score assembly moves into core as an INTERNAL path only — needed so duet wrappers stay thin and byte-identical — but it is NOT exposed as public engine API. `generate_variant()` stays cello-only. DUET-01 remains v2.
- **D-14:** Phase 1 review warnings fixed in this phase (all verified not to affect golden output files):
  - **WR-01:** solo CLI `choices` filtered to presets that actually have solo data (no more silent empty exports for `--genre sexy_duet`).
  - **WR-04:** `environment.Environment()["warnings"] = 0` instead of `environment.UserSettings()` — stop rewriting the user's global `~/.music21rc` on every run.
  - **WR-02/WR-03:** validator holes closed — `validate_pitch` rejects octave-less pitch names and wraps `PitchException` into the documented `ValueError` contract; `validate_bar_duration` rejects non-positive durations.

### Claude's Discretion
- Where the seed lives in the API (engine method parameter vs. a `seed` field added to `GenerationRequest`) — pick during planning; user explicitly delegated.
- Classes (`LoopEngine`/`ExportEngine` per ROADMAP wording) vs. module-level functions (Phase 1 style) — pick what fits; success criteria wording uses class style but the user delegated the call.
- Exact naming of the per-preset legacy-exception mechanism and the "preset_verbatim" strategy identifier.
- WR-05 (frozen MoodPreset aliasing mutable globals) was not selected for this phase — treat as known, non-blocking.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & refactor plan
- `.planning/research/ARCHITECTURE.md` — LoopEngine/ExportEngine responsibilities, extraction map for `generate_cello_dark_ostinato.py` (§Refactoring the Existing CLI Scripts), import-boundary rule (no streamlit below `app/`, no argparse in `core/`)
- `.planning/research/PITFALLS.md` — validator reference implementations (relevant to WR-02/03 fixes)

### Phase 1 outputs (this phase builds directly on them)
- `.planning/phases/01-core-library-skeleton-validators/01-CONTEXT.md` — locked dataclass shapes, golden-regression rules, boundaries
- `.planning/phases/01-core-library-skeleton-validators/01-REVIEW.md` — WR-01…WR-05 with verified fix recipes (WR-01, WR-02, WR-03, WR-04 are in scope for this phase)
- `.planning/phases/01-core-library-skeleton-validators/01-PATTERNS.md` — established code conventions (simple functions, no custom exceptions in registry)

### Source material (brownfield)
- `scripts/generate_cello_dark_ostinato.py` — `build_cello_ostinato()` + `export_score()` to extract
- `scripts/generate_sexy_duet_loop.py`, `scripts/generate_simple_sexy_duet_loop.py`, `scripts/generate_dorian_sexy_duet_loop.py` — two-part score assembly to extract as internal core path
- `core/models.py` — GenerationTrace/LoopVariant/MoodPreset shapes (locked in Phase 1)
- `core/engine/validators.py` — validate_pitch/validate_bar_duration to be called from the engine and hardened (WR-02/03)
- `tests/test_golden_regression.py` + `tests/golden/baseline_hashes.json` — byte-identity guard that must stay green

### Stack
- `CLAUDE.md` — locked project constraints (music21 10.5.0, English comments only where non-obvious)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `core/presets/registry.py` (`get_preset`, `list_presets`): engine's preset source; WR-01 fix needs a way to distinguish solo-capable presets (e.g. non-empty `bars`/`rhythm`)
- `core/engine/validators.py`: called from inside the engine (D-06) after WR-02/03 hardening
- `core/models.py` dataclasses: `LoopVariant.trace` field already exists and defaults to None — engine starts populating it
- `tests/` pytest scaffold + golden hashes: extend with engine/export unit tests; golden suite is the refactor safety net

### Established Patterns
- Simple module-level functions without custom exception types (01-PATTERNS.md) — natural `ValueError` propagation
- `zip(strict=True)` for bars/rhythm pairing in the existing build logic — preserve
- Scripts use `sys.path.insert` bootstrap to import `core` — wrappers keep this

### Integration Points
- `scripts/*.py` → `core/engine/loop_engine.py` + `core/export/exporter.py` (the extraction itself)
- Phase 2.5 will extend LoopEngine with progression-driven strategies consuming the seeded `random.Random`
- Phase 3 TheoryExplainer will read `LoopVariant.trace` — trace fidelity (D-04) is its input contract

</code_context>

<specifics>
## Specific Ideas

- Current generation is fully deterministic (no `random` usage anywhere) — "same seed → same variant" is trivially true in Phase 2; the seed plumbing is deliberately "on growth" for Phase 2.5.
- The golden regression suite currently rewrites `~/.music21rc` 14 times per pytest session via subprocess side effect (WR-04) — fixing this also cleans up the test run.

</specifics>

<deferred>
## Deferred Ideas

- WR-05 (frozen MoodPreset false immutability / shared mutable globals) — reviewed, not selected for this phase; revisit if it bites
- Duet generation as a public feature (InstrumentSet parameter in the engine API) — v2 (DUET-01); Phase 2 only carries the internal two-part assembly path for wrapper byte-identity
- `harmony_advisor.py` refactor — Phase 3 (TheoryExplainer)
- Unique/timestamped export filenames and persistence — Phase 10 (Loop Library) handles history properly

</deferred>

---

*Phase: 02-loopengine-exportengine*
*Context gathered: 2026-07-04*
