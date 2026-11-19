import json
from pathlib import Path

import streamlit as st

STORE = Path(__file__).resolve().parents[2] / "data" / "drafts.json"


def load_drafts() -> list[dict]:
    if not STORE.exists():
        return []
    return json.loads(STORE.read_text(encoding="utf-8"))


def save_drafts(rows: list[dict]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def init_state() -> None:
    if "token" not in st.session_state:
        st.session_state.token = ""
    if "drafts" not in st.session_state:
        st.session_state.drafts = load_drafts()
    if "saved_count" not in st.session_state:
        st.session_state.saved_count = 0


def remember_token() -> None:
    st.session_state.token = st.session_state.token_input.strip()


def add_draft() -> None:
    title = st.session_state.draft_title.strip()
    body = st.session_state.draft_body.strip()
    if not title or not body:
        st.session_state.form_error = "제목과 본문을 입력하세요."
        return
    st.session_state.drafts.append({"title": title, "body": body})
    st.session_state.form_error = ""
    st.session_state.saved_count += 1
    save_drafts(st.session_state.drafts)


st.set_page_config(page_title="세션과 파일", layout="centered")
init_state()
st.title("세션 상태와 파일")
st.text_input("연습용 토큰", key="token_input", on_change=remember_token)
st.caption("세션에 보관 중" if st.session_state.token else "세션에 토큰 없음")
with st.form("draft_form", clear_on_submit=True):
    st.text_input("제목", key="draft_title")
    st.text_area("본문", key="draft_body")
    st.form_submit_button("임시 저장", on_click=add_draft)
if st.session_state.get("form_error"):
    st.error(st.session_state.form_error)
st.write(f"이번 세션에서 저장한 횟수: {st.session_state.saved_count}")
st.json(st.session_state.drafts)
