"""Audio-analysis gateway with local fallback."""

from __future__ import annotations

from collections.abc import Callable

from core.analysis.analyzer import AnalysisResult, analyze_playing


class AnalysisMCPGateway:
    def __init__(
        self,
        analyzer: Callable[[str], AnalysisResult] = analyze_playing,
        *,
        enable_external: bool = False,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._analyzer = analyzer
        self._enable_external = enable_external
        self._timeout_seconds = timeout_seconds

    def analyze(self, wav_path: str) -> tuple[AnalysisResult | None, bool]:
        result = self._try_mcp(wav_path) if self._enable_external else None
        if result is not None:
            return result, True

        try:
            return self._analyzer(wav_path), False
        except Exception:
            return None, False

    def _try_mcp(self, wav_path: str) -> AnalysisResult | None:
        try:
            import mcp  # noqa: F401
        except Exception:
            return None

        # Phase 9 ships the abstraction before an audio-analysis MCP server exists.
        # A real server can replace this method without changing the app/service layer.
        _ = (wav_path, self._timeout_seconds)
        return None
