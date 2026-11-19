import streamlit as st

from board.errors import ApiError


def token() -> str:
    return st.session_state.get("token") or ""


def show_error(exc: ApiError) -> None:
    st.error(exc.message)
    fields = (exc.payload.get("error") or {}).get("fields") or {}
    for name, messages in fields.items():
        st.caption(f"{name}: {', '.join(messages)}")


def ensure_account_state() -> None:
    if "token" not in st.session_state:
        st.session_state.token = ""
    if "me" not in st.session_state:
        st.session_state.me = None
    if "notice" not in st.session_state:
        st.session_state.notice = ""
