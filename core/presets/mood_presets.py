"""MOOD_PRESETS registry: merged data from all 5 pre-existing CLI scripts.

Source of truth for Phase 2's LoopEngine and Phase 3's TheoryExplainer
(ARCHITECTURE.md Pattern 2). Data below was originally migrated verbatim from:

- scripts/generate_cello_dark_ostinato.py (GENRE_PRESETS: tempo/key/rhythm/bars/feel
  for 4 solo moods)
- scripts/harmony_advisor.py (GENRE_IDEAS: progressions/modulations/mood -> mood_tips
  for the same 4 moods)
- scripts/generate_sexy_duet_loop.py, generate_simple_sexy_duet_loop.py,
  generate_dorian_sexy_duet_loop.py (3 standalone duet presets, each with
  per-instrument duet_rhythm/duet_bars)

Musical data (pitches/rhythms) is unchanged from the source scripts; the
originally-Russian prose (feel, progressions, modulations, mood_tips) was
translated to English 2026-07-06 (PLAT-02: all UI-facing copy in English —
Phase 3's TheoryExplainer feeds this prose into TheoryExplanation for
rendering). Pre-existing out-of-range notes still migrate verbatim, not
silently fixed (see the "A1" note below).
"""

from __future__ import annotations

from core.models import MoodPreset

MOOD_PRESETS: dict[str, MoodPreset] = {
    "dark_trip_hop": MoodPreset(
        name="dark_trip_hop",
        tempo_bpm=72,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=76,
        rhythm=(0.5,) * 8,
        bars=(
            ("C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"),
            ("C2", "C2", "G2", "Bb2", "C3", "Bb2", "G2", "Eb2"),
            ("Ab2", "Ab2", "Eb3", "G3", "Ab3", "G3", "Eb3", "C3"),
            ("G2", "G2", "D3", "F3", "G3", "F3", "D3", "Bb2"),
            ("C2", "C2", "G2", "Bb2", "C3", "G2", "Eb2", "G2"),
            ("Eb2", "Eb2", "Bb2", "C3", "Eb3", "C3", "Bb2", "G2"),
            ("F2", "F2", "C3", "Eb3", "F3", "Eb3", "C3", "Ab2"),
            ("G2", "G2", "D3", "F3", "G3", "F3", "D3", "C2"),
        ),
        feel="dark, sexy, loopy trip-hop groove",
        progressions=(
            "i - VI - v - i: C minor -> Ab -> G minor -> C minor. Works because the low tonic holds the hypnotic pull, VI adds dark warmth, and v brings it back without an overly bright classical resolution.",
            "i - bVII - VI - V: C minor -> Bb -> Ab -> G. Works as a downward descent: a feeling of seduction, danger, and inevitable return.",
        ),
        modulations=(
            "Via a common chord: C minor -> Eb major. Eb major is the relative major, so the transition is soft, but the light turns colder and more cinematic.",
            "Via the dominant: C minor -> G minor. Repeat D or G in the bass, then settle into G minor. This gives a sense of a dark turn without breaking the groove.",
        ),
        mood_tips=(
            "Mystery: add the b2 or the natural 7th degree as a passing note, e.g. Db or B in C minor. These tones clash slightly with the mode and cast a shadow.",
            "Sexy effect: keep a steady low pulse and move the upper notes chromatically by a semitone. The semitone sounds bodily and tense because the ear is waiting for resolution.",
            "Drive: shorten the durations to sixteenths and repeat the anchor note between the moving notes. Repetition provides the motor, note movement provides direction.",
        ),
    ),
    "ritual_tribal": MoodPreset(
        name="ritual_tribal",
        tempo_bpm=88,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=88,
        rhythm=(0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5),
        bars=(
            ("D2", "D2", "A2", "D3", "C3", "A2", "F2"),
            ("D2", "D2", "A2", "F3", "E3", "C3", "A2"),
            ("Bb2", "Bb2", "F3", "E3", "D3", "A2", "F2"),
            ("C3", "C3", "G2", "Bb2", "A2", "F2", "D2"),
            ("D2", "D2", "A2", "D3", "C3", "A2", "F2"),
            ("F2", "F2", "C3", "F3", "E3", "C3", "A2"),
            ("G2", "G2", "D3", "F3", "E3", "C3", "Bb2"),
            ("A2", "A2", "E3", "G3", "F3", "E3", "D2"),
        ),
        feel="ritual pulse with accents, more body and movement",
        progressions=(
            "i - bVII - i - bVI: D minor -> C -> D minor -> Bb. Works like a circular rite: the tonic returns often, and the neighboring degrees give a primal sway.",
            "i - iv - bVII - i: D minor -> G minor -> C -> D minor. Good for physical, danceable movement without pop sweetness.",
        ),
        modulations=(
            "Shift the center up a fourth: D minor -> G minor. Hold D as the common tone, then make G the new anchor. This sounds natural on strings and heightens the ritual feel.",
            "Parallel-mode coloring: D minor -> D Phrygian. Replace E with Eb. The modulation is almost imperceptible, but an ancient, dangerous shade appears at once.",
        ),
        mood_tips=(
            "Mystery: use the Phrygian b2 degree. In D that is Eb. It works because the semitone above the tonic sounds like a forbidden door right next to home.",
            "Drive: place accents not only on 1 and 3, but on 1, the last eighth of beat 2, and 4. The shifted accent creates a tribal push.",
            "Sexy effect: alternate a dry low pulse with a soft answer a fourth/fifth above. The contrast of body and answer creates a conversational feel.",
        ),
    ),
    "noir_slow_burn": MoodPreset(
        name="noir_slow_burn",
        tempo_bpm=58,
        key_tonic="A",
        key_mode="minor",
        meter_signature="4/4",
        velocity=68,
        rhythm=(1.0, 0.5, 0.5, 1.0, 1.0),
        bars=(
            ("A2", "E3", "G3", "C3", "B2"),
            ("A2", "E3", "G3", "C3", "D3"),
            ("F2", "C3", "E3", "A2", "G2"),
            ("E2", "B2", "D3", "G2", "A2"),
            ("A2", "E3", "G3", "C3", "B2"),
            ("C3", "G2", "Bb2", "Eb3", "D3"),
            ("F2", "C3", "E3", "A2", "G2"),
            ("E2", "B2", "D3", "G2", "A2"),
        ),
        feel="slow noir, unspoken tension, held pause",
        progressions=(
            "i - iv - bVI - V: A minor -> D minor -> F -> E. Works as noir: minor-key languor, then the bright dominant E begs for resolution.",
            "i - bVI - iiø - V: A minor -> F -> B half-diminished -> E. This is a jazzier route; a smoky ambiguity appears immediately.",
        ),
        modulations=(
            "A minor -> C major via the common chord Am/C. This gives a cold brightening without losing the melancholy.",
            "A minor -> C minor via chromatically lowering E to Eb. This is a sharp noir turn: familiar material suddenly darkens.",
        ),
        mood_tips=(
            "Mystery: leave rests after tense notes. The pause works because the listener completes the threat themselves.",
            "Sexy effect: use slow descending semitones, e.g. C -> B -> Bb -> A. Descending chromaticism sounds like an exhale and a pull.",
            "Drive without speeding up: add ghost notes on weak beats. The tempo stays slow, but a nervous energy appears inside.",
        ),
    ),
    "driving_cinematic": MoodPreset(
        name="driving_cinematic",
        tempo_bpm=104,
        key_tonic="C",
        key_mode="minor",
        meter_signature="4/4",
        velocity=94,
        rhythm=(0.25,) * 16,
        bars=(
            ("C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"),
            ("C2", "G2", "C3", "G2", "C2", "G2", "F3", "G2", "C2", "G2", "Eb3", "G2", "Bb2", "G2", "C3", "G2"),
            ("Ab2", "Eb3", "Ab3", "Eb3", "Ab2", "Eb3", "G3", "Eb3", "Ab2", "Eb3", "F3", "Eb3", "C3", "Eb3", "Ab2", "Eb3"),
            ("G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "Bb2", "D3", "G2", "D3"),
            ("C2", "G2", "C3", "G2", "C2", "G2", "Eb3", "G2", "C2", "G2", "C3", "G2", "Bb2", "G2", "Eb2", "G2"),
            ("Eb2", "Bb2", "Eb3", "Bb2", "Eb2", "Bb2", "G3", "Bb2", "Eb2", "Bb2", "F3", "Bb2", "C3", "Bb2", "G2", "Bb2"),
            ("F2", "C3", "F3", "C3", "F2", "C3", "Ab3", "C3", "F2", "C3", "Eb3", "C3", "Ab2", "C3", "F2", "C3"),
            ("G2", "D3", "G3", "D3", "G2", "D3", "F3", "D3", "G2", "D3", "Eb3", "D3", "C3", "G2", "C2", "G2"),
        ),
        feel="fast cinematic motor, drive and build",
        progressions=(
            "i - bVI - bVII - i: C minor -> Ab -> Bb -> C minor. Works epically: bVI provides scale, bVII lifts the energy without an overly classical V-I.",
            "i - iv - VI - V: C minor -> F minor -> Ab -> G. More dramatic, because V creates a strong expectation of return.",
        ),
        modulations=(
            "C minor -> Eb minor via the common tone Eb. This is a dark cinematic leap: the shared tone binds them, the new key unsettles.",
            "C minor -> D minor by sequence: raise the entire ostinato figure by a whole step. A simple way to intensify a scene without complex theory.",
        ),
        mood_tips=(
            "Drive: hold a pedal tone, e.g. C or G, between each moving note. The pedal tone anchors the ground while the upper movement revs the motor.",
            "Mystery: just before the harmony changes, slip a foreign note onto a weak beat. It flickers and vanishes, so it intrigues without breaking the mode.",
            "Sexy effect: add a syncopation just before the strong beat. The body hears the anticipation of the hit, and the delay makes the groove stickier.",
        ),
    ),
    # Duet presets: theory tuples generated from harmonic analysis of duet bar
    # data and genre research (2026). Originally migrated from standalone duet
    # scripts with no GENRE_IDEAS source; tuples filled in after research.
    "sexy_duet": MoodPreset(
        name="sexy_duet",
        tempo_bpm=76,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=82,
        rhythm=(),
        bars=(),
        feel="sensual duet with chromatic tension",
        progressions=(
            "i - bVI - iv - V7: D minor → Bb → G minor → A7. Works because bVI adds dark warmth, iv creates stepwise bass motion (D→Bb→G→A), and V7 with C# leading tone creates tension that loops back to i.",
            "i pedal - V7: D minor (pedal) → A7. The cello holds tonic while harmony shifts to dominant. The C# leading tone pulls toward D, but the loop restarts before full resolution.",
        ),
        modulations=(
            "Via the dominant: D minor → A minor. Hold A as common tone between V (A7) and new i (Am). The shift stays dark but changes the center of gravity.",
            "Relative major escape: D minor → F major. Use bVI (Bb) as pivot to F. This gives momentary warmth, but the return to D minor feels inevitable.",
        ),
        mood_tips=(
            "Mystery: let the violin use chromatic neighbor tones — C# approaching D, E falling to D. The semitone motion sounds like a sigh because the ear anticipates resolution but the melody delays it.",
            "Sexy effect: keep the cello on tonic arpeggios while the harmony shifts above. The steady bass creates physical grounding, while the changing chords create emotional movement.",
            "Tension without release: use V7 with C# leading tone but let the loop restart before resolving to i. The persistent tension creates a sensual ache.",
        ),
        duet_rhythm={
            "cello": (0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5),
            "violin": (1.0, 0.5, 0.5, 1.0, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "C3", "A2", "F2", "A2"),
                ("D2", "A2", "F3", "E3", "C3", "A2", "F2"),
                ("Bb2", "F3", "A3", "G3", "F3", "D3", "Bb2"),
                ("A2", "E3", "G3", "F3", "E3", "C#3", "D2"),
                ("D2", "A2", "D3", "C3", "A2", "F2", "A2"),
                ("F2", "C3", "E3", "D3", "C3", "A2", "F2"),
                ("G2", "D3", "F3", "E3", "D3", "Bb2", "G2"),
                ("A2", "E3", "G3", "F3", "E3", "C#3", "D2"),
            ),
            "violin": (
                ("A4", "C5", "D5", "F5", "E5"),
                ("A4", "C5", "E5", "D5", "C5"),
                ("Bb4", "D5", "F5", "E5", "D5"),
                ("A4", "C#5", "E5", "G5", "F5"),
                ("A4", "C5", "D5", "F5", "E5"),
                ("C5", "A4", "D5", "E5", "F5"),
                ("Bb4", "D5", "G5", "F5", "E5"),
                ("A4", "C#5", "E5", "G5", "D5"),
            ),
        },
        duet_tempo_bpm=76,
    ),
    "simple_sexy_duet": MoodPreset(
        name="simple_sexy_duet",
        tempo_bpm=64,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=68,
        rhythm=(),
        bars=(),
        feel="intimate duet, slow and sparse",
        progressions=(
            "i - V7: D minor → A7. The simplest sensual progression: tonic darkness alternates with dominant tension. The C# leading tone in V7 creates a semitone pull to D that never fully resolves because the loop restarts.",
            "i - V7 - i - V7 - i (with bVI hint) - V7: Bars 1-6 alternate i-V7, then bar 5 introduces bVI color (D-A-F-E) before returning to the pattern. This brief departure adds variety without breaking the hypnotic loop.",
        ),
        modulations=(
            "Stay in D minor: the simplicity is the point. Modulation would break the intimate spell. If modulation is needed, shift to A minor (v) by treating the V7 (A7) as a new tonic.",
            "Relative major moment: briefly emphasize F major (bVI) by holding F in the bass and letting the violin play A-C-F. This creates a warm breath before returning to D minor's darker intimacy.",
        ),
        mood_tips=(
            "Intimacy through simplicity: use quarter notes and let the harmony breathe. The slow tempo (64 BPM) and sparse texture create physical closeness — like a whispered conversation.",
            "Leading tone as seduction: the C# in every V7 chord pulls toward D like gravity. Don't resolve it fully — let the loop restart so the tension persists and the listener leans in.",
            "Stepwise melody: keep the violin moving by steps (F→E→D, A→G→F→E). Stepwise motion sounds natural and vocal, like someone singing close to your ear.",
        ),
        duet_rhythm={
            "cello": (1.0, 1.0, 1.0, 1.0),
            "violin": (1.0, 1.0, 1.0, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "E3"),
                # NOTE: "A1" (MIDI 33) is below the C2 validator floor — pre-existing
                # in source script, migrated verbatim, not yet validated at
                # generation time (Phase 2 concern).
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "D3", "E3"),
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "F2", "E2"),
                ("A1", "E2", "G2", "C#3"),
                ("D2", "A2", "D3", "E3"),
                ("A1", "E2", "G2", "C#3"),
            ),
            "violin": (
                ("F4", "E4", "D4", "E4"),
                ("E4", "G4", "C#5", "Bb4"),
                ("F4", "E4", "D4", "A4"),
                ("G4", "E4", "C#4", "D4"),
                ("A4", "F4", "E4", "D4"),
                ("E4", "G4", "C#5", "Bb4"),
                ("F4", "E4", "D4", "E4"),
                ("C#4", "E4", "G4", "D4"),
            ),
        },
        duet_tempo_bpm=64,
    ),
    "dorian_sexy_duet": MoodPreset(
        name="dorian_sexy_duet",
        tempo_bpm=88,
        key_tonic="D",
        key_mode="minor",
        meter_signature="4/4",
        velocity=74,
        rhythm=(),
        bars=(),
        feel="D Dorian vamp: Dm9 -> G9. The B natural keeps it warm instead of funeral-dark.",
        progressions=(
            "i9 - IV9: Dm9 → G9. The classic Dorian vamp. The B natural in G9 (G-B-D-F-A) is what makes it Dorian instead of Aeolian. This progression has no dominant tension — it just grooves. The warmth comes from the natural 6th (B) replacing the dark b6 (Bb).",
            "i9 - IV7 - i9: Dm9 → G7 → Dm9. Slight variation: G7 (G-B-D-F) without the 9th creates a bluesier feel, but the B natural still keeps it Dorian warm.",
        ),
        modulations=(
            "Parallel mode shift: D Dorian → D Aeolian. Replace B natural with Bb. The change is subtle but dramatic — warmth turns to darkness. This works because the rest of the scale stays the same, so the shift feels like a color change rather than a key change.",
            "Relative major: D Dorian → C major. Treat C as the new tonic. The Dorian Dm9 becomes ii9 in C, creating a jazzy lift. This modulation is smooth because D Dorian and C major share the same notes.",
        ),
        mood_tips=(
            "Warmth through the natural 6th: emphasize B natural in both cello and violin. The B natural is what makes Dorian sound warm and groovy instead of dark and funeral. Let it ring prominently in the melody.",
            "Modal suspension: don't create dominant tension. Avoid the raised 7th (C#) that would pull to D. Instead, let the i9-IV9 loop create a hypnotic groove that doesn't demand resolution — it just feels good.",
            "Dorian melody: use the A-B-C-B-A ornament (5-6-b7-6-5) in the violin. This pattern emphasizes the natural 6th (B) and flat 7th (C), which are the characteristic Dorian tones. The stepwise motion sounds vocal and natural.",
        ),
        duet_rhythm={
            "cello": (0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5),
            "violin": (0.5, 0.5, 1.0, 0.5, 0.5, 1.0),
        },
        duet_bars={
            "cello": (
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "G2"),
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "G2"),
                ("D2", "A2", "C3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "C3", "B2"),
                ("D2", "A2", "D3", "E3", "F3", "E3", "D3"),
                ("G2", "D3", "F3", "A2", "B2", "A2", "D2"),
            ),
            "violin": (
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "A4", "G4", "E4"),
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "C5", "B4", "A4"),
                ("F4", "A4", "B4", "A4", "F4", "E4"),
                ("G4", "A4", "B4", "A4", "G4", "E4"),
                ("A4", "B4", "C5", "B4", "A4", "F4"),
                ("G4", "A4", "B4", "A4", "F4", "D4"),
            ),
        },
        duet_tempo_bpm=88,
    ),
}
