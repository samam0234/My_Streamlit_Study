import streamlit as st

POSTS = {1: {"title": "첫 글", "body": "안녕하세요"}, 2: {"title": "둘째 글", "body": "경로를 확인합니다"}}
LIST = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "pages" / "list_page.py")


def render() -> None:
    raw_id = st.query_params.get("id")
    if raw_id is None or not str(raw_id).isdigit():
        st.error("글 번호가 올바르지 않습니다.")
        if st.button("목록으로"):
            st.query_params.clear()
            st.switch_page(LIST)
        st.stop()
    post = POSTS.get(int(raw_id))
    if post is None:
        st.error("없는 글입니다.")
        st.stop()
    st.header(post["title"])
    st.write(post["body"])


render()
