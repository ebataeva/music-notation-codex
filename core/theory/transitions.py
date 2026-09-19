from __future__ import annotations

from dataclasses import dataclass

from core.theory.harmony import pitch_class, transpose_name


@dataclass(frozen=True)
class TransitionGuide:
    kind: str
    title: str
    source_key: str
    target_key: str
    method: str
    chords: tuple[tuple[str, ...], ...]
    labels: tuple[str, ...]
    explanation: str
    listen_for: str
    style_note: str
    term_ids: tuple[str, ...]


def normalize_context(tonic: str, mode: str) -> tuple[str, str]:
    tonic = pitch_class(tonic)
    if mode not in {"major", "minor", "dorian"}:
        raise ValueError("Choose major, minor, or dorian for the example.")
    return tonic, mode


def triad(root: str, quality: str = "major", seventh: bool = False) -> tuple[str, ...]:
    intervals = ["P1", "m3" if quality == "minor" else "M3", "P5"]
    if seventh:
        intervals.append("m7")
    return tuple(transpose_name(root, distance) for distance in intervals)


STYLE_NOTES = {
    "dark_trip_hop": "Keep the bass pulse steady; a new center can settle through repetition instead of a grand cadence.",
    "ritual_tribal": "Keep the rhythmic cell recognizable while a repeated bass anchor establishes the destination.",
    "noir_slow_burn": "Leave space around the changed note; chromatic color alone does not establish a new key.",
    "driving_cinematic": "Carry the pulse across the change, then repeat the destination bass to make the shift audible.",
    "sexy_duet": "Let one instrument carry a common tone while the other introduces the destination.",
    "simple_sexy_duet": "Use a short transition and a clear return when you want to preserve the intimate loop.",
    "dorian_sexy_duet": "Preserve the natural sixth for Dorian color; lowering it changes the mode, not the tonic.",
}


def transition_guides(tonic: str, mode: str, preset_name: str = "") -> tuple[TransitionGuide, ...]:
    """Demonstration recipes, not claims that a generated loop has modulated."""
    tonic, mode = normalize_context(tonic, mode)
    quality = "major" if mode == "major" else "minor"
    source = f"{tonic} {mode.capitalize() if mode == 'dorian' else mode}"
    home = triad(tonic, quality)
    home_label = tonic + ("m" if quality == "minor" else "")
    style = STYLE_NOTES.get(preset_name, "A cadence is one option; repetition and phrasing can also establish a new center.")

    if quality == "major":
        target = transpose_name(tonic, "P5")
        pivot = transpose_name(tonic, "M6")
        pivot_quality, pivot_role = "minor", "vi in the source = ii in the destination"
    else:
        target = transpose_name(tonic, "m3")
        pivot = tonic
        pivot_quality, pivot_role = "minor", "i in the source = vi in the destination"
    dominant = transpose_name(target, "P5")
    target_chord = triad(target)
    pivot_label = pivot + "m"
    guides = [TransitionGuide(
        "modulation", "Common-chord modulation", source, f"{target} major", "Common chord",
        (home, triad(pivot, pivot_quality), triad(dominant, seventh=True), target_chord, target_chord),
        (home_label, pivot_label, dominant + "7", target, target),
        f"Use {pivot_label} as {pivot_role}; follow it with {dominant}7 and settle on {target}.",
        f"Hear the closing {dominant}7–{target}, then the repeated {target}; the shared chord alone would not prove a modulation.",
        style, ("pivot-chord", "modulation", "cadence"),
    )]

    # The same secondary-dominant pair is placed in two different phrase contexts.
    destination = transpose_name(tonic, "M6" if quality == "major" else "P5")
    destination_chord = triad(destination, "minor")
    applied_dominant = transpose_name(destination, "P5")
    destination_label = destination + "m"
    home_dominant = transpose_name(tonic, "P5")
    pair = (triad(applied_dominant, seventh=True), destination_chord)
    guides.extend([
        TransitionGuide(
            "tonicization", "A brief tonicization", source, f"{destination} minor, then back to {source}", "Secondary dominant",
            (home, *pair, triad(home_dominant, seventh=True), home),
            (home_label, applied_dominant + "7", destination_label, home_dominant + "7", home_label),
            f"{applied_dominant}7 briefly points to {destination_label}; {home_dominant}7–{home_label} restores the original center.",
            f"Compare the short arrival on {destination_label} with the final return to {home_label}; a single dominant–tonic pair is not enough to prove a lasting key change.",
            style, ("tonicization", "secondary-dominant"),
        ),
        TransitionGuide(
            "modulation", "Establish a new minor key", source, f"{destination} minor", "Dominant of the destination",
            (home, *pair, triad(transpose_name(destination, "P4"), "minor"), *pair, destination_chord),
            (home_label, applied_dominant + "7", destination_label,
             transpose_name(destination, "P4") + "m", applied_dominant + "7", destination_label, destination_label),
            f"After {applied_dominant}7–{destination_label}, continue a phrase in {destination} minor and close there again.",
            f"The later cadence and sustained {destination_label} support the new center; compare this with the example that returns to {home_label}.",
            style, ("modulation", "secondary-dominant", "tonicization"),
        ),
    ])

    fourth = transpose_name(tonic, "P4")
    borrowed_quality = "minor" if quality == "major" or mode == "dorian" else "major"
    starting_fourth_quality = "major" if mode == "dorian" else quality
    borrowed_mode = "natural minor" if mode == "dorian" else ("minor" if quality == "major" else "major")
    borrowed_label = fourth + ("m" if borrowed_quality == "minor" else "")
    guides.append(TransitionGuide(
        "modal_borrowing", "Borrow a color, keep the tonic", source, source, "Parallel-mode borrowing",
        (home, triad(fourth, starting_fourth_quality), triad(fourth, borrowed_quality), home),
        (home_label, fourth + ("m" if starting_fourth_quality == "minor" else ""), borrowed_label, home_label),
        f"Borrow {borrowed_label} from the parallel {borrowed_mode} and return to {home_label}; {tonic} remains the reference tonic.",
        f"Hear the changed third of the chord on {fourth}, then the return home; this is a color change rather than a demonstrated new key.",
        style, ("modal-borrowing", "modes"),
    ))

    direct_target = transpose_name(tonic, "M2")
    direct_home = triad(direct_target, quality)
    direct_label = direct_target + ("m" if quality == "minor" else "")
    direct_dominant = transpose_name(direct_target, "P5")
    guides.append(TransitionGuide(
        "modulation", "Direct change at a phrase boundary", source, f"{direct_target} {quality}", "Direct transition",
        (home, home, direct_home, triad(direct_dominant, seventh=True), direct_home, direct_home),
        (home_label, home_label, direct_label, direct_dominant + "7", direct_label, direct_label),
        f"End the old phrase, start on {direct_label}, and reinforce the new center with {direct_dominant}7–{direct_label}.",
        f"The jump has no prepared common chord; the following phrase, not the jump alone, establishes {direct_target}.",
        style, ("direct-transition", "modulation"),
    ))
    sixth = transpose_name(tonic, "M6")
    flat_sixth = transpose_name(tonic, "m6")
    guides.append(TransitionGuide(
        "mode_shift", "Dorian to natural minor", f"{tonic} Dorian", f"{tonic} natural minor", "Same tonic, different mode",
        (triad(tonic, "minor"), triad(fourth), triad(fourth, "minor"), triad(flat_sixth),
         triad(fourth, "minor"), triad(tonic, "minor"), triad(tonic, "minor")),
        (tonic + "m", fourth, fourth + "m", flat_sixth, fourth + "m", tonic + "m", tonic + "m"),
        f"In this Dorian demonstration, lower {sixth} to {flat_sixth} (6 to b6) while keeping {tonic} as the tonic.",
        f"The later phrase keeps {flat_sixth} in several chords and settles on {tonic}m; the new collection lasts beyond a single borrowed chord.",
        style, ("mode-shift", "modes", "modal-borrowing"),
    ))
    return tuple(guides)
