"""Polished Streamlit showcase for music-notation-codex.

A casual, presentable demo: type a chord progression, pick a mood, get three
playable cello loop variants with theory, notation, audio, and downloads.

This is a showcase surface only -- it reuses the existing
``app.services.generation`` service and touches no core generation logic.
Run with:

    streamlit run apps/demo_streamlit.py
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import streamlit.components.v1 as components

from app.services.generation import generate_loop_variants
from core.presets.registry import list_solo_presets

# A small, friendly label for each solo mood preset.
_MOOD_LABELS: dict[str, str] = {
    "dark_trip_hop": "Dark trip-hop",
    "ritual_tribal": "Ritual tribal",
    "noir_slow_burn": "Noir slow burn",
    "driving_cinematic": "Driving cinematic",
}

_EXAMPLE_PROGRESSION = "Am F C G"
_EXAMPLE_PRESET = "dark_trip_hop"


def _mood_label(name: str) -> str:
    return _MOOD_LABELS.get(name, name.replace("_", " ").title())


@st.cache_data(show_spinner=False)
def _generate(progression: str, preset: str, seed: int) -> list[dict]:
    """Cached wrapper around the generation service.

    Audio rendering (FluidSynth) is the slow part; caching by (progression,
    preset, seed) keeps repeat renders instant while the user browses results.
    """
    return generate_loop_variants(
        chord_progression=progression,
        preset_name=preset,
        seed=seed,
        include_audio=True,
        count=3,
    )


def _render_notation(musicxml_string: str) -> None:
    """Render MusicXML as SVG notation via OpenSheetMusicDisplay."""
    xml_b64 = base64.b64encode(musicxml_string.encode("utf-8")).decode("ascii")
    html = f"""
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"></script>
    <div id="osmd-{id(musicxml_string)}" style="width:100%;overflow-x:auto;min-height:120px;"></div>
    <script>
    (function() {{
        var xml = atob("{xml_b64}");
        var container = document.getElementById("osmd-{id(musicxml_string)}");
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
            container.innerHTML = '<p style="color:#888;font-size:0.8em">Notation unavailable.</p>';
        }});
    }})();
    </script>
    """
    components.html(html, height=200)


def _b64_to_bytes(b64: str) -> bytes:
    return base64.b64decode(b64) if b64 else b""


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cello Loop Lab",
    page_icon="🎻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Quiet header: title + one-line intro, no debug noise.
st.markdown(
    "<h1 style='margin-bottom:0.1em'>🎻 Cello Loop Lab</h1>"
    "<p style='color:#888;margin-top:0'>Type a chord progression, pick a mood, "
    "and get three playable cello loop ideas — each with the theory behind it.</p>",
    unsafe_allow_html=True,
)

# --- Controls -------------------------------------------------------------
solo_presets = list_solo_presets()
preset_options = [_mood_label(p) for p in solo_presets]
default_preset_idx = solo_presets.index(_EXAMPLE_PRESET) if _EXAMPLE_PRESET in solo_presets else 0

col_prog, col_mood, col_example, col_gen = st.columns([5, 3, 1, 1])

with col_prog:
    progression = st.text_input(
        "Chord progression",
        value=st.session_state.get("progression_input", _EXAMPLE_PROGRESSION),
        placeholder="e.g. Am F C G",
        label_visibility="visible",
        key="progression_input",
    )
with col_mood:
    chosen_label = st.selectbox(
        "Mood",
        options=preset_options,
        index=default_preset_idx,
        label_visibility="visible",
    )
    preset_name = solo_presets[preset_options.index(chosen_label)]
with col_example:
    st.write("")  # align with inputs
    st.write("")
    if st.button("✨ Example", use_container_width=True):
        st.session_state["progression_input"] = _EXAMPLE_PROGRESSION
        st.session_state["example_preset"] = _EXAMPLE_PRESET
        st.rerun()
with col_gen:
    st.write("")
    st.write("")
    generate_clicked = st.button("Generate", type="primary", use_container_width=True)

# Apply an example-preset override coming from the Example button.
if "example_preset" in st.session_state:
    preset_name = st.session_state["example_preset"]
    chosen_label = _mood_label(preset_name)

st.divider()

# --- Generation -----------------------------------------------------------
if generate_clicked:
    seed = 0  # deterministic demo seed; change to randomize on each click
    st.session_state["last_run"] = {"progression": progression, "preset": preset_name, "seed": seed}

last_run = st.session_state.get("last_run")

if not last_run:
    st.info("Press **Generate** to hear three cello loop takes on your progression.")
else:
    with st.spinner("Composing cello loops…"):
        try:
            results = _generate(
                last_run["progression"], last_run["preset"], last_run["seed"]
            )
        except Exception as exc:  # noqa: BLE001 -- surface any failure cleanly
            results = [{"error": f"Generation failed: {exc}"}]

    # Surface a single hard failure without crashing the page.
    if results and results[0].get("error"):
        st.warning(results[0]["error"])
    else:
        st.caption(
            f"_{last_run['progression']} · {_mood_label(last_run['preset'])}_"
        )
        cols = st.columns(3)
        for i, (col, result) in enumerate(zip(cols, results)):
            with col:
                st.subheader(f"Take {i + 1}")
                badge = result.get("register_bias", "default")
                st.caption(f"register: {badge}")
                _render_notation(result["musicxml_string"])

                wav = _b64_to_bytes(result.get("wav_bytes_b64", ""))
                if wav:
                    st.audio(wav, format="audio/wav")
                elif result.get("audio_error"):
                    st.caption("🔊 audio unavailable")
                else:
                    st.caption("🔊 audio unavailable")

                st.markdown(f"_{result['why_it_works']}_")
                with st.expander("More theory"):
                    st.markdown(f"**Start:** {result['how_to_start']}")
                    st.markdown(f"**Develop:** {result['how_to_develop']}")
                    st.markdown(f"**End:** {result['how_to_end']}")
                    st.markdown(f"**Transition:** {result['how_to_transition']}")

                d1, d2, d3 = st.columns(3)
                xml_bytes = result["musicxml_string"].encode("utf-8")
                midi_bytes = _b64_to_bytes(result.get("midi_bytes_b64", ""))
                with d1:
                    st.download_button(
                        "MusicXML",
                        xml_bytes,
                        file_name=f"take_{i + 1}.musicxml",
                        mime="application/vnd.recordare.musicxml+xml",
                        use_container_width=True,
                    )
                with d2:
                    st.download_button(
                        "MIDI",
                        midi_bytes,
                        file_name=f"take_{i + 1}.mid",
                        mime="audio/midi",
                        use_container_width=True,
                    )
                with d3:
                    st.download_button(
                        "WAV",
                        wav,
                        file_name=f"take_{i + 1}.wav",
                        mime="audio/wav",
                        use_container_width=True,
                        disabled=not bool(wav),
                    )
