import streamlit as st

from config.settings import settings


SESSION_KEY = "is_authenticated"


def login(username: str, password: str) -> bool:
    is_valid = username == settings.app_username and password == settings.app_password
    st.session_state[SESSION_KEY] = is_valid
    return is_valid


def logout() -> None:
    st.session_state[SESSION_KEY] = False


def is_authenticated() -> bool:
    return bool(st.session_state.get(SESSION_KEY, False))


def require_authentication() -> None:
    if not is_authenticated():
        st.warning("Please sign in from the home page.")
        st.stop()
