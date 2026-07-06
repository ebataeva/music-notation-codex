"""Pytest fixtures for Playwright-based UI tests against the NiceGUI app.

TEST-03: This file MUST NOT import from core/ or app/.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_PORT = 8099
TEST_URL = f"http://localhost:{TEST_PORT}/"


def _wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    """Poll until the port is accepting connections or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def server():
    """Start the NiceGUI app on a test port for the entire test session."""
    env = {**os.environ}
    env["NICEGUI_PORT"] = str(TEST_PORT)
    env["NICEGUI_SCREEN_TEST_PORT"] = str(TEST_PORT)

    # Start the app — it reads NICEGUI_PORT env var to override the default 8080.
    proc = subprocess.Popen(
        [str(PROJECT_ROOT / ".venv" / "bin" / "python"), "app/main.py"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        if not _wait_for_port("localhost", TEST_PORT, timeout=30):
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            pytest.fail(f"NiceGUI server did not start on port {TEST_PORT} within 30s. stderr: {stderr}")
        yield TEST_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def browser():
    """Launch a Playwright Chromium browser for the test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(scope="function")
def page(browser, server):
    """Create a fresh page context for each test, navigated to the app."""
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)  # 30s — NiceGUI Socket.IO async updates
    page.goto(server, wait_until="domcontentloaded")
    yield page
    context.close()
