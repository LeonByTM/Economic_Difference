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

        st.markdown("---")
        with st.expander("🔑 Refresh AWS Credentials", expanded=False):
            with st.form("aws_creds_form"):
                key_id = st.text_input("Access Key ID", placeholder="ASIA…")
                secret = st.text_input("Secret Access Key", type="password", placeholder="…")
                token  = st.text_area("Session Token", placeholder="IQoJb3…", height=80)
                submitted = st.form_submit_button("Apply & Reload Data")
            if submitted:
                if key_id and secret:
                    st.session_state["aws_creds"] = {
                        "key_id": key_id.strip(),
                        "secret": secret.strip(),
                        "token":  token.strip() or None,
                    }
                    st.cache_data.clear()
                    st.success("Credentials updated. Data will reload.")
                else:
                    st.error("Access Key ID and Secret Access Key are required.")
