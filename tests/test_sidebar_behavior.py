from pathlib import Path
from types import SimpleNamespace

import streamlit

import app
from src.ui.sidebar_behavior import (
    MOBILE_BREAKPOINT_PX,
    MOBILE_COLLAPSE_COMPONENT,
    MOBILE_COLLAPSE_REQUEST_KEY,
    SIDEBAR_BEHAVIOR_STYLES,
    consume_mobile_sidebar_collapse_request,
    request_mobile_sidebar_collapse,
)


def test_mobile_sidebar_collapse_request_is_consumed_once() -> None:
    session_state: dict[str, object] = {}

    request_mobile_sidebar_collapse(session_state)

    assert session_state[MOBILE_COLLAPSE_REQUEST_KEY] is True
    assert consume_mobile_sidebar_collapse_request(session_state) is True
    assert consume_mobile_sidebar_collapse_request(session_state) is False


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


def test_sidebar_behavior_targets_streamlit_mobile_overlay_and_open_sidebar() -> None:
    assert MOBILE_BREAKPOINT_PX == 768
    assert f"max-width: {MOBILE_BREAKPOINT_PX}px" in MOBILE_COLLAPSE_COMPONENT
    assert 'getAttribute("aria-expanded") !== "true"' in MOBILE_COLLAPSE_COMPONENT
    assert 'data-testid="stSidebarCollapseButton"' in MOBILE_COLLAPSE_COMPONENT


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
