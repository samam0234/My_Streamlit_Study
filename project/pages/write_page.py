import streamlit as st

from board import source
from board.errors import ApiError
from board.external import save_upload
from board.ui import show_error, token


def render() -> None:
    st.header("작성")
    if not token():
        st.info("글을 쓰려면 로그인하세요.")
        return
    upload = st.file_uploader("텍스트 첨부", type=["txt", "md"])
    with st.form("new_post"):
        title = st.text_input("제목")
        body = st.text_area("본문")
        submitted = st.form_submit_button("작성")
    if not submitted:
        return
    if upload is not None:
        try:
            path = save_upload(upload.name, upload.getvalue())
        except ValueError as exc:
            st.error(str(exc))
            return
        st.caption(f"첨부 저장: {path.name}")
    try:
        created = source.create_post(token(), title, body, [])
    except ApiError as exc:
        show_error(exc)
        return
    st.success("작성 완료")
    st.write(f"글 번호 {created.get('data', {}).get('id')}")


render()
