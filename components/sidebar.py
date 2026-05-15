from pathlib import Path

import streamlit as st

from config.settings import settings

_CSS_FILE = Path(__file__).resolve().parent.parent / "assets" / "styles.css"


def render_sidebar() -> None:
    if _CSS_FILE.exists():
        st.markdown(
            f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    with st.sidebar:
        st.title(settings.app_title)
        st.caption(f"Environment: {settings.app_env}")
