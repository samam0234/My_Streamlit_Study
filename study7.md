# study7. 인증과 보안 기초

## ① 목표

회원가입·로그인으로 액세스 토큰을 세션에 두고, 내 정보와 작성자 권한을 확인하며, 비밀번호 해시·CORS·XSS·CSRF를 Streamlit 앱 기준으로 지킨다.

## ② 📖 이론

### 왜 쓰는지

study6의 작성·수정·삭제는 Bearer 토큰이 있어야 한다. 토큰은 로그인 응답의 `data.accessToken`이고, 보관 위치는 study3에서 만든 `st.session_state.token`이다. 브라우저와 Streamlit 서버는 WebSocket 세션으로 연결되어 있고, API를 부르는 `requests`는 그 서버 안에서 실행된다. 그래서 로그인 상태는 브라우저 `localStorage`가 아니라 서버 세션 키로 공유된다.

### 핵심 개념

- **회원가입**: `POST /api/auth/signup`. 본문은 `email`, `password`, `nickname`. 성공 201. 중복 이메일은 409 `EMAIL_TAKEN`.
- **로그인**: `POST /api/auth/login`. 성공 200. `data.user`와 `data.accessToken`. 실패는 401 `INVALID_CREDENTIALS`이며, 이메일과 비밀번호 중 어느 쪽이 틀렸는지는 문장으로 구분하지 않는다.
- **내 정보**: `GET /api/auth/me`. 토큰이 없거나 만료면 401 `UNAUTHORIZED`.
- **인가**: 수정·삭제는 서버가 작성자만 허용한다. 화면은 `author.id`와 `me.id`가 같을 때만 버튼을 보여 주고, 서버가 403 `FORBIDDEN`을 주면 그 문장을 그대로 표시한다. 버튼을 숨기는 일이 권한 검사를 대신하지 않는다.
- **비밀번호 해시**: 공통 API에 가입할 때는 비밀번호 원문을 HTTPS 뒤의 서버로 보내고, 해시는 API 서버가 저장한다. 화면이 먼저 해시해서 보내면 서버가 한 번 더 해시하거나 검증이 어긋난다. 이 앱이 직접 사용자 파일을 가질 때만 `hash_password`로 PBKDF2 해시를 저장한다.
- **CORS**: `requests`는 브라우저 밖, Streamlit 서버에서 나간다. 이 경로에는 브라우저 CORS가 없다. CORS는 브라우저가 Streamlit이 아닌 다른 출처를 직접 부를 때 서버의 `CORS_ORIGIN` 허용 목록이 결정한다.
- **XSS**: 사용자가 보낸 제목과 본문은 `st.write`로 텍스트로 보여 준다. `st.markdown(..., unsafe_allow_html=True)`에 사용자 문자열을 넣지 않는다.
- **CSRF**: API 인증이 `Authorization` 헤더이면 브라우저가 그 헤더를 다른 사이트 대신 자동으로 붙이지 않는다. 토큰을 쿠키로 옮기는 순간 `SameSite`와 CSRF 토큰을 따로 설계한다. 이 과정은 Bearer와 세션 키를 유지한다.
- **로그아웃**: 세션의 `token`을 빈 문자열로 지운다. 쿠키 방식 서버라면 `POST /api/auth/logout`으로 204를 받는다.

### 비유

세션 키 `token`은 계산대 서랍 속 출입증이다. 손님 브라우저에는 출입증 사본을 적어두지 않는다. 창고(API)가 출입증을 검사해 작성자를 가린다. 계산대가 수정 버튼을 가리는 일은 안내일 뿐이고, 창고의 403이 실제 자물쇠다. 비밀번호 원문은 창구에서 잠깐 받아 창고로 넘기고, 장부에는 창고가 만든 해시만 남는다.

## ③ 🛠️ 실기

`lib/passwords.py`

```python
import hashlib
import hmac
import os


def hash_password(password: str, salt: bytes | None = None) -> str:
    """이 앱이 사용자 파일을 직접 저장할 때만 사용한다. API 가입 요청에는 쓰지 않는다."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, _digest_hex = stored.split(":", 1)
    candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, stored)
```

`lib/auth_api.py`

```python
from lib.api_client import request_json


def signup(email: str, password: str, nickname: str) -> dict:
    return request_json(
        "POST",
        "/api/auth/signup",
        json_body={"email": email, "password": password, "nickname": nickname},
    )


def login(email: str, password: str) -> dict:
    return request_json(
        "POST",
        "/api/auth/login",
        json_body={"email": email, "password": password},
    )


def me() -> dict:
    return request_json("GET", "/api/auth/me")
```

`app.py`에서 로그인 폼과 권한 표시만 발췌해 전체로 적으면 아래와 같다. `list_posts`는 study6 클라이언트를 그대로 쓴다.

```python
import streamlit as st

from lib.api_client import ApiError, delete_post, list_posts
from lib.auth_api import login, me, signup
from lib.passwords import hash_password, verify_password

st.set_page_config(page_title="로그인", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = ""
if "me" not in st.session_state:
    st.session_state.me = None


def pull_me() -> None:
    try:
        payload = me()
    except ApiError as exc:
        st.session_state.token = ""
        st.session_state.me = None
        st.error(exc.message)
        return
    st.session_state.me = payload.get("data")


def on_signup() -> None:
    try:
        signup(
            st.session_state.su_email.strip(),
            st.session_state.su_password,
            st.session_state.su_nickname.strip(),
        )
        st.session_state.notice = "가입했습니다. 로그인해 주세요."
    except ApiError as exc:
        st.session_state.notice = exc.message


def on_login() -> None:
    try:
        payload = login(st.session_state.li_email.strip(), st.session_state.li_password)
    except ApiError as exc:
        st.session_state.notice = exc.message
        return
    data = payload.get("data") or {}
    st.session_state.token = data.get("accessToken") or ""
    st.session_state.me = data.get("user")
    st.session_state.notice = "로그인했습니다."


st.title("계정")
if st.session_state.token and st.session_state.me is None:
    pull_me()

user = st.session_state.me
if user:
    st.write(f"{user.get('nickname')} 님")
    if st.button("로그아웃"):
        st.session_state.token = ""
        st.session_state.me = None
        st.rerun()
else:
    with st.form("signup"):
        st.text_input("이메일", key="su_email")
        st.text_input("닉네임", key="su_nickname")
        st.text_input("비밀번호", type="password", key="su_password")
        st.form_submit_button("가입", on_click=on_signup)
    with st.form("login"):
        st.text_input("이메일", key="li_email")
        st.text_input("비밀번호", type="password", key="li_password")
        st.form_submit_button("로그인", on_click=on_login)

if st.session_state.get("notice"):
    st.info(st.session_state.notice)

st.divider()
st.caption("아래 해시는 API로 나가지 않는 로컬 저장 예시입니다.")
sample = hash_password("password123")
st.code(sample.split(":")[0] + ":(digest 생략)")
st.write("검증 함수 준비됨" if verify_password("password123", sample) else "검증 실패")

if user:
    try:
        listed = list_posts(1, "")
    except ApiError as exc:
        st.error(exc.message)
        listed = {"data": []}
    for post in listed.get("data") or []:
        st.subheader(post["title"])
        st.write(post.get("body") or "")
        author = post.get("author") or {}
        if author.get("id") == user.get("id"):
            if st.button("내 글 삭제", key=f"mine_{post['id']}"):
                try:
                    delete_post(int(post["id"]))
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.message)
```

로컬 해시 예시는 화면에 salt만 보여주고 digest는 생략한다. `verify_password`가 참이면 라운드트립이 된 것이다. 가입 폼의 비밀번호는 `hash_password`를 거치지 않고 `signup`으로 전달된다.

### 줄별 설명

- `hash_password`: 16바이트 salt와 PBKDF2-HMAC-SHA256 20만 회를 쓴다. 저장 형식은 `salt_hex:digest_hex`다.
- `verify_password`: 저장된 salt로 다시 해시하고 `hmac.compare_digest`로 비교한다. 일반 `==`보다 비교 시간 차이를 줄인다.
- `signup` / `login`: 스펙 경로와 camelCase가 아닌 스펙에 적힌 필드 이름 `email`, `password`, `nickname`을 보낸다. 이 세 필드는 스펙의 요청 예시 그대로다.
- `on_login`: `accessToken`만 세션에 넣는다. 비밀번호 키는 다음 폼 제출 전까지 위젯 키에 남을 수 있으므로 성공 로그에 비밀번호를 찍지 않는다.
- `pull_me`: 토큰만 있고 사용자 객체가 없을 때 `/api/auth/me`로 채운다. 401이면 토큰을 지운다.
- 작성자 버튼: `author.id`와 `me.id`가 같을 때만 그린다. `delete_post`가 403을 주면 `st.error`가 서버 문장을 표시한다.
- `st.write(post.get("body") or "")`: 본문을 텍스트로 출력한다. HTML 허용 옵션을 주지 않는다.
- 로그아웃: 세션의 토큰과 내 정보를 비우고 `st.rerun()`으로 게스트 화면을 다시 그린다.

## ④ 🔗 연동 포인트

- 프론트와 백엔드의 로그인 공유는 `st.session_state.token` → `Authorization: Bearer` → API다. 브라우저 저장소에는 토큰을 복사하지 않는다.
- 같은 세션을 쓰는 모든 페이지(`pages/`의 작성·수정)가 `lib/api_client._headers`를 통하면 토큰을 페이지마다 다시 저장하지 않는다.
- 401은 로그인 폼을 다시 보여주는 신호다. 403은 로그인한 사용자에게 서버 문장만 보여 주는 신호다.
- 로컬 `hash_password`는 study11에서 SQLite 사용자 테이블을 직접 만들 때 `password_hash` 컬럼에 저장하는 함수로 재사용한다. API 가입과 동시에 쓰지 않는다.
- OAuth 소셜 로그인은 이 단원의 비밀번호 로그인과 별도로 study13의 `st.login`이 붙인다.

## ⑤ 오류 노트

### 가입했는데 로그인 문장이 이메일 오류와 비밀번호 오류로 나뉜다

- 증상: "없는 이메일"과 "틀린 비밀번호"가 다른 문장으로 보인다.
- 원인: 화면이 상태 코드를 해석해 힌트를 추가했다.
- 해결: 401의 `error.message`만 보여 준다. 스펙의 로그인 실패 코드는 `INVALID_CREDENTIALS`다.

### 해시된 비밀번호를 가입 API에 보냈다

- 증상: 가입은 201인데 같은 비밀번호 로그인이 401이다.
- 원인: 클라이언트가 PBKDF2 결과를 `password` 필드에 넣었고, 서버가 그 문자열을 다시 해시했다.
- 해결: API 로그인·가입의 `password`는 사용자가 입력한 원문이다. 해시는 서버 저장 컬럼에만 존재한다.

### 본문에 HTML이 실행된다

- 증상: 글 본문의 태그가 버튼이나 스크립트처럼 동작한다.
- 원인: `unsafe_allow_html=True`에 사용자 본문을 넘겼다.
- 해결: `st.write` 또는 기본 `st.markdown`으로 출력한다.

### 새로고침하면 로그인이 풀린다

- 증상: 새로고침 후 게스트 화면이다.
- 원인: 토큰을 지역 변수에만 두었거나, 세션 초기화가 매 실행마다 토큰을 빈 문자열로 덮었다.
- 해결: `if "token" not in st.session_state`일 때만 초기화한다. 브라우저를 완전히 닫으면 세션이 끝나는 것은 정상이다. 더 긴 유지는 서버의 토큰 만료 시간(학습용 최대 7일) 안에서 세션이 살아 있을 때 성립한다.

## ⑥ 직접 해보기

1. 같은 이메일로 가입을 두 번 해 409 문장이 `st.info` 또는 오류 자리에 보이는지 확인한다.
2. 다른 작성자의 글에 수정 버튼이 없는지 보고, 그 id로 `delete_post`를 임시 버튼에 연결해 403 `FORBIDDEN` 문장을 확인한 뒤 임시 버튼을 제거한다.
3. `verify_password("틀린값", sample)`이 거짓인지 출력 문장으로 확인한다. digest 전체는 화면에 남기지 않는다.

## ⑦ ☐ 체크리스트

- [ ] 회원가입 `POST /api/auth/signup`과 로그인 `POST /api/auth/login`을 호출한다.
- [ ] `accessToken`을 `st.session_state.token`에만 둔다.
- [ ] `GET /api/auth/me`로 로그인 사용자를 확인하고, 401이면 토큰을 지운다.
- [ ] 작성자 id가 같을 때만 삭제 버튼을 그리고, 403은 서버 문장으로 받는다.
- [ ] API로 보내는 비밀번호는 원문이고, 로컬 저장 예시는 PBKDF2 해시만 남긴다.
- [ ] 사용자 본문을 `unsafe_allow_html=True`로 렌더링하지 않는다.
- [ ] Bearer 세션 방식이라 브라우저가 API에 쿠키를 자동 첨부하지 않는다는 점을 설명할 수 있다.

## ⑧ 다음 단계

인증이 세션과 API 헤더로 이어졌으면, study8은 페이지·클라이언트·설정을 폴더로 나눠 개발 설정과 운영 설정이 같은 코드를 다르게 주입하게 정리한다.
