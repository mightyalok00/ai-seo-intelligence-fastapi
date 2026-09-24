import os
import time
import urllib.request

import pytest


BASE_URL = os.getenv("E2E_BASE_URL")
pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="Set E2E_BASE_URL to run browser tests against a live application.",
)


def wait_for_server():
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    pytest.fail("The application did not become ready for the browser test.")


def test_dashboard_audit_theme_and_export():
    playwright = pytest.importorskip("playwright.sync_api")
    wait_for_server()

    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch()
        page = browser.new_page(accept_downloads=True)
        page.goto(BASE_URL)

        assert page.get_by_role("heading", name="A harder, more honest SEO score.").is_visible()
        page.get_by_role("button", name="Switch to dark theme").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"

        page.get_by_role("button", name="Run strict SEO audit").click()
        page.locator("#dashboard").wait_for(state="visible")
        assert page.locator("#score-chart .chart-row").count() == 16
        assert page.locator("#overall-score").inner_text().isdigit()

        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download JSON").click()
        assert download_info.value.suggested_filename.endswith("-audit.json")
        browser.close()
