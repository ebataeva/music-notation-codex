from __future__ import annotations

import base64
import io
import subprocess
import wave
from dataclasses import replace

import numpy as np
import pytest
from music21 import converter, interval, midi, pitch

from app.services import generation, theory_dictionary
from core.engine.loop_engine import build_duet_score, generate_variant_from_progression
from core.engine.progression import parse_progression
from core.presets.registry import get_preset, list_presets
from core.theory.dictionary import ENTRIES, ENTRY_BY_ID, build_dictionary_example
from core.theory.explainer import explain
from core.theory.harmony import semitone
from core.theory.transitions import transition_guides
from core.theory.summaries import explain_duet_score


TONICS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")


def events(score):
    result = []
    for part in score.parts:
        for event in part.stripTies().flatten().notes:
            for p in event.pitches:
                result.append((round(float(event.offset), 4), round(float(event.quarterLength), 4), p.midi))
    return sorted(result)


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda entry: entry.id)
@pytest.mark.parametrize("tonic", TONICS)
def test_every_article_has_a_transposable_score(entry, tonic):
    example = build_dictionary_example(entry.id, tonic, "minor")
    assert example.score.recurse().notes
    assert example.entry.definition and example.entry.listen_for
    assert all(term in ENTRY_BY_ID for term in example.entry.related_terms)
    reference = build_dictionary_example(entry.id, "C", "minor")
    relative = lambda score, root: [((p.midi - root) % 12, float(event.quarterLength)) for part in score.parts for event in part.recurse().notes for p in event.pitches]
    assert relative(example.score, semitone(tonic)) == relative(reference.score, 0)


@pytest.mark.parametrize("term", ["tonic", "sevenths-ninths", "common-tone", "modulation", "mode-shift"])
@pytest.mark.parametrize("tonic", ["C", "Eb", "F#"])
def test_displayed_notation_and_midi_have_identical_pitches_and_timing(term, tonic):
    result = theory_dictionary.dictionary_example(term, tonic, "major", include_audio=False)
    written = converter.parseData(result["musicxml_string"])
    mf = midi.MidiFile()
    mf.readstr(base64.b64decode(result["midi_bytes_b64"]))
    performed = midi.translate.midiFileToStream(mf, quantizePost=False)
    assert events(written) == events(performed)


def test_modulation_and_tonicization_use_the_same_pair_but_different_destination():
    guides = transition_guides("C", "major")
    temporary, lasting = guides[1], guides[2]
    assert temporary.chords[1:3] == lasting.chords[1:3] == (("E", "G#", "B", "D"), ("A", "C", "E"))
    assert temporary.kind == "tonicization"
    assert temporary.labels[-2:] == ("G7", "C")
    assert lasting.kind == "modulation"
    assert lasting.labels[-3:] == ("E7", "Am", "Am")
    assert "following" not in temporary.target_key


def test_borrowing_and_mode_shift_keep_the_tonic_and_spell_the_changed_note():
    guides = transition_guides("E", "dorian", "dorian_sexy_duet")
    assert guides[3].kind == "modal_borrowing"
    assert guides[3].chords[1] == ("A", "C#", "E")
    assert guides[3].chords[2] == ("A", "C", "E")
    assert guides[5].kind == "mode_shift"
    assert "C# to C (6 to b6)" in guides[5].explanation
    assert guides[5].source_key == "E Dorian"
    assert guides[5].target_key == "E natural minor"
    assert guides[5].chords != guides[3].chords
    assert sum("C" in tones for tones in guides[3].chords) == 1
    assert sum("C" in tones for tones in guides[5].chords[2:]) >= 3
    assert all("C#" not in tones for tones in guides[5].chords[2:])
    assert guides[5].chords[-1] == ("E", "G", "B")


@pytest.mark.parametrize("tonic", TONICS)
@pytest.mark.parametrize("preset_name", list_presets())
def test_short_explanations_and_guides_work_in_all_keys_and_presets(tonic, preset_name):
    preset = replace(get_preset(preset_name), key_tonic=tonic)
    if preset.duet_bars is not None:
        original = get_preset(preset_name)
        score = build_duet_score(original, original.duet_tempo_bpm or original.tempo_bpm, original.velocity, original.velocity)
        distance = interval.Interval(pitch.Pitch(original.key_tonic.replace("b", "-") + "3"), pitch.Pitch(tonic.replace("b", "-") + "3"))
        explanation = explain_duet_score(score.transpose(distance), preset)
    else:
        variant = generate_variant_from_progression(parse_progression(tonic + "m"), preset, seed=42)
        explanation = explain(variant, preset)
    assert len(explanation.short_sections) == 5
    assert any(tonic in text for text in explanation.short_sections.values())
    for section, text in explanation.short_sections.items():
        assert text and len(text.split()) <= 65
        assert all(term in ENTRY_BY_ID for term in explanation.term_ids[section])
    guides = transition_guides(tonic, "minor", preset_name)
    assert all(guide.labels and guide.listen_for and guide.style_note for guide in guides)


@pytest.mark.parametrize("progression,tonic,sixth,degrees", [("Dm9 G9", "D", "B", "i9 → IV9"), ("Em9 A9", "E", "C#", "i9 → IV9")])
def test_dorian_summaries_keep_real_chord_quality_and_transposed_sixth(progression, tonic, sixth, degrees):
    result = generation.generate_loop_variants(progression, "dark_trip_hop", seed=42, count=1, key_tonic=tonic, key_mode="minor")[0]
    assert result["error"] is None
    assert result["key_tonic"] == tonic
    text = result["short_sections"]["why_it_works"]
    assert degrees in text
    assert f"{sixth} (6)" in text
    parsed = converter.parseData(result["musicxml_string"])
    assert parsed.parts[0].recurse().getElementsByClass("KeySignature")[0].sharps == (1 if tonic == "E" else -1)


def test_ritual_authored_collection_is_not_called_phrygian():
    from core.engine.loop_engine import generate_variant
    preset = get_preset("ritual_tribal")
    result = explain(generate_variant(preset, seed=42), preset)
    assert "D natural minor" in result.short_sections["why_it_works"]
    assert "Phrygian" not in result.short_sections["why_it_works"]


@pytest.mark.parametrize("preset_name", ["sexy_duet", "simple_sexy_duet", "dorian_sexy_duet"])
def test_authored_duet_explanation_follows_score_and_ignores_solo_input(preset_name):
    first = generation.generate_loop_variants("", preset_name, key_tonic="E", key_mode="major")[0]
    second = generation.generate_loop_variants("not a chord", preset_name, key_tonic="C", key_mode="minor")[0]
    assert first["error"] is None and first["is_duet"]
    assert first["key_tonic"] == get_preset(preset_name).key_tonic
    assert events(converter.parseData(first["musicxml_string"])) == events(converter.parseData(second["musicxml_string"]))
    assert first["short_sections"] == second["short_sections"]
    score = converter.parseData(first["musicxml_string"])
    for part in score.parts:
        start = part.recurse().notes[0].pitches[0].nameWithOctave.replace("-", "b")
        assert start in first["short_sections"]["how_to_start"]


@pytest.mark.parametrize("error", [FileNotFoundError("missing soundfont"), subprocess.CalledProcessError(255, "fluidsynth"), subprocess.TimeoutExpired("fluidsynth", 30)])
def test_audio_uses_existing_fallback_and_is_audible(monkeypatch, error):
    def missing_soundfont(_):
        raise error
    monkeypatch.setattr(generation, "_midi_to_wav_bytes", missing_soundfont)
    theory_dictionary._example_audio.cache_clear()
    result = theory_dictionary.dictionary_example("tonic", "C", "major")
    assert result["audio_source"] == "cello_synth_reverb"
    with wave.open(io.BytesIO(base64.b64decode(result["wav_bytes_b64"]))) as wav:
        assert wav.getnframes() / wav.getframerate() >= 4
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
        assert np.max(np.abs(samples.astype(float))) > 100


def test_audio_is_lazy_and_cached_per_context(monkeypatch):
    calls = []
    monkeypatch.setattr(theory_dictionary, "_render_wav", lambda data: (calls.append(data) or b"wave", "test"))
    theory_dictionary._example_audio.cache_clear()
    theory_dictionary.dictionary_example("triads", "C", "major", include_audio=False)
    assert not calls
    theory_dictionary.dictionary_example("triads", "C", "major")
    theory_dictionary.dictionary_example("triads", "C", "major")
    theory_dictionary.dictionary_example("triads", "D", "major")
    assert len(calls) == 2 and calls[0] != calls[1]
    theory_dictionary._example_audio.cache_clear()
