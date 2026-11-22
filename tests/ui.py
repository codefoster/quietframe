"""Run with Playwright for Python and its Chromium browser installed."""
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

APP = Path(__file__).resolve().parents[1] / "app" / "index.html"
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
    page = browser.new_page(viewport={"width": 1920, "height": 1080}, offline=True)
    errors = []
    remote_requests = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: (
        remote_requests.append(request.url) if request.url.startswith(("https:", "http:")) else None
    ))
    page.goto(APP.as_uri())

    artwork = page.get_by_role("img")
    assert artwork.evaluate("(img) => img.complete && img.naturalWidth >= 1920")
    assert artwork.bounding_box() == {"x": 0, "y": 0, "width": 1920, "height": 1080}
    jellyfin = page.get_by_role("button", name="Open Jellyfin")
    status = page.get_by_role("status")
    expect(jellyfin).to_be_focused()
    expect(jellyfin).to_have_css("border-top-color", "rgb(255, 241, 211)")
    expect(page.get_by_role("button")).to_have_count(1)
    if len(sys.argv) == 2:
        page.screenshot(path=sys.argv[1])
    for key in (37, 38, 39, 40):
        remote(page, key)
        expect(jellyfin).to_be_focused()
    remote(page, 13)
    expect(status).to_contain_text("TV preview")
    remote(page, 10009)
    expect(status).to_be_empty()

    # Test the exact package configuration against simulated Tizen APIs.
    page.add_init_script(MOCK)
    page.reload()
    page.evaluate("window.result = 'ok'")
    remote(page, 13)
    remote(page, 13, repeat=True)
    assert page.evaluate("calls") == [
        ["http://tizen.org/appcontrol/operation/default", "AprZAARz4r.Jellyfin"]
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
    expect(status).to_contain_text("Opening")
    remote(page, 10009)
    page.evaluate("window.finishLaunch()")
    expect(status).to_be_empty()
    remote(page, 13)
    expect(status).to_have_text("Open Jellyfin from Samsung Home.", timeout=6500)
    remote(page, 10009)
    remote(page, 10009)
    assert page.evaluate("calls[calls.length - 1]") == "exit"
    assert errors == []
    assert remote_requests == []

    # Exercise multiple shortcuts without adding placeholders to the actual app.
    multi = browser.new_page(viewport={"width": 1280, "height": 720}, offline=True)
    multi.add_init_script("""
      Object.defineProperty(window, 'quietFrameShortcuts', {
        set: function(shortcuts) {
          this.shortcutsForTest = shortcuts.concat({
            label: 'Second app', icon: 'assets/media.svg', appId: 'test.second'
          });
        },
        get: function() { return this.shortcutsForTest; }
      });
    """)
    multi.goto(APP.as_uri())
    second = multi.get_by_role("button", name="Open Second app")
    remote(multi, 39)
    expect(second).to_be_focused()
    remote(multi, 39)
    expect(second).to_be_focused()
    remote(multi, 13)
    expect(multi.get_by_role("status")).to_contain_text("Second app")
    remote(multi, 37)
    expect(multi.get_by_role("button", name="Open Jellyfin")).to_be_focused()
    print("PASS 1080p offline artwork, focus, remote codes, launch outcomes, Back, no remote requests")
    print("PASS 720p configurable shortcut row and horizontal D-pad navigation")
