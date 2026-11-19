import streamlit as st


def render() -> None:
    st.header("오류")
    st.error("요청한 화면을 찾지 못했습니다.")


render()
