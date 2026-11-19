import streamlit as st

from board.external import save_upload, send_signup_mail


def render() -> None:
    st.header("외부 서비스")
    uploaded = st.file_uploader("첨부", type=["txt", "md", "png"])
    if uploaded is not None and st.button("파일 저장"):
        try:
            path = save_upload(uploaded.name, uploaded.getvalue())
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success(f"저장했습니다. {path.name}")
    with st.form("mail_form"):
        to_addr = st.text_input("받는 이메일")
        nickname = st.text_input("닉네임")
        mailed = st.form_submit_button("안내 메일")
    if mailed:
        st.info(send_signup_mail(to_addr.strip(), nickname.strip() or "회원"))
    st.caption("결제 비밀 키와 OIDC 설정은 .streamlit/secrets.toml 에 둡니다. 카드 번호는 받지 않습니다.")
    if st.button("결제 설정 확인"):
        try:
            stripe = st.secrets.get("stripe")
        except Exception:
            stripe = None
        if stripe and stripe.get("secret_key"):
            st.success("Stripe 비밀 키가 있습니다. 결제 URL 생성은 study13.md 예제를 이 키로 호출하면 됩니다.")
        else:
            st.info("결제 비밀 키가 없어 링크를 만들지 않았습니다.")


render()
