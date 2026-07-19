"""Streamlit Practice Partner page."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.services.feedback import FeedbackService
from core.analysis.analyzer import AnalysisResult
from core.mcp.gateway import AnalysisMCPGateway


def _service() -> FeedbackService:
    if "practice_service" not in st.session_state:
        st.session_state["practice_service"] = FeedbackService(AnalysisMCPGateway())
    return st.session_state["practice_service"]


def _analyze_audio(audio_bytes: bytes, suffix: str) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)
        result = _service().analyze(str(temp_path))
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    st.session_state["practice_suggestions"] = result.suggestions
    st.session_state["practice_offline"] = result.offline
    st.session_state["practice_analysis"] = result.raw_analysis
    st.session_state.pop("practice_answer", None)


def _format_metric(value: float | None, suffix: str = "") -> str:
    return f"{value:.1f}{suffix}" if value is not None else "—"


def _format_percentage(value: float | None) -> str:
    return f"{value * 100:.0f}%" if value is not None else "—"


st.header(":material/mic: Practice Partner")
st.caption("Record or upload a short WAV and get practical feedback on pitch and timing.")

record_tab, upload_tab = st.tabs(["Record", "Upload WAV"])
with record_tab:
    recorded_audio = st.audio_input(
        "Record your playing",
        sample_rate=16000,
        key="practice_recording",
    )
with upload_tab:
    uploaded_audio = st.file_uploader(
        "Upload a WAV file",
        type=["wav"],
        key="practice_upload",
    )

audio_file = recorded_audio or uploaded_audio
if audio_file is not None:
    audio_bytes = audio_file.getvalue()
    st.audio(audio_bytes, format="audio/wav")
    if st.button(
        "Analyze performance",
        type="primary",
        icon=":material/analytics:",
    ):
        with st.spinner("Analyzing pitch and timing..."):
            _analyze_audio(audio_bytes, Path(audio_file.name).suffix or ".wav")

analysis: AnalysisResult | None = st.session_state.get("practice_analysis")
suggestions: list[str] = st.session_state.get("practice_suggestions", [])

if suggestions:
    if analysis is None:
        st.error("Analysis unavailable. Loop coaching still works.", icon=":material/error:")
    elif st.session_state.get("practice_offline", True):
        st.caption("Local analysis is active. External coaching is optional.")

    for suggestion in suggestions:
        with st.container(border=True):
            st.write(suggestion)

if analysis is not None:
    metric_columns = st.columns(5)
    metric_columns[0].metric("Pitch", _format_metric(analysis.pitch_hz, " Hz"))
    metric_columns[1].metric("Pitch stability", _format_percentage(analysis.pitch_stability))
    metric_columns[2].metric("Tempo", _format_metric(analysis.tempo_bpm, " BPM"))
    metric_columns[3].metric("Beat stability", _format_percentage(analysis.beat_stability))
    metric_columns[4].metric("Duration", _format_metric(analysis.raw_duration_sec, " s"))

    with st.form("practice_question_form"):
        question = st.text_input(
            "Ask about your playing",
            placeholder="How can I improve my intonation?",
        )
        ask_clicked = st.form_submit_button(
            "Ask",
            icon=":material/chat:",
        )
    if ask_clicked:
        st.session_state["practice_answer"] = _service().answer_question(question, analysis)

answer = st.session_state.get("practice_answer")
if answer:
    st.markdown(f"**Practice advice**  \n{answer}")
