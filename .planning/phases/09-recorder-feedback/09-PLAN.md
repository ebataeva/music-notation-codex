# Phase 9 Plan: MCP Gateway + Recorder + Feedback

**Written:** 2026-07-06
**For:** Codex to execute
**Status:** completed

## Context

Phase 9 of music-notation-codex adds a "Practice Partner" page: user records cello playing in browser → gets analysis and improvement suggestions → can ask questions about their playing or loops.

Audio Analysis MCP server does NOT exist. Instead, use **librosa locally** in the app. MCP gateway acts as a stub/abstraction layer.

## What Already Exists

- NiceGUI app at `app/main.py` (loop coach page working)
- `core/` library: engine, export, models, presets, theory
- `app/pages/loop_coach.py` — main loop coach page
- `app/services/generation.py` — generation service
- `.planning/research/ARCHITECTURE.md` — full data flow diagram
- `.planning/research/STACK.md` — tech stack decisions
- `.planning/research/PITFALLS.md` — pitfall #5 (MCP unavailability)

## What To Build

### New Files

#### 1. `core/analysis/__init__.py`
Empty init.

#### 2. `core/analysis/analyzer.py`
Local audio analysis using librosa. No MCP dependency.

```python
# Functions:
# - analyze_pitch(wav_path: str) -> dict  # YIN pitch detection, returns avg pitch, pitch stability, intonation notes
# - analyze_tempo(wav_path: str) -> dict  # beat tracking, returns BPM, beat stability
# - analyze_playing(wav_path: str) -> AnalysisResult  # combined analysis
```

Dataclass:
```python
@dataclass
class AnalysisResult:
    pitch_hz: float | None        # average detected pitch
    pitch_stability: float | None  # 0-1 how stable
    tempo_bpm: float | None
    beat_stability: float | None   # 0-1
    intonation_notes: list[str]    # e.g. ["slightly sharp on higher notes"]
    raw_duration_sec: float
```

#### 3. `core/mcp/__init__.py`
Empty init.

#### 4. `core/mcp/gateway.py`
MCP abstraction layer. Tries external MCP → falls back to local analyzer.

```python
class AnalysisMCPGateway:
    def analyze(self, wav_path: str) -> tuple[AnalysisResult | None, bool]:
        """
        Returns (result, is_mcp_online).
        Tries external MCP connection. If unavailable,
        falls back to local analyzer.
        """
```

External MCP connection attempt: use `mcp` Python SDK (`stdio_client` + `ClientSession`). Wrap in try/except (ConnectionRefusedError, TimeoutError). Timeout: 30 seconds.

#### 5. `app/services/feedback.py`
Takes AnalysisResult → formats plain-language suggestions.

```python
class FeedbackService:
    def __init__(self, gateway: AnalysisMCPGateway):
        ...

    def analyze(self, wav_path: str) -> FeedbackResult:
        """
        Calls gateway, formats results into user-friendly text.
        Returns FeedbackResult with suggestions list and offline flag.
        """

@dataclass
class FeedbackResult:
    suggestions: list[str]
    offline: bool
    raw_analysis: AnalysisResult | None
```

Example suggestions:
- "Your pitch is stable — good intonation!"
- "The tempo varies between 98-104 BPM. Try practicing with a metronome at 100 BPM."
- "Higher notes (above A3) tend slightly sharp — relax your bow arm on the upper strings."

#### 6. `app/pages/recorder.py`
New NiceGUI page: "Practice Partner".

Route: `/practice`

Features:
- **Record button**: uses JavaScript `MediaRecorder` API via `ui.run_javascript()`
- **Upload button**: fallback for pre-recorded WAV files
- **Analyze button**: sends WAV to FeedbackService → displays suggestions as cards
- **Status banner**: "Analysis available" (green) or "MCP offline — local analysis only" (yellow)
- **Q&A input**: text input + "Ask" button → sends question + recent analysis context to DeepSeek API → displays answer
- **Graceful degradation**: if ALL analysis fails → "Analysis unavailable. Loop coaching still works."

Recording limit: 60 seconds max (show countdown in UI).

#### 7. Tests

- `tests/test_analysis.py` — unit tests for analyzer (use synthetic WAV generated with `scipy`)
- `tests/test_mcp_gateway.py` — mock MCP, test fallback path
- `tests/test_feedback.py` — verify suggestions formatting

### Modified Files

#### `app/main.py`
Add new route:
```python
from app.pages.recorder import create_recorder_page

@ui.page("/practice")
def practice_page():
    create_recorder_page()
```

Add link from main page to /practice.

#### `requirements.txt`
Add:
```
librosa>=0.11.0
scipy>=1.14.0
mcp>=1.9,<2
```

### Requirements Covered

- FEEDBACK-01: Record cello playing in browser ✓
- FEEDBACK-02: Plain-language analysis suggestions ✓ (via librosa local analysis)
- FEEDBACK-03: On-demand Q&A ✓ (via DeepSeek API, already configured)
- FEEDBACK-04: Graceful degradation ✓ (try MCP → fallback local → fallback "unavailable")
- SAFE-04: MCP rate limit — 5 analysis calls per session ✓
- SAFE-05: Max explanation length — truncate at 500 words ✓

## Architecture Decision

**No external MCP server for v1.** The MCP gateway (`core/mcp/gateway.py`) is built as an abstraction with `try/except` → local librosa fallback. This satisfies FEEDBACK-04 (graceful degradation) and avoids the chicken-and-egg problem of needing an MCP server that doesn't exist.

When a real Audio Analysis MCP server is built later, swap the gateway's `_try_mcp()` method — no other code changes.

## Q&A Implementation (FEEDBACK-03)

Use DeepSeek API directly (already configured in codewhale config). The app already has `OPENAI_API_KEY` / DeepSeek endpoint access. Send:

```
System: You are a cello teacher. Analyze the playing data and answer the question.
Context: Recording analysis: {json.dumps(analysis_result)}
Question: {user_question}
```

With max_tokens=300. Graceful fallback if API unavailable.

## Verification

1. `python app/main.py` → opens at localhost:8080
2. Navigate to /practice
3. Record 5 seconds of audio (or upload test WAV)
4. Click "Analyze" → see plain-language suggestions
5. Click "Ask" → type "how is my intonation?" → see relevant answer
6. Kill MCP (or leave it unconfigured) → see yellow banner, local analysis still works
7. `pytest tests/ -k analysis` → pass

## Order of Execution

1. `core/analysis/analyzer.py` + `AnalysisResult` dataclass
2. `core/mcp/gateway.py` (stub: skip MCP, go straight to local)
3. `app/services/feedback.py` + `FeedbackResult`
4. `app/pages/recorder.py` (UI)
5. `app/main.py` route
6. Tests
7. requirements.txt update
