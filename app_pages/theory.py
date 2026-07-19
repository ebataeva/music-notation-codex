"""Focused harmony explanation page."""

from __future__ import annotations

import streamlit as st

from apps.streamlit_shared import (
    DEFAULT_PROGRESSION,
    analyze_cached,
    default_preset_index,
    preset_from_label,
    preset_label,
    preset_names,
)


st.header(":material/menu_book: Theory")
st.caption(
    "Explore note-specific harmony, cadence, voice-leading, and development advice "
    "from the latest style policy."
)

names = preset_names()
labels = [preset_label(name) for name in names]

progression_col, preset_col, action_col = st.columns([5, 3, 2], vertical_alignment="bottom")
with progression_col:
    progression = st.text_input(
        "Chord progression",
        value=DEFAULT_PROGRESSION,
        placeholder="e.g. Dm9 G9 Bbmaj7 A7",
        key="theory_progression",
    )
with preset_col:
    selected_label = st.selectbox(
        "Style preset",
        labels,
        index=default_preset_index(names),
        key="theory_preset",
    )
with action_col:
    analyze_clicked = st.button(
        "Analyze harmony",
        type="primary",
        icon=":material/analytics:",
        width="stretch",
    )

if analyze_clicked:
    with st.spinner("Building note-specific explanations..."):
        st.session_state["theory_results"] = analyze_cached(
            progression,
            preset_from_label(selected_label, names),
        )

results = st.session_state.get("theory_results")
if not results:
    st.caption("Choose a progression and style, then analyze the harmony.")
elif results[0].get("error"):
    st.error(results[0]["error"], icon=":material/error:")
else:
    for result in results:
        with st.container(border=True):
            st.subheader(result.get("variant_label") or "Harmony explanation")
            if result.get("harmony_context"):
                st.info(result["harmony_context"], icon=":material/info:")
            st.markdown(f"**Why it works**  \n{result['why_it_works']}")
            theory_columns = st.columns(2)
            with theory_columns[0]:
                st.markdown(f"**How to start**  \n{result['how_to_start']}")
                st.markdown(f"**How to develop**  \n{result['how_to_develop']}")
            with theory_columns[1]:
                st.markdown(f"**How to end**  \n{result['how_to_end']}")
                st.markdown(f"**How to transition**  \n{result['how_to_transition']}")
