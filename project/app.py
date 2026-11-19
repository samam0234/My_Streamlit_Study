import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from board.account import render_account
from board.paths import project_page

st.set_page_config(page_title="Streamlit 게시판", layout="centered")
render_account()
st.title("Streamlit 게시판")
page = st.navigation(
    [
        st.Page(project_page("list_page.py"), title="목록", icon="📋", default=True),
        st.Page(project_page("detail_page.py"), title="상세", icon="📄"),
        st.Page(project_page("write_page.py"), title="작성", icon="✍️"),
        st.Page(project_page("dashboard_page.py"), title="통계", icon="📈"),
        st.Page(project_page("live_page.py"), title="알림", icon="🔔"),
        st.Page(project_page("ai_page.py"), title="문서", icon="📄"),
        st.Page(project_page("services_page.py"), title="외부", icon="🔌"),
        st.Page(project_page("docs_page.py"), title="API", icon="📡"),
        st.Page(project_page("speed_page.py"), title="캐시", icon="⚡"),
    ]
)
page.run()
