from pathlib import Path
from types import SimpleNamespace

import streamlit

import app
from src.ui import sidebar_behavior
from src.ui.sidebar_behavior import (
    MOBILE_BREAKPOINT_PX,
    MOBILE_COLLAPSE_MAX_ATTEMPTS,
    MOBILE_COLLAPSE_REQUEST_KEY,
    MOBILE_COLLAPSE_RETRY_DELAY_MS,
    MOBILE_COLLAPSE_SEQUENCE_KEY,
    SIDEBAR_BEHAVIOR_STYLES,
    build_mobile_sidebar_collapse_component,
    consume_mobile_sidebar_collapse_request,
    request_mobile_sidebar_collapse,
)


def test_mobile_sidebar_collapse_request_ids_are_monotonic_and_consumed_once() -> None:
    session_state: dict[str, object] = {}

    first_request_id = request_mobile_sidebar_collapse(session_state)

    assert first_request_id == 1
    assert session_state[MOBILE_COLLAPSE_SEQUENCE_KEY] == 1
    assert session_state[MOBILE_COLLAPSE_REQUEST_KEY] == 1
    assert consume_mobile_sidebar_collapse_request(session_state) == 1
    assert consume_mobile_sidebar_collapse_request(session_state) is None

    second_request_id = request_mobile_sidebar_collapse(session_state)

    assert second_request_id == 2
    assert session_state[MOBILE_COLLAPSE_SEQUENCE_KEY] == 2
    assert consume_mobile_sidebar_collapse_request(session_state) == 2


def test_repeated_mobile_sidebar_collapse_renders_unique_component_payloads(monkeypatch) -> None:
    session_state: dict[str, object] = {}
    rendered_components: list[tuple[str, int]] = []
    monkeypatch.setattr(
        sidebar_behavior.components,
        "html",
        lambda html, height: rendered_components.append((html, height)),
    )

    request_mobile_sidebar_collapse(session_state)
    sidebar_behavior.render_requested_mobile_sidebar_collapse(session_state)
    request_mobile_sidebar_collapse(session_state)
    sidebar_behavior.render_requested_mobile_sidebar_collapse(session_state)

    assert len(rendered_components) == 2
    assert rendered_components[0] != rendered_components[1]
    assert "mobile-sidebar-collapse-request:1" in rendered_components[0][0]
    assert "mobile-sidebar-collapse-request:2" in rendered_components[1][0]
    assert [height for _, height in rendered_components] == [0, 0]


def test_select_page_updates_navigation_and_requests_mobile_collapse(monkeypatch) -> None:
    fake_streamlit = SimpleNamespace(session_state={})
    collapse_requests: list[bool] = []
    monkeypatch.setattr(app, "st", fake_streamlit)
    monkeypatch.setattr(
        app,
        "request_mobile_sidebar_collapse",
        lambda: collapse_requests.append(True),
    )

    app._select_page("분석 실행", "Project Chat")

    assert fake_streamlit.session_state[app.NAV_STATE_KEY] == {
        "group": "분석 실행",
        "page": "Project Chat",
    }
    assert collapse_requests == [True]


def test_project_settings_navigation_excludes_sample_data_generator() -> None:
    assert tuple(app.PAGE_GROUPS["프로젝트 설정"]) == ("프로젝트/Git 설정", "Git 동기화")


def test_sidebar_behavior_targets_streamlit_mobile_overlay_and_open_sidebar() -> None:
    component = build_mobile_sidebar_collapse_component(1)

    assert MOBILE_BREAKPOINT_PX == 768
    assert f"max-width: {MOBILE_BREAKPOINT_PX}px" in component
    assert 'getAttribute("aria-expanded")' in component
    assert 'data-testid="stSidebarCollapseButton"' in component


def test_mobile_sidebar_collapse_retries_until_streamlit_dom_is_ready() -> None:
    component = build_mobile_sidebar_collapse_component(7)

    assert MOBILE_COLLAPSE_MAX_ATTEMPTS == 20
    assert MOBILE_COLLAPSE_RETRY_DELAY_MS == 50
    assert f"failedAttempts < {MOBILE_COLLAPSE_MAX_ATTEMPTS}" in component
    assert f"setTimeout(tryCollapseSidebar, {MOBILE_COLLAPSE_RETRY_DELAY_MS})" in component
    assert "mobile-sidebar-collapse-request:7" in component


def test_sidebar_header_is_sticky() -> None:
    assert 'data-testid="stSidebarContent"' in SIDEBAR_BEHAVIOR_STYLES
    assert 'data-testid="stSidebarHeader"' in SIDEBAR_BEHAVIOR_STYLES
    assert SIDEBAR_BEHAVIOR_STYLES.count("background-color: inherit") == 2
    assert "#ffffff" not in SIDEBAR_BEHAVIOR_STYLES
    assert "min-height: 2.75rem" in SIDEBAR_BEHAVIOR_STYLES
    assert "padding: 0.375rem 0.75rem" in SIDEBAR_BEHAVIOR_STYLES
    assert "position: sticky" in SIDEBAR_BEHAVIOR_STYLES
    assert "top: 0" in SIDEBAR_BEHAVIOR_STYLES


def test_touch_sidebar_keeps_streamlit_collapse_button_visible() -> None:
    assert "@media (hover: none), (pointer: coarse)" in SIDEBAR_BEHAVIOR_STYLES
    assert 'data-testid="stSidebarCollapseButton"' in SIDEBAR_BEHAVIOR_STYLES
    assert "display: block !important" in SIDEBAR_BEHAVIOR_STYLES


def test_pinned_streamlit_bundle_still_exposes_sidebar_behavior_targets() -> None:
    static_root = Path(streamlit.__file__).parent / "static" / "static" / "js"
    bundle_text = "".join(path.read_text(encoding="utf-8") for path in static_root.glob("*.js"))

    assert "stSidebarHeader" in bundle_text
    assert "stSidebarCollapseButton" in bundle_text
