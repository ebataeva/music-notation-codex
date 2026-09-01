"""Loop Coach page: chord input → generate → 3 variant cards side by side.

Phase 4: text output (theory explanation)
Phase 5: OSMD notation rendering + FluidSynth audio playback
Phase 6: export panel (MusicXML, MIDI, audio, image downloads)
Phase 7 LOOP-02: three register-distinct variants shown as parallel cards.
"""

from __future__ import annotations

import base64

from nicegui import app, run, ui

from app.services.generation import available_presets, generate_loop_variants

KEY_TONICS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEY_MODES = ["minor", "major"]

EXAMPLE_CHORDS = "Am F C G"
EXAMPLE_KEY_TONIC = "A"
EXAMPLE_KEY_MODE = "minor"
EXAMPLE_PRESET = "dark_trip_hop"

# OSMD CDN (pinned version, not @latest). Added to the page body once.
OSMD_JS_URL = "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"

SHEERAN_LOOPER_SUPPORT_URL = "https://sheeranloopers.com/support-plus.html"
SHEERAN_LOOPER_MANUAL_URL = (
    "https://cdn.inmusicbrands.com/SLOOPERS/LP2/"
    "Sheeran%20Looper%20%2B%20-%20User%20Guide%20-%20v2.0.0%20%28RevA%29.pdf"
)

TWIN_LOOPER_MANUAL_URL = "https://www.manualslib.com/manual/1334821/Rowin-Twin-Looper.html"
AQUARIUS_PRODUCT_URL = "https://www.joyoaudio.com/product/10.html"

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
_BLOB_KEYS = (
    "musicxml_string",
    "midi_bytes_b64",
    "wav_bytes_b64",
    "violin_wav_bytes_b64",
    "cello_wav_bytes_b64",
)


def _theory_sections(result: dict) -> list[tuple[str, str]]:
    """Return the (title, text) theory pairs that have non-empty text."""
    return [
        ("Why it works", result.get("why_it_works", "")),
        ("How to start", result.get("how_to_start", "")),
        ("How to develop", result.get("how_to_develop", "")),
        ("How to end", result.get("how_to_end", "")),
        ("How to transition", result.get("how_to_transition", "")),
    ]


def _load_osmd_script() -> None:
    """Load the OSMD CDN script into the page body exactly once.

    Must be called during initial page build (create_loop_coach_page), not
    from a later click handler — ui.add_body_html only takes effect while the
    page is still being delivered; calling it afterwards is a silent no-op.
    """
    ui.add_body_html(f'<script src="{OSMD_JS_URL}"></script>')
    ui.add_body_html(f"<script>{OSMD_INIT_SCRIPT}</script>")


def _render_sheeran_looper_guide() -> None:
    """Render a compact, return-safe setup guide for Sheeran Looper+."""

    with (
        ui.expansion(
            "Sheeran Looper+ — Quick Setup",
            icon="settings_input_component",
            value=False,
        )
        .props("data-testid=sheeran-looper-guide")
        .classes("w-full mt-4 border rounded-lg")
    ):
        with ui.column().classes("w-full gap-3 text-sm"):
            ui.label("Power").classes("font-semibold")
            ui.label(
                "Use 9 V DC, 500 mA minimum, center-negative, 2.1 mm barrel, "
                "or four AA batteries."
            )

            ui.label("Mono signal chain").classes("font-semibold")
            ui.label(
                "Cello → INST L (MONO) → MAIN OUT L (MONO) → "
                "Scarlett LINE input → Mac. Keep 48 V off and start with low gain."
            )

            ui.label("Single-mode controls").classes("font-semibold")
            ui.label(
                "Left pedal: Record → Overdub → Play. Right pedal: Stop. "
                "Hold left for Undo/Redo; hold right to permanently clear the current loop."
            )

            ui.label("Tuner").classes("font-semibold")
            ui.label(
                "There is no built-in tuner. Use a clip-on tuner, a phone app, "
                "or a tuner on the connected computer."
            )

            ui.label("Return-safe test").classes("font-semibold")
            ui.label(
                "Do not save the test loop, register the device, or update firmware. "
                "Clear the temporary loop when finished."
            )

            with ui.card().classes("w-full p-3 bg-orange-50").tight():
                ui.label("Factory reset — erases all user content").classes(
                    "font-semibold text-orange-900"
                )
                ui.label(
                    "With the Looper+ powered off, hold STOP and the encoder while powering on. "
                    "Push the encoder to proceed, then select YES and push it again. "
                    "This cannot be undone."
                ).classes("text-orange-900")

            with ui.row().classes("gap-4 flex-wrap"):
                ui.link(
                    "Official Looper+ support",
                    SHEERAN_LOOPER_SUPPORT_URL,
                    new_tab=True,
                ).classes("text-blue-600")
                ui.link(
                    "Official user guide v2.0.0",
                    SHEERAN_LOOPER_MANUAL_URL,
                    new_tab=True,
                ).props("data-testid=sheeran-looper-manual-link").classes("text-blue-600")


def _render_pedalboard_guide() -> None:
    """Render the guide for the board this coach is actually played through:
    JOYO Atmosphere -> JOYO Aquarius -> VSN Twin Looper.

    The section that earns its place is the last one. Both loopers on this
    board splice the take at the punch-out point, which is exactly the loop
    seam the generator now closes -- and the two time-based pedals sit
    *before* them, so their tails get printed into that splice.
    """

    with (
        ui.expansion(
            "Pedalboard — Atmosphere → Aquarius → Twin Looper",
            icon="graphic_eq",
            value=False,
        )
        .props("data-testid=pedalboard-guide")
        .classes("w-full mt-4 border rounded-lg")
    ):
        with ui.column().classes("w-full gap-3 text-sm"):
            ui.label("Signal chain").classes("font-semibold")
            ui.label(
                "Cello → Atmosphere (reverb) → Aquarius (delay) → Twin Looper LEFT IN → "
                "LEFT/RIGHT OUT → amp or interface. Both time-based pedals sit before the "
                "loopers, so whatever they are doing at the moment you punch out is printed "
                "into the take and repeats on every pass — you cannot dial it back afterwards."
            )

            ui.label("Two loopers, one master").classes("font-semibold")
            ui.label(
                "The Aquarius has its own 5-minute looper on top of its 8 delay modes, and "
                "the Twin Looper records 10 minutes with unlimited overdubs. Drive one of "
                "them and leave the other on delay-only duty — two splice points fighting "
                "each other is the fastest way to lose the downbeat."
            )

            ui.label("Twin Looper controls").classes("font-semibold")
            ui.label(
                "LOOPER footswitch cycles record → play → overdub; FX footswitch triggers "
                "the play mode set by the toggles. CHANGE picks FORWARD or REVERSE, SPEED "
                "picks NORMAL or FAST, and LEVEL L / LEVEL R trim the two channels "
                "independently. Stereo in and out, 44.1 kHz / 24-bit, true bypass."
            )

            with ui.card().classes("w-full p-3 bg-emerald-50").tight():
                ui.label("Closing the loop cleanly").classes(
                    "font-semibold text-emerald-900"
                )
                ui.label(
                    "The loop the coach generates now comes home: its last note lands "
                    "within a few semitones of its first, so the splice falls on a step "
                    "your hand already knows instead of a two-octave jump. Two things on "
                    "this board can still smear that splice. Set Atmosphere TRAIL to OFF "
                    "while you record the foundation layer, or the reverb tail keeps "
                    "ringing past the punch-out and gets printed on top of the next pass. "
                    "Keep Aquarius F.BACK low for that first layer for the same reason — "
                    "repeats still sounding when you close the loop are baked into the "
                    "seam. Raise both once the foundation is down and you are overdubbing "
                    "over it. Punch out on the beat, not on the decay."
                ).classes("text-emerald-900")

            with ui.row().classes("gap-4 flex-wrap"):
                ui.link(
                    "Twin Looper manual",
                    TWIN_LOOPER_MANUAL_URL,
                    new_tab=True,
                ).props("data-testid=twin-looper-manual-link").classes("text-blue-600")
                ui.link(
                    "JOYO Aquarius R-07",
                    AQUARIUS_PRODUCT_URL,
                    new_tab=True,
                ).classes("text-blue-600")


def _render_variant_cards(results: list[dict], container) -> None:
    """Render up to 3 variant cards side by side inside `container`.

    Each card carries its own OSMD container, audio player, and export buttons
    with per-variant element ids (e.g. osmd-container-0, loop-audio-1,
    download-musicxml-btn-2) for Phase 8 Playwright targeting.
    """
    container.clear()

    with container:
        with ui.row().classes("w-full gap-4 items-start"):
            for i, result in enumerate(results):
                _render_single_variant(i, result)


def _render_single_variant(i: int, result: dict) -> None:
    """Render one variant card with theory, notation, audio, and export."""
    with ui.card().classes("flex-1 min-w-0").props(f'data-testid=variant-card-{i}'):
        with ui.column().classes("w-full gap-2"):
            label_text = result.get("variant_label", f"Variant {i + 1}")
            ui.label(label_text).classes("text-lg font-bold").props(
                f'data-testid=variant-title-{i}'
            )
            bias = result.get("register_bias", "")
            if bias:
                ui.label(f"Register: {bias}").classes("text-xs text-gray-400 uppercase tracking-wide")

            if result.get("error"):
                ui.label(result["error"]).classes("text-red-600 font-bold")
                return

            # Theory section
            for title, text in _theory_sections(result):
                if text:
                    ui.label(title).classes("text-xs font-bold text-gray-500 uppercase tracking-wide mt-3")
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
    """Render looping full-mix and per-instrument audio players."""
    wav_b64 = result.get("wav_bytes_b64", "")
    if not wav_b64:
        ui.label("Audio not available.").classes("text-sm text-gray-400")
        return

    tracks = [("Full duet" if result.get("is_duet") else "Cello loop", "full", wav_b64)]
    if result.get("is_duet"):
        tracks.extend([
            ("Violin", "violin", result.get("violin_wav_bytes_b64", "")),
            ("Cello", "cello", result.get("cello_wav_bytes_b64", "")),
        ])

    ui.label("Rehearsal loops").classes("text-xs font-bold text-gray-500 uppercase tracking-wide mt-3")
    for label, track_id, track_wav_b64 in tracks:
        if not track_wav_b64:
            continue
        ui.label(label).classes("text-sm font-medium text-gray-700")
        ui.html(f"""
        <audio id="loop-audio-{i}-{track_id}" controls loop style="width:100%">
            <source src="data:audio/wav;base64,{track_wav_b64}" type="audio/wav">
            Your browser does not support audio playback.
        </audio>
        """)


def _render_variant_export(i: int, result: dict) -> None:
    """Render download buttons for MusicXML, MIDI, WAV, and SVG for variant i."""
    ui.label("Export").classes("text-xs font-bold text-gray-400 uppercase tracking-wide mt-3")
    with ui.row().classes("gap-2 flex-wrap"):
        musicxml_str = result.get("musicxml_string", "")
        if musicxml_str:
            ui.button("MusicXML", color="primary").on(
                "click",
                lambda c=musicxml_str, idx=i: ui.download(
                    c.encode("utf-8"),
                    filename=f"cello_loop_variant_{idx + 1}.musicxml",
                    media_type="application/vnd.recordare.musicxml+xml",
                ),
            ).props(f'data-testid=download-musicxml-btn-{i}')

        midi_b64 = result.get("midi_bytes_b64", "")
        if midi_b64:
            midi_bytes = base64.b64decode(midi_b64)
            ui.button("MIDI", color="primary").on(
                "click",
                lambda c=midi_bytes, idx=i: ui.download(
                    c,
                    filename=f"cello_loop_variant_{idx + 1}.mid",
                    media_type="audio/midi",
                ),
            ).props(f'data-testid=download-midi-btn-{i}')

        wav_b64 = result.get("wav_bytes_b64", "")
        if wav_b64:
            wav_bytes = base64.b64decode(wav_b64)
            ui.button("WAV", color="primary").on(
                "click",
                lambda c=wav_bytes, idx=i: ui.download(
                    c,
                    filename=f"cello_loop_variant_{idx + 1}.wav",
                    media_type="audio/wav",
                ),
            ).props(f'data-testid=download-audio-btn-{i}')

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
        ).props(f'data-testid=download-svg-btn-{i}')


def create_loop_coach_page():
    """Build the loop coach UI with stable element ids for Playwright (Phase 8)."""

    # Page header
    ui.link("Practice Partner", "/practice").classes("text-sm text-blue-600")
    ui.label("Cello Loop Coach").classes("text-2xl font-bold")
    ui.label("Enter a chord progression, pick a mood, and get a cello loop idea with theory guidance.").classes(
        "text-sm text-gray-500"
    )

    _render_sheeran_looper_guide()
    _render_pedalboard_guide()

    # OSMD must load during initial page build, not after a later click handler.
    _load_osmd_script()

    # Input row
    with ui.row().classes("w-full items-end gap-4"):
        chord_input = (
            ui.input(label="Chord progression", placeholder="Am F C G", value="")
            .props('data-testid=chord-input')
            .classes("flex-grow")
        )

        key_tonic_select = (
            ui.select(
                label="Key tonic",
                options=KEY_TONICS,
                value=EXAMPLE_KEY_TONIC,
            )
            .props('data-testid=key-tonic-select')
        )

        key_mode_select = (
            ui.select(
                label="Key mode",
                options=KEY_MODES,
                value=EXAMPLE_KEY_MODE,
            )
            .props('data-testid=key-mode-select')
        )

        mood_select = (
            ui.select(
                label="Mood",
                options=available_presets(),
                value=EXAMPLE_PRESET,
            )
            .props('data-testid=mood-select')
        )

    # Button row
    with ui.row().classes("gap-4 mt-4"):
        generate_btn = (
            ui.button("Generate", color="primary")
            .props('data-testid=generate-btn')
        )

        example_btn = (
            ui.button("Example input", color="secondary")
            .props('data-testid=example-btn')
        )

    # Error/status area
    status_label = ui.label("").classes("text-sm text-gray-500 mt-2")

    # Loading spinner (hidden by default)
    spinner = ui.spinner("puff", size="lg").classes("mt-4")
    spinner.set_visibility(False)

    # Single variants output container (replaces the 4 flat containers)
    variants_container = ui.element("div").props('data-testid=variants-output').classes("mt-6 w-full")

    # Generation in-flight flag (SAFE-08: debounce double-clicks)
    generating = {"in_flight": False}

    async def do_generate():
        if generating["in_flight"]:
            return
        generating["in_flight"] = True
        generate_btn.disable()
        example_btn.disable()
        spinner.set_visibility(True)
        status_label.text = ""

        results = await run.io_bound(
            generate_loop_variants,
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
            status_label.text = f"Ready — 3 variants (seeds: {', '.join(seeds)})"

        spinner.set_visibility(False)
        example_btn.enable()
        generating["in_flight"] = False
        generate_btn.enable()

    def do_example():
        chord_input.value = EXAMPLE_CHORDS
        key_tonic_select.value = EXAMPLE_KEY_TONIC
        key_mode_select.value = EXAMPLE_KEY_MODE
        mood_select.value = EXAMPLE_PRESET

    generate_btn.on("click", do_generate)
    example_btn.on("click", do_example)

    # Visual separator between input and output
    ui.separator().classes("my-6")

    # Restore state from app.storage on page load (SC-4).
    # Notation/audio are not stored, so we only re-render the theory text.
    last_results = app.storage.user.get("last_results")
    if last_results:
        chord_input.value = app.storage.user.get("last_chords", "")
        mood_select.value = app.storage.user.get("last_preset", EXAMPLE_PRESET)
        key_tonic_select.value = app.storage.user.get("last_key_tonic", EXAMPLE_KEY_TONIC)
        key_mode_select.value = app.storage.user.get("last_key_mode", EXAMPLE_KEY_MODE)
        _render_variant_cards(last_results, variants_container)
        status_label.text = "Restored from previous session — click Generate to refresh notation and audio"
