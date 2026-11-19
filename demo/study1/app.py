import streamlit as st

st.set_page_config(page_title="Hello Streamlit", layout="centered")
st.title("안녕하세요, Streamlit")
st.header("기본 출력")
st.write("이 문장은 st.write가 그립니다.")
st.markdown("**굵은 글씨**와 코드는 마크다운으로 씁니다.")
st.caption("보조 설명은 caption입니다.")
st.code("streamlit run demo/study1/app.py", language="text")

name = st.text_input("이름", value="방문자")
tool = st.selectbox("오늘 볼 것", ["출력", "입력", "버튼"])
pressed = st.button("인사하기")
st.write(f"{name}님, 오늘은 {tool}을 봅니다.")
if pressed:
    st.success(f"{name}님, 버튼을 눌렀습니다.")
