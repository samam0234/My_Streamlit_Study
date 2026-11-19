import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from board.stats import daily_counts, posts_frame

SAMPLE = [
    {"id": 1, "title": "첫 글", "createdAt": "2026-11-01T09:00:00Z", "commentCount": 2},
    {"id": 2, "title": "둘째 글", "createdAt": "2026-11-02T09:00:00Z", "commentCount": 0},
    {"id": 3, "title": "셋째 글", "createdAt": "2026-11-02T11:00:00Z", "commentCount": 1},
]

st.set_page_config(page_title="통계", layout="centered")
st.title("게시글 통계")
if "range_days" not in st.session_state:
    st.session_state.range_days = 7
with st.form("range_form"):
    days = st.selectbox("기간(일)", [7, 14, 30], index=[7, 14, 30].index(int(st.session_state.range_days)))
    submitted = st.form_submit_button("필터 적용")
if submitted:
    st.session_state.range_days = int(days)
frame = posts_frame(SAMPLE)
chart = daily_counts(frame, int(st.session_state.range_days), datetime(2026, 11, 2, tzinfo=timezone.utc))
st.metric("글 수", int(len(frame)))
st.line_chart(chart, y="posts")
st.dataframe(frame, hide_index=True, width="stretch")
