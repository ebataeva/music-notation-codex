"""Playwright end-to-end happy-path tests for the Cello Loop Coach app.

These tests drive the running NiceGUI app via the Playwright sync API.
The `page` fixture (a Playwright ``Page``) is provided by conftest.py,
which already navigates to the app URL.

Per TEST-03, this file MUST NOT import from ``core`` or ``app``.
"""

import allure
from playwright.sync_api import Page

# Stable data-testid attributes exposed by the Loop Coach UI.
CHORD_INPUT = "[data-testid=chord-input]"
GENERATE_BTN = "[data-testid=generate-btn]"
EXAMPLE_BTN = "[data-testid=example-btn]"
VARIANT_CARDS = [
    "[data-testid=variant-card-0]",
    "[data-testid=variant-card-1]",
    "[data-testid=variant-card-2]",
]
VARIANT_TITLES = [
    "[data-testid=variant-title-0]",
    "[data-testid=variant-title-1]",
    "[data-testid=variant-title-2]",
]

# NiceGUI uses Socket.IO for async DOM updates; allow generous wait time.
ASYNC_TIMEOUT_MS = 30_000


@allure.feature("Loop Coach")
@allure.story("Happy Path")
@allure.title("Generate produces three non-empty variant cards")
def test_happy_path_generate_three_variants(page: Page):
    """Fill the chord progression, generate, and assert 3 variant cards appear."""

    chord_progression = "Am F C G"

    with allure.step("Wait for chord input to be visible"):
        page.wait_for_selector(CHORD_INPUT, timeout=ASYNC_TIMEOUT_MS)

    with allure.step(f'Fill chord input with "{chord_progression}"'):
        chord_field = page.locator(CHORD_INPUT)
        chord_field.click()
        chord_field.fill(chord_progression)
        assert chord_field.input_value() == chord_progression

    with allure.step("Click the Generate button"):
        page.locator(GENERATE_BTN).click()

    with allure.step("Wait for the first variant card to render"):
        page.wait_for_selector(VARIANT_CARDS[0], timeout=ASYNC_TIMEOUT_MS)

    with allure.step("Assert all three variant cards are visible"):
        for card_selector in VARIANT_CARDS:
            card = page.locator(card_selector)
            card.wait_for(state="visible", timeout=ASYNC_TIMEOUT_MS)
            assert card.is_visible(), f"Expected {card_selector} to be visible"

    with allure.step("Assert each variant card has non-empty text"):
        for card_selector, title_selector in zip(VARIANT_CARDS, VARIANT_TITLES):
            card_text = page.locator(card_selector).inner_text(timeout=ASYNC_TIMEOUT_MS)
            assert card_text.strip(), f"{card_selector} has empty text"
            title_text = page.locator(title_selector).inner_text(timeout=ASYNC_TIMEOUT_MS)
            assert title_text.strip(), f"{title_selector} has empty text"


@allure.feature("Loop Coach")
@allure.story("Happy Path")
@allure.title("Example button fills the chord form")
def test_example_button_fills_form(page: Page):
    """Clicking #example-btn should populate the chord input with the default progression."""

    expected_value = "Am F C G"

    with allure.step("Wait for chord input to be visible"):
        page.wait_for_selector(CHORD_INPUT, timeout=ASYNC_TIMEOUT_MS)

    with allure.step("Click the Example button"):
        page.locator(EXAMPLE_BTN).click()

    with allure.step(f"Assert chord input value equals \"{expected_value}\""):
        # NiceGUI updates the input over Socket.IO; poll until value settles.
        page.wait_for_function(
            f"() => document.querySelector('{CHORD_INPUT}')?.value === {expected_value!r}",
            timeout=ASYNC_TIMEOUT_MS,
        )
        assert page.locator(CHORD_INPUT).input_value() == expected_value
