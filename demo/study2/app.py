import streamlit as st


def post_card(post: dict) -> None:
    st.subheader(post["title"])
    st.write(post["body"])
    st.caption("태그: " + ", ".join(post["tags"]))


def count_label(posts: list[dict], label: str) -> str:
    return f"{label} {len(posts)}건"


POSTS = [
    {"title": "첫 글", "body": "안녕하세요", "tags": ["intro"]},
    {"title": "둘째 글", "body": "재실행을 봅니다", "tags": ["rerun"]},
]


def on_ping() -> None:
    st.toast("콜백이 버튼 처리 중에 실행되었습니다.")


st.set_page_config(page_title="구조", layout="centered")
st.title("함수로 나눈 화면")
st.text_input("검색어", key="keyword")
kind = st.selectbox("보기", ["전체", "태그 있음"], key="kind")
st.button("신호", on_click=on_ping)
with st.form("filter_form"):
    note = st.text_input("메모")
    submitted = st.form_submit_button("메모 적용")
st.caption(f"현재 보기: {kind}")
st.write(count_label(POSTS, "샘플"))
keyword = st.session_state.get("keyword", "")
for post in POSTS:
    if keyword and keyword not in post["title"]:
        continue
    post_card(post)
if submitted and note:
    st.info(f"폼에서 받은 메모: {note}")
