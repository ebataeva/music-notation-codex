from __future__ import annotations

from core.analysis.analyzer import AnalysisResult
from core.mcp.gateway import AnalysisMCPGateway


def test_gateway_falls_back_to_local_analyzer():
    expected = AnalysisResult(
        pitch_hz=220.0,
        pitch_stability=0.9,
        tempo_bpm=100.0,
        beat_stability=0.8,
        intonation_notes=["Stable"],
        raw_duration_sec=2.0,
    )
    gateway = AnalysisMCPGateway(analyzer=lambda _: expected)

    result, online = gateway.analyze("practice.wav")

    assert result == expected
    assert online is False


def test_gateway_returns_none_when_fallback_fails():
    def broken(_):
        raise RuntimeError("bad audio")

    result, online = AnalysisMCPGateway(analyzer=broken).analyze("bad.wav")

    assert result is None
    assert online is False
