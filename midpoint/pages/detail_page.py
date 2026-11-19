import streamlit as st

from board import source
from board.errors import ApiError
from board.paths import midpoint_page
from board.ui import show_error, token


def render() -> None:
    raw_id = st.query_params.get("id")
    if raw_id is None or not str(raw_id).isdigit():
        st.error("글 번호가 올바르지 않습니다.")
        st.stop()
    try:
        data = (source.get_post(int(raw_id)).get("data")) or {}
    except ApiError as exc:
        show_error(exc)
        return
    st.header(data.get("title") or "")
    st.write(data.get("body") or "")
    author = data.get("author") or {}
    st.caption((author.get("nickname") or "") + " · " + (data.get("createdAt") or ""))
    me = st.session_state.get("me") or {}
    if not me or author.get("id") != me.get("id"):
        return
    edit_key = f"mid_edit_{raw_id}"
    if st.session_state.get("mid_edit_for") != raw_id:
        st.session_state.mid_edit_title = data.get("title") or ""
        st.session_state.mid_edit_body = data.get("body") or ""
        st.session_state.mid_edit_for = raw_id
    with st.form(edit_key):
        st.text_input("제목", key="mid_edit_title")
        st.text_area("본문", key="mid_edit_body")
        submitted = st.form_submit_button("수정")
    if submitted:
        try:
            source.update_post(token(), int(raw_id), st.session_state.mid_edit_title, st.session_state.mid_edit_body)
        except ApiError as exc:
            show_error(exc)
            return
        st.session_state.mid_edit_for = None
        st.success("수정 완료")
        st.rerun()
    if st.button("삭제"):
        try:
            source.delete_post(token(), int(raw_id))
        except ApiError as exc:
            show_error(exc)
            return
        st.query_params.clear()
        st.switch_page(midpoint_page("list_page.py"))


render()
