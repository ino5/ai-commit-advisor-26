from collections.abc import MutableMapping

import streamlit as st
import streamlit.components.v1 as components


MOBILE_BREAKPOINT_PX = 768
MOBILE_COLLAPSE_REQUEST_KEY = "_mobile_sidebar_collapse_requested"
MOBILE_COLLAPSE_SEQUENCE_KEY = "_mobile_sidebar_collapse_sequence"
MOBILE_COLLAPSE_RETRY_DELAY_MS = 50
MOBILE_COLLAPSE_MAX_ATTEMPTS = 20

SIDEBAR_BEHAVIOR_STYLES = """
<style>
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background-color: inherit;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    align-items: center;
    background-color: inherit;
    box-sizing: border-box;
    min-height: 2.75rem;
    padding: 0.375rem 0.75rem;
    position: sticky;
    top: 0;
    z-index: 2;
}
@media (hover: none), (pointer: coarse) {
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        display: block !important;
    }
}
</style>
"""


def build_mobile_sidebar_collapse_component(request_id: int) -> str:
    if not isinstance(request_id, int) or isinstance(request_id, bool) or request_id < 1:
        raise ValueError("request_id must be a positive integer")

    return f"""
<!-- mobile-sidebar-collapse-request:{request_id} -->
<script>
(() => {{
    const parentWindow = window.parent;
    if (!parentWindow.matchMedia("(max-width: {MOBILE_BREAKPOINT_PX}px)").matches) {{
        return;
    }}

    let failedAttempts = 0;

    const scheduleRetry = () => {{
        failedAttempts += 1;
        if (failedAttempts < {MOBILE_COLLAPSE_MAX_ATTEMPTS}) {{
            window.setTimeout(tryCollapseSidebar, {MOBILE_COLLAPSE_RETRY_DELAY_MS});
        }}
    }};

    function tryCollapseSidebar() {{
        const sidebar = parentWindow.document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) {{
            scheduleRetry();
            return;
        }}

        const expanded = sidebar.getAttribute("aria-expanded");
        if (expanded === "false") {{
            return;
        }}
        if (expanded !== "true") {{
            scheduleRetry();
            return;
        }}

        const collapseButton = sidebar.querySelector(
            '[data-testid="stSidebarCollapseButton"] button'
        );
        if (!collapseButton) {{
            scheduleRetry();
            return;
        }}

        collapseButton.click();
    }}

    tryCollapseSidebar();
}})();
</script>
"""


def inject_sidebar_behavior_styles() -> None:
    st.markdown(SIDEBAR_BEHAVIOR_STYLES, unsafe_allow_html=True)


def request_mobile_sidebar_collapse(
    session_state: MutableMapping[str, object] | None = None,
) -> int:
    state = st.session_state if session_state is None else session_state
    raw_sequence = state.get(MOBILE_COLLAPSE_SEQUENCE_KEY, 0)
    sequence = (
        raw_sequence
        if isinstance(raw_sequence, int) and not isinstance(raw_sequence, bool) and raw_sequence >= 0
        else 0
    )
    request_id = sequence + 1
    state[MOBILE_COLLAPSE_SEQUENCE_KEY] = request_id
    state[MOBILE_COLLAPSE_REQUEST_KEY] = request_id
    return request_id


def consume_mobile_sidebar_collapse_request(
    session_state: MutableMapping[str, object] | None = None,
) -> int | None:
    state = st.session_state if session_state is None else session_state
    request_id = state.pop(MOBILE_COLLAPSE_REQUEST_KEY, None)
    if request_id is True:
        raw_sequence = state.get(MOBILE_COLLAPSE_SEQUENCE_KEY, 1)
        request_id = (
            raw_sequence
            if isinstance(raw_sequence, int) and not isinstance(raw_sequence, bool) and raw_sequence > 0
            else 1
        )
        state[MOBILE_COLLAPSE_SEQUENCE_KEY] = request_id
    if isinstance(request_id, int) and not isinstance(request_id, bool) and request_id > 0:
        return request_id
    return None


def render_requested_mobile_sidebar_collapse(
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    request_id = consume_mobile_sidebar_collapse_request(session_state)
    if request_id is None:
        return
    components.html(build_mobile_sidebar_collapse_component(request_id), height=0)
