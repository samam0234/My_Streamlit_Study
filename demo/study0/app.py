import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

st.set_page_config(page_title="환경 확인", layout="centered")
st.title("Streamlit 첫 화면")
st.write("개발 서버가 이 스크립트를 위에서 아래로 실행했습니다.")
st.caption(f"API_BASE_URL 설정됨: {bool(os.getenv('API_BASE_URL', ''))}")
st.caption(f"POST_SOURCE: {os.getenv('POST_SOURCE', 'local')}")
st.caption(f"작업 폴더: {Path.cwd()}")
