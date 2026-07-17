"""Violin + Cello Loop Lab — a friend-shareable demo for music-notation-codex.

Type a chord progression, pick a mood, and get playable string-loop ideas —
solo cello takes or an authored violin+cello duet, with theory and downloads.

This is the deployed Streamlit Cloud app at ear-check.streamlit.app.
Run locally with:

    streamlit run apps/ear_check_streamlit.py
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
from core.presets.registry import list_presets

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FRIENDLY_MOOD: dict[str, str] = {
    "dark_trip_hop": "Dark trip-hop · 72 BPM",
    "ritual_tribal": "Ritual tribal · 88 BPM",
    "noir_slow_burn": "Noir slow burn · 58 BPM",
    "driving_cinematic": "Driving cinematic · 104 BPM",
    "sexy_duet": "Violin + cello sensual duet · 76 BPM",
    "simple_sexy_duet": "Violin + cello intimate duet · 64 BPM",
    "dorian_sexy_duet": "Violin + cello Dorian duet · 88 BPM",
}

_DEFAULT_PROGRESSION = "Dm9 G9 Dm9 G9 Bbmaj7 A7 Dm9 A7"
_DEFAULT_PRESET = "dorian_sexy_duet"


def _preset_index(preset_name: str, presets: list[str] = None) -> int:
    """Index of preset_name in the preset list (safe default)."""
    if presets is None:
        presets = list_presets()
    return presets.index(preset_name) if preset_name in presets else 0


def _mood_label(name: str) -> str:
    friendly = _FRIENDLY_MOOD.get(name, name.replace("_", " ").title())
    return f"{name} · {friendly}"


def _render_notation(musicxml_string: str, uid: str) -> None:
    """Render MusicXML as SVG via OpenSheetMusicDisplay (CDN)."""
    xml_b64 = base64.b64encode(musicxml_string.encode("utf-8")).decode("ascii")
    html = f"""
    <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"></script>
    <div id="osmd-{uid}" style="width:100%;overflow-x:auto;background:#fff;padding:8px 0;"></div>
    <script>
    (function() {{
        var xml = atob("{xml_b64}");
        var c = document.getElementById("osmd-{uid}");
        var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(c, {{
            autoResize: true,
            backend: 'svg',
            drawTitle: false,
            drawSubtitle: false,
            drawComposer: false,
            drawCredits: false,
            scaling: 1.4,
        }});
        osmd.load(xml).then(function() {{
            osmd.render();
        }}).catch(function() {{
            c.innerHTML = '<p style="color:#999;font-size:0.8em">Notation preview unavailable.</p>';
        }});
    }})();
    </script>
    """
    components.html(html, height=280)


@st.cache_data(show_spinner=False)
def _generate(progression: str, preset: str, seed: int) -> list[dict]:
    """Cached generation — FluidSynth is the slow part, caching keeps
    re-renders instant while the user browses results."""
    return generate_loop_variants(
        chord_progression=progression,
        preset_name=preset,
        seed=seed,
        include_audio=True,
        count=3,
    )


def _b64_to_bytes(b64: str) -> bytes:
    return base64.b64decode(b64) if b64 else b""


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Violin + Cello Loop Lab",
    page_icon=":material/music_note:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Header (compact, no debug text) -------------------------------------
st.markdown(
    "<h1 style='margin-bottom:0.15em'>Violin + Cello Loop Lab</h1>"
    "<p style='color:#888;margin-top:0'>Pick a mood and hear a theory-backed string idea: "
    "three cello takes for solo presets, or a ready violin+cello duet for duet presets.</p>",
    unsafe_allow_html=True,
)

# ---- Controls row --------------------------------------------------------
all_presets = list_presets()
preset_labels = [_mood_label(p) for p in all_presets]

c_prog, c_mood, c_ex, c_gen = st.columns([5, 3, 1, 1])

with c_prog:
    _override_prog = st.session_state.pop("_prog_override", None)
    progression = st.text_input(
        "Chord progression",
        value=_override_prog or _DEFAULT_PROGRESSION,
        placeholder="e.g. Dm9 G9 Dm9 G9 Bbmaj7 A7",
    )

with c_mood:
    _override_mood = st.session_state.pop("_mood_override", None)
    _initial_mood = _override_mood or _DEFAULT_PRESET
    chosen_label = st.selectbox(
        "Mood",
        options=preset_labels,
        index=_preset_index(_initial_mood, all_presets),
    )
    preset_name = all_presets[preset_labels.index(chosen_label)]
    st.caption(f"Preset ID: `{preset_name}`")

with c_ex:
    st.write("")  # vertical alignment
    st.write("")
    if st.button("Example", icon=":material/auto_awesome:", width="stretch"):
        st.session_state["_prog_override"] = _DEFAULT_PROGRESSION
        st.session_state["_mood_override"] = _DEFAULT_PRESET
        st.rerun()

with c_gen:
    st.write("")
    st.write("")
    generate_clicked = st.button("Generate", type="primary", icon=":material/play_arrow:", width="stretch")

st.space("small")

# ---- Generation ----------------------------------------------------------
if generate_clicked:
    seed = 0  # deterministic for demo; remove for random each click
    st.session_state["run"] = {"prog": progression, "preset": preset_name, "seed": seed}

run = st.session_state.get("run")

if not run:
    st.caption("Press Generate to hear the Dorian violin+cello showcase, or choose any preset.")
else:
    with st.spinner("Composing string loops..."):
        try:
            results = _generate(run["prog"], run["preset"], run["seed"])
        except Exception as exc:  # noqa: BLE001
            results = [{"error": f"Generation failed: {exc}"}]

    if results and results[0].get("error"):
        st.warning(results[0]["error"])
    else:
        st.caption(f"_{run['prog']} · {_mood_label(run['preset'])}_")

        is_duet = bool(results[0].get("is_duet"))
        cols = st.columns(1 if is_duet else 3)
        for i, (col, r) in enumerate(zip(cols, results)):
            with col:
                bias = r.get("register_bias", "default")
                title = r.get("variant_label") or f"Take {i + 1}"
                st.subheader(title)
                if is_duet:
                    st.caption("Violin melody + cello foundation")
                else:
                    st.caption(f"{bias} register")

                phrase_map = r.get("phrase_map") or []
                if phrase_map:
                    st.markdown(" · ".join(f":blue-badge[{phrase}]" for phrase in phrase_map))
                if r.get("notation_note"):
                    st.caption(r["notation_note"])

                # Notation
                _render_notation(r["musicxml_string"], uid=f"v{i}")

                # Audio
                wav = _b64_to_bytes(r.get("wav_bytes_b64", ""))
                if wav:
                    st.audio(wav, format="audio/wav")
                    src = r.get("audio_source", "")
                    if src == "cello_synth_reverb":
                        st.caption("string synth + reverb" if is_duet else "cello synth + reverb")
                else:
                    st.caption("audio unavailable")

                st.markdown(f"**Why it works:** {r['why_it_works']}")
                with st.expander("Theory and playing advice"):
                    st.markdown(f"**Start:** {r['how_to_start']}")
                    st.markdown(f"**Develop:** {r['how_to_develop']}")
                    st.markdown(f"**End:** {r['how_to_end']}")
                    st.markdown(f"**Transition:** {r['how_to_transition']}")

                d1, d2, d3 = st.columns(3)
                xml_bytes = r["musicxml_string"].encode("utf-8")
                midi_bytes = _b64_to_bytes(r.get("midi_bytes_b64", ""))
                file_stub = "violin_cello_duet" if is_duet else f"take_{i + 1}"
                with d1:
                    st.download_button(
                        "MusicXML",
                        xml_bytes,
                        file_name=f"{file_stub}.musicxml",
                        mime="application/vnd.recordare.musicxml+xml",
                        width="stretch",
                    )
                with d2:
                    st.download_button(
                        "MIDI",
                        midi_bytes,
                        file_name=f"{file_stub}.mid",
                        mime="audio/midi",
                        width="stretch",
                    )
                with d3:
                    st.download_button(
                        "WAV",
                        wav,
                        file_name=f"{file_stub}.wav",
                        mime="audio/wav",
                        width="stretch",
                        disabled=not bool(wav),
                    )
