"""Smoke and interaction tests for the unified Streamlit app."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import apps.streamlit_shared as shared


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_page(relative_path: str) -> AppTest:
    return AppTest.from_file(PROJECT_ROOT / relative_path, default_timeout=20).run()


@pytest.mark.parametrize(
    ("relative_path", "expected_text"),
    [
        ("streamlit_app.py", None),
        ("apps/ear_check_streamlit.py", "Generate"),
        ("app_pages/theory.py", "Analyze harmony"),
        ("app_pages/cloud_audio.py", "Render audio"),
        ("app_pages/practice_partner.py", "Practice Partner"),
    ],
)
def test_streamlit_pages_load_without_exceptions(relative_path: str, expected_text: str | None) -> None:
    app = _run_page(relative_path)

    assert not app.exception
    if expected_text is not None:
        rendered_labels = [item.label for item in app.button]
        rendered_labels.extend(item.value for item in app.header)
        assert any(expected_text in value for value in rendered_labels)


def test_theory_page_renders_latest_explanation_fields(monkeypatch) -> None:
    monkeypatch.setattr(shared, "generate_cached", lambda *args, **kwargs: [_fake_result()])
    app = _run_page("app_pages/theory.py")

    app.button[0].click().run()

    assert not app.exception
    rendered = "\n".join(item.value for item in app.markdown)
    assert "Because the cadence resolves." in rendered
    assert "Develop chromatically." in rendered
    assert "Transition through the dominant." in rendered


def test_cloud_audio_page_reports_renderer_without_audio_blob(monkeypatch) -> None:
    monkeypatch.setattr(shared, "generate_cached", lambda *args, **kwargs: [_fake_result()])
    app = _run_page("app_pages/cloud_audio.py")

    app.button[0].click().run()

    assert not app.exception
    captions = [item.value for item in app.caption]
    assert "Cloud synth + reverb" in captions
    assert "Audio preview unavailable." in captions


def _fake_result() -> dict:
    return {
        "variant_label": "Variant 1",
        "why_it_works": "Because the cadence resolves.",
        "how_to_start": "Start softly.",
        "how_to_develop": "Develop chromatically.",
        "how_to_end": "End on the tonic.",
        "how_to_transition": "Transition through the dominant.",
        "preset_name": "dorian_sexy_duet",
        "is_duet": False,
        "wav_bytes_b64": "",
        "audio_source": "cello_synth_reverb",
        "error": None,
    }
