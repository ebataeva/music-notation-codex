"""Plain-language feedback service for practice recordings."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from core.analysis.analyzer import AnalysisResult
from core.mcp.gateway import AnalysisMCPGateway

MAX_QA_WORDS = 500


@dataclass(frozen=True)
class FeedbackResult:
    suggestions: list[str]
    offline: bool
    raw_analysis: AnalysisResult | None


class FeedbackService:
    def __init__(self, gateway: AnalysisMCPGateway, max_calls: int = 5) -> None:
        self._gateway = gateway
        self._max_calls = max_calls
        self._calls = 0

    def analyze(self, wav_path: str) -> FeedbackResult:
        if self._calls >= self._max_calls:
            return FeedbackResult(
                suggestions=["Analysis limit reached for this session. Try again after refreshing the page."],
                offline=True,
                raw_analysis=None,
            )

        self._calls += 1
        analysis, is_mcp_online = self._gateway.analyze(wav_path)
        if analysis is None:
            return FeedbackResult(
                suggestions=["Analysis unavailable. Loop coaching still works."],
                offline=True,
                raw_analysis=None,
            )

        return FeedbackResult(
            suggestions=self._format_suggestions(analysis),
            offline=not is_mcp_online,
            raw_analysis=analysis,
        )

    def answer_question(self, question: str, analysis: AnalysisResult | None) -> str:
        clean_question = question.strip()
        if not clean_question:
            return "Ask a specific question about intonation, timing, or bow control."

        if analysis is None:
            return "I need a recent analysis first. Record or upload a short WAV, then ask again."

        answer = self._ask_deepseek(clean_question, analysis)
        if answer:
            return _truncate_words(answer, MAX_QA_WORDS)

        return self._fallback_answer(clean_question, analysis)

    def _format_suggestions(self, analysis: AnalysisResult) -> list[str]:
        suggestions: list[str] = []
        if analysis.pitch_stability is not None:
            if analysis.pitch_stability >= 0.85:
                suggestions.append("Your pitch is stable — good intonation!")
            elif analysis.pitch_stability >= 0.6:
                suggestions.append("Your pitch is mostly centered. Slow practice can make the start of each note cleaner.")
            else:
                suggestions.append("Pitch is moving around. Try one sustained note with a relaxed bow before playing the loop.")

        if analysis.tempo_bpm is not None:
            tempo = round(analysis.tempo_bpm)
            if analysis.beat_stability is not None and analysis.beat_stability < 0.7:
                suggestions.append(f"The tempo is around {tempo} BPM but it varies. Try a metronome at {tempo} BPM.")
            else:
                suggestions.append(f"Tempo sits around {tempo} BPM. Keep that pulse while changing strings.")

        suggestions.extend(analysis.intonation_notes)
        if not suggestions:
            suggestions.append("Analysis unavailable. Loop coaching still works.")
        return suggestions

    def _ask_deepseek(self, question: str, analysis: AnalysisResult) -> str | None:
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        payload = {
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cello teacher. Use the playing analysis to answer briefly and practically.",
                },
                {
                    "role": "user",
                    "content": (
                        "Recording analysis: "
                        + json.dumps(asdict(analysis), ensure_ascii=True)
                        + "\nQuestion: "
                        + question
                    ),
                },
            ],
            "max_tokens": 300,
        }
        endpoint = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            return None

        choices = data.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message") or {}
        content = message.get("content")
        return content if isinstance(content, str) else None

    def _fallback_answer(self, question: str, analysis: AnalysisResult) -> str:
        q = question.lower()
        if "intonation" in q or "pitch" in q:
            if analysis.pitch_stability is not None and analysis.pitch_stability >= 0.85:
                return "Your intonation looks stable. Keep listening for clean note starts and relaxed shifts."
            return "Focus on slower sustained notes first. The analysis suggests pitch stability can improve before adding tempo."
        if "tempo" in q or "rhythm" in q or "timing" in q:
            if analysis.tempo_bpm is None:
                return "I could not detect a clear pulse. Try recording with a stronger attack on the beat."
            return f"Practice with a metronome around {round(analysis.tempo_bpm)} BPM and keep the bow changes even."
        return "Start with intonation and timing: one clear sustained tone, then the loop at a slow steady pulse."


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."
