"""Loop Coach page: chord input → generate → 3 variant cards side by side.

Phase 4: text output (theory explanation)
Phase 5: OSMD notation rendering + FluidSynth audio playback
Phase 6: export panel (MusicXML, MIDI, audio, image downloads)
Phase 7 LOOP-02: three register-distinct variants shown as parallel cards.
"""

from __future__ import annotations

import base64

from nicegui import app, ui

from app.services.generation import available_presets, generate_loop_variants

KEY_TONICS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_MODES = ["minor", "major"]

EXAMPLE_CHORDS = "Am F C G"
EXAMPLE_KEY_TONIC = "A"
EXAMPLE_KEY_MODE = "minor"
EXAMPLE_PRESET = "dark_trip_hop"

# OSMD CDN (pinned version, not @latest). Added to the page body once.
OSMD_JS_URL = "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"

# Inline helper kept for parity with earlier phases; the CDN <script> tag below
# is the primary load path, but loadOsmd remains available to client code.
OSMD_INIT_SCRIPT = """
function loadOsmd(callback) {
    if (window.osmdLoaded) { callback(); return; }
    var script = document.createElement('script');
    script.src = arguments[0] || 'https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js';
    script.onload = function() { window.osmdLoaded = true; callback(); };
    document.head.appendChild(script);
}
"""

# Keys stripped from each variant before persisting to app.storage (too large).
_BLOB_KEYS = ("musicxml_string", "midi_bytes_b64", "wav_bytes_b64")


def _theory_sections(result: dict) -> list[tuple[str, str]]:
    """Return the (title, text) theory pairs that have non-empty text."""
    return [
        ("Why it works", result.get("why_it_works", "")),
        ("How to start", result.get("how_to_start", "")),
        ("How to develop", result.get("how_to_develop", "")),
        ("How to end", result.get("how_to_end", "")),
        ("How to transition", result.get("how_to_transition", "")),
    ]


def _render_variant_cards(results: list[dict], container) -> None:
    """Render up to 3 variant cards side by side inside `container`.

    Each card carries its own OSMD container, audio player, and export buttons
    with per-variant element ids (e.g. osmd-container-0, loop-audio-1,
    download-musicxml-btn-2) for Phase 8 Playwright targeting.
    """
    container.clear()

    # Make sure OSMD is available on the page exactly once.
    ui.add_body_html(f'<script src="{OSMD_JS_URL}"></script>')
    ui.add_body_html(f"<script>{OSMD_INIT_SCRIPT}</script>")

    with container:
        with ui.row().classes("w-full gap-4 items-start"):
            for i, result in enumerate(results):
                _render_single_variant(i, result)


def _render_single_variant(i: int, result: dict) -> None:
    """Render one variant card with theory, notation, audio, and export."""
    with ui.card().classes("flex-1 min-w-0").props(f'id=variant-card-{i}'):
        with ui.column().classes("w-full gap-2"):
            ui.label(f"Variant {i + 1}").classes("text-lg font-bold").props(
                f'id=variant-title-{i}'
            )
            ui.label(result.get("variant_label", "")).classes("text-sm text-gray-500")

            if result.get("error"):
                ui.label(result["error"]).classes("text-red-600 font-bold")
                return

            # Theory section
            for title, text in _theory_sections(result):
                if text:
                    ui.label(title).classes("text-sm font-bold mt-2")
                    ui.label(text).classes("text-sm text-gray-700")

            _render_variant_notation(i, result)
            _render_variant_audio(i, result)
            _render_variant_export(i, result)


def _render_variant_notation(i: int, result: dict) -> None:
    """Render MusicXML as SVG notation via OSMD into variant i's container."""
    musicxml = result.get("musicxml_string", "")
    if not musicxml:
        return

    ui.html(
        f'<div id="osmd-container-{i}" style="width:100%;overflow-x:auto;min-height:120px;"></div>'
    )

    # Base64-encode the MusicXML to avoid quoting issues
    xml_b64 = base64.b64encode(musicxml.encode("utf-8")).decode("ascii")

    ui.run_javascript(
        f"""
        (function() {{
            var xml = atob("{xml_b64}");
            var container = document.getElementById('osmd-container-{i}');
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
                var checkInterval = setInterval(function() {{
                    if (window.opensheetmusicdisplay) {{
                        clearInterval(checkInterval);
                        render();
                    }}
                }}, 200);
            }}
        }})();
        """
    )


def _render_variant_audio(i: int, result: dict) -> None:
    """Render audio playback widget for variant i from WAV bytes."""
    wav_b64 = result.get("wav_bytes_b64", "")
    if not wav_b64:
        ui.label("Audio not available.").classes("text-sm text-gray-400")
        return

    audio_html = f"""
    <audio id="loop-audio-{i}" controls style="width:100%">
        <source src="data:audio/wav;base64,{wav_b64}" type="audio/wav">
        Your browser does not support audio playback.
    </audio>
    """
    ui.html(audio_html)


def _render_variant_export(i: int, result: dict) -> None:
    """Render download buttons for MusicXML, MIDI, WAV, and SVG for variant i."""
    with ui.row().classes("gap-2 mt-2 flex-wrap"):
        musicxml_str = result.get("musicxml_string", "")
        if musicxml_str:
            ui.button("MusicXML", color="primary").on(
                "click",
                lambda c=musicxml_str, idx=i: ui.download(
                    content=c.encode("utf-8"),
                    filename=f"cello_loop_variant_{idx + 1}.musicxml",
                    media_type="application/vnd.recordare.musicxml+xml",
                ),
            ).props(f'id=download-musicxml-btn-{i}')

        midi_b64 = result.get("midi_bytes_b64", "")
        if midi_b64:
            midi_bytes = base64.b64decode(midi_b64)
            ui.button("MIDI", color="primary").on(
                "click",
                lambda c=midi_bytes, idx=i: ui.download(
                    content=c,
                    filename=f"cello_loop_variant_{idx + 1}.mid",
                    media_type="audio/midi",
                ),
            ).props(f'id=download-midi-btn-{i}')

        wav_b64 = result.get("wav_bytes_b64", "")
        if wav_b64:
            wav_bytes = base64.b64decode(wav_b64)
            ui.button("WAV", color="primary").on(
                "click",
                lambda c=wav_bytes, idx=i: ui.download(
                    content=c,
                    filename=f"cello_loop_variant_{idx + 1}.wav",
                    media_type="audio/wav",
                ),
            ).props(f'id=download-audio-btn-{i}')

        # SVG is queried from this variant's OSMD container only.
        ui.button("SVG", color="secondary").on(
            "click",
            lambda idx=i: ui.run_javascript(
                f"""
                (function() {{
                    var svg = document.querySelector('#osmd-container-{i} svg');
                    if (!svg) {{ alert('No notation rendered yet for variant {i + 1}.'); return; }}
                    var serializer = new XMLSerializer();
                    var svgStr = serializer.serializeToString(svg);
                    var blob = new Blob([svgStr], {{type: 'image/svg+xml'}});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = 'cello_loop_variant_{i + 1}.svg';
                    a.click();
                    URL.revokeObjectURL(url);
                }})();
                """
            ),
        ).props(f'id=download-svg-btn-{i}')


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

    # Single variants output container (replaces the 4 flat containers)
    variants_container = ui.element("div").props('id=variants-output').classes("mt-6 w-full")

    # Generation in-flight flag (SAFE-08: debounce double-clicks)
    generating = {"in_flight": False}

    def do_generate():
        if generating["in_flight"]:
            return
        generating["in_flight"] = True
        generate_btn.disable()
        status_label.text = "Generating 3 variants..."

        results = generate_loop_variants(
            chord_progression=chord_input.value,
            preset_name=mood_select.value,
            include_audio=True,
            count=3,
        )

        # Persist to app.storage for refresh survival (SC-4).
        # Strip large base64 blobs; only theory text + seeds survive refresh.
        storage_results = [
            {k: v for k, v in r.items() if k not in _BLOB_KEYS} for r in results
        ]
        app.storage.user["last_results"] = storage_results
        app.storage.user["last_chords"] = chord_input.value
        app.storage.user["last_preset"] = mood_select.value
        app.storage.user["last_key_tonic"] = key_tonic_select.value
        app.storage.user["last_key_mode"] = key_mode_select.value

        _render_variant_cards(results, variants_container)

        # Status: show all 3 seeds (or error).
        errors = [r for r in results if r.get("error")]
        if errors:
            status_label.text = "Generation failed."
        else:
            seeds = [str(r.get("seed", "?")) for r in results]
            status_label.text = f"Generated 3 variants (seeds: {', '.join(seeds)})."

        generating["in_flight"] = False
        generate_btn.enable()

    def do_example():
        chord_input.value = EXAMPLE_CHORDS
        key_tonic_select.value = EXAMPLE_KEY_TONIC
        key_mode_select.value = EXAMPLE_KEY_MODE
        mood_select.value = EXAMPLE_PRESET

    generate_btn.on("click", do_generate)
    example_btn.on("click", do_example)

    # Restore state from app.storage on page load (SC-4).
    # Notation/audio are not stored, so we only re-render the theory text.
    last_results = app.storage.user.get("last_results")
    if last_results:
        chord_input.value = app.storage.user.get("last_chords", "")
        mood_select.value = app.storage.user.get("last_preset", EXAMPLE_PRESET)
        key_tonic_select.value = app.storage.user.get("last_key_tonic", EXAMPLE_KEY_TONIC)
        key_mode_select.value = app.storage.user.get("last_key_mode", EXAMPLE_KEY_MODE)
        _render_variant_cards(last_results, variants_container)
        status_label.text = "Restored from previous session (click Generate to refresh notation and audio)."
