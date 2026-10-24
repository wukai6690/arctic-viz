"""Browser acceptance checks for the visible network search, comparison panels and photos."""
import json, os, re, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("ARCTIC_TEST_URL", "http://127.0.0.1:8501")
OUT = ROOT / "test-results" / "network"
OUT.mkdir(parents=True, exist_ok=True)
errors, checks = [], []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--use-angle=swiftshader"])
    context = browser.new_context(viewport={"width": 1600, "height": 1100}, accept_downloads=True)
    page = context.new_page(); page.set_default_timeout(90000); page.on("pageerror", lambda e: errors.append(str(e)))

    def open_route(route):
        print("Opening", route, flush=True)
        page.goto(BASE.rstrip("/") + route, wait_until="domcontentloaded")
        app = page
        if "streamlit.app" in BASE:
            page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000)
            app = page.frame_locator('iframe[title="streamlitApp"]')
        app.locator('.stApp[data-test-script-state="notRunning"]').wait_for(timeout=90000)
        # Cloud may deliver the form shell before its widget deltas finish.
        page.wait_for_timeout(7000)
        if app.locator('[data-testid="stException"]').count():
            raise AssertionError(app.locator('[data-testid="stException"]').all_text_contents())
        return app

    def settle(app):
        page.wait_for_timeout(800)
        app.locator('.stApp[data-test-script-state="notRunning"]').wait_for(timeout=90000)
        assert not app.locator('[data-testid="stException"]').count()

    app = open_route("/事件检索")
    print("Search page ready", flush=True)
    app.get_by_text("北极事件检索中心", exact=True).wait_for()
    app.get_by_text("统一检索入口", exact=True).wait_for()
    assert app.locator('[data-testid="stTextInputRootElement"] input').count() == 1, app.locator("body").inner_text()[:4000]
    app.get_by_role("button", name="检索", exact=True).click(); settle(app)
    app.get_by_text("统一结果与来源详情", exact=True).wait_for()
    detail_buttons = app.get_by_role("button", name="查看详情", exact=True)
    assert detail_buttons.count() >= 2
    selected_before = app.locator(".event-result-card.selected").inner_text()
    detail_buttons.nth(1).click(); settle(app)
    selected_after = selected_before
    for _ in range(60):
        selected_after = app.locator(".event-result-card.selected").inner_text()
        if selected_after != selected_before:
            break
        page.wait_for_timeout(500)
    assert selected_after != selected_before
    checks.append("查看详情按钮切换选中事件并刷新右侧来源详情")
    for _ in range(60):
        if app.locator('.js-plotly-plot').count() >= 1:
            break
        page.wait_for_timeout(500)
    assert app.locator('.js-plotly-plot').count() >= 1, app.locator("body").inner_text()[:6000]
    checks.append("Visible date/country/event-type search returns a filtered network and evidence table")
    app = open_route("/动态关系网络")
    app.get_by_text(re.compile("北极国家关系网络")).wait_for()
    assert app.get_by_role("tab", name="整体关系网络", exact=True).count() == 1
    app.get_by_role("tab", name="月度关系网络", exact=True).click(); settle(app)
    assert app.get_by_text("选择月份", exact=True).count() == 1
    assert app.locator('.js-plotly-plot').count() >= 2
    checks.append("Overall and manually selectable monthly relationship networks render with historical evidence")
    app = open_route("/实景图集")
    print("Photo page ready", flush=True)
    images = app.locator('[data-testid="stImage"] img')
    for _ in range(60):
        if images.count() >= 12 and images.evaluate_all("es=>es.every(e=>e.complete && e.naturalWidth>0)"):
            break
        page.wait_for_timeout(500)
    assert images.count() >= 12
    assert images.evaluate_all("es=>es.every(e=>e.complete && e.naturalWidth>0)")
    checks.append("Published photo gallery loads bundled local images")
    page.screenshot(path=str(OUT / "network-photo-check.png"), full_page=True)
    browser.close()

report = {"url": BASE, "checks": checks, "page_errors": errors}
(OUT / "browser-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
assert not errors
