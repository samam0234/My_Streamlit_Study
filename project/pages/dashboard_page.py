import streamlit as st

from board import source
from board.errors import ApiError
from board.stats import daily_counts, posts_frame
from board.ui import show_error


def render() -> None:
    st.header("게시글 통계")
    if "range_days" not in st.session_state:
        st.session_state.range_days = 7
    with st.form("range_form"):
        days = st.selectbox("기간(일)", [7, 14, 30], index=[7, 14, 30].index(int(st.session_state.range_days)))
        submitted = st.form_submit_button("필터 적용")
    if submitted:
        st.session_state.range_days = int(days)
    try:
        payload = source.list_posts(1, "", limit=50)
    except ApiError as exc:
        show_error(exc)
        return
    rows = [
        {
            "id": post.get("id"),
            "title": post.get("title"),
            "createdAt": post.get("createdAt"),
            "commentCount": post.get("commentCount", 0),
        }
        for post in payload.get("data") or []
    ]
    frame = posts_frame(rows)
    chart = daily_counts(frame, int(st.session_state.range_days))
    st.metric("불러온 글 수", int(len(frame)))
    st.line_chart(chart, y="posts")
    st.dataframe(frame, hide_index=True, width="stretch")


render()
