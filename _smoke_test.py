"""Quick smoke test for the generation service."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.generation import generate_loop, available_presets

result = generate_loop("Am F C G", "dark_trip_hop", seed=42)
print("Error:", result.get("error"))
print("Why it works:", result.get("why_it_works", "")[:100])
print("Seed:", result.get("seed"))
print("MIDI bytes (b64):", len(result.get("midi_bytes_b64", "")), "chars")
print("Presets:", available_presets())
print("SUCCESS")
