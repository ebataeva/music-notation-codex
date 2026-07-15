from __future__ import annotations

from app.pages import loop_coach


class _FakeElement:
    def classes(self, _value: str):
        return self


class _FakeUi:
    def __init__(self) -> None:
        self.labels: list[str] = []
        self.html_blocks: list[str] = []

    def label(self, text: str) -> _FakeElement:
        self.labels.append(text)
        return _FakeElement()

    def html(self, content: str) -> _FakeElement:
        self.html_blocks.append(content)
        return _FakeElement()


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
