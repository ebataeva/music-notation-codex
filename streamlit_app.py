"""Unified Streamlit entrypoint for the music notation studio."""

from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="Music notation studio",
    page_icon=":material/music_note:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

page = st.navigation(
    [
        st.Page(
            "apps/ear_check_streamlit.py",
            title="Loop Lab",
            icon=":material/music_note:",
            default=True,
        ),
        st.Page(
            "app_pages/theory.py",
            title="Theory",
            icon=":material/menu_book:",
            url_path="theory",
        ),
        st.Page(
            "app_pages/cloud_audio.py",
            title="Cloud audio",
            icon=":material/graphic_eq:",
            url_path="cloud-audio",
        ),
        st.Page(
            "app_pages/practice_partner.py",
            title="Practice Partner",
            icon=":material/mic:",
            url_path="practice-partner",
        ),
    ],
    position="top",
)

page.run()
