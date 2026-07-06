from __future__ import annotations

from app.services.feedback import FeedbackService
from core.analysis.analyzer import AnalysisResult
from core.mcp.gateway import AnalysisMCPGateway


def _analysis(**overrides) -> AnalysisResult:
    values = {
        "pitch_hz": 220.0,
        "pitch_stability": 0.92,
        "tempo_bpm": 100.0,
        "beat_stability": 0.65,
        "intonation_notes": ["Higher notes need relaxed shifts."],
        "raw_duration_sec": 3.0,
    }
    values.update(overrides)
    return AnalysisResult(**values)


def test_feedback_formats_plain_language_suggestions():
    service = FeedbackService(AnalysisMCPGateway(analyzer=lambda _: _analysis()))

    result = service.analyze("practice.wav")

    assert result.offline is True
    assert result.raw_analysis is not None
    assert any("pitch is stable" in suggestion for suggestion in result.suggestions)
    assert any("metronome" in suggestion for suggestion in result.suggestions)


def test_feedback_enforces_analysis_limit():
    service = FeedbackService(AnalysisMCPGateway(analyzer=lambda _: _analysis()), max_calls=1)

    first = service.analyze("practice.wav")
    second = service.analyze("practice.wav")

    assert first.raw_analysis is not None
    assert second.raw_analysis is None
    assert "limit reached" in second.suggestions[0]


def test_feedback_question_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = FeedbackService(AnalysisMCPGateway(analyzer=lambda _: _analysis()))

    answer = service.answer_question("How is my intonation?", _analysis(pitch_stability=0.5))

    assert "sustained notes" in answer
