# Pitfalls Research

**Domain:** Local Streamlit + Python/music21 cello loop-coach & practice-partner app
**Researched:** 2026-06-22
**Confidence:** HIGH (music correctness, Streamlit mechanics) / MEDIUM (MCP integration, Playwright-Python/Allure)

---

## Critical Pitfalls

### Pitfall 1: Generated Loops Outside Playable Cello Range

**What goes wrong:**
The generator emits a note string (e.g. `"C6"` or `"B1"`) that is physically impossible on a standard 4-string cello (tuned C2–A3 open strings, practical upper limit ~C6 in first-position thumb). The MusicXML exports fine, MuseScore renders fine, but the cellist cannot play it. With user-entered chord progressions driving generation, the mapping from chord tones to cello pitches is unconstrained unless explicitly guarded.

**Why it happens:**
The existing generator hardcodes pitches in `bars` arrays and stays safe by inspection. Once the Streamlit UI allows arbitrary chord-progression input driving dynamic generation, pitch selection becomes algorithmic. A naive "pick the root of each chord" without octave clamping can easily land on `C1` (below the C string) or `D6` (above thumb-position reach for most cellists).

Standard playable cello range (HIGH confidence, confirmed by orchestration references):
- Lowest: C2 (open C string)
- Safe practical upper limit for an intermediate player: approximately D5 (first thumb position)
- Extended (advanced / electric): up to C6

**How to avoid:**
Implement a `validate_cello_range(pitch_name: str) -> bool` utility in a shared `engine/validators.py` module. Check MIDI pitch number: C2 = MIDI 36, D5 = MIDI 62 (intermediate cap), C6 = MIDI 84 (hard cap). Clamp or flag at generation time, not at export time. Add an assertion in `build_cello_ostinato` or its successor that raises `ValueError` with a human-readable message before the score object is created.

```python
CELLO_MIN_MIDI = 36   # C2
CELLO_MAX_MIDI = 74   # D5 safe for intermediate; extend to 84 for electric advanced

def validate_pitch(pitch_name: str) -> None:
    from music21 import pitch as m21pitch
    p = m21pitch.Pitch(pitch_name)
    if not (CELLO_MIN_MIDI <= p.midi <= CELLO_MAX_MIDI):
        raise ValueError(f"Pitch {pitch_name} (MIDI {p.midi}) is outside playable cello range.")
```

**Warning signs:**
- Any generated note below `C2` or above `D5` in logs or MusicXML
- User reports "this note doesn't exist on the instrument"
- MuseScore shows notes requiring ledger lines far above the bass clef staff

**Phase to address:** Phase 1 (Streamlit UI + generation engine) — before any user-facing chord input is wired up

---

### Pitfall 2: Bar Duration Mismatch Silently Corrupts the Score

**What goes wrong:**
The `zip(pitches, preset.rhythm, strict=True)` in the existing script guards against length mismatches between pitch list and rhythm list, but does NOT check that `sum(rhythm) == beats_per_bar`. If a newly generated bar sums to 3.75 instead of 4.0 in a 4/4 meter, music21 will accept it, MusicXML will be malformed, MuseScore will show unexpected rests or barlines in wrong positions, and MIDI playback will drift. The README explicitly warns: "the sum of durations in each bar must match the meter."

**Why it happens:**
When generation becomes dynamic (user picks meter, mood, chord progression), rhythm lists are computed rather than hand-authored. Off-by-one in rhythm subdivision math (e.g. mixing `0.25` and `0.33` triplets, or generating 7 sixteenth notes for a 4/4 bar) creates silent corruptions that pass Python without error.

**How to avoid:**
Add a per-measure sum check in `build_cello_ostinato` (or its Streamlit successor) immediately after appending notes:

```python
from music21 import meter as m21meter

ts = m21meter.TimeSignature(preset.meter_signature)
expected_ql = ts.barDuration.quarterLength

for measure_number, pitches in enumerate(preset.bars, start=1):
    measure = stream.Measure(number=measure_number)
    actual_ql = sum(preset.rhythm[:len(pitches)])
    if abs(actual_ql - expected_ql) > 1e-9:
        raise ValueError(
            f"Bar {measure_number}: duration {actual_ql} != {expected_ql} "
            f"for {preset.meter_signature}"
        )
```

Use `music21.meter.TimeSignature.barDuration.quarterLength` (confirmed available in music21 docs) as the authoritative expected value — do not hardcode `4.0`.

**Warning signs:**
- MuseScore shows unexpected rests or barlines mid-measure
- MIDI playback tempo drifts over multiple bars
- `music21` `makeNotation()` logs warnings about incomplete measures

**Phase to address:** Phase 1 (generation engine hardening, before Streamlit UI)

---

### Pitfall 3: Streamlit Rerun Clobbers the Generated Loop

**What goes wrong:**
User generates a loop — it appears on screen. User adjusts any widget (changes tempo slider, clicks a button, resizes anything). Streamlit reruns the entire script top-to-bottom. If the generated loop result is stored in a local variable (not `st.session_state`), it is lost. The user sees a blank result area or the "generate" button resets to initial state. This is the single most common Streamlit beginner trap.

**Why it happens:**
Streamlit's execution model: every interaction triggers a full script re-execution with a blank slate. Local variables do not persist. Developers coming from request/response web frameworks assume variables survive between user actions.

Specific sub-trap for this app: `st.audio_input` returns `None` on every rerun until the user records again. If the audio bytes are not immediately stored in `session_state` via an `on_change` callback, the recorded audio is lost on the next widget interaction.

**How to avoid:**
- Store ALL generated results in `st.session_state` with explicit keys: `st.session_state["current_loop"]`, `st.session_state["loop_variants"]`, `st.session_state["last_recording"]`.
- Use `on_change` callback for `st.audio_input` to capture audio bytes into `session_state` immediately, not inline in script body.
- Initialize all `session_state` keys at the top of the script with `if "key" not in st.session_state:` guards.
- Use `@st.cache_data` for expensive deterministic computations (MusicXML rendering, score export) with input-based keys.
- Never hold generated `music21` stream objects in local variables across UI sections.

**Warning signs:**
- Generated notation disappears when user changes any other widget
- Recording is lost after clicking "Play" or "Export"
- Loop variants reset to empty on tab switch or sidebar interaction

**Phase to address:** Phase 1 (Streamlit UI architecture) — must be solved in the first UI spike, not retrofitted

---

### Pitfall 4: Long-Running Generation Blocks the Streamlit UI Thread

**What goes wrong:**
Calling `music21` generation, MCP audio analysis, or LLM explanation in the main Streamlit script thread blocks the entire app for all reruns. With music21 on complex scores or MCP analysis of a 30-second recording, this can take 5–30 seconds. During this time the browser shows a spinner but ALL user interactions are queued — the app is frozen. If the user clicks something, a new rerun is queued, and Streamlit may cancel the running generation mid-flight.

**Why it happens:**
Streamlit runs one script execution per session. Synchronous blocking calls in the main script thread prevent the event loop from responding to the browser. `music21.stream.Score.write()` in particular can be slow on large scores (calls MuseScore subprocess if configured that way).

**How to avoid:**
- Use `st.spinner()` for short operations (< 3 seconds) — acceptable for basic loop generation.
- For MCP audio analysis (potentially 5–15 seconds): run in a `concurrent.futures.ThreadPoolExecutor`, store future in `session_state`, poll with `st.rerun()` or use `st.fragment` (Streamlit 1.37+) for partial-page reruns.
- Keep `music21` generation lean: do NOT call `score.show()` (opens MuseScore subprocess) in the web app. Use `score.write("musicxml", fp=...)` to a temp file, then serve the bytes.
- Use `@st.cache_data` with appropriate `ttl` to avoid re-generating identical loops on every rerun.

**Warning signs:**
- Browser tab shows "Running..." for more than 3 seconds on generation
- User interaction during generation causes the result to disappear (rerun cancelled)
- `st.spinner` blocks all other widgets on the page

**Phase to address:** Phase 1 for basic generation; Phase 3 (MCP integration) for async analysis pattern

---

### Pitfall 5: MCP Audio Analysis Is Unavailable and the App Breaks Entirely

**What goes wrong:**
PROJECT.md explicitly requires graceful degradation when the Audio Analysis MCP is unavailable. If the MCP client call is not wrapped in a try/except with a clean fallback, a connection error surfaces as a Python traceback in the Streamlit UI, making the entire loop-coach feature feel broken — even though the core generation workflow is independent of MCP.

**Why it happens:**
MCP servers are external processes (local socket or HTTP). They can fail to start, crash, time out, or simply not be configured yet. Developers often wire up the happy path first and add error handling only after seeing failures in production.

Additional risks:
- Audio payload size: `st.audio_input` returns WAV bytes; a 60-second recording at 44.1kHz is ~5 MB. Some MCP server implementations have payload limits or slow base64 encoding.
- Latency: audio analysis MCP round-trips can take 10–30 seconds on first call (model loading). Without a timeout, the Streamlit thread blocks indefinitely.

**How to avoid:**
- Wrap ALL MCP calls in a `try/except` with a `MCPUnavailableError` fallback state stored in `session_state`.
- Show a clear UI message: "Performance feedback is unavailable — MCP server not connected. Loop coaching still works."
- Set explicit timeouts on MCP client calls (e.g. 30 seconds max).
- Send audio as streaming chunks or limit `st.audio_input` recordings to < 60 seconds with a UI warning.
- Log MCP availability at startup and surface it in a sidebar status indicator.

**Warning signs:**
- Uncaught `ConnectionRefusedError` or `TimeoutError` in Streamlit traceback
- App freezes for > 30 seconds on "Analyze my playing" button
- No fallback message when MCP is down

**Phase to address:** Phase 3 (MCP integration) — define the graceful degradation contract before writing any MCP client code

---

### Pitfall 6: MCP Analysis Returns Generic, Useless Feedback

**What goes wrong:**
The MCP returns raw analysis output (pitch histogram, onset timestamps, tempo estimate). The app passes this directly to an LLM prompt and gets back generic feedback like "Your intonation could be improved" or "Try to play more evenly." This is worse than no feedback because it wastes the user's time and erodes trust.

**Why it happens:**
The gap between raw audio analysis data and actionable loop-coaching advice requires explicit prompt engineering. Generic prompts produce generic answers. The user of this app is a beginner-to-intermediate electric cellist working on specific loop vibes — not a classically trained student.

**How to avoid:**
- Design the MCP-to-advice pipeline with a structured intermediate step: raw analysis → structured JSON summary → advice prompt.
- The advice prompt must include: the specific chord progression the user was practicing, the loop variant they were playing, the mood/genre context, and the raw analysis summary. Example: "The player was practicing a dark_trip_hop loop in C minor at 72 BPM over [Am F C G]. Analysis shows: tempo drift of ±8ms, pitch center at A2–C3. Give 2 specific suggestions to improve the groove feel."
- Define a `format_analysis_for_prompt(analysis: dict, loop_context: dict) -> str` function in a separate module and write unit tests for it.
- Never surface raw MCP JSON directly in the UI.

**Warning signs:**
- User feedback: "the advice is too vague to act on"
- Advice does not mention the specific loop, key, or genre
- All suggestions sound identical regardless of what was played

**Phase to address:** Phase 3 (MCP integration) — design the prompt template before the MCP client is wired up

---

### Pitfall 7: Theory Explanations Are Jargon-Heavy or Factually Wrong

**What goes wrong:**
The app's core value is explaining *why* a generated loop works in plain language for a beginner-to-intermediate player. If the explanation uses terms like "Phrygian dominant mode" or "tritone substitution" without unpacking them, the user is lost. If the explanation is factually incorrect (e.g. says a note is "the 5th of the chord" when it's actually the b7), the user internalizes wrong theory and the app actively harms their learning.

**Why it happens:**
LLM-generated explanations default to theory jargon because training data is full of theory textbooks. Without explicit prompt constraints, the model writes for a theory student, not for someone who says "vibey/sexy loops just don't work out."

**How to avoid:**
- System prompt must include explicit persona: "Explain as if to someone who plays music by feel and wants to understand the *why* without jargon. Define any term you must use in plain language."
- Ground explanations in the actual generated notes: "This loop uses C, G, Eb, Bb — that's the C minor chord broken up into a bouncy pattern. Minor = darker, tense. The Bb on beat 3 adds a jazzy color because it's just one step below the root."
- Add a `validate_explanation_against_score(explanation: str, score: music21.Score) -> list[str]` function that checks factual claims (mentioned notes exist in the score, named chords are correct).
- Human review the first 10 generated explanations before shipping the feature.

**Warning signs:**
- Explanation uses 3+ theory terms in a row without defining them
- Explanation mentions note names that do not appear in the generated loop
- User asks "what does that mean?" in the on-demand Q&A immediately after reading the explanation

**Phase to address:** Phase 2 (theory explanations feature) — establish prompt templates and validation before the explanation feature ships

---

### Pitfall 8: Playwright Tests Are Flaky Due to Streamlit's WebSocket Rerun Model

**What goes wrong:**
Playwright drives a real browser against the Streamlit app. Streamlit communicates over WebSocket — when a rerun completes, the DOM is re-rendered. Tests that interact with an element immediately after clicking a button may hit the element while Streamlit is mid-rerun, causing `ElementNotAttachedException`, stale locators, or false positives where the test passes because it checked state from the *previous* render.

**Why it happens:**
Streamlit's rerun cycle: click → WebSocket message → Python script re-executes → new DOM rendered. This is not a standard HTTP request/response; the browser DOM is unstable for 200ms–5s after any interaction. Playwright's auto-wait works for standard DOM mutations but may not correctly handle Streamlit's full WebSocket rerun completion.

Additional problem: `wait_for_timeout()` (fixed sleeps) is the naive fix but creates slow, still-flaky tests.

**How to avoid:**
- Use the canonical Streamlit Playwright wait pattern: after any interaction, wait for the "Running..." status indicator to appear and then disappear:
  ```python
  # After clicking a button:
  page.get_by_text("Running...").wait_for(state="visible", timeout=5000)
  page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
  ```
  Note: on fast operations "Running..." may appear and disappear before Playwright can catch it — add a fallback `expect(locator).to_be_visible()` assertion.
- Never store element references across rerun boundaries — always re-query with `page.locator(selector)`.
- Use data-testid attributes on key UI elements (`st.markdown(..., unsafe_allow_html=True)` with `data-testid` or wrap in a container with a unique ID) to get stable locators.
- Streamlit app must be fully started before tests begin. Use a pytest fixture that polls `http://localhost:8501/_stcore/health` until 200 OK, not a fixed `sleep(10)`.
- Set `STREAMLIT_SERVER_HEADLESS=true` in the test environment.

**Warning signs:**
- Tests pass locally but fail in CI (timing-dependent)
- `ElementNotAttachedException` on element interactions
- Test passes but UI shows wrong state (checked stale DOM)
- Test suite takes > 60 seconds due to `wait_for_timeout` calls

**Phase to address:** Phase 4 (testing framework setup) — establish the wait pattern and fixture as the first thing in the test framework, before writing any test cases

---

### Pitfall 9: Allure + Playwright-Python Integration Is Non-Standard

**What goes wrong:**
The locked decision is Playwright (Python) + Allure reports. The `allure-playwright` npm package is designed for JavaScript/TypeScript Playwright. For Python, the integration path is `pytest-playwright` + `allure-pytest` — a different package entirely. Developers who follow JavaScript Playwright/Allure guides will set up the wrong toolchain and spend hours debugging missing reports.

**Why it happens:**
Most Playwright/Allure documentation and blog posts target JavaScript. A GitHub issue in `microsoft/playwright-python` (#1265) confirms that the Python integration path is `allure-pytest`, not `allure-playwright`. The Allure official docs list "Playwright" as a separate entry that assumes JavaScript.

**How to avoid:**
Use this exact Python toolchain:
```
pip install pytest pytest-playwright allure-pytest
playwright install chromium
```
Run tests:
```bash
pytest tests-ui/ --alluredir=allure-results
allure serve allure-results  # or: allure generate allure-results -o allure-report
```
Do NOT install `allure-playwright` (the npm package) — it will not work with Python tests.
Add `conftest.py` with a `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]` block specifying `addopts = "--alluredir=allure-results"` so the flag is always present.

**Warning signs:**
- `allure-results/` directory is empty after test run
- `allure serve` shows 0 tests
- Following a JavaScript Playwright/Allure guide that mentions `allure-playwright` npm install

**Phase to address:** Phase 4 (testing framework setup) — first commit in `tests-ui/`

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode pitch lists in presets (current approach) | Zero generation errors | Cannot support user chord input | Acceptable for Phase 1 preset-only mode; must change in Phase 2 |
| Call `score.write()` synchronously in Streamlit | Simple code | Blocks UI for 1–5s per generation | Acceptable for MVP; move to thread executor by Phase 3 |
| Store everything in `session_state` with string keys | Works fast | No type safety, key collisions | Acceptable short-term; add a typed state dataclass by Phase 3 |
| Skip MCP availability check, assume server is up | Faster dev loop | App crashes for any user without MCP running | Never — add availability check from day one of Phase 3 |
| Use `wait_for_timeout(2000)` in Playwright tests | Tests pass locally | Flaky in CI, slow suite | Never — use the "Running..." wait pattern instead |
| LLM explanation with no factual grounding | Faster to implement | User internalizes wrong theory | Never for shipped feature; acceptable in prototype |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|-----------------|
| `st.audio_input` | Read `.value` in script body; bytes are lost on next rerun | Capture bytes in `on_change=` callback into `session_state["last_recording"]` immediately |
| `st.audio_input` on Firefox | Playback via `st.audio` plays sped-up and doubled (confirmed GitHub issue #9799) | Test on Chrome/Chromium (the locked browser for this app); document Firefox limitation |
| `st.audio_input` > 10s recordings | Works locally; throws error on some deployed instances (GitHub issue #9892) | Cap recording at 60s with UI warning; test at target duration on target machine (local macOS) |
| music21 `score.show()` | Opens MuseScore subprocess; never returns in headless Streamlit | Use `score.write("musicxml", fp=tmp_path)` + serve bytes via `st.download_button` |
| MCP client timeout | Default timeout may be None (blocks forever) | Always set explicit `timeout=30` seconds on MCP tool calls |
| Playwright + Streamlit startup | Fixed `sleep(10)` before tests | Poll `/_stcore/health` endpoint in pytest fixture with retry loop |
| `allure-pytest` Python | Following JS `allure-playwright` guide | Install `allure-pytest` (Python), not `allure-playwright` (npm) |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Regenerating the full score on every Streamlit rerun | UI freezes for 1–5s on any widget interaction | `@st.cache_data` on generation function keyed by (chord_progression, mood, seed) | From first user interaction |
| Sending full WAV bytes to MCP on every analysis click | 5–60s latency, potential payload errors | Cap recording length, stream or chunk if MCP supports it | At recordings > 30s |
| music21 `makeNotation()` called implicitly on export | Slow on complex scores with ties/beams | Profile `score.write()` time; use flat streams when notation rendering is not needed | At > 4 bars with complex rhythms |
| Playwright tests with `wait_for_timeout` | Test suite takes 5+ minutes | Use event-based waiting ("Running..." pattern) | From the first test run in CI |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing raw MusicXML notation link without in-browser playback | User must open MuseScore to hear anything; breaks the "hear the vibe before playing" core value | Implement MIDI-to-audio playback in browser (e.g. `midi.js`, SOUNDFONT, or pre-rendered MP3) as part of Phase 1 |
| Theory explanation above the notation | User reads abstract text before seeing what it refers to | Show notation + playback first, explanation below |
| No "which loop variant am I looking at?" indicator | User generates 3 variants, clicks between them, loses track | Label each variant clearly: "Variant 2 of 3: noir groove" with persistent indicator in `session_state` |
| "Analyze my playing" with no status during MCP call | 10-30s silence feels like the app is broken | Show a streaming progress indicator: "Uploading... Analyzing... Preparing advice..." |
| Generic "invalid input" on bad chord progression | User typed `"Am7b5 Fdim"` and gets a Python error | Validate chord string format eagerly and show "We don't recognize 'Fdim' — try 'F#dim' or 'Fdim7'" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Loop generation:** Visually looks correct in MusicXML — verify bar duration sums and pitch range programmatically, not just by eye
- [ ] **In-browser playback:** `st.audio` widget renders — verify it actually plays the *current* loop, not a cached/stale file from a previous generation
- [ ] **Recording capture:** `st.audio_input` shows a recording button — verify the bytes are in `session_state` after rerun, not just during the callback
- [ ] **MCP analysis:** "Analyze" button works when MCP is running — verify the app shows a clear error state (not traceback) when MCP is stopped
- [ ] **Theory explanation:** Explanation text appears — verify it references the actual notes in the generated loop, not generic advice
- [ ] **Playwright tests pass:** Tests pass on developer machine — verify they pass in a fresh environment without `sleep()` workarounds
- [ ] **Allure reports:** `allure serve` shows tests — verify non-zero test count and that failed tests show screenshots

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Out-of-range pitches shipped to users | MEDIUM | Add `validate_pitch()` as a guard; re-generate all presets through validator; no data migration needed |
| Bar duration mismatch in exported files | MEDIUM | Add sum check; invalidate cached exports; regenerate affected score files |
| Session state not preserved (rerun clobber) | HIGH (requires architectural refactor) | Refactor all generated data to `session_state` from the start; retrofitting after the fact touches every widget interaction |
| Playwright tests all flaky | MEDIUM | Replace all `wait_for_timeout` calls with "Running..." wait pattern; typically 1–2 days of rework |
| Wrong Allure toolchain installed | LOW | `pip uninstall allure-behave; pip install allure-pytest`; rerun tests |
| MCP returns no useful feedback | MEDIUM | Redesign prompt template with structured intermediate; requires 1–3 iterations of manual evaluation |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Out-of-range cello pitches | Phase 1: Generation engine | Unit test: `validate_pitch("B1")` raises; `validate_pitch("G4")` passes |
| Bar duration mismatch | Phase 1: Generation engine | Unit test: bar with wrong rhythm sum raises `ValueError` |
| Streamlit rerun clobbers loop | Phase 1: Streamlit UI architecture | Manual test: generate loop, change any slider, loop still visible |
| Blocking UI on generation | Phase 1 (basic); Phase 3 (MCP async) | Measure: UI responsive within 1s of clicking Generate |
| MCP unavailable crashes app | Phase 3: MCP integration | Integration test: stop MCP server, click Analyze, see graceful message |
| Generic MCP feedback | Phase 3: MCP integration | Human review: 5 explanations mention specific notes from the loop |
| Wrong/jargon theory explanations | Phase 2: Theory explanations | Human review: non-musician test reader understands all explanations |
| Flaky Playwright tests (rerun model) | Phase 4: Testing framework | CI run: 0 flaky failures across 5 consecutive runs |
| Wrong Allure toolchain | Phase 4: Testing framework | First commit: `allure serve` shows non-zero test count |

---

## Sources

- Streamlit session state docs: https://docs.streamlit.io/develop/concepts/architecture/session-state
- `st.audio_input` docs and known issues: https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input
- GitHub issue: `st.audio` plays sped-up on Firefox: https://github.com/streamlit/streamlit/issues/9799
- GitHub issue: `st.audio_input` fails > 10s on EC2: https://github.com/streamlit/streamlit/issues/9892
- Streamlit background task discussion: https://discuss.streamlit.io/t/how-to-run-a-background-task-in-streamlit-and-notify-the-ui-when-it-finishes/95033
- Testing Streamlit with Playwright (Playwright "Running..." wait pattern): https://www.stefsmeets.nl/posts/streamlit-pytest/
- Playwright WebSocket testing docs: https://playwright.dev/docs/api/class-websocket
- Flaky Playwright tests analysis: https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/
- Allure + Playwright Python (GitHub issue confirming `allure-pytest` path): https://github.com/microsoft/playwright-python/issues/1265
- Allure + Playwright setup guide: https://allurereport.org/docs/playwright/
- music21 TimeSignature barDuration: https://music21.org/music21docs/moduleReference/moduleMeterBase.html
- music21 Chapter 14 (Time Signatures): https://music21.org/music21docs/usersGuide/usersGuide_14_timeSignatures.html
- Cello range reference: https://www.mathew-arrellin.com/blog/cello-range
- Cello orchestration reference: https://arranging.fandom.com/wiki/Cello
- MCP best practices (graceful degradation): https://modelcontextprotocol.info/docs/best-practices/
- MCP long-running tasks pattern: https://agnost.ai/blog/long-running-tasks-mcp/
- AI music pedagogy pitfalls: https://act.maydaygroup.org/pedagogy-of-the-prompt-music-education-artificial-intelligence-and-big-tech-magic/

---
*Pitfalls research for: local Streamlit cello loop-coach app (Python/music21 + MCP + Playwright)*
*Researched: 2026-06-22*
