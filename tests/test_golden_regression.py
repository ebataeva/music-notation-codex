"""Golden-file regression guard for the 5 existing CLI scripts.

This test protects Roadmap Phase 1 success criterion 3: after Plan 04 moves
preset data into ``core/presets/``, all 5 existing scripts must still produce
the same output as before the move.

Why MIDI is hashed directly but MusicXML is normalized first (RESEARCH.md
Pitfall 1, verified live): ``music21.base.Music21Object.id`` defaults to
``builtins.id(self)`` (the object's memory address) whenever ``.id`` is not
explicitly set. The MusicXML exporter mints ``<score-part id="P...">``,
``<score-instrument id="I...">`` and ``<midi-instrument id="I...">``
attributes from these ids, so two runs of the same script with zero data
change still produce byte-different MusicXML. The ``<encoding-date>`` field
also varies by calendar day. MIDI output has no such id/date artifacts and
was verified byte-identical across repeated runs. So: MIDI is the primary,
fully deterministic guard; MusicXML is normalized (strip encoding-date and
P.../I... id attribute values) before hashing as a secondary guard.

Where the output comes from: the scripts are re-run into a temporary
directory, chosen by pointing ``ExportEngine`` at it through the
``MNC_SCORES_DIR`` environment variable, and the hashes are computed from
that directory. This module therefore neither reads nor writes anything
under ``scores/`` -- the tracked files there are a by-product of running the
scripts by hand, not the baseline. The baseline is
``tests/golden/baseline_hashes.json`` and nothing else.

Recapture procedure (only run deliberately, when an intentional data or
script change requires a new baseline -- e.g. after Plan 04's data move is
verified correct):

    .venv/bin/python3 -c "from tests.test_golden_regression import capture_baseline; capture_baseline()"

This overwrites tests/golden/baseline_hashes.json with hashes freshly
captured from a temporary re-run of the scripts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = PROJECT_ROOT / "tests" / "golden" / "baseline_hashes.json"
PYTHON = sys.executable

# (script, extra_args, output_name) for every invocation that must be re-run
# to regenerate the golden set. The ostinato script needs one invocation per
# genre; the three duet scripts take no CLI args and always write one
# fixed-name pair each.
INVOCATIONS: list[tuple[str, list[str], str]] = [
    ("generate_cello_dark_ostinato.py", ["--genre", "dark_trip_hop"], "cello_dark_trip_hop_ostinato"),
    ("generate_cello_dark_ostinato.py", ["--genre", "ritual_tribal"], "cello_ritual_tribal_ostinato"),
    ("generate_cello_dark_ostinato.py", ["--genre", "noir_slow_burn"], "cello_noir_slow_burn_ostinato"),
    ("generate_cello_dark_ostinato.py", ["--genre", "driving_cinematic"], "cello_driving_cinematic_ostinato"),
    ("generate_sexy_duet_loop.py", [], "sexy_d_minor_violin_cello_loop"),
    ("generate_simple_sexy_duet_loop.py", [], "simple_sexy_d_minor_violin_cello_loop"),
    ("generate_dorian_sexy_duet_loop.py", [], "dorian_sexy_violin_cello_loop"),
]

# Strips volatile MusicXML fields before hashing: the encoding-date element,
# and every id="P..." / id="I..." attribute value (score-part,
# score-instrument, midi-instrument ids are minted from Python object
# memory addresses and differ on every run).
_ENCODING_DATE_RE = re.compile(r"<encoding-date>.*?</encoding-date>")
_VOLATILE_ID_RE = re.compile(r'id="[PI][^"]*"')


def run_all_scripts(output_dir: Path) -> None:
    """Re-run all 5 scripts' 7 invocations, writing into output_dir.

    MNC_SCORES_DIR redirects every script's no-arg ``ExportEngine()`` at
    output_dir, so the pairs land in ``output_dir/midi`` and
    ``output_dir/musicxml`` and never in the repo working tree. The scripts
    still run with cwd=PROJECT_ROOT because their imports depend on it.
    """
    env = {**os.environ, "MNC_SCORES_DIR": str(output_dir)}
    for script_name, args, _output_name in INVOCATIONS:
        script_path = PROJECT_ROOT / "scripts" / script_name
        subprocess.run([PYTHON, str(script_path), *args], check=True, cwd=PROJECT_ROOT, env=env)


def normalize_musicxml(text: str) -> str:
    """Strip volatile encoding-date and P.../I... id attributes before hashing."""
    text = _ENCODING_DATE_RE.sub("<encoding-date></encoding-date>", text)
    text = _VOLATILE_ID_RE.sub('id="STRIPPED"', text)
    return text


def sha1_of_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def sha1_of_normalized_musicxml(path: Path) -> str:
    normalized = normalize_musicxml(path.read_text(encoding="utf-8"))
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def compute_current_hashes(output_dir: Path) -> dict[str, dict[str, str]]:
    midi_dir = output_dir / "midi"
    musicxml_dir = output_dir / "musicxml"
    midi_hashes: dict[str, str] = {}
    musicxml_hashes: dict[str, str] = {}
    for _script_name, _args, output_name in INVOCATIONS:
        midi_path = midi_dir / f"{output_name}.mid"
        musicxml_path = musicxml_dir / f"{output_name}.musicxml"
        midi_hashes[midi_path.name] = sha1_of_file(midi_path)
        musicxml_hashes[musicxml_path.name] = sha1_of_normalized_musicxml(musicxml_path)
    return {"midi": midi_hashes, "musicxml_normalized": musicxml_hashes}


def capture_baseline() -> None:
    """Re-run all scripts and write tests/golden/baseline_hashes.json.

    Run this deliberately (see module docstring) whenever an intentional
    change to script output requires a new baseline. Do not run this to
    "fix" a failing regression test without first confirming the output
    change was intentional.

    The scripts are re-run into a throwaway temporary directory, so this
    touches nothing under scores/; the only file it writes is BASELINE_PATH.
    """
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        run_all_scripts(output_dir)
        hashes = compute_current_hashes(output_dir)
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_baseline() -> dict[str, dict[str, str]]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_midi_outputs_match_baseline(tmp_path) -> None:
    """Runs every invocation into tmp_path and compares with the committed baseline.

    This is the guard Plan 04's data-move into core/presets/ must keep green.
    """
    run_all_scripts(tmp_path)
    baseline = _load_baseline()
    current = compute_current_hashes(tmp_path)
    assert current["midi"] == baseline["midi"]


def test_musicxml_outputs_match_baseline_normalized(tmp_path) -> None:
    """Runs every invocation into tmp_path and compares with the committed baseline.

    Compares normalized MusicXML (encoding-date and P.../I... ids stripped)
    rather than raw bytes -- see module docstring for why raw-byte hashing
    always fails, even with zero data change.
    """
    run_all_scripts(tmp_path)
    baseline = _load_baseline()
    current = compute_current_hashes(tmp_path)
    assert current["musicxml_normalized"] == baseline["musicxml_normalized"]
