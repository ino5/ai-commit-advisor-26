from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Error, Page, sync_playwright


@dataclass(frozen=True)
class FeatureScenario:
    name: str
    sidebar_label: str | None
    wait_text: str
    required_texts: tuple[str, ...]
    forbidden_texts: tuple[str, ...] = field(default_factory=tuple)
    default_screenshot: str = ""
    description: str = ""
    verify_sidebar_stability: bool = False
    scroll_to_text: str | None = None
    full_page: bool = True


SCENARIOS: dict[str, FeatureScenario] = {
    "home": FeatureScenario(
        name="home",
        sidebar_label="Home",
        wait_text="분석 상태",
        required_texts=(
            "AI Commit Advisor",
            "계획, 커밋, 진척도, 리스크 현황",
            "Dashboard",
            "AI Progress",
            "프로젝트/Git 설정",
            "분석 상태",
            "다음 작업",
            "추정 진척도",
        ),
        forbidden_texts=(
            "분석 파이프라인 상태",
            "업무 의미",
            "AI 분석 결과는 근거 데이터와 함께 검증하는 보조 지표로 활용하세요.",
        ),
        default_screenshot="docs/images/features/home.png",
        description="Home 분석 관제 화면",
        verify_sidebar_stability=True,
    ),
    "project-chat": FeatureScenario(
        name="project-chat",
        sidebar_label="Project Chat",
        wait_text="현재 소스 파일에서 검증된 RAG 근거로 프로젝트 질문에 답합니다.",
        required_texts=(
            "Project Chat",
            "현재 소스 파일에서 검증된 RAG 근거로 프로젝트 질문에 답합니다.",
        ),
        forbidden_texts=(),
        default_screenshot="docs/images/features/project-chat.png",
        description="Project Chat 질문/근거 화면",
    ),
    "git-history": FeatureScenario(
        name="git-history",
        sidebar_label="Git History",
        wait_text="현재 프로젝트의 Git 커밋 이력",
        required_texts=(
            "Git History",
            "현재 프로젝트의 Git 커밋 이력",
            "커밋 목록",
            "조회 커밋",
            "변경 파일",
            "전체 diff",
        ),
        forbidden_texts=(),
        default_screenshot="docs/images/features/git-history.png",
        description="Git History 커밋 이력/diff 탐색 화면",
    ),
    "git-history-detail": FeatureScenario(
        name="git-history-detail",
        sidebar_label="Git History",
        wait_text="현재 프로젝트의 Git 커밋 이력",
        required_texts=(
            "Git History",
            "커밋 상세",
            "변경 파일",
            "저장된 diff preview",
            "전체 diff",
        ),
        forbidden_texts=(),
        default_screenshot="docs/images/features/git-history-detail.png",
        description="Git History 커밋 상세/diff preview 화면",
        scroll_to_text="저장된 diff preview",
        full_page=False,
    ),
}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture verified feature screenshots from a running Streamlit app."
    )
    parser.add_argument("--url", default="http://localhost:8501", help="Streamlit app URL.")
    parser.add_argument(
        "--feature",
        choices=tuple(SCENARIOS.keys()) + ("all",),
        default="home",
        help="Feature scenario to capture.",
    )
    parser.add_argument(
        "--screenshot",
        help="Screenshot output path. Only valid when capturing a single feature.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory used when --screenshot is not set. Defaults to each scenario path.",
    )
    parser.add_argument(
        "--expect-text",
        action="append",
        default=[],
        help="Additional text that must be visible before the screenshot is saved.",
    )
    parser.add_argument(
        "--forbid-text",
        action="append",
        default=[],
        help="Additional text that must not be visible before the screenshot is saved.",
    )
    parser.add_argument(
        "--surface",
        default="local",
        choices=("local", "docker", "other"),
        help="Runtime surface used for this capture. Printed in the result for traceability.",
    )
    parser.add_argument("--width", type=int, default=1440, help="Browser viewport width.")
    parser.add_argument("--height", type=int, default=1000, help="Browser viewport height.")
    return parser.parse_args(argv)


def _open_app(page: Page, url: str) -> None:
    page.goto(url, wait_until="networkidle", timeout=30_000)


def _navigate_to_sidebar_item(page: Page, label: str) -> None:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    item = sidebar.get_by_text(label, exact=True).last
    item.wait_for(timeout=15_000)
    item.click()


def _page_text(page: Page, wait_text: str) -> str:
    page.get_by_text(wait_text).first.wait_for(timeout=20_000)
    return page.locator("body").inner_text(timeout=10_000)


def _wait_for_texts(page: Page, texts: tuple[str, ...]) -> None:
    for text in texts:
        page.get_by_text(text).first.wait_for(timeout=20_000)


def _assert_texts(
    text: str,
    required_texts: tuple[str, ...],
    forbidden_texts: tuple[str, ...],
) -> None:
    missing = [value for value in required_texts if value not in text]
    if missing:
        raise AssertionError(f"Missing expected text: {', '.join(missing)}")

    stale = [value for value in forbidden_texts if value in text]
    if stale:
        raise AssertionError(f"Forbidden text is visible: {', '.join(stale)}")


def _sidebar_item_box(page: Page, label: str) -> dict[str, float]:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    locator = sidebar.get_by_text(label, exact=True).last
    box = locator.bounding_box(timeout=10_000)
    if box is None:
        raise AssertionError(f"Sidebar item has no bounding box: {label}")
    return box


def _sidebar_item_metrics(page: Page, labels: tuple[str, ...]) -> dict[str, dict[str, float]]:
    metrics = page.evaluate(
        """
        (labels) => {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar) {
                throw new Error("Sidebar not found");
            }
            const activeMarkupCount = sidebar.querySelectorAll('.nav-active').length;
            if (activeMarkupCount > 0) {
                throw new Error(`Unexpected custom active sidebar markup: ${activeMarkupCount}`);
            }
            const buttons = Array.from(sidebar.querySelectorAll('.stButton > button'));
            const result = {};
            for (const label of labels) {
                const button = buttons.find((item) => (item.innerText || item.textContent || '').trim() === label);
                if (!button) {
                    throw new Error(`Sidebar button not found: ${label}`);
                }
                const box = button.getBoundingClientRect();
                const text = button.querySelector('p') || button;
                const textBox = text.getBoundingClientRect();
                result[label] = {
                    x: box.x,
                    y: box.y,
                    width: box.width,
                    height: box.height,
                    textRelX: textBox.x - box.x,
                    textRelY: textBox.y - box.y,
                    textHeight: textBox.height,
                };
            }
            return result;
        }
        """,
        list(labels),
    )
    return metrics


def _assert_metric_delta(
    before: dict[str, dict[str, float]],
    after: dict[str, dict[str, float]],
    labels: tuple[str, ...],
    fields: tuple[str, ...],
    max_delta: float,
) -> None:
    unstable: dict[str, dict[str, float]] = {}
    for label in labels:
        deltas = {
            field: abs(after[label][field] - before[label][field])
            for field in fields
            if abs(after[label][field] - before[label][field]) > max_delta
        }
        if deltas:
            unstable[label] = deltas

    if unstable:
        raise AssertionError(f"Sidebar item metrics changed after navigation: {unstable}")


def _sidebar_spacing(metrics: dict[str, dict[str, float]], first: str, second: str) -> float:
    first_box = metrics[first]
    second_box = metrics[second]
    return second_box["y"] - (first_box["y"] + first_box["height"])


def _verify_sidebar_layout_stability(page: Page) -> None:
    top_labels = ("Home", "Dashboard", "AI Progress")
    before_top = _sidebar_item_metrics(page, top_labels)
    before_dashboard_spacing = _sidebar_spacing(before_top, "Dashboard", "AI Progress")

    _navigate_to_sidebar_item(page, "Dashboard")
    page.get_by_text("프로젝트 계획, AI 분석, Git 활동을 한 화면에서 확인합니다.").wait_for(timeout=15_000)
    after_dashboard = _sidebar_item_metrics(page, top_labels)

    _assert_metric_delta(
        before_top,
        after_dashboard,
        top_labels,
        ("x", "y", "width", "height", "textRelX", "textRelY", "textHeight"),
        max_delta=1.0,
    )

    after_dashboard_spacing = _sidebar_spacing(after_dashboard, "Dashboard", "AI Progress")
    if abs(after_dashboard_spacing - before_dashboard_spacing) > 1.0:
        raise AssertionError(
            "Sidebar adjacent item spacing changed after active item navigation: "
            f"{before_dashboard_spacing} -> {after_dashboard_spacing}"
        )

    before_mapping = _sidebar_item_box(page, "Mapping")
    _navigate_to_sidebar_item(page, "프로젝트/Git 설정")
    page.get_by_text("프로젝트 저장").wait_for(timeout=15_000)
    after_mapping = _sidebar_item_box(page, "Mapping")

    max_delta = 1.0
    deltas = {
        "x": abs(after_mapping["x"] - before_mapping["x"]),
        "y": abs(after_mapping["y"] - before_mapping["y"]),
        "width": abs(after_mapping["width"] - before_mapping["width"]),
    }
    unstable = {name: delta for name, delta in deltas.items() if delta > max_delta}
    if unstable:
        raise AssertionError(f"Sidebar menu moved after navigation: {unstable}")


def _default_output_path(scenario: FeatureScenario, output_dir: str | None) -> Path:
    if scenario.default_screenshot:
        return Path(scenario.default_screenshot)
    return Path(output_dir or "docs/images/features") / f"{scenario.name}.png"


def _capture_scenario(
    page: Page,
    url: str,
    scenario: FeatureScenario,
    screenshot_path: Path,
    extra_required_texts: tuple[str, ...],
    extra_forbidden_texts: tuple[str, ...],
) -> str:
    _open_app(page, url)
    if scenario.sidebar_label:
        _navigate_to_sidebar_item(page, scenario.sidebar_label)

    _wait_for_texts(page, scenario.required_texts + extra_required_texts)
    text = _page_text(page, scenario.wait_text)
    _assert_texts(
        text,
        scenario.required_texts + extra_required_texts,
        scenario.forbidden_texts + extra_forbidden_texts,
    )

    if scenario.verify_sidebar_stability:
        _verify_sidebar_layout_stability(page)
        _navigate_to_sidebar_item(page, scenario.sidebar_label or "Home")
        _wait_for_texts(page, scenario.required_texts + extra_required_texts)
        text = _page_text(page, scenario.wait_text)
        _assert_texts(
            text,
            scenario.required_texts + extra_required_texts,
            scenario.forbidden_texts + extra_forbidden_texts,
        )

    if scenario.scroll_to_text:
        page.get_by_text(scenario.scroll_to_text).first.scroll_into_view_if_needed(timeout=10_000)

    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=scenario.full_page)
    return text


def _selected_scenarios(feature: str) -> list[FeatureScenario]:
    if feature == "all":
        return list(SCENARIOS.values())
    return [SCENARIOS[feature]]


def _screenshot_path(
    args: argparse.Namespace,
    scenario: FeatureScenario,
    scenario_count: int,
) -> Path:
    if args.screenshot:
        if scenario_count > 1:
            raise SystemExit("--screenshot can only be used with a single --feature value.")
        return Path(args.screenshot)
    if args.output_dir:
        return Path(args.output_dir) / f"{scenario.name}.png"
    return _default_output_path(scenario, args.output_dir)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    scenarios = _selected_scenarios(args.feature)
    extra_required_texts = tuple(args.expect_text)
    extra_forbidden_texts = tuple(args.forbid_text)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": args.width, "height": args.height})
            for scenario in scenarios:
                path = _screenshot_path(args, scenario, len(scenarios))
                text = _capture_scenario(
                    page,
                    args.url,
                    scenario,
                    path,
                    extra_required_texts,
                    extra_forbidden_texts,
                )
                preview = "\n".join(line for line in text.splitlines() if line.strip())[:1000]
                print(
                    f"{scenario.name} screenshot captured on {args.surface}: {path}\n"
                    f"{preview}\n"
                )
            browser.close()
    except Error as exc:
        raise SystemExit(
            "Playwright browser 실행에 실패했습니다. "
            "필요하면 `.venv\\Scripts\\python.exe -m playwright install chromium`을 실행하세요.\n"
            f"{exc}"
        ) from exc


if __name__ == "__main__":
    main()
