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

        st.markdown("---")
        with st.expander("🔑 Refresh AWS Credentials", expanded=False):
            with st.form("aws_creds_form"):
                key_id = st.text_input("Access Key ID", placeholder="ASIA...")
                secret = st.text_input("Secret Access Key", type="password", placeholder="Enter AWS Secret Access Key...")
                token = st.text_area("Session Token", placeholder="IQoJb3...", height=160)
                submitted = st.form_submit_button("Apply & Load Data")
            if submitted:
                if key_id and secret and token:
                    normalized_key_id = "".join(key_id.split())
                    normalized_secret = "".join(secret.split())
                    normalized_token = "".join(token.split())
                    st.session_state["aws_creds"] = {
                        "key_id": normalized_key_id,
                        "secret": normalized_secret,
                        "token": normalized_token,
                    }
                    st.cache_data.clear()
                    st.success("Credentials updated — data will reload.")
                else:
                    st.error("Access Key ID, Secret Access Key, and Session Token are required.")
