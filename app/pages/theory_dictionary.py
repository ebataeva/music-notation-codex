from __future__ import annotations

from urllib.parse import urlencode

from nicegui import run, ui

from app.components.notation import load_notation_script, render_musicxml
from app.services.theory_dictionary import dictionary_entries, dictionary_example, transition_examples


TONICS = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
GUIDE_TERMS = ("pivot-chord", "tonicization", "modulation", "modal-borrowing", "direct-transition", "mode-shift")


def theory_url(term: str, tonic: str, mode: str, preset: str = "") -> str:
    return "/theory?" + urlencode({"term": term, "tonic": tonic, "mode": mode, "preset": preset})


def create_theory_dictionary_page(term: str = "tonic", tonic: str = "C", mode: str = "major", preset: str = "") -> None:
    entries = {entry["id"]: entry for entry in dictionary_entries()}
    load_notation_script()
    ui.link("Loop Coach", "/").classes("text-sm text-blue-600")
    ui.label("Theory Dictionary").classes("text-3xl font-bold").props("data-testid=theory-heading")
    ui.label("See the notes, hear the idea, then try it in your loop.").classes("text-gray-600")
    if term not in entries:
        ui.label("That article was not found. Choose a term below.").classes("text-amber-700")
        term = "tonic"
    if tonic not in TONICS:
        TONIC_OPTIONS = list(dict.fromkeys([tonic, *TONICS]))
    else:
        TONIC_OPTIONS = TONICS
    with ui.row().classes("w-full items-end gap-4"):
        term_select = ui.select({key: entry["title"] for key, entry in entries.items()}, value=term, label="Theory term").classes("min-w-64").props("data-testid=theory-term")
        tonic_select = ui.select(TONIC_OPTIONS, value=tonic, label="Example tonic").classes("w-36").props("data-testid=theory-tonic")
        mode_select = ui.select(["major", "minor", "dorian"], value=mode if mode in {"major", "minor", "dorian"} else "major", label="Source mode").classes("w-36").props("data-testid=theory-mode")
    status = ui.label("").classes("text-gray-600").props("data-testid=theory-status")
    content = ui.column().classes("w-full max-w-5xl gap-4").props("data-testid=theory-content")
    generation = {"version": 0}

    async def load_example() -> None:
        generation["version"] += 1
        version = generation["version"]
        selected, selected_tonic, selected_mode = term_select.value, tonic_select.value, mode_select.value
        status.text = "Preparing notation and audio…"
        content.clear()
        try:
            example = await run.io_bound(dictionary_example, selected, selected_tonic, selected_mode, preset)
        except ValueError as exc:
            if version == generation["version"]:
                status.text = str(exc)
            return
        except Exception:
            if version == generation["version"]:
                status.text = "The example could not load. Select the term again to retry."
            return
        if version != generation["version"]:
            return
        with content:
            ui.label(example["title"]).classes("text-2xl font-semibold").props("data-testid=theory-title")
            ui.label(example["definition"]).classes("text-base")
            ui.label(f"Reference: {selected_tonic} · {selected_mode}").classes("text-sm font-medium").props("data-testid=theory-context")
            ui.label(example["caption"]).classes("text-gray-700")
            if example["guide"]:
                guide = example["guide"]
                ui.label(f"{guide['source_key']} → {guide['target_key']} · {guide['method']}").classes("font-medium")
                ui.label(" → ".join(guide["labels"])).props("data-testid=theory-progression")
            render_musicxml(example["musicxml_string"], "dictionary-score")
            if example.get("wav_bytes_b64"):
                ui.html(f'<audio id="theory-audio" data-testid="theory-audio" controls preload="auto" style="width:100%"><source src="data:audio/wav;base64,{example["wav_bytes_b64"]}" type="audio/wav"></audio>').classes("w-full")
            else:
                ui.label(example.get("audio_error", "Audio is unavailable.")).classes("text-amber-700")
            ui.label("Listen for").classes("font-semibold")
            ui.label(example["guide"]["listen_for"] if example["guide"] else example["listen_for"])
            with ui.row().classes("gap-3"):
                for related in example["related_terms"]:
                    ui.link(entries[related]["title"], theory_url(related, selected_tonic, selected_mode, preset)).classes("text-blue-600")
            if selected in GUIDE_TERMS or selected == "modes":
                ui.separator()
                ui.label("Compare transitions").classes("text-xl font-semibold")
                ui.label("These are ideas to try, not changes detected in your loop.").classes("text-gray-600")
                guides = transition_examples(selected_tonic, selected_mode, preset)
                ui.label(guides[0]["style_note"]).classes("text-sm text-gray-600")
                for guide, guide_term in zip(guides, GUIDE_TERMS, strict=True):
                    with ui.card().classes("w-full"):
                        ui.label(guide["title"]).classes("font-semibold")
                        ui.label(f"{guide['source_key']} → {guide['target_key']}")
                        ui.label(" → ".join(guide["labels"]))
                        ui.label(guide["explanation"])
                        ui.link("Hear and see this example", theory_url(guide_term, selected_tonic, selected_mode, preset)).classes("text-blue-600")
        status.text = "Ready" if example.get("wav_bytes_b64") else "Notation ready; audio is unavailable."

    for selector in (term_select, tonic_select, mode_select):
        selector.on_value_change(load_example)
    ui.timer(0.1, load_example, once=True)
