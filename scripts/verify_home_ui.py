from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import Error, Page, sync_playwright


EXPECTED_TEXT = [
    "AI Commit Advisor",
    "계획, 커밋, 진척도, 리스크 현황",
    "분석 상태",
    "다음 작업",
    "추정 진척도",
]

REMOVED_TEXT = [
    "분석 파이프라인 상태",
    "업무 의미",
    "AI 분석 결과는 근거 데이터와 함께 검증하는 보조 지표로 활용하세요.",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the Home page renders with compact copy.")
    parser.add_argument("--url", default="http://localhost:8501", help="Streamlit app URL.")
    parser.add_argument(
        "--screenshot",
        default=".tmp/home-ui-check.png",
        help="Screenshot output path.",
    )
    return parser.parse_args()


def _page_text(page: Page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=30_000)
    page.get_by_text("분석 상태").first.wait_for(timeout=15_000)
    return page.locator("body").inner_text(timeout=10_000)


def _verify_text(text: str) -> None:
    missing = [value for value in EXPECTED_TEXT if value not in text]
    if missing:
        raise AssertionError(f"Missing expected Home text: {', '.join(missing)}")

    stale = [value for value in REMOVED_TEXT if value in text]
    if stale:
        raise AssertionError(f"Stale explanatory text still visible: {', '.join(stale)}")


def _sidebar_item_box(page: Page, label: str) -> dict[str, float]:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    locator = sidebar.get_by_text(label, exact=True).last
    box = locator.bounding_box(timeout=10_000)
    if box is None:
        raise AssertionError(f"Sidebar item has no bounding box: {label}")
    return box


def _verify_sidebar_layout_stability(page: Page) -> None:
    before = _sidebar_item_box(page, "Mapping")
    page.locator('section[data-testid="stSidebar"]').get_by_text("프로젝트", exact=True).last.click()
    page.get_by_text("프로젝트 저장").wait_for(timeout=15_000)
    after = _sidebar_item_box(page, "Mapping")

    max_delta = 1.0
    deltas = {
        "x": abs(after["x"] - before["x"]),
        "y": abs(after["y"] - before["y"]),
        "width": abs(after["width"] - before["width"]),
    }
    unstable = {name: delta for name, delta in deltas.items() if delta > max_delta}
    if unstable:
        raise AssertionError(f"Sidebar menu moved after navigation: {unstable}")


def _return_home(page: Page) -> None:
    page.locator('section[data-testid="stSidebar"]').get_by_text("Home", exact=True).last.click()
    page.get_by_text("분석 상태").first.wait_for(timeout=15_000)


def main() -> None:
    screenshot_path = Path(args.screenshot)
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            text = _page_text(page, args.url)
            _verify_text(text)
            _verify_sidebar_layout_stability(page)
            _return_home(page)
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
    except Error as exc:
        raise SystemExit(
            "Playwright browser 실행에 실패했습니다. "
            "필요하면 `.venv\\Scripts\\python.exe -m playwright install chromium`을 실행하세요.\n"
            f"{exc}"
        ) from exc

    preview = "\n".join(line for line in text.splitlines() if line.strip())[:1200]
    print(f"Home UI verification passed. Screenshot: {screenshot_path}")
    print(preview)


if __name__ == "__main__":
    args = _parse_args()
    main()
