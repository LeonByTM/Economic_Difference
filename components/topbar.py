from pathlib import Path

import streamlit as st

from config.settings import settings

_CSS_FILE = Path(__file__).resolve().parent.parent / "assets" / "styles.css"

PAGES = [
    ("Overview",              "Overview",                  "/"),
    ("Interest Rate",         "Interest_Rate_Employment",  "/Interest_Rate_Employment"),
    ("GDP Divergence",        "GDP_Divergence",            "/GDP_Divergence"),
    ("Population & Growth",   "Population_Growth",         "/Population_Growth"),
    ("Market Monitor",        "Market_Monitor",            "/Market_Monitor"),
]


def render_topbar(active: str = "") -> None:
    if _CSS_FILE.exists():
        st.markdown(
            f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.markdown('<div class="hslu-sidebar-title">HSLU</div>', unsafe_allow_html=True)

