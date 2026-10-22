"""Browser regression check and screenshots: python tests/ui_smoke.py.

Requires Playwright and a dashboard running at http://127.0.0.1:8502.
"""
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

expect.set_options(timeout=30000)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".impeccable" / "review"
OUTPUT.mkdir(parents=True, exist_ok=True)


def settle(page):
    page.wait_for_timeout(800)
    expect(page.get_by_test_id("stException")).to_have_count(0)


def fill(page, label, value):
    control = page.get_by_role("textbox", name=label, exact=True)
    control.fill(value)
    control.press("Enter")
    settle(page)


def select(page, index, value):
    page.get_by_role("combobox").nth(index).click()
    page.get_by_role("option", name=value, exact=True).click()
    settle(page)


def capture(page, name, width, height):
    page.set_viewport_size({"width": width, "height": height})
    settle(page)
    page.get_by_test_id("stMain").evaluate("el => el.scrollTop = 0")
    # Streamlit scrolls its main region rather than the document. Expand the
    # capture height to include that region without changing the tested width.
    content_height = page.get_by_test_id("stMain").evaluate("el => el.scrollHeight")
    if content_height > height:
        page.set_viewport_size({"width": width, "height": content_height + 16})
        settle(page)
    page.screenshot(path=str(OUTPUT / name), full_page=True)
    overflow = page.evaluate("""() => {
        const main = document.querySelector('[data-testid="stMain"]');
        return {width: innerWidth, document: document.documentElement.scrollWidth,
                main: main.scrollWidth, client: main.clientWidth};
    }""")
    assert overflow["document"] <= width, overflow
    assert overflow["main"] <= overflow["client"], overflow
    return overflow


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
    page.set_default_timeout(30000)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8502", wait_until="domcontentloaded")
    expect(page.locator(".pave-empty")).to_be_visible()
    capture(page, "empty-state.png", 1440, 1080)
    page.locator('input[type="file"]').set_input_files(str(ROOT / "assets" / "sample_traffic.csv"))
    expect(page.get_by_text("Please complete all engineering input parameters before analysis.", exact=True)).to_be_visible()
    select(page, 0, "Flexible")
    select(page, 1, "3")
    fill(page, "Annual Growth Rate (%)", "10")
    fill(page, "Design Life (Years)", "5")
    fill(page, "Project Location", "Dips")
    expect(page.get_by_text("Traffic File Processed Successfully", exact=True)).to_be_visible()
    expect(page.locator(".pave-location")).to_have_text("Location: Dips")
    page.get_by_role("heading", name="PAVEtrack Intelligent Pavement Monitoring Dashboard", exact=True).click()
    page.mouse.move(0, 0)
    for value in ("10,468.16", "36.67", "81,722.48"):
        expect(page.get_by_text(value, exact=True)).to_be_visible()
    expect(page.locator(".pave-thickness")).to_contain_text("150")
    expect(page.locator(".pave-chart")).to_be_visible()

    reports = {"desktop": capture(page, "desktop.png", 1440, 1080),
               "user": capture(page, "user-1920.png", 1920, 1080),
               "mobile": capture(page, "mobile.png", 390, 844),
               "tablet": capture(page, "tablet.png", 768, 1024),
               "small_desktop": capture(page, "small-desktop.png", 1024, 900)}
    boundaries = page.locator('[data-testid="stTextInputRootElement"], .react-aria-ComboBox > [role="group"]').evaluate_all('''els => els.map(el => ({
        style:getComputedStyle(el).borderStyle, width:getComputedStyle(el).borderWidth,
        color:getComputedStyle(el).borderColor, background:getComputedStyle(el).backgroundColor
    }))''')
    assert len(boundaries) == 5 and all(item["width"] == "1px" and item["style"] == "solid" for item in boundaries), boundaries
    reports["field_boundaries"] = boundaries
    gap = page.evaluate('''() => document.querySelector('.pave-recommendation').getBoundingClientRect().top
        - document.querySelector('.pave-metrics').getBoundingClientRect().bottom''')
    assert gap >= 12, gap
    reports["result_panel_gap"] = gap
    page.set_viewport_size({"width": 1440, "height": 1080})
    page.get_by_role("tab", name="Uploaded Traffic Data", exact=True).click()
    expect(page.get_by_test_id("stDataFrame")).to_be_visible()
    capture(page, "traffic-data.png", 1440, 1080)
    with page.expect_download() as download:
        page.get_by_role("button", name="Download processed CSV").click()
    downloaded = download.value
    assert downloaded.suggested_filename == "pavetrack_traffic_analysis.csv"
    csv_text = Path(downloaded.path()).read_text()
    assert "TOTAL COUNT,TOTAL ESAL" in csv_text and "Motorcycles" in csv_text

    page.get_by_role("tab", name="Calculation details", exact=True).click()
    expect(page.get_by_text("Calculated thickness", exact=True)).to_be_visible()
    expect(page.get_by_text("128.5 mm", exact=True)).to_be_visible()
    select(page, 0, "Rigid")
    expect(page.locator(".pave-thickness")).to_contain_text("200")
    select(page, 0, "Flexible")
    fill(page, "Annual Growth Rate (%)", "0")
    expect(page.get_by_text("Annual Growth Rate must be greater than 0% for this model.")).to_be_visible()
    fill(page, "Annual Growth Rate (%)", "10")
    fill(page, "Design Life (Years)", "abc")
    expect(page.get_by_text("Enter a numeric annual growth rate and a whole number of design years.")).to_be_visible()
    fill(page, "Design Life (Years)", "5")
    fill(page, "Project Location", '<img src=x onerror="alert(1)"> A long project location for responsive layout verification')
    assert page.locator(".pave-location img").count() == 0
    expect(page.get_by_text("Traffic File Processed Successfully", exact=True)).to_be_visible()
    fill(page, "Project Location", "Dips")
    page.locator('input[type="file"]').set_input_files({
        "name": "missing_columns.csv", "mimeType": "text/csv",
        "buffer": b"VEHICLE CLASS,DAY1\nCars,5\n",
    })
    expect(page.get_by_text("Your CSV is missing a required column.", exact=False)).to_be_visible()
    page.locator('input[type="file"]').set_input_files(str(ROOT / "assets" / "sample_traffic.csv"))
    expect(page.get_by_text("Traffic File Processed Successfully", exact=True)).to_be_visible()
    assert not errors, errors
    reports["checks"] = ["empty and incomplete states", "CSV upload", "baseline calculation outputs",
                         "responsive overflow", "data table", "CSV download", "calculation details",
                         "rigid/flexible switching", "invalid input recovery", "HTML escaping", "malformed CSV recovery"]
    (OUTPUT / "browser-report.json").write_text(json.dumps(reports, indent=2))
    print(json.dumps(reports, indent=2))
    browser.close()
