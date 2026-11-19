import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from board.errors import ApiError, error_payload
from board.ui import show_error
from board.validate import validate_post

st.set_page_config(page_title="작성 폼", layout="centered")
if "result" not in st.session_state:
    st.session_state.result = None

st.title("글 작성")
st.selectbox("응답 연습", ["ok", "invalid", "unprocessable"], key="mode")
with st.form("new_post"):
    st.text_input("제목", key="form_title")
    st.text_area("본문", key="form_body")
    submitted = st.form_submit_button("작성", disabled=False)
if submitted:
    title = st.session_state.form_title.strip()
    body = st.session_state.form_body.strip()
    fields = validate_post(title, body)
    mode = st.session_state.mode
    if fields:
        st.session_state.result = (400, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", fields))
    elif mode == "invalid":
        st.session_state.result = (400, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", {"body": ["본문을 입력하세요."]}))
    elif mode == "unprocessable":
        st.session_state.result = (422, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", {"title": ["1~200자로 입력하세요."]}))
    else:
        st.session_state.result = (201, {"data": {"id": 1, "title": title, "body": body}})

result = st.session_state.result
if result:
    code, payload = result
    if code in (200, 201):
        st.success("작성 완료")
        st.write(payload.get("data", {}).get("title", ""))
    elif code in (400, 422):
        show_error(ApiError(code, payload))
