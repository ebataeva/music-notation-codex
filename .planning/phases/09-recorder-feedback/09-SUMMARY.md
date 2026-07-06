---
phase: 09-recorder-feedback
plan: 09
subsystem: app
tags: [nicegui, audio-analysis, feedback, mcp-fallback]

requires:
  - phase: 08-ui-test-framework
provides:
  - core/analysis/analyzer.py local WAV analysis with pitch, tempo, stability, and intonation notes
  - core/mcp/gateway.py AnalysisMCPGateway fallback abstraction for future external MCP wiring
  - app/services/feedback.py plain-language suggestions and question answering fallback
  - app/pages/recorder.py NiceGUI Practice Partner page at /practice

key-files:
  created:
    - core/analysis/__init__.py
    - core/analysis/analyzer.py
    - core/mcp/__init__.py
    - core/mcp/gateway.py
    - app/services/feedback.py
    - app/pages/recorder.py
    - tests/test_analysis.py
    - tests/test_mcp_gateway.py
    - tests/test_feedback.py
  modified:
    - app/main.py
    - app/pages/loop_coach.py
    - requirements.txt

requirements-completed: [FEEDBACK-01, FEEDBACK-02, FEEDBACK-03, FEEDBACK-04, SAFE-04, SAFE-05]
completed: 2026-07-06
---

# Phase 9: MCP Gateway + Recorder + Feedback Summary

Implemented the Practice Partner flow: `/practice` can record browser audio as WAV, upload WAV files, run local analysis, display plain-language practice suggestions, and answer questions from the latest analysis with DeepSeek when configured or a deterministic cello-teacher fallback when not.

## Accomplishments

- Added `AnalysisResult` plus local analysis for pitch, tempo, pitch stability, beat stability, duration, and practical intonation notes.
- Added `AnalysisMCPGateway` as the stable abstraction layer; Phase 9 ships with local fallback because no external Audio Analysis MCP server exists yet.
- Added `FeedbackService` with a 5-analysis session limit, local/offline status, suggestion formatting, and 500-word Q&A truncation.
- Added NiceGUI `/practice` page with Record, Stop, Upload WAV, Analyze, and Ask controls, plus status banner and feedback cards.
- Linked the main Loop Coach page to Practice Partner.
- Fixed NiceGUI storage setup by passing `storage_secret` directly to `ui.run()`.
- Added dependencies to `requirements.txt`: `librosa>=0.11.0`, `scipy>=1.14.0`, and `mcp>=1.9,<2`.

## Verification

- `.venv/bin/python -m pytest tests/test_analysis.py tests/test_mcp_gateway.py tests/test_feedback.py -q` -> 8 passed.
- `.venv/bin/python -m pytest tests/ -q` -> 137 passed, 1 existing warning.
- `NICEGUI_PORT=8091 .venv/bin/python app/main.py` starts successfully outside sandbox.
- `GET /` -> 200; `GET /practice` -> 200.

## Notes

- The current venv did not have `librosa`, `scipy`, or `mcp` installed during execution, so the analyzer uses optional imports and keeps a `soundfile`/`numpy` fallback path. Installing the updated requirements enables the planned library path without changing callers.
- Browser recording is encoded to WAV client-side with Web Audio so the local analyzer receives a real WAV file instead of a browser-specific MediaRecorder container.
