import streamlit as st

from board.doc_ai import search_excerpts, stream_answer
from board.external import MAX_BYTES


def render() -> None:
    st.header("문서 요약과 질문")
    st.caption("발췌에 있는 내용만 답합니다. 모델 키가 없으면 발췌 문장을 그대로 보여 줍니다.")
    if "doc_text" not in st.session_state:
        st.session_state.doc_text = ""
    upload = st.file_uploader("TXT 또는 MD", type=["txt", "md"])
    if upload is not None:
        data = upload.getvalue()
        if len(data) > MAX_BYTES:
            st.error("10MB 이하만 올립니다.")
        else:
            st.session_state.doc_text = data.decode("utf-8", errors="replace")
            st.success(f"{len(st.session_state.doc_text)}자를 읽었습니다.")
    text = st.session_state.doc_text
    if text and st.button("요약 카드"):
        excerpts = search_excerpts(text, " ".join(text.split()[:30]))
        st.write_stream(stream_answer("다섯 줄 안으로 요약하세요.", excerpts))
    question = st.text_input("질문")
    if st.button("질문하기", disabled=not text or not question.strip()):
        excerpts = search_excerpts(text, question.strip())
        st.write("근거")
        for item in excerpts:
            st.caption(f"(발췌 {item['n']}) {item['text']}")
        st.write_stream(stream_answer(question.strip(), excerpts))


render()
