# study13. 외부 서비스 연동

## ① 목표

파일 업로드, 가입 안내 메일, 결제 페이지 링크, OpenID Connect 소셜 로그인을 Streamlit 화면에 연결한다.

## ② 📖 이론

### 왜 쓰는지

게시판만으로는 첨부 파일, 가입 확인 메일, 결제, 소셜 계정이 없다. 이 기능은 전부 앱 밖의 서비스가 비밀 키를 갖고 수행한다. Streamlit은 사용자의 입력을 받아 그 서비스의 문서화된 API를 서버에서 호출하고, 돌아온 주소나 결과만 화면에 보여 준다.

### 핵심 개념

- **업로드**: `st.file_uploader`가 바이트를 서버 메모리로 받는다. 10MB를 넘기면 저장하지 않고 `PAYLOAD_TOO_LARGE`에 해당하는 문장을 보여 준다.
- **메일**: `smtplib`이 SMTP 서버로 텍스트 메일을 보낸다. 호스트와 비밀번호는 시크릿이다. 학습 중 SMTP가 없으면 같은 본문을 로그로만 남기는 연습 모드를 둔다.
- **결제**: 결제 비밀 키로 결제 서비스의 세션을 만들면 결제 페이지 URL이 돌아온다. 화면은 `st.link_button`으로 그 URL만 연다. 카드 번호는 이 앱이 받지 않는다.
- **소셜 로그인**: `st.login`은 OpenID Connect 공급자로 이동하고, 돌아오면 `st.user`에 신원 속성이 생긴다. 패키지는 `streamlit[auth]`(Authlib 1.3.2 이상)이다. 일반 OAuth만 제공하고 OIDC 메타데이터가 없는 공급자는 이 함수의 대상이 아니다.

### 비유

업로드는 창구의 서류 접수함이다. 메일은 창구가 대신 부치는 엽서다. 결제는 창구가 카드 번호를 받아 적지 않고, 금고(결제 서비스)가 만든 접수증 링크만 손님에게 건네는 일이다. 소셜 로그인은 다른 건물 안내소에서 신원을 확인하고 돌아온 이름표(`st.user`)다.

## ③ 🛠️ 실기

시크릿 예시는 값을 `xxx`로 두고 실제 파일은 커밋하지 않는다.

`.streamlit/secrets.toml` 예시

```toml
[smtp]
host = "smtp.example.com"
port = 587
user = "board@example.com"
password = "xxx"
from_addr = "board@example.com"

[stripe]
secret_key = "xxx"
price_id = "price_xxx"

[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "xxx"
client_id = "xxx"
client_secret = "xxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

배포 호스트가 바뀌면 `redirect_uri`를 그 절대 URL의 `/oauth2callback`으로 바꾸고, 공급자 콘솔의 허용 주소도 같이 바꾼다.

### 전체 코드

`lib/external.py`

```python
import smtplib
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

MAX_BYTES = 10 * 1024 * 1024


def save_upload(name: str, data: bytes) -> Path:
    if len(data) > MAX_BYTES:
        raise ValueError("업로드는 10MB 이하만 받습니다.")
    folder = Path("data") / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / Path(name).name
    target.write_bytes(data)
    return target


def send_signup_mail(to_addr: str, nickname: str) -> str:
    body = f"{nickname}님, 가입을 확인했습니다."
    smtp = st.secrets.get("smtp")
    if not smtp:
        return "연습 모드: " + body
    message = EmailMessage()
    message["Subject"] = "가입 안내"
    message["From"] = smtp["from_addr"]
    message["To"] = to_addr
    message.set_content(body)
    with smtplib.SMTP(smtp["host"], int(smtp["port"]), timeout=10) as client:
        client.starttls()
        client.login(smtp["user"], smtp["password"])
        client.send_message(message)
    return "가입 안내 메일을 보냈습니다."


def payment_link() -> str | None:
    stripe = st.secrets.get("stripe")
    if not stripe:
        return None
    import requests

    response = requests.post(
        "https://api.stripe.com/v1/checkout/sessions",
        auth=(stripe["secret_key"], ""),
        data={
            "mode": "payment",
            "line_items[0][price]": stripe["price_id"],
            "line_items[0][quantity]": 1,
            "success_url": "http://localhost:8501/?paid=1",
            "cancel_url": "http://localhost:8501/?paid=0",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("url")
```

`pages/services_page.py`

```python
import streamlit as st

from lib.external import payment_link, save_upload, send_signup_mail

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

if st.button("결제 페이지 만들기"):
    url = payment_link()
    if url:
        st.link_button("결제로 이동", url)
    else:
        st.info("결제 비밀 키가 없어 링크를 만들지 않았습니다.")

if not st.user.is_logged_in:
    if st.button("소셜 로그인"):
        st.login()
else:
    st.write(f"{st.user.name} 님")
    if st.button("소셜 로그아웃"):
        st.logout()
```

소셜 로그인 버튼은 `[auth]` 시크릿이 있을 때만 동작한다. 시크릿 없이 예제를 읽을 때는 업로드와 메일 연습 모드만 실행한다.

### 줄별 설명

- `MAX_BYTES`: 10MB다. 넘는 파일은 디스크에 쓰지 않는다.
- `Path(name).name`: 경로 구분자를 제거해 `data/uploads` 밖으로 나가지 않게 한다.
- `save_upload`: 바이트를 파일로 쓴다. 이름 충돌은 학습용으로 같은 이름을 덮어쓴다. 운영에서는 id를 접두어로 붙인다.
- `send_signup_mail`: 시크릿이 없으면 본문 문자열만 반환한다. 있으면 STARTTLS 뒤 로그인하고 보낸다.
- `EmailMessage`: 제목, 보내는 주소, 받는 주소, 본문을 나눈다. HTML 본문은 쓰지 않는다.
- `payment_link`: Stripe Checkout 세션 API에 비밀 키를 기본 인증으로 보낸다. 응답의 `url`만 돌려준다. 카드 입력란은 이 함수에 없다.
- `success_url`: 결제 서비스가 사람을 돌려보낼 주소다. 배포 후에는 localhost 대신 HTTPS 도메인을 시크릿으로 뺀다.
- `st.file_uploader`: 브라우저에서 고른 파일을 서버 위젯 값으로 받는다.
- `st.link_button`: 새 결제 페이지로 이동하는 앵커다.
- `st.user.is_logged_in`: OIDC 쿠키가 유효한지 Streamlit이 해석한 값이다.
- `st.login()`: 시크릿의 공급자로 리다이렉트한다. 인자가 없으면 `[auth]` 전체를 공급자 설정으로 쓴다.
- `st.logout()`: 신원 쿠키를 지우고 세션을 새로 시작한다.

## ④ 🔗 연동 포인트

- 업로드한 파일 경로는 study18이 문서를 읽어 요약할 때 `data/uploads`에서 찾는다. DocuForge형 흐름의 입구가 이 업로더다.
- 가입 메일은 study7 `signup`이 201을 받은 직후에 `send_signup_mail`을 부르면 연결된다. 메일 실패가 가입 롤백을 대신하게 두지 않고, 화면에는 메일 결과만 따로 보여 준다.
- 결제 URL은 게시판 API와 다른 호스트다. `API_BASE_URL`과 Stripe 비밀을 한 문자열에 합치지 않는다.
- `st.user.email`이 있으면 그 값을 스펙의 로그인 이메일과 맞춰 기존 `accessToken` 세션을 발급하는 일은 API에 소셜 연결 엔드포인트가 생긴 뒤에 붙인다. 지금은 신원 표시까지가 이 단원의 범위다.
- 운영 `redirect_uri`는 study10의 HTTPS 도메인과 같아야 한다.

## ⑤ 오류 노트

### 업로드 직후 경로가 프로젝트 밖을 가리킨다

- 증상: 저장 경로에 `..`가 포함된다.
- 원인: 파일 이름을 그대로 `Path`에 이어 붙였다.
- 해결: `Path(name).name`만 저장 폴더에 붙인다.

### 메일 연습 모드인데 SMTP 오류가 난다

- 증상: 시크릿을 비웠는데 `SMTP` 예외가 난다.
- 원인: `st.secrets.get("smtp")`가 빈 테이블을 참으로 본다.
- 해결: 호스트 키가 있을 때만 SMTP 분기로 들어가게 `if not smtp or "host" not in smtp`로 조건에 맞춘다.

### `st.login`이 공급자를 찾지 못한다

- 증상: 인증 설정이 없다는 예외가 난다.
- 원인: `secrets.toml`에 `redirect_uri`, `cookie_secret`, `client_id`, `client_secret`, `server_metadata_url` 중 하나가 빠졌다.
- 해결: 다섯 키를 `[auth]`에 절대 URL로 채운다. `pip install "streamlit[auth]"`로 Authlib을 설치한다.

### 결제 응답이 400이다

- 증상: `raise_for_status`가 실패한다.
- 원인: `price_id`가 테스트 상품과 다르거나 비밀 키가 공개 키와 뒤바뀌었다.
- 해결: 대시보드의 가격 id와 비밀 키만 시크릿에 다시 넣는다. 카드 번호를 앱 폼에 추가하지 않는다.

## ⑥ 직접 해보기

1. 1KB 텍스트 파일을 저장하고 `data/uploads` 아래 파일 이름이 원본의 베이스 이름과 같은지 확인한다.
2. SMTP 시크릿 없이 안내 메일을 눌러 연습 모드 문장이 본문을 포함하는지 확인한다.
3. `[auth]`를 채운 로컬에서 소셜 로그인과 로그아웃을 한 번씩 눌러 `st.user.name`이 생겼다 사라지는지 확인한다. 공급자 계정이 없으면 설정 키 목록만 대조한다.

## ⑦ ☐ 체크리스트

- [ ] 10MB 이하의 파일만 `data/uploads`에 저장한다.
- [ ] 가입 안내 메일은 시크릿이 있을 때만 SMTP로 나간다.
- [ ] 결제 화면은 서비스가 돌려준 URL만 열고 카드 번호를 받지 않는다.
- [ ] `st.login`과 `st.user`, `st.logout`으로 OIDC 로그인을 붙였다.
- [ ] 비밀 키는 `secrets.toml` 예시의 자리만 문서에 있고 실제 값은 커밋하지 않는다.
- [ ] 운영 리다이렉트 주소는 HTTPS 절대 URL이다.

## ⑧ 다음 단계

외부 호출이 늘면 경로와 오류 모양을 한 규칙으로 적어야 한다. study14는 이 앱이 소비하는 REST API의 문서, 버전, 페이지, 오류 형식을 정리한다.
