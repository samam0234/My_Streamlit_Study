import streamlit as st

from board import source
from board.errors import ApiError


if "seen_id" not in st.session_state:
    st.session_state.seen_id = 0
if "notices" not in st.session_state:
    st.session_state.notices = []


@st.fragment(run_every="5s")
def notice_board() -> None:
    try:
        payload = source.list_posts(1, "", limit=10)
    except ApiError as exc:
        st.caption(exc.message)
        return
    fresh = []
    newest = int(st.session_state.seen_id)
    for post in payload.get("data") or []:
        post_id = int(post["id"])
        if post_id > int(st.session_state.seen_id):
            fresh.append(post["title"])
        if post_id > newest:
            newest = post_id
    if fresh:
        st.session_state.seen_id = newest
        st.session_state.notices = (fresh + list(st.session_state.notices))[:10]
        st.toast(f"새 글 {len(fresh)}건")
    st.write("알림")
    for title in st.session_state.notices:
        st.caption(title)


def render() -> None:
    st.header("알림")
    if st.button("현재 글을 읽음으로 표시"):
        try:
            payload = source.list_posts(1, "", limit=50)
            ids = [int(post["id"]) for post in payload.get("data") or []]
            st.session_state.seen_id = max(ids or [0])
            st.session_state.notices = []
        except ApiError as exc:
            st.error(exc.message)
    notice_board()


render()
