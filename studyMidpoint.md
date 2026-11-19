# studyMidpoint. 기초만으로 만드는 작은 게시판

## ① 목표

study0부터 study10까지 배운 Streamlit만으로, 로그인과 게시글 CRUD가 되는 작은 게시판을 한 앱으로 조립한다.

## ② 📖 이론

### 왜 쓰는지

단원마다 나뉜 예제는 한 가지 기술만 보여 준다. 작은 서비스는 그 기술을 한 입구, 한 설정, 한 API 클라이언트로 묶었을 때 비로소 화면이 된다. 이 조립에는 study11 이후의 DB 교체, 캐시, 외부 결제, AI를 넣지 않는다.

### 핵심 개념

재실행, 세션의 토큰, `pages/` 라우팅, 폼 검증, 스펙 v1 클라이언트, 개발·운영 설정, 배포 점검이 한 폴더 안에 있다.

### 비유

기초 단원은 부품이고 이 문서는 조립 설명서다. 새 부품 서랍은 열지 않는다. 계산대(Streamlit)와 창고(공통 API) 사이의 주문서만 이어 붙인다.

## ③ 🛠️ 실기

### 기능 목록

- 이메일·비밀번호·닉네임으로 가입하고 로그인한다.
- 액세스 토큰은 `st.session_state.token`에만 둔다.
- 목록은 `q`, `page`, `limit` 10, `sort=-createdAt`으로 가져온다.
- 상세는 `id` 쿼리로 `GET /api/posts/{id}`를 연다.
- 작성은 화면에서 1~200자 제목과 본문을 검사한 뒤 POST한다.
- 작성자 본인만 수정·삭제 버튼을 보고, 서버의 403을 그대로 표시한다.
- 오류는 `error.message`와 `error.fields`만 화면에 낸다.
- 로그아웃은 세션의 토큰과 내 정보를 지운다.

### 폴더 구조

```text
midpoint/
├── app.py
├── pages/
│   ├── list_page.py
│   ├── detail_page.py
│   └── write_page.py
├── lib/
│   ├── __init__.py
│   ├── settings.py
│   ├── api_client.py
│   ├── auth_api.py
│   ├── validate.py
│   └── ui.py
├── .streamlit/config.toml
├── .env.example
├── requirements.txt
└── Dockerfile
```

각 파일의 내용은 study6, study7, study8의 최종 형태를 이 폴더에 모은 것이다. 아래는 입구와 목록·상세·작성의 전체다. `lib`은 study8의 `settings.py`, `ui.py`, study6의 클라이언트, study7의 `auth_api.py`, study5의 `validate_post`를 그대로 둔다.

### 단계별 구현 순서

1. study0 절차로 `midpoint` 가상환경을 만들고 `streamlit==1.67.0`, `python-dotenv`, `requests`를 설치한다.
2. `.gitignore`와 `.env.example`을 두고 `API_BASE_URL`을 채운다.
3. `lib/settings.py`와 `lib/api_client.py`를 넣어 목록 GET만 되는 페이지를 확인한다.
4. `lib/auth_api.py`와 로그인 폼을 `app.py` 공통 영역에 넣어 토큰이 세션에 남는지 확인한다.
5. `pages/write_page.py`에 검증과 POST를 연결한다.
6. `pages/detail_page.py`에 `id` 검사, 수정 PATCH, 삭제 DELETE를 연결한다.
7. `st.navigation`으로 세 페이지를 등록한다.
8. study9의 검증 테스트와 목록 mock 테스트를 `tests/`에 복사해 `pytest -q`를 통과시킨다.
9. study10 Dockerfile로 이미지를 만들고 배포 점검표를 수행한다.

### 전체 코드

`app.py`

```python
import streamlit as st

from lib.api_client import ApiError
from lib.auth_api import login, me, signup
from lib.ui import show_error

st.set_page_config(page_title="작은 게시판", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = ""
if "me" not in st.session_state:
    st.session_state.me = None
if "notice" not in st.session_state:
    st.session_state.notice = ""


def on_signup() -> None:
    try:
        signup(st.session_state.su_email.strip(), st.session_state.su_password, st.session_state.su_nickname.strip())
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


def render_account() -> None:
    if st.session_state.token and st.session_state.me is None:
        try:
            st.session_state.me = (me().get("data"))
        except ApiError as exc:
            st.session_state.token = ""
            show_error(exc)
    user = st.session_state.me
    if user:
        st.sidebar.write(f"{user.get('nickname')} 님")
        if st.sidebar.button("로그아웃"):
            st.session_state.token = ""
            st.session_state.me = None
            st.rerun()
        return
    with st.sidebar.form("signup"):
        st.text_input("이메일", key="su_email")
        st.text_input("닉네임", key="su_nickname")
        st.text_input("비밀번호", type="password", key="su_password")
        st.form_submit_button("가입", on_click=on_signup)
    with st.sidebar.form("login"):
        st.text_input("이메일", key="li_email")
        st.text_input("비밀번호", type="password", key="li_password")
        st.form_submit_button("로그인", on_click=on_login)
    if st.session_state.notice:
        st.sidebar.info(st.session_state.notice)


render_account()
st.title("작은 게시판")
page = st.navigation(
    [
        st.Page("pages/list_page.py", title="목록", icon="📋", default=True),
        st.Page("pages/detail_page.py", title="상세", icon="📄"),
        st.Page("pages/write_page.py", title="작성", icon="✍️"),
    ]
)
page.run()
```

`pages/list_page.py`

```python
import streamlit as st

from lib.api_client import ApiError, list_posts
from lib.ui import show_error


def render() -> None:
    st.header("목록")
    q = st.text_input("검색", value=st.query_params.get("q", ""))
    page_raw = st.query_params.get("page", "1")
    page = int(page_raw) if str(page_raw).isdigit() else 1
    if st.button("검색"):
        st.query_params["q"] = q
        st.query_params["page"] = "1"
        st.rerun()
    try:
        payload = list_posts(page, st.query_params.get("q", ""))
    except ApiError as exc:
        show_error(exc)
        return
    meta = payload.get("meta") or {}
    st.caption(f"{meta.get('page', 1)} / {meta.get('totalPages', 1)}")
    for post in payload.get("data") or []:
        st.subheader(post["title"])
        st.write(post.get("body") or "")
        if st.button("열기", key=f"open_{post['id']}"):
            st.query_params["id"] = str(post["id"])
            st.switch_page("pages/detail_page.py")


render()
```

`pages/detail_page.py`

```python
import streamlit as st

from lib.api_client import ApiError, delete_post, get_post, update_post
from lib.ui import show_error
from lib.validate import validate_post


def render() -> None:
    raw_id = st.query_params.get("id")
    if raw_id is None or not str(raw_id).isdigit():
        st.error("글 번호가 올바르지 않습니다.")
        st.stop()
    try:
        data = (get_post(int(raw_id)).get("data")) or {}
    except ApiError as exc:
        show_error(exc)
        return
    st.header(data.get("title") or "")
    st.write(data.get("body") or "")
    author = data.get("author") or {}
    me = st.session_state.get("me") or {}
    if not me or author.get("id") != me.get("id"):
        return
    with st.form("edit"):
        title = st.text_input("제목", value=data.get("title") or "")
        body = st.text_area("본문", value=data.get("body") or "")
        submitted = st.form_submit_button("수정")
    if submitted:
        fields = validate_post(title.strip(), body.strip())
        if fields:
            show_error(ApiError(400, {"error": {"message": "입력값을 확인하세요.", "fields": fields}}))
            return
        try:
            update_post(int(raw_id), title.strip(), body.strip())
        except ApiError as exc:
            show_error(exc)
            return
        st.success("수정 완료")
    if st.button("삭제"):
        try:
            delete_post(int(raw_id))
        except ApiError as exc:
            show_error(exc)
            return
        st.query_params.clear()
        st.switch_page("pages/list_page.py")


render()
```

`pages/write_page.py`는 study8의 작성 페이지와 같다. `lib` 파일은 study5~study8의 최종 코드를 이 폴더로 옮긴다.

### 줄별 설명

- `render_account`: 사이드바에 가입·로그인을 두어 모든 페이지가 같은 세션 토큰을 본다.
- `on_login`: `accessToken`과 `user`를 세션에 넣는다. 비밀번호는 로그에 남기지 않는다.
- `me()` 재조회: 새로고침 뒤 토큰만 남고 사용자 객체가 비었을 때 `/api/auth/me`로 채운다. 401이면 토큰을 지운다.
- `st.navigation`: `pages/`의 세 파일을 메뉴로 등록한다. 자동 탐색과 중복으로 쓰지 않는다.
- 목록의 `page` 쿼리: 숫자가 아니면 1로 본다.
- 열기 버튼: 상세가 읽을 `id`를 쿼리에 넣고 `st.switch_page`한다.
- 상세의 `st.stop()`: 잘못된 id면 수정 폼을 그리지 않는다.
- 작성자 비교: 화면 버튼의 조건이다. `update_post`와 `delete_post`의 403은 `show_error`가 담당한다.
- 삭제 성공: 쿼리를 지우고 목록 페이지로 이동해 새 GET을 유도한다.

## ④ 🔗 연동 포인트

### DB·API 연동 구성도

```text
브라우저
  │  WebSocket, 세션 쿠키(Streamlit 세션)
  ▼
Streamlit (midpoint/app.py, pages/)
  │  st.session_state.token
  │  requests  Authorization: Bearer
  │  API_BASE_URL  (development=.env / production=프로세스 환경변수)
  ▼
공통 API 스펙 v1
  POST /api/auth/signup
  POST /api/auth/login
  GET  /api/auth/me
  GET  /api/posts?q&page&limit&sort
  GET  /api/posts/{id}
  POST /api/posts
  PATCH /api/posts/{id}
  DELETE /api/posts/{id}
  │
  ▼
API 서버가 소유한 DB
```

Streamlit 프로세스는 DB 비밀번호를 갖지 않는다. 글의 원본은 API 뒤의 DB이고, 이 앱의 디스크에는 시크릿 파일을 제외한 학습 데이터를 남기지 않는다.

### 1차 배포 체크리스트

- [ ] `pytest -q`가 가짜 API로 통과한다.
- [ ] `.env`가 이미지에 없다.
- [ ] `APP_ENV=production`과 운영 `API_BASE_URL`이 프로세스에 있다.
- [ ] HTTPS 도메인으로 목록이 열린다.
- [ ] 가입, 로그인, 작성, 본인 수정, 본인 삭제, 로그아웃을 한 번씩 수행했다.
- [ ] 빈 제목은 400 계열 문장으로 남고 글이 만들어지지 않는다.
- [ ] 다른 작성자 삭제 시도는 403 문장이다.
- [ ] 로그에 비밀번호와 토큰이 없다.

## ⑤ 오류 노트

### 사이드바 로그인 후 목록이 401이다

- 증상: 로그인 문구는 있는데 목록이 인증 오류다.
- 원인: 토큰을 사이드바 지역 변수에만 두었거나, 목록 페이지가 다른 키를 읽는다.
- 해결: 키 이름을 `token` 하나로 통일하고 `lib/api_client._headers`만 헤더를 만든다.

### 상세 수정 폼이 매 글자마다 API를 호출하는 것처럼 느리다

- 증상: 제목을 고치는 동안 오류가 나거나 값이 튄다.
- 원인: 폼 밖에서 PATCH를 호출하거나, `value=`와 세션 키를 동시에 같은 필드에 물렸다.
- 해결: PATCH는 `form_submit_button`이 참인 실행에서만 호출한다.

### 배포 점검에서만 검색이 빈 목록이다

- 증상: 로컬은 되는데 운영 목록이 항상 비어 있다.
- 원인: 운영 `API_BASE_URL`이 다른 환경의 빈 데이터베이스를 가리킨다.
- 해결: `/health`와 `GET /api/posts`를 그 주소로 직접 확인해 앱 코드와 데이터를 분리해서 본다.

## ⑥ 직접 해보기

1. 기능 목록의 여덟 줄을 체크하면서 가입부터 로그아웃까지 한 번에 진행한다.
2. `API_BASE_URL`만 다른 v1 서버로 바꿔 화면 코드를 수정하지 않고 목록이 바뀌는지 확인한다.
3. 1차 배포 체크리스트를 로컬 Docker에 대해 수행하고, 막힌 칸의 증상과 해결을 오류 노트에 한 줄 추가한다.

## ⑦ ☐ 체크리스트

- [ ] 기능 목록의 가입, 로그인, 목록, 상세, 작성, 수정, 삭제, 로그아웃이 한 앱에 있다.
- [ ] 사용한 기법은 study0~study10 안에 있다.
- [ ] 폴더가 `app.py`, `pages/`, `lib/`로 나뉘고 페이지에 호스트 문자열이 없다.
- [ ] 구성도의 Bearer와 `API_BASE_URL`이 실제 코드와 같다.
- [ ] 1차 배포 체크리스트를 수행했다.
- [ ] 회고에 막힌 지점과 다음 심화에서 다룰 거리를 적었다.

## 회고

기초 조립에서 자주 막히는 지점은 토큰 키의 불일치와 폼 밖의 성급한 PATCH다. 화면이 버튼으로 권한을 숨겨도 서버 403을 처리하지 않으면 점검표가 실패한다. DB를 앱이 직접 소유하지 않았으므로 저장소 교체는 아직 없다. 그 작업은 study11에서 연결 문자열부터 시작한다. 캐시와 통계 화면, 파일 업로드와 AI 요약은 이 조립에 넣지 않았다.

## ⑧ 다음 단계

작은 게시판이 스펙 v1 위에서 동작하면, study11부터는 같은 Streamlit 앱이 DB를 직접 바꿀 수 있게 연결을 확장한다.
