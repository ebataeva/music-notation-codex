from urllib.parse import parse_qs, urlparse

import allure
from playwright.sync_api import expect


def choose(page, test_id, text):
    page.locator(f'[data-testid="{test_id}"]').click()
    page.get_by_role("option", name=text, exact=True).click()


def assert_notation_and_playback(page):
    expect(page.locator("#dictionary-score svg").first).to_be_visible(timeout=60000)
    audio = page.locator("#theory-audio")
    expect(audio).to_be_visible(timeout=60000)
    page.get_by_test_id("theory-title").click()
    audio.evaluate("element => element.play()")
    page.wait_for_function("document.querySelector('#theory-audio')?.currentTime > 0.3", timeout=10000)
    assert audio.evaluate("element => !element.paused && element.duration > 0")


@allure.feature("Theory Dictionary")
def test_dictionary_opens_in_requested_key_and_plays_notes(page, server):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(server + "theory?term=mode-shift&tonic=E&mode=dorian&preset=dorian_sexy_duet")
    expect(page.get_by_test_id("theory-title")).to_have_text("Same-tonic mode shift", timeout=60000)
    expect(page.get_by_test_id("theory-context")).to_contain_text("E · dorian")
    expect(page.get_by_test_id("theory-progression")).to_have_text("Em → A → Am → C → Am → Em → Em")
    assert_notation_and_playback(page)
    page.screenshot(path="/tmp/music-theory-dictionary-e.png", full_page=True)
    assert not errors


@allure.feature("Theory Dictionary")
def test_card_link_preserves_solo_key_and_original_loop(page):
    page.get_by_test_id("chord-input").fill("Em9 A9")
    choose(page, "key-tonic-select", "E")
    page.get_by_test_id("generate-btn").click()
    why = page.get_by_test_id("theory-0-why_it_works")
    expect(why).to_contain_text("i9 → IV9", timeout=60000)
    expect(why).to_contain_text("C# (6)")
    loop_audio = page.locator("#loop-audio-0-full")
    expect(loop_audio).to_be_visible()
    loop_audio.evaluate("audio => audio.play()")
    page.wait_for_function("document.querySelector('#loop-audio-0-full').currentTime > 0.3")
    link = page.get_by_test_id("term-0-why_it_works-sevenths-ninths")
    assert parse_qs(urlparse(link.get_attribute("href")).query)["tonic"] == ["E"]
    with page.expect_popup() as popup:
        link.click()
    dictionary = popup.value
    expect(dictionary.get_by_test_id("theory-context")).to_contain_text("E ·", timeout=60000)
    assert_notation_and_playback(dictionary)
    expect(page.get_by_test_id("chord-input")).to_have_value("Em9 A9")
    expect(page.locator("#osmd-container-0 svg").first).to_be_visible()
    loop_time = loop_audio.evaluate("audio => audio.currentTime")
    page.wait_for_function("previous => {const a = document.querySelector('#loop-audio-0-full'); return !a.paused && a.currentTime !== previous;}", arg=loop_time)
    page.screenshot(path="/tmp/music-theory-loop-e.png", full_page=True)
    dictionary.close()


@allure.feature("Theory Dictionary")
def test_dictionary_distinguishes_tonicization_and_modulation(page, server):
    page.goto(server + "theory?term=tonicization&tonic=C&mode=major")
    expect(page.get_by_test_id("theory-progression")).to_have_text("C → E7 → Am → G7 → C", timeout=60000)
    choose(page, "theory-term", "Modulation")
    expect(page.get_by_test_id("theory-progression")).to_have_text("C → E7 → Am → Dm → E7 → Am → Am", timeout=60000)
    assert_notation_and_playback(page)
    page.screenshot(path="/tmp/music-theory-modulation-c.png", full_page=True)


@allure.feature("Theory Dictionary")
def test_authored_duet_uses_score_context_instead_of_disabled_inputs(page):
    choose(page, "mood-select", "dorian_sexy_duet")
    expect(page.get_by_test_id("chord-input")).to_be_disabled()
    expect(page.get_by_test_id("score-source")).to_contain_text("Authored duet in D")
    page.get_by_test_id("generate-btn").click()
    expect(page.get_by_test_id("variant-key-0")).to_have_text("Reference key: D dorian", timeout=60000)
    expect(page.get_by_test_id("theory-0-why_it_works")).to_contain_text("B (6)")
    expect(page.locator("#osmd-container-0 svg").first).to_be_visible(timeout=60000)
