# study6. DB와 API 연동

## ① 목표

공통 API 스펙 v1의 `/api/posts`를 `requests`로 호출해 목록, 상세, 등록, 수정, 삭제를 만들고, 주소는 환경변수로 분리한다.

## ② 📖 이론

### 왜 쓰는지

Streamlit 화면에 글을 직접 파일로만 쌓으면 다른 화면과 글을 공유하기 어렵다. 게시판의 원본은 API 뒤의 DB다. 이 단원의 Streamlit은 DB 드라이버를 직접 열지 않고, HTTP로 명세된 자원만 다룬다. DB 종류를 바꾸는 설정은 study11에서 앱이 저장을 직접 가질 때 다룬다.

공통 스펙의 출처는 노션 페이지 [HTTP · REST · API 설계](https://app.notion.com/p/3d6d7dec5e2e8139adbfd36dd506c65e)다. Streamlit 페이지는 이 `/api/posts`를 그대로 호출하고, 오류의 `error.message`를 `st.error`로 보여 달라고 적는다.

### 핵심 개념

- **베이스 URL**: `API_BASE_URL`. 코드에 호스트를 고정하지 않는다. 끝의 `/`는 호출 직전에 제거한다.
- **자원**: `GET/POST /api/posts`, `GET/PATCH/DELETE /api/posts/{id}`.
- **목록 응답**: `data` 배열과 `meta`(`page`, `limit`, `total`, `totalPages`, `q`).
- **단건 응답**: `data` 객체. 필드는 `id`, `title`, `body`, `tags`, `author`, `commentCount`, `createdAt`, `updatedAt`.
- **작성 본문**: `title`, `body`, `tags`. 성공 201. 스케치에 보이던 `content` 키는 쓰지 않는다.
- **삭제**: 성공 204, 본문 없음.
- **오류**: 4xx·5xx는 `error.code`, `error.message`, 필요하면 `error.fields`.
- **시간 초과와 연결 실패**: 예외를 화면의 `error.message`로 바꾼다.

### 비유

Streamlit은 계산대이고 API는 창고다. 계산대는 창고 선반(DB 테이블)을 직접 열지 않고 주문서만 넣는다. 창고 주소는 벽의 환경변수에 붙어 있어, 매장을 옮겨도 계산대 프로그램을 고치지 않는다. 창고가 거절 전표를 주면 계산대는 전표의 `message`만 손님에게 읽어 준다.

## ③ 🛠️ 실기

### 연결 설정

`.env`

```text
API_BASE_URL=http://localhost:8000
```

`requirements.txt`에 `requests`를 추가한다.

```text
streamlit==1.67.0
python-dotenv==1.1.1
requests==2.32.5
```

서버는 스펙 v1을 구현한 백엔드를 `http://localhost:8000`에 띄운 상태로 둔다. 이 저장소는 그 서버를 포함하지 않는다. 서버가 꺼져 있으면 목록 자리에 연결 오류 문장이 나온다.

### 전체 코드

`lib/api_client.py`

```python
import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class ApiError(Exception):
    def __init__(self, status: int, payload: dict):
        self.status = status
        self.payload = payload
        error = payload.get("error") or {}
        self.message = error.get("message") or f"요청 실패 ({status})"
        super().__init__(self.message)


def _base() -> str:
    raw = os.getenv("API_BASE_URL", "").rstrip("/")
    if not raw:
        raise ApiError(0, {"error": {"code": "CONFIG", "message": "API_BASE_URL이 없습니다."}})
    return raw


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    token = st.session_state.get("token", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request_json(method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> Any:
    try:
        response = requests.request(
            method,
            _base() + path,
            headers=_headers(),
            json=json_body,
            params=params,
            timeout=5,
        )
    except requests.RequestException:
        raise ApiError(0, {"error": {"code": "NETWORK", "message": "API 서버에 연결하지 못했습니다."}}) from None
    if response.status_code == 204:
        return None
    try:
        payload = response.json() if response.content else {}
    except ValueError:
        raise ApiError(response.status_code, {"error": {"code": "BAD_RESPONSE", "message": "JSON이 아닌 응답입니다."}}) from None
    if not response.ok:
        raise ApiError(response.status_code, payload if isinstance(payload, dict) else {})
    return payload


def list_posts(page: int, q: str) -> dict:
    return request_json("GET", "/api/posts", params={"page": page, "limit": 10, "q": q, "sort": "-createdAt"})


def get_post(post_id: int) -> dict:
    return request_json("GET", f"/api/posts/{post_id}")


def create_post(title: str, body: str, tags: list[str]) -> dict:
    return request_json("POST", "/api/posts", json_body={"title": title, "body": body, "tags": tags})


def update_post(post_id: int, title: str, body: str) -> dict:
    return request_json("PATCH", f"/api/posts/{post_id}", json_body={"title": title, "body": body})


def delete_post(post_id: int) -> None:
    request_json("DELETE", f"/api/posts/{post_id}")
```

`app.py`

```python
import streamlit as st

from lib.api_client import ApiError, create_post, delete_post, get_post, list_posts, update_post

st.set_page_config(page_title="게시판", layout="centered")

if "token" not in st.session_state:
    st.session_state.token = ""
if "page" not in st.session_state:
    st.session_state.page = 1


def show_error(exc: ApiError) -> None:
    st.error(exc.message)
    fields = (exc.payload.get("error") or {}).get("fields") or {}
    for name, messages in fields.items():
        st.caption(f"{name}: {', '.join(messages)}")


st.title("게시판")
st.session_state.token = st.text_input("액세스 토큰", value=st.session_state.token, type="password")
q = st.text_input("검색", value=st.query_params.get("q", ""))
if st.button("검색"):
    st.query_params["q"] = q
    st.session_state.page = 1

try:
    listed = list_posts(st.session_state.page, st.query_params.get("q", ""))
except ApiError as exc:
    show_error(exc)
    st.stop()

meta = listed.get("meta") or {}
st.caption(f"{meta.get('page', 1)} / {meta.get('totalPages', 1)} 페이지, 총 {meta.get('total', 0)}건")
for post in listed.get("data") or []:
    st.subheader(post["title"])
    st.write(post.get("body") or "")
    st.caption(post.get("createdAt", ""))
    if st.button("상세 새로고침", key=f"detail_{post['id']}"):
        try:
            detail = get_post(int(post["id"]))
            st.json(detail.get("data"))
        except ApiError as exc:
            show_error(exc)
    if st.button("삭제", key=f"del_{post['id']}"):
        try:
            delete_post(int(post["id"]))
            st.success("삭제했습니다.")
        except ApiError as exc:
            show_error(exc)

with st.form("new"):
    title = st.text_input("제목")
    body = st.text_area("본문")
    submitted = st.form_submit_button("작성")
if submitted:
    try:
        created = create_post(title.strip(), body.strip(), [])
        st.success("작성 완료")
        st.write(created.get("data", {}).get("id"))
    except ApiError as exc:
        show_error(exc)

with st.form("edit"):
    edit_id = st.number_input("수정할 id", min_value=1, step=1)
    edit_title = st.text_input("새 제목")
    edit_body = st.text_area("새 본문")
    edit_submitted = st.form_submit_button("수정")
if edit_submitted:
    try:
        updated = update_post(int(edit_id), edit_title.strip(), edit_body.strip())
        st.success("수정 완료")
        st.write(updated.get("data", {}).get("title"))
    except ApiError as exc:
        show_error(exc)
```

### 줄별 설명

`lib/api_client.py`

- `ApiError`: 상태 코드, 원본 JSON, 화면용 문장을 한 예외로 모은다.
- `_base`: 환경변수가 없거나 끝 슬래시가 중복되지 않게 주소를 만든다.
- `_headers`: JSON 헤더를 항상 넣고, 세션에 토큰이 있을 때만 Bearer를 붙인다.
- `requests.request`: 메서드와 경로를 한 함수로 보낸다. `timeout=5`는 매 호출에 둔다.
- 204: 본문이 없으므로 `None`을 반환한다. 삭제가 이 경로다.
- `response.ok`가 거짓이면 `ApiError`다. 200, 201만 호출자에게 JSON으로 돌아간다.
- `list_posts`: `page`, `limit` 10, `q`, `sort=-createdAt`. limit 상한 50은 서버가 지킨다.
- `create_post`: JSON 키 `title`, `body`, `tags`.
- `update_post`: PATCH로 제목과 본문만 보낸다.
- `delete_post`: 반환값 없이 204를 확인한다.

`app.py`

- 토큰 입력은 `type="password"`라 화면에서 가려진다. 값은 세션에 남고 study7의 로그인 결과로 대체된다.
- 검색 버튼이 `q` 쿼리와 페이지 번호 1을 맞춘다.
- `list_posts`가 실패하면 `st.error` 후 `st.stop()`이라 빈 목록을 성공처럼 그리지 않는다.
- `meta` 캡션은 페이지네이션 정보를 스펙 키 그대로 보여 준다.
- 목록 항목은 `title`, `body`, `createdAt`을 출력한다.
- 상세 버튼은 `GET /api/posts/{id}` 결과를 `st.json`으로 확인한다.
- 삭제 버튼은 204가 예외 없이 끝나면 성공 문장을 보여 준다.
- 작성 폼은 study5의 요청 본문과 같다. 성공 시 "작성 완료"를 보여 준다.
- 수정 폼은 id와 바꿀 필드만 PATCH한다.

노션 최소 코드는 한 파일에서 작성과 목록을 보여 준다. 이 단원은 그 흐름을 유지하면서 클라이언트를 `lib/api_client.py`로 분리하고, 상세·수정·삭제와 스펙 필드를 보탰다.

## ④ 🔗 연동 포인트

```text
브라우저 ──WebSocket── Streamlit 서버
                         │  requests + API_BASE_URL
                         ▼
                    GET/POST/PATCH/DELETE /api/posts
                         │
                         ▼
                    공통 API 스펙 v1을 구현한 백엔드 ── DB
```

- 브라우저가 API를 직접 부르지 않는다. `requests`는 Streamlit 서버 프로세스에서 실행된다. 따라서 이 호출에는 브라우저 CORS가 적용되지 않는다. CORS가 필요한 경우는 브라우저 안에서 다른 출처를 부르는 컴포넌트를 쓸 때이며 study7에서 구분한다.
- 환경변수 `API_BASE_URL`만 바꾸면 같은 화면이 다른 호스트의 v1 서버를 본다.
- 토큰 칸은 study7이 `POST /api/auth/login`의 `data.accessToken`으로 채운다.
- 목록의 `meta`는 study14에서 이전·다음 버튼과 문서화 표로 확장한다.
- 캐시로 목록 GET을 감싸는 일은 study15의 `st.cache_data`가 담당한다. 이 단원은 매 재실행마다 서버 값을 다시 읽어 학습 중 최신 글을 보게 한다.

## ⑤ 오류 노트

### `API_BASE_URL이 없습니다.`

- 증상: 목록 자리에 설정 오류가 나온다.
- 원인: `.env`가 없거나 키가 다르다.
- 해결: `.env.example`을 복사해 `API_BASE_URL`을 넣고 Streamlit을 다시 실행한다. `load_dotenv()`는 프로세스 시작 시점에 읽는다.

### 연결 오류 문장만 보인다

- 증상: `API 서버에 연결하지 못했습니다.`
- 원인: 8000 포트에 서버가 없거나 주소가 틀렸다.
- 해결: 브라우저나 `curl http://localhost:8000/health`로 `{ "status": "ok" }`를 확인한 뒤 Streamlit을 재실행한다.

### 작성 직후 `error.message`에 인증 문장이 나온다

- 증상: 목록은 보이는데 작성만 401 `UNAUTHORIZED`다.
- 원인: POST는 스펙상 인증이 필요하다. 토큰 칸이 비어 있다.
- 해결: 학습 서버에서 발급한 액세스 토큰을 칸에 넣거나 study7 로그인으로 세션 토큰을 채운다. 빈 토큰으로 글을 만들지 않는다.

### 삭제했는데 목록에 그대로다

- 증상: 성공 문장 뒤에도 같은 제목이 보인다.
- 원인: 삭제 요청은 끝났지만 아래 목록이 그 실행에서 이미 그려졌다.
- 해결: 삭제 성공 직후 `st.rerun()`을 호출해 목록 GET부터 다시 실행한다.

### 본문을 `content`로 보내 400이 난다

- 증상: 서버 `fields`에 본문 관련 검증 오류가 있다.
- 원인: 스케치의 `content` 키를 그대로 보냈다.
- 해결: JSON 키를 `body`로 보낸다.

## ⑥ 직접 해보기

1. 서버를 끈 상태에서 앱을 열어 연결 오류가 `st.error`로만 보이는지 확인한다.
2. 서버를 켠 뒤 검색어 `q`를 넣고 목록 `meta.q`와 주소의 `q`가 같은지 확인한다.
3. 토큰 없이 작성을 시도해 401 문장을 보고, 토큰을 넣은 뒤 201에 해당하는 성공 흐름으로 글 id가 보이는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 백엔드(FastAPI 등) 게시판 API를 `requests` 로 호출해 목록·작성·삭제 화면
- [ ] `API_BASE_URL`을 환경변수로 두었고 코드에 호스트를 고정하지 않았다.
- [ ] 모델에 해당하는 화면 필드를 스펙의 `title`, `body`, `tags`, `author`, `createdAt`으로 맞췄다.
- [ ] 목록 GET, 상세 GET, 등록 POST, 수정 PATCH, 삭제 DELETE를 각각 호출한다.
- [ ] 오류는 `error.message`를 `st.error`로 보여 준다.
- [ ] 204 삭제는 본문이 없어도 성공으로 처리한다.
- [ ] 목록은 `data`와 `meta`를 함께 읽는다.

## ⑧ 다음 단계

CRUD가 토큰 칸에 의존하기 시작했으니, study7은 회원가입과 로그인으로 그 칸을 채우고 권한·해시·CORS·XSS·CSRF를 Streamlit 서버 기준으로 정리한다.
