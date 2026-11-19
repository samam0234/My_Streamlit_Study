import streamlit as st

from board.contract import API_PREFIX, ERROR_GUIDE, PATHS, page_params
from board.source import api_base, request_json


def render() -> None:
    st.header("API 계약")
    st.caption(f"접두어 {API_PREFIX}")
    st.dataframe(
        [{"name": name, "path": path} for name, path in PATHS.items()],
        hide_index=True,
        width="stretch",
    )
    page = st.number_input("page", min_value=1, value=1, step=1)
    limit = st.number_input("limit", min_value=1, max_value=50, value=10, step=1)
    q = st.text_input("q")
    st.json(page_params(int(page), int(limit), q.strip()))
    st.subheader("오류 코드")
    st.dataframe(
        [{"status": status, "screen": label} for status, label in ERROR_GUIDE.items()],
        hide_index=True,
        width="stretch",
    )
    if st.button("OpenAPI 경로 불러오기"):
        try:
            document = request_json("GET", "/api-docs")
        except Exception as exc:
            st.error("API 문서를 불러오지 못했습니다.")
            st.caption(exc.__class__.__name__)
            st.caption(api_base())
        else:
            server_paths = sorted((document.get("paths") or {}).keys())
            st.dataframe({"path": server_paths}, width="stretch")


render()
