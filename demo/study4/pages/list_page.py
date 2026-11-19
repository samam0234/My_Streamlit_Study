import streamlit as st

POSTS = [{"id": 1, "title": "첫 글"}, {"id": 2, "title": "둘째 글"}]
DETAIL = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pages" / "detail_page.py")


def render() -> None:
    st.header("목록")
    page = st.query_params.get("page", "1")
    st.caption(f"목록 페이지 번호: {page}")
    for post in POSTS:
        if st.button(post["title"], key=f"open_{post['id']}"):
            st.query_params["id"] = str(post["id"])
            st.switch_page(DETAIL)


render()
