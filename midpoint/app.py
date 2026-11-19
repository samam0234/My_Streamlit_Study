import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from board.account import render_account
from board.paths import midpoint_page

st.set_page_config(page_title="작은 게시판", layout="centered")
render_account()
st.title("작은 게시판")
page = st.navigation(
    [
        st.Page(midpoint_page("list_page.py"), title="목록", icon="📋", default=True),
        st.Page(midpoint_page("detail_page.py"), title="상세", icon="📄"),
        st.Page(midpoint_page("write_page.py"), title="작성", icon="✍️"),
    ]
)
page.run()
