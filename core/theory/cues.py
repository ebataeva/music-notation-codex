from __future__ import annotations

from core.models import GenerationTrace, MoodPreset


def tempo_band(tempo_bpm: int) -> str:
    if tempo_bpm < 70:
        return "slow"
    if tempo_bpm < 96:
        return "medium"
    return "fast"


def primary_register(trace: GenerationTrace) -> str:
    registers = trace.register_choices or []
    for register in registers:
        if register:
            return register
    return "working register"


def cue_pair_for(preset: MoodPreset, trace: GenerationTrace) -> tuple[str, str]:
    band = tempo_band(preset.duet_tempo_bpm or preset.tempo_bpm)
    register = primary_register(trace)

    if band == "slow":
        start = f"Start with a quiet bow on the {register}, leaving space around the first loop pulse."
        transition = "Transition by swelling the bow pressure, then release into the next loop entrance."
    elif band == "fast":
        start = f"Start with short bow strokes in the {register} so the loop has a clear motor."
        transition = "Transition by tightening the dynamics for one bar, then open the register on the repeat."
    else:
        start = f"Start with an even bow pulse in the {register}, keeping each loop entrance grounded."
        transition = "Transition by leaning into the last pulse, then answer it in a nearby register."

    return start, transition
