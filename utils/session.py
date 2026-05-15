import streamlit as st


def get_session_value(key: str, default=None):
    return st.session_state.get(key, default)


def set_session_value(key: str, value) -> None:
    st.session_state[key] = value
