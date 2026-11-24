"""Verify daily artwork in the app or a self-contained local preview."""
from datetime import datetime, timezone
from pathlib import Path
import sys

from playwright.sync_api import expect, sync_playwright

APP = Path(__file__).resolve().parents[1] / "app" / "index.html"


def instant(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def selected(page):
    return page.evaluate("""() => {
        const image = document.querySelector('.artwork');
        return quietFrameGallery.findIndex(work => image.getAttribute('src') === work.src);
    }""")


def wait_for_work(page, index):
    page.wait_for_function("""i => {
        const image = document.querySelector('.artwork');
        return image.complete && image.naturalWidth > 0 &&
               image.getAttribute('src') === quietFrameGallery[i].src;
    }""", arg=index)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else APP
    page = browser.new_page(
        viewport={"width": 1920, "height": 1080}, offline=True,
        locale="en-US", timezone_id="America/Los_Angeles",
    )
    requests, errors = [], []
    page.on("request", lambda request: requests.append(request.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.clock.install(time=instant("2026-11-01T06:59:55"))
    page.goto(path.as_uri())
    count = page.evaluate("quietFrameGallery.length")
    assert 30 <= count <= 40
    assert page.evaluate("""new Set(quietFrameGallery.map(work => work.objectId)).size""") == count
    assert page.evaluate("""quietFrameGallery.every(work => work.rights === 'CC0' &&
        work.museum && work.artist && work.title && work.objectUrl && work.rightsEvidence)""")
    expect(page.locator(".artwork")).to_have_css("object-fit", "contain")
    expected = lambda date: int(instant(date).timestamp() // 86400) % count
    before = expected("2026-10-31T00:00:00")
    wait_for_work(page, before)
    page.reload()
    wait_for_work(page, before)

    page.clock.pause_at(instant("2026-11-01T06:59:59.900"))
    page.clock.run_for(100)
    after = (before + 1) % count
    wait_for_work(page, after)
    expect(page.locator(".calendar")).to_have_text("Sunday, November 1, 2026")

    # At the fall clock change, 1:59 AM becomes 1:00 AM on the same civil date.
    page.clock.set_system_time(instant("2026-11-01T08:59:59.900"))
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator(".clock")).to_have_text("1:59 AM")
    page.clock.run_for(100)
    expect(page.locator(".clock")).to_have_text("1:00 AM")
    assert selected(page) == after

    # Returning after sleep should catch up to the current local calendar day.
    page.evaluate("""Object.defineProperty(document, 'hidden', {value: true, configurable: true});
      document.dispatchEvent(new Event('visibilitychange'));""")
    page.clock.set_system_time(instant("2026-11-03T09:20:00"))
    assert selected(page) == after
    page.evaluate("""Object.defineProperty(document, 'hidden', {value: false, configurable: true});
      document.dispatchEvent(new Event('visibilitychange'));""")
    resumed = (after + 2) % count
    wait_for_work(page, resumed)
    page.reload()
    wait_for_work(page, resumed)

    page.clock.set_system_time(instant("2026-03-08T09:59:59.900"))
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    spring = expected("2026-03-08T00:00:00")
    wait_for_work(page, spring)
    expect(page.locator(".clock")).to_have_text("1:59 AM")
    page.clock.run_for(100)
    expect(page.locator(".clock")).to_have_text("3:00 AM")
    assert selected(page) == spring

    # Force a corrupt file on the next date using a local malformed image.
    bad = (spring + 1) % count
    page.evaluate("i => quietFrameGallery[i].src = 'data:image/jpeg;base64,AAAA'", bad)
    page.clock.set_system_time(instant("2026-03-09T08:00:00"))
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator(".artwork")).to_have_attribute("alt", "Oil painting of a quiet coastal inlet at dusk, with dark firs and warm light on the horizon")
    assert page.locator(".artwork").evaluate("(img) => img.complete && img.naturalWidth > 0")

    # The target file runs without remote requests. The browser also retains the shortcut UI.
    assert not any(url.startswith(("http:", "https:")) for url in requests)
    prime = page.get_by_role("button", name="Open Prime Video")
    expect(prime).to_be_focused()
    page.keyboard.press("ArrowRight")
    expect(page.get_by_role("button", name="Open YouTube")).to_be_focused()
    page.get_by_role("button",name="Open Jellyfin").click()
    expect(page.get_by_role("status")).to_have_text("TV preview. Open Jellyfin on your Samsung TV.")
    assert errors == [], errors
    print(f"PASS {count} works, local midnight, restart, both DST transitions, resume, decode fallback and shortcuts")