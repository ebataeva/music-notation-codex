from __future__ import annotations

from core.models import LoopVariant, MoodPreset, TheoryExplanation
from core.theory.harmony import chord_facts, compatible_collections, pitch_class, roman_label, semitone, transpose_name
from core.theory.transitions import transition_guides


SECTION_TITLES = {
    "why_it_works": "Why it works",
    "how_to_start": "How to start",
    "how_to_develop": "How to develop",
    "how_to_end": "How to end",
    "how_to_transition": "How to transition",
}

PLAYING_TIPS = {
    "dark_trip_hop": "Leave a gap after the accent for a sparse trip-hop feel.",
    "ritual_tribal": "Keep the repeated rhythm even to maintain a ritual pulse.",
    "noir_slow_burn": "Let the color note decay before answering it for a slow noir feel.",
    "driving_cinematic": "Keep the subdivision driving while you broaden the phrase.",
    "sexy_duet": "Try a restrained dynamic contrast between the cello and violin.",
    "simple_sexy_duet": "Keep the repeated gesture simple and the dynamic changes small.",
    "dorian_sexy_duet": "Give the natural sixth space without making every note an accent.",
}


def _collection(tones: list[str], tonic: str) -> tuple[str, str]:
    names = list(dict.fromkeys(pitch_class(tone) for tone in tones))
    collections = compatible_collections(names, tonic)
    offsets = {(semitone(tone) - semitone(tonic)) % 12 for tone in names}
    if "Dorian" in collections and {3, 9, 10} <= offsets:
        sixth = transpose_name(tonic, "M6")
        return f"{sixth} (6) gives the supplied minor harmony a Dorian color", "dorian"
    if len(collections) == 1:
        return f"the supplied notes fit {tonic} {collections[0]}", "minor" if "minor" in collections[0] else "major"
    if collections:
        return f"these notes allow more than one modal reading around {tonic}", "minor"
    return f"chromatic notes add color around the reference tonic {tonic}", "minor"


def _transition_summary(tonic: str, mode: str, preset_name: str) -> str:
    guides = transition_guides(tonic, mode, preset_name)
    if mode == "dorian":
        guide = guides[-1]
        return guide.explanation + " This changes mode, not the tonic."
    guide = guides[0]
    return f"Try {' → '.join(guide.labels[:-1])} to explore {guide.target_key}; repeat the destination tonic. This is a proposed transition, not a detected key change."


def summarize_trace(variant: LoopVariant, preset: MoodPreset) -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    trace = variant.trace
    if trace is None:
        raise ValueError("Short theory requires a generation trace.")
    groups = [tones for tones in trace.chord_tones_used or [] if tones]
    if not groups:
        raise ValueError("Short theory requires at least one supplied note.")
    tones = [tone for group in groups for tone in group]
    tonic = pitch_class(preset.key_tonic)
    anchor = pitch_class(tones[0])
    color, detected_mode = _collection(tones, tonic)
    mode = "dorian" if detected_mode == "dorian" else preset.key_mode
    chords = [chord_facts(group) for group in groups] if trace.pattern_strategy == "progression_driven_register_mapped" else []
    if chords:
        shown = chords if len(chords) <= 3 else (chords[0], chords[-1])
        separator = " → " if len(chords) <= 3 else " … "
        progression = separator.join(ch.symbol for ch in shown)
        degrees = separator.join(roman_label(ch, tonic) for ch in shown)
        why = f"Your progression is {progression} ({degrees}, relative to {tonic}); {color}."
        if any(ch.quality == "incomplete" for ch in shown):
            why = f"The supplied notes around {tonic} include incomplete or ambiguous chords. Keep the missing tones open instead of assuming a major or minor quality."
        color_note = chords[0].tones[-1]
        develop = f"Try emphasizing {color_note} from {chords[0].symbol}. {PLAYING_TIPS.get(preset.name, 'Keep the pulse steady so the change in emphasis is audible.')}"
        end = f"Return to the opening {chords[0].symbol} and soften the final bow stroke. This is a possible loop ending, not an inferred cadence."
        why_terms = ("scale-degrees", "chord-tones", "modes")
        if any(ch.extension for ch in chords):
            why_terms = ("sevenths-ninths", "scale-degrees", "modes")
    else:
        why = f"The cello line starts on {anchor}; {color}. A single line does not establish complete duet harmony."
        develop = f"Repeat the opening {anchor} gesture, then vary its rhythm. Keep a recognizable ostinato underneath the change."
        end = f"Return to {anchor} and let the last bow stroke decay. Leave enough space for the next entrance."
        why_terms = ("tonic", "modes", "chord-tones")
    register = trace.register_bias or "default"
    starting = {
        "low": f"Start on {anchor} in the low register for weight. Give the first attack space before repeating the pulse.",
        "high": f"Enter on {anchor} with a light bow in the upper register. Let the line sing above the pulse.",
        "default": f"Set the pulse on {anchor} at about {preset.tempo_bpm} BPM. Bring in the rest of the pattern once that entrance feels steady.",
    }
    sections = {
        "why_it_works": why,
        "how_to_start": starting.get(register, starting["default"]),
        "how_to_develop": develop,
        "how_to_end": end,
        "how_to_transition": _transition_summary(tonic, mode, preset.name),
    }
    terms = {
        "why_it_works": why_terms,
        "how_to_start": ("tonic", "ostinato"),
        "how_to_develop": ("chord-tones", "ostinato"),
        "how_to_end": ("cadence",),
        "how_to_transition": ("mode-shift", "modal-borrowing") if mode == "dorian" else ("modulation", "pivot-chord", "tonicization"),
    }
    return sections, terms


def explain_duet_score(score, preset: MoodPreset) -> TheoryExplanation:
    """Read both performed parts; never use progression input as duet evidence."""
    voices = []
    all_tones = []
    for part in score.parts:
        notes = list(part.recurse().notes)
        if not notes:
            continue
        label = part.partName or str(part.id)
        first = notes[0].pitches[0].nameWithOctave.replace("-", "b")
        last = notes[-1].pitches[-1].nameWithOctave.replace("-", "b")
        voices.append((label, first, last))
        all_tones.extend(p.name for event in notes for p in event.pitches)
    if not voices:
        raise ValueError("The authored duet has no notes to explain.")
    tonic = pitch_class(preset.key_tonic)
    color, mode = _collection(all_tones, tonic)
    first_label, first_note, last_note = voices[0]
    other_label, other_first, other_last = voices[-1]
    sections = {
        "why_it_works": f"In this authored duet, {color}. Listen to how the two written lines combine rather than treating either line as a complete chord.",
        "how_to_start": f"{first_label} opens on {first_note}; {other_label} opens on {other_first}. Match those written entrances at {preset.duet_tempo_bpm or preset.tempo_bpm} BPM.",
        "how_to_develop": f"Shape {first_label}'s line from {first_note} toward {last_note}. {PLAYING_TIPS.get(preset.name, 'Let the other part stay audible as you vary your dynamics.')}",
        "how_to_end": f"The written parts finish on {last_note} and {other_last}. For another pass, connect them gently back to {first_note} and {other_first}.",
        "how_to_transition": _transition_summary(tonic, mode, preset.name),
    }
    terms = {
        "why_it_works": ("modes", "voice-leading"),
        "how_to_start": ("tonic", "voice-leading"),
        "how_to_develop": ("voice-leading",),
        "how_to_end": ("cadence",),
        "how_to_transition": ("mode-shift", "modal-borrowing") if mode == "dorian" else ("modulation", "pivot-chord"),
    }
    return TheoryExplanation(**sections, short_sections=sections, term_ids=terms)
