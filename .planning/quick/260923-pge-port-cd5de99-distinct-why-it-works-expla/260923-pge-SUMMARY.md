---
quick_id: 260923-pge
status: complete
commits: [240d49e, 2f2dc80, 4b96119, b205330]
---

# Summary

- **LOOP-02 engine:** register-bias octave pools overlap and the pick is random, so takes collided (135 pairs / 960 sets; 122 on single-chord C, Em). `generate_variants` now re-draws a colliding take (seed `base + i*1000 + k`, k < 50) and records the seed used. Already-distinct takes keep their seed. Wide corpus: 0 collisions.
- **VAR-01 explainer:** `_Take` built from `played_pitches` adds outline (opening/closing/span/most repeated), bar-entry phrase, last bar, hand-off and span hint. Long why_it_works writes each bar's played notes out, so it always differs when notes differ. `written_name()` prints `B-2` as `Bb2` and keeps the written octave; applied to shape and seam sentences too.
- **Known limits:** cards may still match for takes that differ only by one inner octave (24 of 2880 pairs). End/transition cards match when takes share their opening and closing notes (honest: same ending).
- **Tests:** 1171 → 1286 passed.
