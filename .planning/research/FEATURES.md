# Feature Research

**Domain:** Loop coach and practice partner for solo electric cellist
**Researched:** 2026-06-22
**Confidence:** HIGH (core features), MEDIUM (Audio Analysis MCP integration), LOW (violin duet / drum machine specifics)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the user assumes exist. Missing any of these = the app feels broken or pointless.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Chord-text input field | Entry point of the whole workflow; without it nothing starts | LOW | Already works in CLI scripts as genre presets; needs text parsing `Am F C G` → music21 objects |
| Key and mood/genre selector | Without context, the generation is generic and vibeless | LOW | 4 genre presets already exist (`dark_trip_hop`, `noir_slow_burn`, `ritual_tribal`, `driving_cinematic`); exposed in UI |
| Generate multiple loop variants from one input | User specifically said "playing from chords is boring" — one variant is no better than the sheet music she already has | MEDIUM | Core loop generation already in `generate_cello_dark_ostinato.py`; needs parameterization to produce 3–4 distinct variants |
| Plain-language theory explanation per variant | This IS the core value proposition. Without it the app is just another notation generator | MEDIUM | `harmony_advisor.py` already outputs this logic as text; needs integration into UI per-variant |
| In-browser audio playback | Without hearing it before touching the cello, the loop is abstract | MEDIUM | `st.audio()` supports WAV/MP3/OGG. music21 can render MIDI → FluidSynth can convert to audio server-side. Direct browser MIDI playback needs a JS synthesizer (e.g. MIDI.js, Tone.js) or a server-side render-to-WAV step |
| MusicXML export | Needed to open in MuseScore for practice reference | LOW | Already working in existing scripts; expose via UI download button |
| MIDI export | Needed to import into Ableton | LOW | Already working; same download button pattern |
| Graceful degradation when Audio Analysis MCP is offline | App must remain fully usable as a loop generator even without the MCP | LOW | Design: record/analysis section shows "MCP unavailable" banner, rest of UI unaffected |

### Differentiators (Competitive Advantage)

Features that set this app apart from generic chord tools and notation generators. These map directly to the user's stated pain points.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| "Why it works" theory panel per variant | No competitor explains the theory behind cello-specific loop choices in plain, non-jargon language. Hooktheory does this for songwriters, but not for looping string players. This directly addresses "theory feels opaque" | MEDIUM | Output structured as: (1) what this loop does harmonically, (2) why it sounds the way it does, (3) what the cello-specific techniques are doing. Already proto-typed in `harmony_advisor.py` — needs per-variant rendering, not per-genre only |
| Start / Develop / End / Transition guidance per loop | No tool tells a looper "how to get INTO and OUT OF this pattern." This is the most-cited pain point for live loopers. Generic practice apps ignore loop lifecycle entirely | MEDIUM | Guidance structured as 4 named sections: "How to enter," "How to build intensity," "How to close," "How to transition to the next loop." Can be template-driven text per variant initially, upgraded to LLM-generated later |
| Mood/vibe shaping as first-class dimension | Most chord tools generate harmonically correct material with no emotional intent. User wants "noir," "ritual," "trip-hop," "cinematic" — not just "minor chord" | LOW-MEDIUM | Already the strongest thing in the existing code. Differentiator is making mood the primary axis the UI is organized around, not an afterthought |
| Cello-specific loop patterns (register, bow techniques, ostinato idioms) | Generic chord generators output piano-voice voicings that don't translate to cello. Cello loops are single-voice, use specific registers, rely on pedal tones and rhythmic pattern rather than chord spread | MEDIUM | `generate_cello_dark_ostinato.py` already enforces this. Key to preserving: all generated patterns must stay in playable cello range and remain monophonic/idiomatic |
| Record own playing → concrete improvement suggestions | Yousician and SmartMusic do generic pitch/rhythm feedback. This app knows WHAT LOOP the user is practicing and gives feedback in that context: "you rushed the transition into bar 5 of the noir loop" rather than just "your timing was off" | HIGH | Depends on Audio Analysis MCP. Context-awareness (which loop, which variant) is the differentiator over generic pitch-detection apps |
| On-demand music Q&A in the session context | No loop generator lets you ask "why does this note sound dark here?" mid-session. Hooktheory has static educational content; this would be live Q&A grounded in the currently-loaded loop | HIGH | Depends on LLM integration (likely the same LLM backbone that generates explanations). Can be implemented as a simple chat component in Streamlit if the explanation engine is already LLM-based |
| Looper-style slot view with independent regeneration | No practice app lets you treat each 8-bar section as a regenerable slot like a hardware looper does. This maps to how live loopers actually think: A-loop, B-loop, transition | HIGH | Post-v1 feature. Requires persistent session state per slot, independent generation calls, slot comparison UI |

### Anti-Features (Deliberately NOT Build)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Third-party song transcription (chord extraction from Spotify/YouTube/MP3) | Seems useful — "analyze this song for me" | High DSP complexity, licensing risk, and does not fit the workflow: user already knows the chords or finds them online. Distracts from core loop generation | User enters chords manually or finds them via Hooktheory/Ultimate Guitar; app focuses on what to DO with those chords |
| Humming / voice melody input | Seems natural — "hum what you're thinking" | Pitch detection is brittle, adds major ML dependency, and the user's primary input mode is chord text. Adds complexity for a secondary workflow | Defer to v2+. Core value is chord-text → loop, which is faster and more reliable |
| Real-time pitch correction or effects | "Electric cello" implies signal chain thinking | This is a DAW / effects pedal problem. Building an effects chain in a Python web app adds audio latency, complexity, and competes with Ableton rather than complementing it | Route cello output through Ableton for effects; app focuses on notation, theory, and recorded-audio analysis only |
| Social sharing / community features | Seems engaging | This is a personal local tool. Social features require authentication, backend infrastructure, privacy design — all orthogonal to the core value | Keep it local-only; user can share MusicXML/MIDI files manually |
| Full DAW / sequencer replacement | Feels like "one app for everything" | Ableton already exists and is already in the user's workflow. Trying to replicate DAW features in Streamlit creates an inferior, harder-to-maintain tool | App exports MIDI; Ableton is the performance/DAW environment |
| Mobile app | Wider reach | Declared out of scope; adds entirely separate codebase. Desktop web-first is correct for a notation-heavy tool | Web app on desktop; can be opened on any device via localhost if needed |
| Chord suggestion "what comes next" auto-compose | Appears helpful for beginners | Shifts user from active musical decision-maker to passive recipient. The goal is to teach the user WHY progressions work, not to make choices for them | Show which chords work NEXT and WHY, but let the user choose — e.g., "If you want tension: try bVII. Here's why:" |

---

## Feature Dependencies

```
[Chord-text input + key/mood selector]
    └──required by──> [Multi-variant loop generation]
                          └──required by──> [Theory explanation per variant]
                          └──required by──> [Start/Develop/End/Transition guidance]
                          └──required by──> [In-browser audio playback]
                          └──required by──> [MusicXML export]
                          └──required by──> [MIDI export]

[In-browser audio playback]
    └──depends on──> [server-side MIDI→audio render OR JS synthesizer]
                          (music21 MIDI → FluidSynth WAV → st.audio() is the simplest path;
                           direct browser MIDI synthesis via Tone.js is the cleanest UX)

[Record own playing → improvement suggestions]
    └──requires──> [Audio Analysis MCP connection]
    └──context-enhanced by──> [Multi-variant loop generation] (to know WHICH loop user practiced)

[On-demand music Q&A]
    └──requires──> [LLM integration] (same engine as theory explanations if LLM-driven)
    └──enhanced by──> [Record own playing] (can answer questions about the recording)

[Looper-style slot view]
    └──requires──> [Multi-variant loop generation] (slots are independently regenerable variants)
    └──requires──> [Persistent session state] (Streamlit session_state)
    └──enhanced by──> [In-browser audio playback] (per-slot playback comparison)

[Violin duet mode]
    └──requires──> [Multi-variant loop generation] (adds a second voice layer)
    └──requires──> [MusicXML export] (for two-staff notation)

[Drum machine patterns]
    └──requires──> [MIDI export] (drum patterns are MIDI-only, not notation)
    └──compatible with──> [Ableton import] (existing workflow)
```

### Dependency Notes

- **Theory explanation requires multi-variant generation:** Explaining "why this works" only makes sense when there are multiple variants to compare. "This variant uses a pedal tone; the other uses chromatic motion — here's why each creates a different vibe."
- **Audio playback is the hardest table-stakes feature to implement cleanly:** Streamlit's `st.audio()` only plays WAV/MP3/OGG. music21's native playback uses pygame (desktop, not browser). The simplest working path: generate MIDI → render to WAV server-side via FluidSynth → serve WAV via `st.audio()`. This needs FluidSynth + a soundfont installed. The cleanest UX path (no server-side render latency): use a JS-based synthesizer in a Streamlit custom component, but that's higher complexity.
- **Audio Analysis MCP is a hard external dependency:** The app must be designed from day one to operate fully without it. MCP integration should be an additive layer, never load-bearing for the core loop generation flow.
- **Looper-style slots conflict with simple single-output design:** Introducing slots requires a persistent multi-variant session model in Streamlit (session_state dict of variants). This is MEDIUM complexity but must be designed into the data model early — retrofitting it is painful.

---

## Pedagogical Angle: How to Explain Theory to a Non-Theory User

This is the most important dimension to get right and the one generic tools fail at most consistently.

### What good looks like (from Hooktheory, harmony_advisor.py, and research)

1. **Lead with sensation, follow with name.** Say "this sounds dark because..." before saying "this is a Phrygian mode." The user already knows the sensation; the name is just a label for something they've heard.

2. **Explain the "mechanism," not the rule.** The existing `harmony_advisor.py` already does this correctly: *"Полутон звучит телесно и напряженно, потому что ухо ждет разрешения."* (A semitone sounds bodily and tense because the ear awaits resolution.) This is the right pattern: sensation → cause → what to do about it.

3. **Explain via contrast between variants.** "Variant A uses a pedal tone — notice how the loop feels locked and driving. Variant B uses chromatic motion in the upper register — notice how that creates tension and movement. Same chords, different vibe." Contrast is the fastest teacher.

4. **Name techniques only after demonstrating them.** Don't say "use chromaticism." Show the note in the score, let the user hear it, then say "that half-step move is called chromaticism — it works because..."

5. **Keep theory explanations short and action-oriented.** Each explanation should end with something the user can do right now: "try adding the Db as a passing note on beat 3."

### What bad looks like (to avoid)

- Dumping Roman numeral analysis without connecting it to sound: "This uses i-VI-IV-V." → Meaningless to a beginner.
- Explaining theory in abstract before demonstrating it: "Phrygian mode has a flat second degree." → Disconnected from the loop.
- Using conservatory vocabulary without grounding: "The tritone substitution here resolves to the tonic." → User will close the app.

### Structure of a good variant explanation card

```
[Loop name / vibe label]
[Notation display + playback button]

WHY THIS SOUNDS [VIBE]:
  [1-2 sentences: the harmonic mechanism in plain language]

THE CELLO MOVE:
  [1 sentence: what the specific pattern is doing technically]

HOW TO ENTER:
  [1 sentence: start note / pickup / count-in]

HOW TO BUILD:
  [1 sentence: add dynamics / bow pressure / rhythm variation]

HOW TO END:
  [1 sentence: resolution note or cut]

HOW TO TRANSITION:
  [1 sentence: common tone or rhythmic fill to next loop]

TRY NEXT:
  [1 suggestion with WHY: "If you want more tension, add a Db on beat 4 — it's a half-step above C and creates pull."]
```

---

## MVP Definition

### Launch With (v1)

Minimum to validate the core value: "chord text → vibe-shaped cello loop with explanation."

- [x] Chord-text input + key/mood selector in Streamlit UI
- [x] Generate 3 distinct loop variants (different rhythmic patterns, register choices, techniques) for the same chord input and mood
- [x] Theory explanation per variant (why it works, plain language, 2–4 sentences) — initially template-driven from `harmony_advisor.py` logic
- [x] Start/Develop/End/Transition guidance per variant — initially template-driven
- [x] In-browser audio playback of generated loop (server-side MIDI→WAV render via FluidSynth)
- [x] MusicXML and MIDI download buttons
- [x] Graceful degradation: full UI works when Audio Analysis MCP is offline

### Add After Validation (v1.x)

Add once core loop generation + explanation is confirmed working and useful.

- [ ] Record own cello playing + Audio Analysis MCP integration → concrete improvement suggestions in context of current loop
- [ ] On-demand music Q&A chat (LLM, scoped to current session: current loop + current recording if any)
- [ ] More mood presets beyond the 4 existing ones (e.g., "melancholic folk," "aggressive metal," "meditative ambient")
- [ ] Variant comparison view: display all 3 variants side-by-side with score + playback

### Future Consideration (v2+)

Defer until v1 is working and user has validated the core workflow.

- [ ] Looper-style slot view (A-loop, B-loop, transition slot, each independently regenerable)
- [ ] Violin duet mode (second voice layer, two-staff export)
- [ ] Drum machine pattern generation (MIDI-only, Ableton-compatible, locked to the same tempo/key as the cello loop)
- [ ] LLM-generated (not template-driven) theory explanations for infinite variety
- [ ] Humming / voice melody input for loop seeding (high complexity, low priority)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Chord-text input + mood selector | HIGH | LOW | P1 |
| Multi-variant loop generation | HIGH | MEDIUM | P1 |
| Theory explanation per variant (template-driven) | HIGH | MEDIUM | P1 |
| Start/Develop/End/Transition guidance | HIGH | MEDIUM | P1 |
| In-browser audio playback (MIDI→WAV) | HIGH | MEDIUM | P1 |
| MusicXML + MIDI export | HIGH | LOW | P1 |
| Graceful MCP degradation | MEDIUM | LOW | P1 |
| Record + Audio Analysis MCP feedback | HIGH | HIGH | P2 |
| On-demand Q&A chat | MEDIUM | MEDIUM | P2 |
| More mood presets | MEDIUM | LOW | P2 |
| Variant comparison side-by-side | MEDIUM | MEDIUM | P2 |
| Looper-style slot view | HIGH (later) | HIGH | P3 |
| Violin duet mode | MEDIUM | HIGH | P3 |
| Drum machine patterns | MEDIUM | MEDIUM | P3 |
| LLM-generated explanations | HIGH (upgrade) | HIGH | P3 |

---

## Competitor Feature Analysis

| Feature | Hooktheory | ChordChord / ChordGen | Yousician / SmartMusic | This App |
|---------|------------|----------------------|------------------------|----------|
| Chord-text input | No (click-based) | Yes (text/click) | No (song-based) | Yes — primary input |
| Cello-specific output | No (piano-centric) | No | No | Yes — monophonic, cello register, bow idioms |
| Theory explanation plain language | Yes (song examples) | No | No | Yes — per-variant, mechanism-first |
| Mood/vibe as first-class dimension | No | Partial (genre tags) | No | Yes — primary axis |
| Loop lifecycle guidance (start/develop/end/transition) | No | No | No | Yes — differentiator |
| In-browser playback | Yes | Yes | Yes | Yes (via MIDI→WAV render) |
| MusicXML export | No | No | No | Yes |
| MIDI export | Yes | Yes | No | Yes |
| Record own playing + feedback | No | No | Yes (generic) | Yes (context-aware: knows which loop) |
| Multiple variants per input | No | Yes (chord-only) | No | Yes (pattern + technique variants) |

---

## Sources

- Hooktheory features and pedagogy approach: https://www.hooktheory.com/ and https://hyperbits.com/hooktheory/
- ChordChord: https://chordchord.com/
- ChordLoops (voice leading + rhythm generation): https://chordloops.net/
- Yousician and SmartMusic as performance feedback references: https://www.soundverse.ai/blog/article/ai-practice-tools-for-musicians
- Live looping for string players: https://christianhowes.com/2013/03/04/how-to-use-looping-and-loop-pedals-to-practice-perform-teach-and-improve-musicianship/
- Loop lifecycle and transition techniques: https://hackmusictheory.com/blogs/theory/posts/5916043/how-to-transition-between-sections-of-a-song
- Streamlit audio limitations: https://docs.streamlit.io/develop/api-reference/media/st.audio
- OpenSheetMusicDisplay for browser notation rendering: https://opensheetmusicdisplay.org/
- music21j for browser MIDI playback: https://web.mit.edu/music21/doc/about/what.html
- Existing codebase: `scripts/harmony_advisor.py`, `scripts/generate_cello_dark_ostinato.py`

---

*Feature research for: loop coach and practice partner — solo electric cellist*
*Researched: 2026-06-22*
