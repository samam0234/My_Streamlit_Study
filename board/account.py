import streamlit as st

from board import source
from board.errors import ApiError
from board.ui import ensure_account_state, show_error, token


def render_account() -> None:
    ensure_account_state()
    st.sidebar.caption("저장: 로컬 DB" if source.use_local() else "저장: API")
    if st.session_state.token and st.session_state.me is None:
        try:
            st.session_state.me = (source.me(token()).get("data"))
        except ApiError as exc:
            st.session_state.token = ""
            st.session_state.me = None
            show_error(exc)

    user = st.session_state.me
    if user:
        st.sidebar.write(f"{user.get('nickname')} 님")
        if st.sidebar.button("로그아웃"):
            try:
                source.logout(token())
            except ApiError as exc:
                show_error(exc)
            st.session_state.token = ""
            st.session_state.me = None
            st.rerun()
        return

    with st.sidebar.form("signup"):
        st.text_input("이메일", key="su_email")
        st.text_input("닉네임", key="su_nickname")
        st.text_input("비밀번호", type="password", key="su_password")
        signup_submitted = st.form_submit_button("가입")
    if signup_submitted:
        try:
            source.signup(
                st.session_state.su_email.strip(),
                st.session_state.su_password,
                st.session_state.su_nickname.strip(),
            )
            st.session_state.notice = "가입했습니다. 로그인해 주세요."
        except ApiError as exc:
            st.session_state.notice = exc.message

    with st.sidebar.form("login"):
        st.text_input("이메일", key="li_email")
        st.text_input("비밀번호", type="password", key="li_password")
        login_submitted = st.form_submit_button("로그인")
    if login_submitted:
        try:
            payload = source.login(st.session_state.li_email.strip(), st.session_state.li_password)
        except ApiError as exc:
            st.session_state.notice = exc.message
        else:
            data = payload.get("data") or {}
            st.session_state.token = data.get("accessToken") or ""
            st.session_state.me = data.get("user")
            st.session_state.notice = "로그인했습니다."
            st.rerun()

    if source.use_local():
        st.sidebar.caption("연습 계정 mina@example.com / password123")
    if st.session_state.notice:
        st.sidebar.info(st.session_state.notice)
