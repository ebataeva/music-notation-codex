"""Cloud-compatible audio rendering page."""

from __future__ import annotations

import streamlit as st

from apps.streamlit_shared import (
    DEFAULT_PROGRESSION,
    audio_source_label,
    decode_b64,
    default_preset_index,
    generate_cached,
    preset_from_label,
    preset_label,
    preset_names,
)


st.header(":material/graphic_eq: Cloud audio")
st.caption(
    "Render WAV previews with the latest engine. When FluidSynth is unavailable, "
    "the app automatically uses the cloud-safe string synth and reverb fallback."
)

names = preset_names()
labels = [preset_label(name) for name in names]

progression_col, preset_col, action_col = st.columns([5, 3, 2], vertical_alignment="bottom")
with progression_col:
    progression = st.text_input(
        "Chord progression",
        value=DEFAULT_PROGRESSION,
        placeholder="e.g. Dm9 G9 Bbmaj7 A7",
        key="audio_progression",
    )
with preset_col:
    selected_label = st.selectbox(
        "Style preset",
        labels,
        index=default_preset_index(names),
        key="audio_preset",
    )
with action_col:
    render_clicked = st.button(
        "Render audio",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    )

if render_clicked:
    with st.spinner("Rendering audio..."):
        st.session_state["audio_results"] = generate_cached(
            progression,
            preset_from_label(selected_label, names),
            include_audio=True,
        )

results = st.session_state.get("audio_results")
if not results:
    st.caption("Choose a progression and style, then render the audio preview.")
elif results[0].get("error"):
    st.error(results[0]["error"], icon=":material/error:")
else:
    for index, result in enumerate(results):
        with st.container(border=True):
            st.subheader(result.get("variant_label") or f"Variant {index + 1}")
            if result.get("audio_error"):
                st.warning(result["audio_error"], icon=":material/warning:")

            tracks = [
                (
                    "Full duet" if result.get("is_duet") else "Cello loop",
                    result.get("wav_bytes_b64"),
                    result.get("audio_source"),
                    "full",
                )
            ]
            if result.get("is_duet"):
                tracks.extend(
                    [
                        (
                            "Violin",
                            result.get("violin_wav_bytes_b64"),
                            result.get("violin_audio_source"),
                            "violin",
                        ),
                        (
                            "Cello",
                            result.get("cello_wav_bytes_b64"),
                            result.get("cello_audio_source"),
                            "cello",
                        ),
                    ]
                )

            for title, wav_b64, source, track_id in tracks:
                wav = decode_b64(wav_b64)
                st.markdown(f"**{title}**")
                st.caption(audio_source_label(source))
                if wav:
                    st.audio(wav, format="audio/wav", loop=True)
                    st.download_button(
                        "Download WAV",
                        wav,
                        file_name=f"{result['preset_name']}_{track_id}.wav",
                        mime="audio/wav",
                        icon=":material/download:",
                        key=f"audio_download_{index}_{track_id}",
                    )
                else:
                    st.caption("Audio preview unavailable.")
