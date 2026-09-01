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
SHEERAN_LOOPER_GUIDE = "[data-testid=sheeran-looper-guide]"
SHEERAN_LOOPER_MANUAL_LINK = "[data-testid=sheeran-looper-manual-link]"
SHEERAN_LOOPER_MANUAL_URL = (
    "https://cdn.inmusicbrands.com/SLOOPERS/LP2/"
    "Sheeran%20Looper%20%2B%20-%20User%20Guide%20-%20v2.0.0%20%28RevA%29.pdf"
)
PEDALBOARD_GUIDE = "[data-testid=pedalboard-guide]"
TWIN_LOOPER_MANUAL_LINK = "[data-testid=twin-looper-manual-link]"
TWIN_LOOPER_MANUAL_URL = "https://www.manualslib.com/manual/1334821/Rowin-Twin-Looper.html"
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
@allure.story("Sheeran Looper+ Guide")
@allure.title("Quick setup guide is collapsed and exposes return-safe instructions")
def test_sheeran_looper_guide(page: Page):
    guide = page.locator(SHEERAN_LOOPER_GUIDE)
    power_text = guide.get_by_text("Use 9 V DC, 500 mA minimum", exact=False)

    with allure.step("Assert the guide is present and collapsed by default"):
        guide.wait_for(state="visible", timeout=ASYNC_TIMEOUT_MS)
        assert guide.is_visible()
        assert not power_text.is_visible()

    with allure.step("Expand the guide"):
        guide.click()
        power_text.wait_for(state="visible", timeout=ASYNC_TIMEOUT_MS)

    with allure.step("Assert setup, control, tuner, and return-safe guidance"):
        assert guide.get_by_text("Cello → INST L (MONO)", exact=False).is_visible()
        assert guide.get_by_text("Left pedal: Record → Overdub → Play", exact=False).is_visible()
        assert guide.get_by_text("There is no built-in tuner", exact=False).is_visible()
        assert guide.get_by_text("Do not save the test loop", exact=False).is_visible()
        assert guide.get_by_text("Factory reset — erases all user content", exact=True).is_visible()

    with allure.step("Assert the manual link targets the official inMusic guide"):
        manual_link = guide.locator(SHEERAN_LOOPER_MANUAL_LINK)
        assert manual_link.get_attribute("href") == SHEERAN_LOOPER_MANUAL_URL

    with allure.step("Assert the expanded guide fits a mobile viewport"):
        page.set_viewport_size({"width": 390, "height": 844})
        guide_box = guide.bounding_box()
        assert guide_box is not None
        assert guide_box["x"] >= 0
        assert guide_box["x"] + guide_box["width"] <= 390


@allure.feature("Loop Coach")
@allure.story("Pedalboard Guide")
@allure.title("Pedalboard guide is collapsed and explains the loop-seam settings")
def test_pedalboard_guide(page: Page):
    guide = page.locator(PEDALBOARD_GUIDE)
    chain_text = guide.get_by_text("Cello → Atmosphere (reverb)", exact=False)

    with allure.step("Assert the guide is present and collapsed by default"):
        guide.wait_for(state="visible", timeout=ASYNC_TIMEOUT_MS)
        assert guide.is_visible()
        assert not chain_text.is_visible()

    with allure.step("Expand the guide"):
        guide.click()
        chain_text.wait_for(state="visible", timeout=ASYNC_TIMEOUT_MS)

    with allure.step("Assert chain, two-looper, and Twin Looper control guidance"):
        assert guide.get_by_text("printed into the take", exact=False).is_visible()
        assert guide.get_by_text("Drive one of them", exact=False).is_visible()
        assert guide.get_by_text("CHANGE picks FORWARD or REVERSE", exact=False).is_visible()

    with allure.step("Assert the seam guidance names both offending controls"):
        seam = guide.get_by_text("Set Atmosphere TRAIL to OFF", exact=False)
        assert seam.is_visible()
        assert guide.get_by_text("Keep Aquarius F.BACK low", exact=False).is_visible()
        assert guide.get_by_text("Closing the loop cleanly", exact=True).is_visible()

    with allure.step("Assert the manual link targets the Twin Looper manual"):
        manual_link = guide.locator(TWIN_LOOPER_MANUAL_LINK)
        assert manual_link.get_attribute("href") == TWIN_LOOPER_MANUAL_URL

    with allure.step("Assert the expanded guide fits a mobile viewport"):
        page.set_viewport_size({"width": 390, "height": 844})
        guide_box = guide.bounding_box()
        assert guide_box is not None
        assert guide_box["x"] >= 0
        assert guide_box["x"] + guide_box["width"] <= 390


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
