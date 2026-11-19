import streamlit as st

from board import source
from board.errors import ApiError
from board.paths import midpoint_page
from board.ui import show_error


def render() -> None:
    st.header("목록")
    q = st.text_input("검색", value=st.query_params.get("q", ""))
    page_raw = st.query_params.get("page", "1")
    page = int(page_raw) if str(page_raw).isdigit() else 1
    if st.button("검색"):
        st.query_params["q"] = q
        st.query_params["page"] = "1"
        st.rerun()
    try:
        payload = source.list_posts(page, st.query_params.get("q", ""))
    except ApiError as exc:
        show_error(exc)
        return
    meta = payload.get("meta") or {}
    st.caption(f"{meta.get('page', 1)} / {meta.get('totalPages', 0)} · 총 {meta.get('total', 0)}건")
    current = int(meta.get("page") or 1)
    total_pages = int(meta.get("totalPages") or 0)
    left, right = st.columns(2)
    if current > 1 and left.button("이전"):
        st.query_params["page"] = str(current - 1)
        st.rerun()
    if total_pages and current < total_pages and right.button("다음"):
        st.query_params["page"] = str(current + 1)
        st.rerun()
    for post in payload.get("data") or []:
        st.subheader(post["title"])
        st.write(post.get("body") or "")
        st.caption(post.get("createdAt", ""))
        if st.button("열기", key=f"open_{post['id']}"):
            st.query_params["id"] = str(post["id"])
            st.switch_page(midpoint_page("detail_page.py"))


render()
