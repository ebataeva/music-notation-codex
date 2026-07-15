from __future__ import annotations

import base64

from app.pages import loop_coach


class _FakeElement:
    def classes(self, _value: str):
        return self


class _FakeButton:
    def __init__(self, label) -> None:
        self.label = label
        self.callbacks: dict = {}

    def on(self, event, callback):
        self.callbacks[event] = callback
        return self

    def props(self, _value):
        return self


class _FakeRow:
    def classes(self, _value):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeContainer:
    def clear(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeUi:
    def __init__(self) -> None:
        self.labels: list[str] = []
        self.html_blocks: list[str] = []
        self.add_body_html_calls: list[str] = []
        self.buttons: list = []
        self.downloads: list[tuple] = []

    def label(self, text: str) -> _FakeElement:
        self.labels.append(text)
        return _FakeElement()

    def html(self, content: str) -> _FakeElement:
        self.html_blocks.append(content)
        return _FakeElement()

    def add_body_html(self, content: str) -> None:
        self.add_body_html_calls.append(content)

    def button(self, text, color=None) -> _FakeButton:
        fake_button = _FakeButton(text)
        self.buttons.append(fake_button)
        return fake_button

    def download(self, *args, **kwargs) -> None:
        self.downloads.append((args, kwargs))

    def row(self, *args, **kwargs) -> _FakeRow:
        return _FakeRow()

    def run_javascript(self, _script) -> None:
        return None


def test_duet_audio_renders_full_violin_and_cello_loop_players(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._render_variant_audio(
        2,
        {
            "is_duet": True,
            "wav_bytes_b64": "full-audio",
            "violin_wav_bytes_b64": "violin-audio",
            "cello_wav_bytes_b64": "cello-audio",
        },
    )

    assert fake_ui.labels == ["Rehearsal loops", "Full duet", "Violin", "Cello"]
    assert len(fake_ui.html_blocks) == 3
    assert 'id="loop-audio-2-full"' in fake_ui.html_blocks[0]
    assert 'id="loop-audio-2-violin"' in fake_ui.html_blocks[1]
    assert 'id="loop-audio-2-cello"' in fake_ui.html_blocks[2]
    assert "full-audio" in fake_ui.html_blocks[0]
    assert "violin-audio" in fake_ui.html_blocks[1]
    assert "cello-audio" in fake_ui.html_blocks[2]
    assert all(" controls loop " in html for html in fake_ui.html_blocks)


def test_solo_audio_renders_one_loop_player(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._render_variant_audio(0, {"wav_bytes_b64": "solo-audio"})

    assert fake_ui.labels == ["Rehearsal loops", "Cello loop"]
    assert len(fake_ui.html_blocks) == 1
    assert 'id="loop-audio-0-full"' in fake_ui.html_blocks[0]
    assert "solo-audio" in fake_ui.html_blocks[0]
    assert " controls loop " in fake_ui.html_blocks[0]


def test_missing_audio_renders_unavailable_message(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._render_variant_audio(0, {"is_duet": True})

    assert fake_ui.labels == ["Audio not available."]
    assert fake_ui.html_blocks == []


def test_load_osmd_script_adds_body_html_exactly_once(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._load_osmd_script()

    assert len(fake_ui.add_body_html_calls) == 2
    assert loop_coach.OSMD_JS_URL in fake_ui.add_body_html_calls[0]
    assert "loadOsmd" in fake_ui.add_body_html_calls[1]


def test_render_variant_cards_does_not_call_add_body_html(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._render_variant_cards([], _FakeContainer())

    assert fake_ui.add_body_html_calls == []


def test_export_buttons_call_ui_download_with_positional_bytes(monkeypatch) -> None:
    fake_ui = _FakeUi()
    monkeypatch.setattr(loop_coach, "ui", fake_ui)

    loop_coach._render_variant_export(
        0,
        {
            "musicxml_string": "<score/>",
            "midi_bytes_b64": base64.b64encode(b"midi-bytes").decode("ascii"),
            "wav_bytes_b64": base64.b64encode(b"wav-bytes").decode("ascii"),
        },
    )

    assert len(fake_ui.buttons) == 4  # MusicXML, MIDI, WAV, SVG

    fake_ui.buttons[0].callbacks["click"]()
    fake_ui.buttons[1].callbacks["click"]()
    fake_ui.buttons[2].callbacks["click"]()

    assert len(fake_ui.downloads) == 3
    for args, kwargs in fake_ui.downloads:
        assert len(args) == 1
        assert "content" not in kwargs

    assert fake_ui.downloads[0][0][0] == "<score/>".encode("utf-8")
    assert fake_ui.downloads[0][1]["filename"] == "cello_loop_variant_1.musicxml"
    assert fake_ui.downloads[1][0][0] == b"midi-bytes"
    assert fake_ui.downloads[2][0][0] == b"wav-bytes"
