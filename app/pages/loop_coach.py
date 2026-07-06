"""Loop Coach page: chord input → generate → theory + notation + playback + export.

Phase 4: text output (theory explanation)
Phase 5: OSMD notation rendering + FluidSynth audio playback
Phase 6: export panel (MusicXML, MIDI, audio, image downloads)
"""

from __future__ import annotations

import base64

from nicegui import app, ui

from app.services.generation import available_presets, generate_loop

KEY_TONICS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_MODES = ["minor", "major"]

EXAMPLE_CHORDS = "Am F C G"
EXAMPLE_KEY_TONIC = "A"
EXAMPLE_KEY_MODE = "minor"
EXAMPLE_PRESET = "dark_trip_hop"

# OSMD CDN (pinned version, not @latest)
OSMD_JS_URL = "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"

OSMD_INIT_SCRIPT = """
// Load OSMD script if not already loaded
function loadOsmd(callback) {
    if (window.osmdLoaded) { callback(); return; }
    var script = document.createElement('script');
    script.src = arguments[0] || 'https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js';
    script.onload = function() { window.osmdLoaded = true; callback(); };
    document.head.appendChild(script);
}
"""


def _render_theory_output(result: dict, container) -> None:
    """Render the 5 TheoryExplanation fields into the container."""
    container.clear()
    with container:
        if result.get("error"):
            ui.label(result["error"]).classes("text-red-600 font-bold")
            return

        sections = [
            ("Why it works", result.get("why_it_works", "")),
            ("How to start", result.get("how_to_start", "")),
            ("How to develop", result.get("how_to_develop", "")),
            ("How to end", result.get("how_to_end", "")),
            ("How to transition", result.get("how_to_transition", "")),
        ]
        for title, text in sections:
            if text:
                ui.label(title).classes("text-lg font-bold mt-4")
                ui.label(text).classes("text-sm text-gray-700")


def _render_notation(result: dict, container) -> None:
    """Render MusicXML as SVG notation via OSMD."""
    container.clear()
    musicxml = result.get("musicxml_string", "")
    if not musicxml:
        return

    with container:
        ui.html(f'<div id="osmd-container" style="width:100%;overflow-x:auto;"></div>')

        # Base64-encode the MusicXML to avoid quoting issues
        xml_b64 = base64.b64encode(musicxml.encode("utf-8")).decode("ascii")

        ui.add_body_html(f'<script src="{OSMD_JS_URL}"></script>')

        ui.run_javascript(f"""
        (function() {{
            var xml = atob("{xml_b64}");
            var container = document.getElementById('osmd-container');
            if (!container) return;
            container.innerHTML = '';

            function render() {{
                try {{
                    var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(container);
                    osmd.load(xml).then(function() {{
                        osmd.setOptions({{
                            autoResize: true,
                            backend: 'svg',
                            drawTitle: false,
                            drawSubtitle: false,
                            drawComposer: false,
                        }});
                        osmd.render();
                    }}).catch(function(e) {{
                        container.innerHTML = '<p style="color:red">Notation render error: ' + e.message + '</p>';
                    }});
                }} catch(e) {{
                    container.innerHTML = '<p style="color:red">OSMD error: ' + e.message + '</p>';
                }}
            }}

            if (window.opensheetmusicdisplay) {{
                render();
            }} else {{
                // Wait for OSMD to load
                var checkInterval = setInterval(function() {{
                    if (window.opensheetmusicdisplay) {{
                        clearInterval(checkInterval);
                        render();
                    }}
                }}, 200);
            }}
        }})();
        """)


def _render_audio(result: dict, container) -> None:
    """Render audio playback widget from WAV bytes."""
    container.clear()
    wav_b64 = result.get("wav_bytes_b64", "")
    if not wav_b64:
        with container:
            ui.label("Audio not available (FluidSynth render failed or not requested).").classes(
                "text-sm text-gray-400"
            )
        return

    # Serve the WAV as a data URL
    audio_html = f"""
    <audio id="loop-audio" controls style="width:100%">
        <source src="data:audio/wav;base64,{wav_b64}" type="audio/wav">
        Your browser does not support audio playback.
    </audio>
    """
    with container:
        ui.html(audio_html).props('id=audio-player')


def _render_export_panel(result: dict, container) -> None:
    """Render download buttons for MusicXML, MIDI, audio, and notation image."""
    container.clear()
    with container:
        ui.label("Download").classes("text-lg font-bold mt-4")
        ui.label("Export the current loop for MuseScore, Ableton, or sharing.").classes(
            "text-sm text-gray-500"
        )

        with ui.row().classes("gap-4 mt-2"):
            # MusicXML download
            musicxml_str = result.get("musicxml_string", "")
            if musicxml_str:
                ui.button("Download MusicXML", color="primary").on(
                    "click",
                    lambda: ui.download(
                        content=musicxml_str.encode("utf-8"),
                        filename="cello_loop.musicxml",
                        media_type="application/vnd.recordare.musicxml+xml",
                    ),
                ).props('id=download-musicxml-btn')

            # MIDI download
            midi_b64 = result.get("midi_bytes_b64", "")
            if midi_b64:
                midi_bytes = base64.b64decode(midi_b64)
                ui.button("Download MIDI", color="primary").on(
                    "click",
                    lambda: ui.download(
                        content=midi_bytes,
                        filename="cello_loop.mid",
                        media_type="audio/midi",
                    ),
                ).props('id=download-midi-btn')

            # Audio (WAV) download
            wav_b64 = result.get("wav_bytes_b64", "")
            if wav_b64:
                wav_bytes = base64.b64decode(wav_b64)
                ui.button("Download audio (WAV)", color="primary").on(
                    "click",
                    lambda: ui.download(
                        content=wav_bytes,
                        filename="cello_loop.wav",
                        media_type="audio/wav",
                    ),
                ).props('id=download-audio-btn')

            # Notation image (SVG from OSMD container)
            ui.button("Download notation (SVG)", color="secondary").on(
                "click",
                lambda: ui.run_javascript("""
                (function() {
                    var svg = document.querySelector('#osmd-container svg');
                    if (!svg) { alert('No notation rendered yet.'); return; }
                    var serializer = new XMLSerializer();
                    var svgStr = serializer.serializeToString(svg);
                    var blob = new Blob([svgStr], {type: 'image/svg+xml'});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = 'cello_loop_notation.svg';
                    a.click();
                    URL.revokeObjectURL(url);
                })();
                """),
            ).props('id=download-svg-btn')


def create_loop_coach_page():
    """Build the loop coach UI with stable element ids for Playwright (Phase 8)."""

    # Page header
    ui.label("Cello Loop Coach").classes("text-2xl font-bold")
    ui.label("Enter a chord progression, pick a mood, and get a cello loop idea with theory guidance.").classes(
        "text-sm text-gray-500"
    )

    # Input row
    with ui.row().classes("w-full items-end gap-4"):
        chord_input = (
            ui.input(label="Chord progression", placeholder="Am F C G", value="")
            .props('id=chord-input')
            .classes("flex-grow")
        )

        key_tonic_select = (
            ui.select(
                label="Key tonic",
                options=KEY_TONICS,
                value=EXAMPLE_KEY_TONIC,
            )
            .props('id=key-tonic-select')
        )

        key_mode_select = (
            ui.select(
                label="Key mode",
                options=KEY_MODES,
                value=EXAMPLE_KEY_MODE,
            )
            .props('id=key-mode-select')
        )

        mood_select = (
            ui.select(
                label="Mood",
                options=available_presets(),
                value=EXAMPLE_PRESET,
            )
            .props('id=mood-select')
        )

    # Button row
    with ui.row().classes("gap-4 mt-4"):
        generate_btn = (
            ui.button("Generate", color="primary")
            .props('id=generate-btn')
        )

        example_btn = (
            ui.button("Example input", color="secondary")
            .props('id=example-btn')
        )

    # Error/status area
    status_label = ui.label("").classes("text-sm text-gray-500 mt-2")

    # Output containers with stable ids
    theory_container = ui.element("div").props('id=theory-output').classes("mt-6 w-full")
    notation_container = ui.element("div").props('id=notation-output').classes("mt-6 w-full")
    audio_container = ui.element("div").props('id=audio-output').classes("mt-4 w-full")
    export_container = ui.element("div").props('id=export-output').classes("mt-6 w-full")

    # Generation in-flight flag (SAFE-08: debounce double-clicks)
    generating = {"in_flight": False}

    def do_generate():
        if generating["in_flight"]:
            return
        generating["in_flight"] = True
        generate_btn.disable()
        status_label.text = "Generating..."

        result = generate_loop(
            chord_progression=chord_input.value,
            preset_name=mood_select.value,
            include_audio=True,
        )

        # Persist to app.storage for refresh survival (SC-4)
        # Store without the large base64 strings to avoid storage bloat;
        # only theory text + seed survive refresh. Notation/audio regenerate on click.
        storage_result = {k: v for k, v in result.items() if k not in ("musicxml_string", "midi_bytes_b64", "wav_bytes_b64")}
        app.storage.user["last_result"] = storage_result
        app.storage.user["last_chords"] = chord_input.value
        app.storage.user["last_preset"] = mood_select.value
        app.storage.user["last_key_tonic"] = key_tonic_select.value
        app.storage.user["last_key_mode"] = key_mode_select.value

        _render_theory_output(result, theory_container)
        _render_notation(result, notation_container)
        _render_audio(result, audio_container)
        _render_export_panel(result, export_container)

        if result.get("error"):
            status_label.text = "Generation failed."
        else:
            seed_str = result.get("seed", "?")
            status_label.text = f"Generated (seed: {seed_str})."
            if result.get("audio_error"):
                status_label.text += f" Audio: {result['audio_error']}"

        generating["in_flight"] = False
        generate_btn.enable()

    def do_example():
        chord_input.value = EXAMPLE_CHORDS
        key_tonic_select.value = EXAMPLE_KEY_TONIC
        key_mode_select.value = EXAMPLE_KEY_MODE
        mood_select.value = EXAMPLE_PRESET

    generate_btn.on("click", do_generate)
    example_btn.on("click", do_example)

    # Restore state from app.storage on page load (SC-4)
    last_result = app.storage.user.get("last_result")
    if last_result:
        chord_input.value = app.storage.user.get("last_chords", "")
        mood_select.value = app.storage.user.get("last_preset", EXAMPLE_PRESET)
        key_tonic_select.value = app.storage.user.get("last_key_tonic", EXAMPLE_KEY_TONIC)
        key_mode_select.value = app.storage.user.get("last_key_mode", EXAMPLE_KEY_MODE)
        _render_theory_output(last_result, theory_container)
        status_label.text = "Restored from previous session (click Generate to refresh notation and audio)."
