import streamlit as st

from board import source
from board.doc_ai import search_excerpts, stream_answer
from board.errors import ApiError
from board.paths import project_page
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
    body = data.get("body") or ""
    st.write(body)
    author = data.get("author") or {}
    st.caption(f"{author.get('nickname', '')} · {data.get('createdAt', '')}")
    if body and st.button("본문 요약"):
        excerpts = search_excerpts(body, " ".join(body.split()[:20]) or body[:80])
        st.write_stream(stream_answer("다섯 줄 안으로 요약하세요.", excerpts))

    me = st.session_state.get("me") or {}
    if not me or author.get("id") != me.get("id"):
        return
    if st.session_state.get("edit_for") != raw_id:
        st.session_state.edit_title = data.get("title") or ""
        st.session_state.edit_body = body
        st.session_state.edit_for = raw_id
    with st.form(f"edit_{raw_id}"):
        st.text_input("제목", key="edit_title")
        st.text_area("본문", key="edit_body")
        submitted = st.form_submit_button("수정")
    if submitted:
        try:
            source.update_post(token(), int(raw_id), st.session_state.edit_title, st.session_state.edit_body)
        except ApiError as exc:
            show_error(exc)
            return
        st.session_state.edit_for = None
        st.success("수정 완료")
        st.rerun()
    if st.button("삭제"):
        try:
            source.delete_post(token(), int(raw_id))
        except ApiError as exc:
            show_error(exc)
            return
        st.query_params.clear()
        st.switch_page(project_page("list_page.py"))


render()
