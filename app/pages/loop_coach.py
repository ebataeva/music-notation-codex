"""Loop Coach page: chord input → generate → 3 variant cards side by side.

Phase 4: text output (theory explanation)
Phase 5: OSMD notation rendering + FluidSynth audio playback
Phase 6: export panel (MusicXML, MIDI, audio, image downloads)
Phase 7 LOOP-02: three register-distinct variants shown as parallel cards.
"""

from __future__ import annotations

import base64

from nicegui import app, run, ui

from app.services.generation import authored_presets, available_presets, generate_loop_variants
from app.services.theory_dictionary import dictionary_entries
from app.pages.theory_dictionary import theory_url
from app.components.notation import load_notation_script, render_musicxml

_THEORY_KEYS = ("why_it_works", "how_to_start", "how_to_develop", "how_to_end", "how_to_transition")
_TERM_TITLES = {entry["id"]: entry["title"] for entry in dictionary_entries()}

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
_BLOB_KEYS = (
    "musicxml_string",
    "midi_bytes_b64",
    "wav_bytes_b64",
    "violin_wav_bytes_b64",
    "cello_wav_bytes_b64",
)


def _theory_sections(result: dict) -> list[tuple[str, str]]:
    """Prefer short explanations while accepting previously stored results."""
    titles = ("Why it works", "How to start", "How to develop", "How to end", "How to transition")
    brief = result.get("short_sections", {})
    return [(title, brief.get(key, result.get(key, ""))) for key, title in zip(_THEORY_KEYS, titles, strict=True)]


def _load_osmd_script() -> None:
    """Load the OSMD CDN script into the page body exactly once.

    Must be called during initial page build (create_loop_coach_page), not
    from a later click handler — ui.add_body_html only takes effect while the
    page is still being delivered; calling it afterwards is a silent no-op.
    """
    load_notation_script()


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

            if result.get("key_tonic"):
                ui.label(f"Reference key: {result['key_tonic']} {result.get('key_mode', '')}").classes("text-sm text-gray-600").props(f'data-testid=variant-key-{i}')
            if result.get("is_duet"):
                ui.label("Authored duet · explanations follow this score").classes("text-sm font-medium")

            for section_index, (title, text) in enumerate(_theory_sections(result)):
                if text:
                    ui.label(title).classes("text-xs font-bold text-gray-500 uppercase tracking-wide mt-3")
                    section_key = _THEORY_KEYS[section_index]
                    ui.label(text).classes("text-sm text-gray-700").props(f'data-testid=theory-{i}-{section_key}')
                    term_ids = result.get("term_ids", {}).get(section_key, ())
                    if term_ids:
                        with ui.row().classes("gap-3"):
                            for term_id in term_ids:
                                if term_id in _TERM_TITLES:
                                    target = theory_url(term_id, result.get("key_tonic", "C"), result.get("key_mode", "major"), result.get("preset_name", ""))
                                    ui.link(_TERM_TITLES[term_id], target, new_tab=True).classes("text-xs text-blue-600").props(f'data-testid=term-{i}-{section_key}-{term_id}')

            _render_variant_notation(i, result)
            _render_variant_audio(i, result)
            _render_variant_export(i, result)


def _render_variant_notation(i: int, result: dict) -> None:
    """Render notation using the same component as the dictionary."""
    render_musicxml(result.get("musicxml_string", ""), f"osmd-container-{i}")


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
        """).classes("w-full")


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
    with ui.row().classes("gap-4"):
        ui.link("Practice Partner", "/practice").classes("text-sm text-blue-600")
        ui.link("Theory Dictionary", "/theory", new_tab=True).classes("text-sm text-blue-600")
    ui.label("Cello Loop Coach").classes("text-2xl font-bold")
    ui.label("Enter a chord progression, pick a mood, and get a cello loop idea with theory guidance.").classes(
        "text-sm text-gray-500"
    )

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
            .classes("w-28")
        )

        key_mode_select = (
            ui.select(
                label="Key mode",
                options=KEY_MODES,
                value=EXAMPLE_KEY_MODE,
            )
            .props('data-testid=key-mode-select')
            .classes("w-28")
        )

        mood_select = (
            ui.select(
                label="Mood",
                options=available_presets(),
                value=EXAMPLE_PRESET,
            )
            .props('data-testid=mood-select')
        )

    authored = authored_presets()
    source_label = ui.label("").classes("text-sm text-gray-600").props("data-testid=score-source")

    def update_source_controls():
        is_authored = mood_select.value in authored
        for control in (chord_input, key_tonic_select, key_mode_select):
            control.set_enabled(not is_authored)
        source_label.text = f"Authored duet in {authored[mood_select.value]}: the fixed score supplies its own notes and harmony." if is_authored else "Your chord progression and selected reference key guide the solo loop."

    mood_select.on_value_change(update_source_controls)
    update_source_controls()

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
            key_tonic=key_tonic_select.value,
            key_mode=key_mode_select.value,
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
            status_label.text = "Ready — authored violin + cello duet" if results[0].get("is_duet") else f"Ready — {len(results)} loop variants"

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
        update_source_controls()
        _render_variant_cards(last_results, variants_container)
        status_label.text = "Restored from previous session — click Generate to refresh notation and audio"
