"""Public browser check for the standalone patent database page."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("ARCTIC_TEST_URL", "http://127.0.0.1:8501")
OUT = ROOT / "test-results" / "patent"
OUT.mkdir(parents=True, exist_ok=True)
errors, checks = [], []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--use-angle=swiftshader"])
    context = browser.new_context(viewport={"width": 1600, "height": 1100}, accept_downloads=True)
    page = context.new_page(); page.set_default_timeout(90000); page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE.rstrip("/") + "/patents", wait_until="domcontentloaded")
    app = page
    if "streamlit.app" in BASE:
        page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000)
        app = page.frame_locator('iframe[title="streamlitApp"]')
    app.locator('.stApp[data-test-script-state="notRunning"]').wait_for(timeout=90000)
    assert not app.locator('[data-testid="stException"]').count(), app.locator("body").inner_text()[:5000]
    page.wait_for_timeout(7000)
    app.get_by_text("北极技术专利与公开文本", exact=True).wait_for()
    assert app.get_by_text("统计日期口径", exact=True).count() >= 1
    app.locator('[data-testid="stMetricLabel"]').first.wait_for(timeout=30000)
    assert app.get_by_text("匹配公开文本", exact=True).count() >= 1
    for _ in range(60):
        if app.locator('.js-plotly-plot').count() >= 1:
            break
        page.wait_for_timeout(500)
    assert app.locator('.js-plotly-plot').count() >= 1
    assert app.locator('.js-plotly-plot').first.locator('.bars').count() >= 1
    app.get_by_role("tab", name="专利态势分析", exact=True).click()
    app.locator('.js-plotly-plot').nth(1).wait_for(timeout=30000)
    assert app.locator('.js-plotly-plot').count() >= 5
    app.get_by_role("tab", name="专利检索工作台", exact=True).click()
    app.get_by_text("检索工作台", exact=True).wait_for()
    assert app.get_by_text("首项权利要求", exact=False).count() >= 1
    assert app.get_by_role("link", name="打开聚合公开页", exact=True).count() == 1
    checks.append("Patent page loads on the public site with trend, two heatmaps, searchable records and source text")
    page.screenshot(path=str(OUT / "public-patent.png"), full_page=True)
    browser.close()

report = {"url": BASE, "checks": checks, "page_errors": errors}
(OUT / "browser-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
assert not errors
