import ast
from pathlib import Path

FORBIDDEN = {"streamlit", "argparse"}


def _forbidden_imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = {node.module.split(".")[0]}
        else:
            continue
        found |= names & FORBIDDEN
    return found


def test_core_has_no_forbidden_imports():
    core_root = Path(__file__).resolve().parents[1] / "core"
    for py_file in core_root.rglob("*.py"):
        violations = _forbidden_imports_in_file(py_file)
        assert not violations, f"{py_file} imports forbidden module(s): {violations}"


def test_checker_detects_forbidden_import_in_fixture(tmp_path):
    # Proves the checker is not vacuously passing (e.g. due to an empty glob
    # or a typo in the forbidden-set check) by pointing it at a known-bad file.
    fixture = tmp_path / "fake_module.py"
    fixture.write_text("import argparse\n")

    violations = _forbidden_imports_in_file(fixture)

    assert violations == {"argparse"}
