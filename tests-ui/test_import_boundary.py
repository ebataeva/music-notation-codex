"""Static import boundary check for tests-ui/.

Ensures no .py file under tests-ui/ imports from `core` or `app`,
per TEST-03 requirement.
"""

from pathlib import Path

import allure
import pytest


@allure.feature("Import Boundary")
@allure.story("TEST-03")
def test_no_imports_from_core_or_app():
    """Scan every .py file in tests-ui/ and assert none import core/app."""
    tests_ui_dir = Path(__file__).parent
    py_files = sorted(tests_ui_dir.rglob("*.py"))

    violations = []
    for py_file in py_files:
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if (
                stripped.startswith("from core")
                or stripped.startswith("import core")
                or stripped.startswith("from app")
                or stripped.startswith("import app")
            ):
                violations.append(f"{py_file.name}:{lineno}: {stripped}")

    assert not violations, (
        "Import boundary violations in tests-ui/ (must not import core/ or app/):\n"
        + "\n".join(violations)
    )
