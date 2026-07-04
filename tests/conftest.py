import pytest


@pytest.fixture
def tolerance() -> float:
    """Float-comparison tolerance for later plans' bar-duration/validator tests."""
    return 1e-9
