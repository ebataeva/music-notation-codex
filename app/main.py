"""NiceGUI app entry point for the Cello Loop Coach.

Run: python app/main.py
Opens: http://localhost:8080
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nicegui import app, ui

from app.pages.loop_coach import create_loop_coach_page
from app.pages.recorder import create_recorder_page

STORAGE_SECRET = "cello-loop-coach-v1"


@ui.page("/")
def main_page():
    create_loop_coach_page()


@ui.page("/practice")
def practice_page():
    create_recorder_page()


app.storage.secret = STORAGE_SECRET
ui.run(
    host="0.0.0.0",
    port=int(os.environ.get("NICEGUI_PORT", "8080")),
    title="Cello Loop Coach",
    reload=False,
    storage_secret=STORAGE_SECRET,
)
