import streamlit as st

from board import source
from board.errors import ApiError
from board.ui import show_error, token


def render() -> None:
    st.header("작성")
    if not token():
        st.info("글을 쓰려면 로그인하세요.")
        return
    with st.form("mid_new_post"):
        title = st.text_input("제목")
        body = st.text_area("본문")
        submitted = st.form_submit_button("작성")
    if not submitted:
        return
    try:
        created = source.create_post(token(), title, body, [])
    except ApiError as exc:
        show_error(exc)
        return
    st.success("작성 완료")
    st.write(f"글 번호 {created.get('data', {}).get('id')}")


render()
