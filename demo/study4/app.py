import streamlit as st

from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIST = str(ROOT / "pages" / "list_page.py")
DETAIL = str(ROOT / "pages" / "detail_page.py")
MISSING = str(ROOT / "pages" / "missing_page.py")

st.set_page_config(page_title="경로", layout="centered")
st.title("멀티페이지")
page = st.navigation(
    [
        st.Page(LIST, title="목록", icon="📋", default=True),
        st.Page(DETAIL, title="상세", icon="📄"),
        st.Page(MISSING, title="오류", icon="⚠️"),
    ]
)
page.run()
