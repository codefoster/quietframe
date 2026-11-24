"""Run with Playwright for Python and its Chromium browser installed."""
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

from playwright.sync_api import expect, sync_playwright

APP = Path(__file__).resolve().parents[1] / "app" / "index.html"
SHORTCUTS = [
    ("Prime Video", "org.tizen.primevideo"),
    ("YouTube", "9Ur5IzDKqV.TizenYouTube"),
    ("Jellyfin", "AprZAARz4r.Jellyfin"),
]
MOCK = """
window.calls = [];
window.tizen = {
  ApplicationControl: function(operation) { this.operation = operation; },
  application: {
    launchAppControl: function(control, id, success, failure) {
      calls.push([control.operation, id]);
      if (window.result === 'throw') throw new Error('SecurityError');
      if (window.result === 'error') failure({name: 'NotFoundError'});
      if (window.result === 'ok') success();
      if (window.result === 'delayed') window.finishLaunch = failure;
    },
    getCurrentApplication: function() {
      return {exit: function() { calls.push('exit'); }};
    }
  }
};
"""


def remote(page, code, repeat=False):
    page.evaluate(
        """([keyCode, repeat]) => document.dispatchEvent(new KeyboardEvent(
          'keydown', {keyCode, repeat, bubbles: true, cancelable: true}
        ))""",
        [code, repeat],
    )


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for width, height in ((1280, 720), (1920, 1080)):
        page = browser.new_page(
            viewport={"width": width, "height": height}, offline=True,
            locale="en-US", timezone_id="America/Los_Angeles",
        )
        errors, network = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: network.append(request.url)
                if request.url.startswith(("https:", "http:")) else None)
        page.clock.install(time=datetime(2026, 11, 23, 7, 59, 59, tzinfo=timezone.utc))
        page.goto(APP.as_uri())

        artwork = page.get_by_role("img")
        expect(artwork).to_have_attribute("src", re.compile(r"assets/gallery/"))
        assert artwork.evaluate("(img) => img.complete && img.naturalWidth >= 1280")
        assert artwork.bounding_box() == {"x": 0, "y": 0, "width": width, "height": height}
        for selector in (".dock", ".clock-panel"):
            rect = page.locator(selector).bounding_box()
            assert 0 <= rect["x"] < rect["x"] + rect["width"] <= width
            assert 0 <= rect["y"] < rect["y"] + rect["height"] <= height

        clock = page.locator(".clock")
        date = page.locator(".calendar")
        # Freeze at a known local date, then let the minute timer cross midnight.
        page.clock.pause_at(datetime(2026, 11, 23, 7, 59, 59, 900000, tzinfo=timezone.utc))
        expect(clock).to_have_text("11:59 PM")
        expect(date).to_have_text("Sunday, November 22, 2026")
        page.clock.run_for(100)
        expect(clock).to_have_text("12:00 AM")
        expect(date).to_have_text("Monday, November 23, 2026")
        page.clock.set_system_time(datetime(2026, 11, 23, 12, 34, tzinfo=timezone.utc))
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        expect(clock).to_have_text("4:34 AM")

        buttons = [page.get_by_role("button", name="Open " + label) for label, _ in SHORTCUTS]
        expect(page.get_by_role("button")).to_have_count(3)
        for button in buttons:
            img = button.locator("img")
            fallback = button.locator(".shortcut-fallback")
            name = img.get_attribute("src")
            if (APP.parent / name).exists():
                expect(img).to_be_visible()
                expect(fallback).to_be_hidden()
            else:
                expect(fallback).to_be_visible()
        expect(buttons[0]).to_be_focused()
        expect(buttons[0]).to_have_css("border-top-color", "rgb(255, 241, 211)")
        for key in (37, 38, 40):
            remote(page, key)
            expect(buttons[0]).to_be_focused()
        remote(page, 39)
        expect(buttons[1]).to_be_focused()
        remote(page, 39)
        remote(page, 39)
        expect(buttons[2]).to_be_focused()
        remote(page, 37)
        expect(buttons[1]).to_be_focused()
        status = page.get_by_role("status")
        remote(page, 13)
        expect(status).to_have_text("TV preview. Open YouTube on your Samsung TV.")
        remote(page, 10009)
        expect(status).to_be_empty()

        if width == 1920 and len(sys.argv) == 2:
            # The preview intentionally uses a sample time.
            page.clock.set_system_time(datetime(2026, 11, 24, 3, 24, tzinfo=timezone.utc))
            page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            page.screenshot(path=sys.argv[1])

        page.add_init_script(MOCK)
        page.reload()
        page.evaluate("window.result = 'ok'")
        remote(page, 13)
        remote(page, 13, repeat=True)
        for _ in SHORTCUTS[1:]:
            remote(page, 39)
            remote(page, 13)
        assert page.evaluate("calls") == [
            ["http://tizen.org/appcontrol/operation/default", app_id] for _, app_id in SHORTCUTS
        ]
        expect(status).to_be_empty()
        for failure in ("error", "throw"):
            page.evaluate("(value) => window.result = value", failure)
            remote(page, 13)
            expect(status).to_have_text("Open Jellyfin from Samsung Home.")
            remote(page, 10009)
            expect(status).to_be_empty()
        page.evaluate("window.result = 'delayed'")
        remote(page, 13)
        remote(page, 10009)
        page.evaluate("window.finishLaunch()")
        expect(status).to_be_empty()
        remote(page, 13)
        page.clock.run_for(5000)
        expect(status).to_have_text("Open Jellyfin from Samsung Home.")
        remote(page, 10009)
        remote(page, 10009)
        assert page.evaluate("calls[calls.length - 1]") == "exit"
        assert errors == []
        assert network == []
        page.close()
        print(f"PASS {width}x{height} offline layout, clock rollover and resume, icons, D-pad, all launch IDs and fallback")