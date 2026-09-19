from __future__ import annotations

from dataclasses import dataclass

from music21 import chord, clef, expressions, instrument, key, metadata, meter, note, pitch, stream, tempo

from core.theory.harmony import transpose_name
from core.theory.transitions import TransitionGuide, normalize_context, transition_guides, triad


@dataclass(frozen=True)
class TheoryEntry:
    id: str
    title: str
    definition: str
    listen_for: str
    related_terms: tuple[str, ...]


ENTRIES = (
    TheoryEntry("tonic", "Tonic", "The note or chord heard as home; a key label proposes that home, but phrasing and repeated arrivals make it audible.", "Hear the melody leave home and settle back on the last, longer note.", ("scale-degrees", "cadence")),
    TheoryEntry("scale-degrees", "Scale degrees", "Numbers describe notes relative to a tonic. Here 1–7 refer to the major scale; b3 means its third lowered by a semitone.", "Follow the numbered ascent and the return to 1; the same shape works in another key.", ("tonic", "modes")),
    TheoryEntry("chord-tones", "Chord tones", "The pitches that belong to a specified chord. A melody can outline them one at a time without sounding the whole chord together.", "Compare the separate root, third, and fifth with the same notes sounded together.", ("triads", "voice-leading")),
    TheoryEntry("triads", "Triads", "A three-note chord built from a root, third, and fifth. The third and fifth determine qualities such as major, minor, diminished, and augmented.", "The root stays fixed while the third or fifth changes; compare the four chord qualities.", ("chord-tones", "sevenths-ninths")),
    TheoryEntry("sevenths-ninths", "Sevenths and ninths", "A seventh extends a triad; a ninth extends the harmony further. A ninth chord includes a seventh, whereas add9 does not.", "Hear the plain minor triad, then its added seventh, ninth, and finally add9 without the seventh.", ("triads", "chord-tones")),
    TheoryEntry("modes", "Modes and minor collections", "Modes organize intervals around a tonic. Natural minor has b6 and b7, harmonic minor raises 7, and Dorian has a natural 6 with b3 and b7.", "Compare natural minor, harmonic minor, and Dorian over the same tonic; focus on degrees 6 and 7.", ("tonic", "modal-borrowing")),
    TheoryEntry("cadence", "Cadence", "A harmonic and melodic gesture at a phrase ending. A chord pair can suggest closure, but rhythm, melody, and placement determine how final it feels.", "Hear the dominant seventh move home, then the longer tonic and the pause; compare this with a continuous loop.", ("tonic", "modulation")),
    TheoryEntry("pedal-point", "Pedal point", "A sustained or repeated pitch held while other notes or harmonies move. A low register alone does not create a pedal point.", "Follow the unchanged bass under the moving upper line.", ("ostinato", "common-tone")),
    TheoryEntry("ostinato", "Ostinato", "A short rhythmic or melodic pattern repeated through a passage. It may support changing harmony without itself changing.", "Count each return of the same four-note cell; distinguish the repeated pattern from a single held note.", ("pedal-point", "chord-tones")),
    TheoryEntry("voice-leading", "Voice leading", "How individual musical lines move from one sonority to the next. Shared pitch classes do not prove that a performer held the same voice.", "Follow the upper line by step while the lower note stays in place.", ("common-tone", "chord-tones")),
    TheoryEntry("common-tone", "Common tone", "A pitch shared by two chords. Keeping it in one voice can connect them, but sharing a pitch does not by itself change the key.", "The marked shared pitch is actually held across the two harmonies in this example.", ("voice-leading", "pivot-chord")),
    TheoryEntry("chromatic-approach", "Chromatic approach", "A note a semitone above or below a target that moves into it. The approach is a local gesture, not automatically a change of key.", "Hear the lower neighbor rise to the tonic, then the upper neighbor fall to it.", ("tonic", "scale-degrees")),
    TheoryEntry("modulation", "Modulation", "A change of tonal center supported by the following phrase. A new chord or a shared note alone does not establish a new key.", "Compare a brief visit with a phrase that continues and closes in the destination key.", ("tonicization", "pivot-chord", "direct-transition")),
    TheoryEntry("tonicization", "Tonicization", "A chord is treated briefly as a local tonic, often through its own dominant, while the surrounding phrase retains the original key.", "Hear the temporary arrival, then the return to the original tonic.", ("secondary-dominant", "modulation")),
    TheoryEntry("modal-borrowing", "Modal borrowing", "A chord or pitch is borrowed from a parallel mode while the tonic remains the reference center. Borrowing need not become a lasting mode change.", "Listen for one changed chord color followed by the original tonic.", ("modes", "modulation")),
    TheoryEntry("pivot-chord", "Common chord / pivot chord", "A chord belongs to both the starting and destination keys and can be reinterpreted between them. Later music must establish the new center.", "Follow the shared chord into the destination dominant and final tonic.", ("common-tone", "modulation")),
    TheoryEntry("secondary-dominant", "Secondary dominant", "A major dominant chord, often with a seventh, directed toward a chord other than the main tonic. Its leading tone points toward that temporary target.", "Hear the altered note pull toward the local tonic, then notice where the phrase goes next.", ("tonicization", "modulation")),
    TheoryEntry("direct-transition", "Direct transition", "A new phrase starts in another key without a prepared pivot chord. Continued emphasis on the destination distinguishes a key change from a brief color.", "Notice the sudden change at the phrase boundary and the repeated destination tonic afterward.", ("modulation", "cadence")),
    TheoryEntry("mode-shift", "Same-tonic mode shift", "A passage can change its scale collection while keeping the same tonic. A sustained mode change is different from borrowing a single color.", "Hear the natural sixth become flat while the tonic remains in place.", ("modes", "modal-borrowing")),
)
ENTRY_BY_ID = {entry.id: entry for entry in ENTRIES}


@dataclass
class DictionaryExample:
    entry: TheoryEntry
    tonic: str
    mode: str
    score: stream.Score
    caption: str
    guide: TransitionGuide | None = None


def _pitch(name: str, octave: int = 3) -> pitch.Pitch:
    result = pitch.Pitch(name.replace("b", "-"))
    result.octave = octave
    return result


def _new_score(title: str, tonic: str, mode: str) -> tuple[stream.Score, stream.Part]:
    score = stream.Score()
    score.metadata = metadata.Metadata(title=title)
    part = stream.Part(id="example")
    part.append(instrument.Violoncello())
    part.append(clef.BassClef())
    part.append(meter.TimeSignature("4/4"))
    part.append(key.Key(tonic.replace("b", "-"), mode))
    part.append(tempo.MetronomeMark(number=84))
    score.append(part)
    return score, part


def _append_chords(part: stream.Part, groups: tuple[tuple[str, ...], ...], labels: tuple[str, ...]) -> None:
    for i, (tones, label) in enumerate(zip(groups, labels, strict=True)):
        pitches = []
        for name in tones:
            current = _pitch(name)
            while pitches and current.midi <= pitches[-1].midi:
                current.octave += 1
            pitches.append(current)
        event = chord.Chord(pitches, quarterLength=4)
        event.volume.velocity = 68
        measure = stream.Measure(number=i + 1)
        measure.append(expressions.TextExpression(label))
        measure.append(event)
        part.append(measure)


def _append_melody(part: stream.Part, tonic: str, intervals: tuple[str, ...], labels: tuple[str, ...] = ()) -> None:
    origin = _pitch(tonic)
    for i, distance in enumerate(intervals):
        event = note.Note(origin.transpose(distance), quarterLength=1)
        event.volume.velocity = 70
        if labels:
            event.addLyric(labels[i])
        part.append(event)


def build_dictionary_example(term: str, tonic: str = "C", mode: str = "major", preset_name: str = "") -> DictionaryExample:
    tonic, mode = normalize_context(tonic, mode)
    if term not in ENTRY_BY_ID:
        raise ValueError("That theory term is not in the dictionary.")
    entry = ENTRY_BY_ID[term]
    score, part = _new_score(entry.title, tonic, mode)
    third = "M3" if mode == "major" else "m3"
    quality = "major" if mode == "major" else "minor"
    home = triad(tonic, quality)
    guide = None
    caption = f"Example tonic: {tonic}. Stacked notes demonstrate harmony across several voices."
    guide_index = {"pivot-chord": 0, "tonicization": 1, "secondary-dominant": 1, "modulation": 2, "modal-borrowing": 3, "direct-transition": 4, "mode-shift": 5}
    if term in guide_index:
        guide = transition_guides(tonic, mode, preset_name)[guide_index[term]]
        _append_chords(part, guide.chords, guide.labels)
        caption = guide.explanation
    elif term == "tonic":
        _append_melody(part, tonic, ("P1", third, "P5", "M2", "P1", "P1", "P1", "P1"))
        part.notes[-4].quarterLength = 4
        for event in list(part.notes)[-3:]:
            part.remove(event)
    elif term == "scale-degrees":
        _append_melody(part, tonic, ("P1", "M2", "M3", "P4", "P5", "M6", "M7", "P8"), ("1", "2", "3", "4", "5", "6", "7", "1"))
    elif term == "chord-tones":
        _append_melody(part, tonic, ("P1", third, "P5", "P8"), ("root", "third", "fifth", "root"))
        part.append(chord.Chord([_pitch(n) for n in home], quarterLength=4))
    elif term == "triads":
        groups = tuple(tuple(transpose_name(tonic, d) for d in distances) for distances in (("P1", "M3", "P5"), ("P1", "m3", "P5"), ("P1", "m3", "d5"), ("P1", "M3", "A5")))
        _append_chords(part, groups, ("major", "minor", "diminished", "augmented"))
    elif term == "sevenths-ninths":
        groups = tuple(tuple(transpose_name(tonic, d) for d in distances) for distances in (("P1", "m3", "P5"), ("P1", "m3", "P5", "m7"), ("P1", "m3", "P5", "m7", "M9"), ("P1", "m3", "P5", "M9")))
        _append_chords(part, groups, (tonic + "m", tonic + "m7", tonic + "m9", tonic + "m(add9)"))
    elif term == "modes":
        for name, sixth, seventh in (("Natural minor", "m6", "m7"), ("Harmonic minor", "m6", "M7"), ("Dorian", "M6", "m7")):
            part.append(expressions.TextExpression(name))
            _append_melody(part, tonic, ("P1", "M2", "m3", "P4", "P5", sixth, seventh, "P8"))
        caption = f"Three collections on {tonic}; the tonic stays fixed while degrees 6 and 7 change."
    elif term == "cadence":
        dominant = transpose_name(tonic, "P5")
        _append_chords(part, (triad(dominant, seventh=True), home, home), (dominant + "7", tonic + ("m" if quality == "minor" else ""), "settle"))
        part.append(note.Rest(quarterLength=4))
    elif term in {"pedal-point", "voice-leading", "common-tone"}:
        bass = stream.Part(id="held-tone")
        bass.append(instrument.Violoncello())
        bass.append(clef.BassClef())
        bass.append(note.Note(_pitch(tonic, 2), quarterLength=8))
        score.insert(0, bass)
        if term == "common-tone":
            _append_chords(part, (home, triad(transpose_name(tonic, "P4"), quality)), ("first harmony", "shared tonic held below"))
        else:
            _append_melody(part, tonic, (third, "P4", "P5", "P4", third, "M2", "P1", "P1"))
    elif term == "ostinato":
        _append_melody(part, tonic, ("P1", "P5", third, "P5") * 3)
    elif term == "chromatic-approach":
        _append_melody(part, tonic, ("-m2", "P1", "m2", "P1", "-m2", "P1", "m2", "P1"))
    score.makeMeasures(inPlace=True)
    return DictionaryExample(entry, tonic, mode, score, caption, guide)
