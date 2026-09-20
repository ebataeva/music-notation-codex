# music-notation-codex

Local workflow for generating cello parts as MusicXML and MIDI, with genre presets and harmonic-development guidance.

## What's inside

- `scripts/generate_cello_dark_ostinato.py` — generates 8-bar cello ostinatos across genres.
- `scripts/harmony_advisor.py` — suggests chord progressions, modulations, and techniques for mystery, drive, and sensual tension.
- `scores/musicxml/` — MusicXML files for MuseScore.
- `scores/midi/` — MIDI files for Ableton.
- `scores/pdf/` — PDF export destination from MuseScore.
- `references/` — reference sketches and materials.

## Setup

From the project folder:

```bash
cd /Users/ebataeva/Brain/Projects/music-notation-codex
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `.venv` already exists:

```bash
cd /Users/ebataeva/Brain/Projects/music-notation-codex
source .venv/bin/activate
```

## Generate MusicXML and MIDI

Basic usage:

```bash
python scripts/generate_cello_dark_ostinato.py
```

List available genres:

```bash
python scripts/generate_cello_dark_ostinato.py --list-genres
```

Generate a specific genre:

```bash
python scripts/generate_cello_dark_ostinato.py --genre ritual_tribal
python scripts/generate_cello_dark_ostinato.py --genre noir_slow_burn
python scripts/generate_cello_dark_ostinato.py --genre driving_cinematic
python scripts/generate_cello_dark_ostinato.py --genre dark_trip_hop
```

Set an output name:

```bash
python scripts/generate_cello_dark_ostinato.py --genre driving_cinematic --output-name cello_drive_take_01
```

The script saves:

- `scores/musicxml/<output-name>.musicxml`
- `scores/midi/<output-name>.mid`

## Available genres

- `dark_trip_hop` — dark, sensual, looping trip-hop groove.
- `ritual_tribal` — ritual pulse with more accents and physical motion.
- `noir_slow_burn` — slow noir, subtext, tense pause.
- `driving_cinematic` — fast cinematic motor, drive, and build.

## Harmony, modulation, and mood guidance

List advisor genres:

```bash
python scripts/harmony_advisor.py --list-genres
```

Get ideas for a genre:

```bash
python scripts/harmony_advisor.py --genre dark_trip_hop
python scripts/harmony_advisor.py --genre ritual_tribal
python scripts/harmony_advisor.py --genre noir_slow_burn
python scripts/harmony_advisor.py --genre driving_cinematic
```

The advisor explains:

- which harmonic progressions to try;
- how to modulate;
- what adds mystery;
- what adds drive;
- what adds sensual tension;
- why each device works musically.

## Open MusicXML in MuseScore

1. Open MuseScore.
2. Choose `File -> Open`.
3. Open a file from `scores/musicxml/`.
4. If needed, export PDF via `File -> Export`.

## Import MIDI into Ableton

1. Open Ableton Live.
2. Drag a `.mid` file from `scores/midi/` onto a MIDI track.
3. Assign a cello instrument or any bass/string timbre.
4. Enable loop on the clip if you want to use the ostinato as a repeating groove.

## Change the music in code

Open `scripts/generate_cello_dark_ostinato.py`.

- Genres are defined in `GENRE_PRESETS`.
- Change key via `key_tonic` and `key_mode`.
- Change tempo via `tempo_bpm`.
- Change meter via `meter_signature`.
- Change pitches in `bars`.
- Change rhythm in `rhythm`.
- Change MIDI velocity via `velocity`.

Important: the total duration in each bar must match the meter. For 4/4 that is `4.0`. For example, eight eighth notes are `[0.5] * 8`, and sixteen sixteenth notes are `[0.25] * 16`.

Current parts are single-voice, with no impossible double stops, in the playable cello register.
