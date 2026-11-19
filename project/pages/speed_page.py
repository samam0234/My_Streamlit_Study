import time

import streamlit as st

from board.source import use_local
from board.store import db_path


@st.cache_data(ttl=60, show_spinner=False)
def cached_count(seed: int) -> int:
    time.sleep(0.4)
    return seed


def render() -> None:
    st.header("캐시")
    st.caption("로컬 연습은 0.4초 sleep을 캐시합니다. 같은 숫자를 두 번 누르면 둘째가 짧습니다.")
    seed = st.number_input("캐시 키", min_value=1, value=1, step=1)
    if st.button("두 번 재기"):
        for label in ("첫 호출", "둘째 호출"):
            start = time.perf_counter()
            value = cached_count(int(seed))
            st.caption(f"{label} {time.perf_counter() - start:.3f}초 · 값 {value}")
    if st.button("이 키의 캐시 비우기"):
        cached_count.clear()
        st.success("캐시를 비웠습니다.")
    st.caption("로컬 DB" if use_local() else "API")
    st.caption(f"DB 파일 {db_path().name}")


render()
