from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from core.engine.progression import ParsedChord, parse_progression
from core.presets.registry import get_preset


@dataclass(frozen=True)
class EarCheckCase:
    slug: str
    title: str
    progression: str
    preset_name: str
    seed: int
    intent: str

    @property
    def audio_path(self) -> Path:
        return PROJECT_ROOT / "scores" / "audio" / f"{self.slug}.wav"

    @property
    def midi_path(self) -> Path:
        return PROJECT_ROOT / "scores" / "midi" / f"{self.slug}.mid"

    @property
    def musicxml_path(self) -> Path:
        return PROJECT_ROOT / "scores" / "musicxml" / f"{self.slug}.musicxml"

    @property
    def mscz_path(self) -> Path:
        return PROJECT_ROOT / "scores" / "musicxml" / f"{self.slug}.mscz"


CASES = [
    EarCheckCase(
        slug="earcheck_am_f_c_g_dark_trip_hop_seed42",
        title="Am F C G / dark trip-hop",
        progression="Am F C G",
        preset_name="dark_trip_hop",
        seed=42,
        intent="Baseline minor-pop loop: the harmony should feel like four distinct bars, not a single static pattern.",
    ),
    EarCheckCase(
        slug="earcheck_am_f_c_g_driving_cinematic_seed42",
        title="Am F C G / driving cinematic",
        progression="Am F C G",
        preset_name="driving_cinematic",
        seed=42,
        intent="Same harmony with a faster motor rhythm: transitions should still be readable through the denser pattern.",
    ),
    EarCheckCase(
        slug="earcheck_bb_eb_ab_f_dark_trip_hop_seed3",
        title="Bb Eb Ab F / dark trip-hop",
        progression="Bb Eb Ab F",
        preset_name="dark_trip_hop",
        seed=3,
        intent="Flat-key check: the line should change color clearly without sounding like accidental wrong notes.",
    ),
    EarCheckCase(
        slug="earcheck_bb_eb_ab_f_driving_cinematic_seed3",
        title="Bb Eb Ab F / driving cinematic",
        progression="Bb Eb Ab F",
        preset_name="driving_cinematic",
        seed=3,
        intent="Fast flat-key check: this is the stress case for whether chord changes survive the rhythmic drive.",
    ),
]

RATING_OPTIONS = ["Not checked", "Clear", "Weak", "Missing", "Bad jump"]


def _bar_seconds(case: EarCheckCase) -> float:
    preset = get_preset(case.preset_name)
    return sum(preset.rhythm) * 60 / preset.tempo_bpm


def _format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    remainder = seconds - minutes * 60
    return f"{minutes}:{remainder:04.1f}"


def _transition_label(chords: list[ParsedChord], index: int, bar_seconds: float) -> str:
    left = chords[index]
    right = chords[index + 1]
    timestamp = _format_timestamp((index + 1) * bar_seconds)
    return f"{timestamp} - Bar {index + 1} -> {index + 2}: {left.name} -> {right.name}"


def _case_key(case: EarCheckCase, suffix: str) -> str:
    return f"{case.slug}:{suffix}"


def _rating_payload() -> dict[str, object]:
    cases = []
    for case in CASES:
        chords = parse_progression(case.progression)
        transition_ratings = {}
        for index in range(len(chords) - 1):
            key = _case_key(case, f"transition:{index}")
            transition_ratings[f"{chords[index].name}->{chords[index + 1].name}"] = (
                st.session_state.get(key, "Not checked")
            )
        cases.append(
            {
                "case": case.slug,
                "progression": case.progression,
                "preset": case.preset_name,
                "seed": case.seed,
                "overall": st.session_state.get(
                    _case_key(case, "overall"), "Not checked"
                ),
                "transitions": transition_ratings,
                "notes": st.session_state.get(_case_key(case, "notes"), ""),
            }
        )
    return {"test": "phase-02.5-progression-ear-check", "cases": cases}


def _render_download(path: Path, label: str, mime: str) -> None:
    if path.exists():
        st.download_button(label, path.read_bytes(), file_name=path.name, mime=mime)


st.set_page_config(page_title="Progression Ear Check", page_icon="audio", layout="wide")

st.title("Progression Ear Check")
st.caption(
    "A short listening test for an early cello-pattern generator. The goal is to judge whether chord changes are audible, not whether the music is release-ready."
)

with st.expander("About this project", expanded=False):
    st.markdown("### What is this?")
    st.markdown(
        "I'm building a **loop coach for an electric cellist** — "
        "a tool where you type a chord progression, pick a mood, "
        "and it generates playable cello loop ideas, each one "
        "explained with the music theory behind *why* it works."
    )
    st.info(
        "**The vision:** open the app, get a fresh loop idea in seconds, "
        "hear it, then take it to your looper and play. "
        "No more staring at a blank loop station."
    )

    st.markdown("### Roadmap")
    stage1, stage2, stage3, stage4 = st.columns(4)
    with stage1:
        st.markdown(
            "<div style='text-align:center;font-size:2em'>"
            "<span style='font-size:1.8em'>1</span><br>"
            "<b>Cello</b><br>"
            "<small>Ostinato loop<br>foundations</small>"
            "</div>",
            unsafe_allow_html=True,
        )
    with stage2:
        st.markdown(
            "<div style='text-align:center;font-size:2em'>"
            "<span style='font-size:1.8em'>2</span><br>"
            "<b>Violin duet</b><br>"
            "<small>Counter-line<br>over the cello</small>"
            "</div>",
            unsafe_allow_html=True,
        )
    with stage3:
        st.markdown(
            "<div style='text-align:center;font-size:2em'>"
            "<span style='font-size:1.8em'>3</span><br>"
            "<b>Drum machine</b><br>"
            "<small>Rhythmic layer<br>completes the loop</small>"
            "</div>",
            unsafe_allow_html=True,
        )
    with stage4:
        st.markdown(
            "<div style='text-align:center;font-size:2em'>"
            "<span style='font-size:1.8em'>4</span><br>"
            "<b>Record & feedback</b><br>"
            "<small>Play in, get analysis<br>on intonation & timing</small>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.caption("*Right now: Phase 2.5 — cello only, two presets.*")

    st.markdown("### Two presets so far")
    preset_left, preset_right = st.columns(2)
    with preset_left:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:12px;"
            "border-left:4px solid #6c63ff'>"
            "<b>dark trip-hop</b><br>"
            "<small>Slow, spacious, low-register ostinato<br>"
            "72 bpm &middot; 4/4</small>"
            "</div>",
            unsafe_allow_html=True,
        )
    with preset_right:
        st.markdown(
            "<div style='background:#1a1a2e;padding:16px;border-radius:12px;"
            "border-left:4px solid #ff6b6b'>"
            "<b>driving cinematic</b><br>"
            "<small>Fast, motoric, mid-register pulse<br>"
            "130 bpm &middot; 4/4</small>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("### Why this ear check?")
    st.markdown(
        "The engine can produce notes, but I have no way to measure "
        "whether the output actually *sounds* like the harmony is changing. "
        "A machine checks that the right pitch classes appear in each bar — "
        "but only a musician's ear can tell whether the transition feels "
        "**musical or mechanical**."
    )
    st.success(
        "Your ratings will tell me exactly which chord boundaries need "
        "better voice-leading, smoother register choices, or more "
        "expressive chord-tone distribution."
    )

    st.markdown("### What happens next?")
    st.markdown(
        "I'll tune the engine based on the weak or missing transitions "
        "you flag. **The goal: sketch a progression, hear a musically "
        "plausible cello line instantly** — a starting point for real "
        "writing and looping, not a finished piece."
    )

with st.expander("Your task", expanded=True):
    st.write(
        "Please listen to each example and focus on the moments where one chord changes into the next. "
        "The labels under the player show the exact bar boundary and timestamp to check."
    )
    st.write(
        "For every boundary, choose: Clear if the change is easy to hear, Weak if it is present but vague, "
        "Missing if the line sounds like it did not really change, and Bad jump if the transition sounds abrupt or awkward."
    )
    st.write(
        "Use the notes box for anything musical that matters: static harmony, strange register, unclear bass motion, "
        "mechanical cycling, or a transition that works especially well. When finished, download the ratings JSON and send it back."
    )

selected_title = st.sidebar.radio("Example", [case.title for case in CASES])
case = next(case for case in CASES if case.title == selected_title)
chords = parse_progression(case.progression)
preset = get_preset(case.preset_name)
bar_seconds = _bar_seconds(case)

st.sidebar.divider()
st.sidebar.write("Current target")
st.sidebar.write(f"Preset: `{case.preset_name}`")
st.sidebar.write(f"Seed: `{case.seed}`")
st.sidebar.write(f"Tempo: `{preset.tempo_bpm} bpm`")

left, right = st.columns([1.2, 1])

with left:
    st.subheader(case.title)
    st.write(case.intent)

    bar_columns = st.columns(len(chords))
    for index, chord in enumerate(chords):
        with bar_columns[index]:
            st.metric(f"Bar {index + 1}", chord.name)
            st.caption(", ".join(chord.components))

    if case.audio_path.exists():
        st.audio(case.audio_path.read_bytes(), format="audio/wav")
    else:
        st.error(f"Missing audio file: {case.audio_path}")

    st.write("Listen for these boundaries")
    for index in range(len(chords) - 1):
        left_chord = chords[index]
        right_chord = chords[index + 1]
        st.radio(
            _transition_label(chords, index, bar_seconds),
            RATING_OPTIONS,
            horizontal=True,
            key=_case_key(case, f"transition:{index}"),
            help=(
                f"Before: {left_chord.name} ({', '.join(left_chord.components)}). "
                f"After: {right_chord.name} ({', '.join(right_chord.components)})."
            ),
        )

with right:
    st.subheader("Decision")
    st.write(
        "Rate the selected example as a whole after checking its individual boundaries."
    )
    st.radio(
        "Overall result for this example",
        RATING_OPTIONS,
        horizontal=True,
        key=_case_key(case, "overall"),
    )
    st.text_area(
        "What did you hear?",
        placeholder="Examples: transition 2->3 is not obvious; the line sounds static; the F bar feels like a real color change; the fast preset hides the harmony.",
        key=_case_key(case, "notes"),
        height=140,
    )

    st.write("Files")
    _render_download(case.audio_path, "Download WAV", "audio/wav")
    _render_download(case.midi_path, "Download MIDI", "audio/midi")
    _render_download(
        case.musicxml_path,
        "Download MusicXML",
        "application/vnd.recordare.musicxml+xml",
    )
    _render_download(case.mscz_path, "Download MSCZ", "application/vnd.musescore")

st.divider()
st.subheader("What counts as a pass?")
st.write(
    "A pass means the chord changes are audible enough for an engine prototype: no jarring boundary leaps, no fully static pattern, and at least some sense that each chord changes the line's color."
)
st.write(
    "A fail is useful too. Mark weak or missing boundaries so the next fix can target voice-leading or chord-tone distribution instead of guessing."
)

payload = json.dumps(_rating_payload(), indent=2)
st.download_button(
    "Download ratings JSON",
    payload,
    file_name="phase-02.5-ear-check-ratings.json",
    mime="application/json",
)
