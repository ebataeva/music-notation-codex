"""Practice Partner page for recording, uploading, and analyzing cello practice."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from nicegui import app, events, ui

from app.services.feedback import FeedbackResult, FeedbackService
from core.analysis.analyzer import AnalysisResult
from core.mcp.gateway import AnalysisMCPGateway


def create_recorder_page() -> None:
    service = FeedbackService(AnalysisMCPGateway())
    state: dict[str, str | AnalysisResult | None] = {"wav_path": None, "analysis": None}

    ui.link("Back to Loop Coach", "/").classes("text-sm text-blue-600")
    ui.label("Practice Partner").classes("text-2xl font-bold")
    ui.label("Record or upload a cello WAV and get practical feedback.").classes("text-sm text-gray-500")

    status = ui.label("Ready — record or upload a WAV to begin").classes("text-sm rounded px-3 py-2 bg-blue-50 text-blue-700")
    suggestions_container = ui.column().classes("w-full gap-2 mt-4")
    answer_label = ui.label("").classes("text-sm text-gray-700 mt-2")
    countdown_label = ui.label("").classes("text-sm text-gray-500")

    _install_recorder_javascript()

    async def start_recording() -> None:
        countdown_label.text = "Recording for up to 60 seconds..."
        await ui.run_javascript("window.practicePartnerStartRecording && window.practicePartnerStartRecording(60)")

    async def stop_recording() -> None:
        result = await ui.run_javascript("window.practicePartnerStopRecording && window.practicePartnerStopRecording()")
        if isinstance(result, str) and result:
            state["wav_path"] = _write_base64_wav(result)
            countdown_label.text = "Recording ready."
        else:
            countdown_label.text = "No recording captured."

    def handle_upload(event: events.UploadEventArguments) -> None:
        suffix = Path(event.name).suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(event.content.read())
            state["wav_path"] = tmp.name
        countdown_label.text = f"Uploaded {event.name}."

    def analyze_recording() -> None:
        wav_path = state.get("wav_path")
        if not isinstance(wav_path, str):
            _render_result(
                FeedbackResult(["Record or upload a WAV before analyzing."], offline=True, raw_analysis=None),
                status,
                suggestions_container,
            )
            return

        result = service.analyze(wav_path)
        state["analysis"] = result.raw_analysis
        app.storage.user["practice_last_analysis"] = (
            result.raw_analysis.__dict__ if result.raw_analysis is not None else None
        )
        _render_result(result, status, suggestions_container)

    def ask_question() -> None:
        answer_label.text = service.answer_question(question_input.value or "", state.get("analysis"))

    ui.separator().classes("my-4")
    with ui.row().classes("gap-3 mt-2 flex-wrap"):
        ui.button("Record", on_click=start_recording, color="primary").props("data-testid=record-btn")
        ui.button("Stop", on_click=stop_recording, color="secondary").props("data-testid=stop-recording-btn")
        ui.button("Analyze", on_click=analyze_recording, color="primary").props("data-testid=analyze-btn")

    ui.upload(on_upload=handle_upload, label="Upload WAV").props("accept=.wav,audio/wav data-testid=upload-wav")

    question_input = ui.input(label="Ask about your playing", placeholder="How is my intonation?").classes("w-full")
    ui.button("Ask", on_click=ask_question, color="secondary").props("data-testid=ask-btn")


def _render_result(result: FeedbackResult, status, container) -> None:
    if result.offline and result.raw_analysis is not None:
        status.text = "MCP offline — local analysis only"
        status.classes(replace="text-sm rounded px-3 py-2 bg-yellow-100 text-yellow-800")
    elif result.raw_analysis is None:
        status.text = "Analysis unavailable. Loop coaching still works."
        status.classes(replace="text-sm rounded px-3 py-2 bg-red-100 text-red-800")
    else:
        status.text = "Analysis available"
        status.classes(replace="text-sm rounded px-3 py-2 bg-green-100 text-green-800")

    container.clear()
    with container:
        for suggestion in result.suggestions:
            with ui.card().classes("w-full p-3").tight().props("data-testid=feedback-card"):
                ui.label(suggestion).classes("text-sm")


def _write_base64_wav(data_url_or_base64: str) -> str:
    data = data_url_or_base64.split(",", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(base64.b64decode(data))
        return tmp.name


def _install_recorder_javascript() -> None:
    ui.add_body_html(
        """
        <script>
        window.practicePartnerAudioContext = null;
        window.practicePartnerProcessor = null;
        window.practicePartnerBuffers = [];
        window.practicePartnerStream = null;
        window.practicePartnerStartRecording = async function(maxSeconds) {
            window.practicePartnerBuffers = [];
            window.practicePartnerStream = await navigator.mediaDevices.getUserMedia({audio: true});
            window.practicePartnerAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            var source = window.practicePartnerAudioContext.createMediaStreamSource(window.practicePartnerStream);
            window.practicePartnerProcessor = window.practicePartnerAudioContext.createScriptProcessor(4096, 1, 1);
            window.practicePartnerProcessor.onaudioprocess = function(event) {
                window.practicePartnerBuffers.push(new Float32Array(event.inputBuffer.getChannelData(0)));
            };
            source.connect(window.practicePartnerProcessor);
            window.practicePartnerProcessor.connect(window.practicePartnerAudioContext.destination);
            setTimeout(function() {
                if (window.practicePartnerProcessor) {
                    window.practicePartnerStopRecording();
                }
            }, maxSeconds * 1000);
            return true;
        };
        window.practicePartnerStopRecording = async function() {
            if (!window.practicePartnerAudioContext) return "";
            var sampleRate = window.practicePartnerAudioContext.sampleRate;
            if (window.practicePartnerProcessor) {
                window.practicePartnerProcessor.disconnect();
                window.practicePartnerProcessor = null;
            }
            if (window.practicePartnerStream) {
                window.practicePartnerStream.getTracks().forEach(function(track) { track.stop(); });
            }
            await window.practicePartnerAudioContext.close();
            window.practicePartnerAudioContext = null;
            var totalLength = window.practicePartnerBuffers.reduce(function(sum, b) { return sum + b.length; }, 0);
            var samples = new Float32Array(totalLength);
            var offset = 0;
            window.practicePartnerBuffers.forEach(function(buffer) {
                samples.set(buffer, offset);
                offset += buffer.length;
            });
            var wav = window.practicePartnerEncodeWav(samples, sampleRate);
            var blob = new Blob([wav], {type: 'audio/wav'});
            return await new Promise(function(resolve) {
                var reader = new FileReader();
                reader.onloadend = function() { resolve(reader.result); };
                reader.readAsDataURL(blob);
            });
        };
        window.practicePartnerEncodeWav = function(samples, sampleRate) {
            var buffer = new ArrayBuffer(44 + samples.length * 2);
            var view = new DataView(buffer);
            function writeString(offset, string) {
                for (var i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
            }
            writeString(0, 'RIFF');
            view.setUint32(4, 36 + samples.length * 2, true);
            writeString(8, 'WAVE');
            writeString(12, 'fmt ');
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true);
            view.setUint16(22, 1, true);
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);
            writeString(36, 'data');
            view.setUint32(40, samples.length * 2, true);
            var offset = 44;
            for (var i = 0; i < samples.length; i++, offset += 2) {
                var sample = Math.max(-1, Math.min(1, samples[i]));
                view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
            }
            return view;
        };
        </script>
        """
    )
