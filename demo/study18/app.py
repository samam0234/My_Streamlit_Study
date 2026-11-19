import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from board.doc_ai import search_excerpts, stream_answer
from board.external import MAX_BYTES

st.set_page_config(page_title="문서 질문", layout="centered")
st.title("문서 요약과 질문")
if "doc_text" not in st.session_state:
    st.session_state.doc_text = "첫 줄은 세션 상태를 설명합니다.\n둘째 줄은 캐시를 설명합니다.\n셋째 줄은 배포를 설명합니다."
upload = st.file_uploader("TXT 또는 MD", type=["txt", "md"])
if upload is not None:
    data = upload.getvalue()
    if len(data) > MAX_BYTES:
        st.error("10MB 이하만 올립니다.")
    else:
        st.session_state.doc_text = data.decode("utf-8", errors="replace")
text = st.session_state.doc_text
st.text_area("문서", value=text, height=140, disabled=True)
if st.button("요약"):
    excerpts = search_excerpts(text, " ".join(text.split()[:20]))
    st.write_stream(stream_answer("요약하세요.", excerpts))
question = st.text_input("질문", value="세션")
if st.button("질문하기") and question.strip():
    excerpts = search_excerpts(text, question.strip())
    for item in excerpts:
        st.caption(f"(발췌 {item['n']}) {item['text']}")
    st.write_stream(stream_answer(question.strip(), excerpts))
