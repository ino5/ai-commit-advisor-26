from collections.abc import MutableMapping

import streamlit as st
import streamlit.components.v1 as components


MOBILE_BREAKPOINT_PX = 768
MOBILE_COLLAPSE_REQUEST_KEY = "_mobile_sidebar_collapse_requested"

SIDEBAR_BEHAVIOR_STYLES = """
<style>
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    background: var(--secondary-background-color, #ffffff);
    position: sticky;
    top: 0;
    z-index: 2;
}
</style>
"""

MOBILE_COLLAPSE_COMPONENT = f"""
<script>
(() => {{
    const parentWindow = window.parent;
    if (!parentWindow.matchMedia("(max-width: {MOBILE_BREAKPOINT_PX}px)").matches) {{
        return;
    }}

    const sidebar = parentWindow.document.querySelector('[data-testid="stSidebar"]');
    if (!sidebar || sidebar.getAttribute("aria-expanded") !== "true") {{
        return;
    }}

    const collapseButton = sidebar.querySelector(
        '[data-testid="stSidebarCollapseButton"] button'
    );
    collapseButton?.click();
}})();
</script>
"""


def inject_sidebar_behavior_styles() -> None:
    st.markdown(SIDEBAR_BEHAVIOR_STYLES, unsafe_allow_html=True)


def request_mobile_sidebar_collapse(
    session_state: MutableMapping[str, object] | None = None,
) -> None:
    state = st.session_state if session_state is None else session_state
    state[MOBILE_COLLAPSE_REQUEST_KEY] = True


def consume_mobile_sidebar_collapse_request(
    session_state: MutableMapping[str, object] | None = None,
) -> bool:
    state = st.session_state if session_state is None else session_state
    return state.pop(MOBILE_COLLAPSE_REQUEST_KEY, False) is True


def render_requested_mobile_sidebar_collapse() -> None:
    if not consume_mobile_sidebar_collapse_request():
        return
    components.html(MOBILE_COLLAPSE_COMPONENT, height=0)
