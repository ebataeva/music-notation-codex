"""NiceGUI app entry point for the Cello Loop Coach.

Run: python app/main.py
Opens: http://localhost:8080
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nicegui import app, ui

from app.pages.loop_coach import create_loop_coach_page

STORAGE_SECRET = "cello-loop-coach-v1"


@ui.page("/")
def main_page():
    create_loop_coach_page()


app.storage.secret = STORAGE_SECRET
ui.run(host="0.0.0.0", port=8080, title="Cello Loop Coach", reload=False)
