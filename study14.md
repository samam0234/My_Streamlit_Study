# study14. API 설계

## ① 목표

Streamlit 클라이언트가 따르는 REST 규칙, OpenAPI 문서, 버전 접두어, 페이지네이션, 오류 본문 형식을 한 모듈에 고정한다.

## ② 📖 이론

### 왜 쓰는지

화면이 경로 문자열을 제각각 만들면 `page`가 0부터인지 1부터인지부터 어긋난다. 설계 단원은 새 화면을 추가하기 전에 클라이언트의 계약을 코드와 표로 고정하는 일이다. 기준은 공통 API 스펙 v1이다. 서버의 OpenAPI는 `/api-docs`에서 확인하고, 화면은 그 문서와 같은 경로만 호출한다.

### 핵심 개념

- **자원 이름**: 복수 명사와 소문자. `/api/posts`, `/api/posts/{id}`. 동사 경로는 쓰지 않는다.
- **메서드**: 목록·상세는 GET, 작성은 POST, 수정은 PATCH, 삭제는 DELETE.
- **버전**: 스펙의 베이스는 `/api`다. 접두어를 `API_PREFIX` 상수 한 곳에 두어, 서버가 버전 경로를 바꾸면 클라이언트는 그 상수만 고친다.
- **페이지**: `page`는 1부터, `limit` 기본 10, 상한 50. 응답 `meta.totalPages`로 이전·다음을 계산한다.
- **오류**: `error.code`, `error.message`, 선택적 `error.fields`, `error.requestId`. 화면은 표에 적힌 코드만 분기로 다룬다.
- **문서**: 서버의 OpenAPI JSON을 읽어 경로 목록을 화면에 보여 주고, 클라이언트가 호출하는 경로가 그 목록에 있는지 대조한다.

### 비유

`API_PREFIX`와 경로 함수는 주문서 양식 서랍이다. 점원은 서랍 밖의 즉석 주소를 만들지 않는다. OpenAPI는 창고가 붙여 둔 취급 설명서이고, `meta`는 상자 겉의 "3쪽 중 1쪽" 라벨이다. 거절 도장 모양(`error`)이 설명서와 다르면 점원은 상자를 성공으로 진열하지 않는다.

## ③ 🛠️ 실기

### 전체 코드

`lib/contract.py`

```python
API_PREFIX = "/api"

PATHS = {
    "health": "/health",
    "signup": f"{API_PREFIX}/auth/signup",
    "login": f"{API_PREFIX}/auth/login",
    "logout": f"{API_PREFIX}/auth/logout",
    "me": f"{API_PREFIX}/auth/me",
    "posts": f"{API_PREFIX}/posts",
    "post": f"{API_PREFIX}/posts/{{id}}",
    "comments": f"{API_PREFIX}/posts/{{id}}/comments",
}


def post_path(post_id: int) -> str:
    return PATHS["post"].format(id=post_id)


def clamp_limit(limit: int) -> int:
    if limit < 1:
        return 1
    if limit > 50:
        return 50
    return limit


def page_params(page: int, limit: int, q: str, sort: str = "-createdAt") -> dict:
    safe_page = page if page >= 1 else 1
    allowed = {"createdAt", "-createdAt", "-commentCount"}
    safe_sort = sort if sort in allowed else "-createdAt"
    params = {"page": safe_page, "limit": clamp_limit(limit), "sort": safe_sort}
    if q:
        params["q"] = q
    return params


ERROR_GUIDE = {
    400: "입력 또는 요청 형식 오류",
    401: "로그인 필요 또는 로그인 실패",
    403: "권한 없음",
    404: "없는 자원",
    409: "이메일 중복",
    413: "본문이 너무 큼",
    429: "호출 제한",
    500: "서버 오류",
}
```

`pages/docs_page.py`

```python
import os

import requests
import streamlit as st

from lib.contract import API_PREFIX, ERROR_GUIDE, PATHS, page_params
from lib.settings import load_settings

st.header("API 계약")
st.caption(f"접두어 {API_PREFIX}")
st.dataframe(
    [{"name": name, "path": path} for name, path in PATHS.items()],
    hide_index=True,
    width="stretch",
)

page = st.number_input("page", min_value=1, value=1, step=1)
limit = st.number_input("limit", min_value=1, max_value=50, value=10, step=1)
q = st.text_input("q")
st.json(page_params(int(page), int(limit), q.strip()))

st.subheader("오류 코드")
st.dataframe(
    [{"status": status, "screen": label} for status, label in ERROR_GUIDE.items()],
    hide_index=True,
    width="stretch",
)

if st.button("OpenAPI 경로 불러오기"):
    settings = load_settings()
    try:
        response = requests.get(settings.api_base_url + "/api-docs", timeout=settings.request_timeout)
        response.raise_for_status()
        document = response.json()
    except requests.RequestException as exc:
        st.error("API 문서를 불러오지 못했습니다.")
        st.caption(str(exc.__class__.__name__))
    else:
        server_paths = sorted((document.get("paths") or {}).keys())
        st.write(f"문서 제목: {(document.get('info') or {}).get('title', '')}")
        st.dataframe({"path": server_paths}, width="stretch")
        missing = [path for path in PATHS.values() if path != "/health" and path not in server_paths and "{" not in path]
        if missing:
            st.warning("클라이언트에만 있는 경로가 있습니다.")
            st.write(missing)
        else:
            st.success("고정 경로가 OpenAPI에 있습니다.")
```

목록 함수는 쿼리를 직접 만들지 않고 `page_params`를 사용한다.

```python
def list_posts(page: int, q: str, limit: int = 10) -> dict:
    return request_json("GET", PATHS["posts"], params=page_params(page, limit, q))
```

### 줄별 설명

- `API_PREFIX`: 버전 자리이다. 스펙은 `/api`를 쓴다.
- `PATHS`: 클라이언트가 허용하는 경로 사전이다. 상세처럼 id가 필요한 항목은 `{id}`를 남긴다.
- `post_path`: `str.format`으로 id를 넣는다. 화면이 f-string으로 경로를 조립하지 않게 한다.
- `clamp_limit`: 1 미만은 1, 50 초과는 50이다. 스펙의 limit 범위와 같다.
- `page_params`: `page`는 1 미만을 1로 올린다. `sort`는 세 가지 값만 허용한다. 빈 `q`는 쿼리에서 뺀다.
- `ERROR_GUIDE`: 상태 코드와 화면에서 할 일을 한 줄로 적는다. 실제 문장은 서버의 `error.message`를 우선한다.
- `docs_page`의 표: 학습자가 경로 사전을 화면에서 읽게 한다.
- `number_input`: 페이지와 limit을 스펙 범위 안에서만 고르게 한다.
- `GET /api-docs`: OpenAPI JSON이다. 실패하면 클래스 이름만 캡션에 남겨 내부 주소를 과하게 노출하지 않는다.
- `missing`: 변수가 없는 고정 경로가 문서에 없는지 본다. `{id}` 템플릿은 문서의 실제 키와 표기가 달라 이 단순 비교에서 제외한다.
- `list_posts`: study6 함수의 쿼리 생성을 `page_params`로 교체한 형태다.

이전·다음 버튼은 `meta`로 계산한다.

```python
meta = payload.get("meta") or {}
current = int(meta.get("page") or 1)
total_pages = int(meta.get("totalPages") or 1)
if current > 1 and st.button("이전"):
    st.query_params["page"] = str(current - 1)
    st.rerun()
if current < total_pages and st.button("다음"):
    st.query_params["page"] = str(current + 1)
    st.rerun()
```

## ④ 🔗 연동 포인트

- study6 클라이언트의 경로 리터럴을 `PATHS` 조회로 바꾸면 작성·수정·삭제가 같은 버전 접두어를 쓴다.
- 통계 대시보드가 전체 글이 필요하면 `totalPages`까지 `page_params`로 반복한 뒤 DataFrame을 만든다.
- 오류 분기는 study5의 400·422 입력 오류, 401 로그인, 403 권한, 404 없는 글, 409 가입 중복을 이 표의 상태 코드와 같은 화면에 둔다.
- 서버 구현이 `/api-docs`를 아직 제공하지 않으면 버튼은 오류 상자만 보여 주고 목록 CRUD는 `PATHS`로 계속 동작한다.
- 운영에서 접두어가 바뀌면 환경변수로 `API_PREFIX`를 읽게 `contract.py` 한 파일만 수정한다.

## ⑤ 오류 노트

### 두 번째 페이지가 항상 첫 페이지다

- 증상: 다음을 눌러도 같은 글이 나온다.
- 원인: 쿼리에 `page`를 안 실었거나 0부터 세는 값을 서버에 보냈다.
- 해결: `page_params`의 1 기준을 사용하고 `st.query_params["page"]`와 요청 파라미터를 같은 숫자로 둔다.

### limit 80을 보냈더니 서버와 화면의 개수가 다르다

- 증상: 화면은 80칸을 기대하는데 50개만 온다.
- 원인: 서버가 50으로 자른다.
- 해결: 클라이언트도 `clamp_limit`으로 50을 넘기지 않고, 개수는 `meta.limit`을 표시한다.

### OpenAPI와 클라이언트의 작성 필드가 다르다

- 증상: 문서는 `content`를 요구하고 클라이언트는 `body`를 보낸다.
- 원인: 스케치 키와 스펙 키가 섞였다.
- 해결: 스펙 v1의 작성 필드는 `title`, `body`, `tags`다. 문서를 이 필드에 맞춘다.

### 500 본문의 스택이 화면에 나타난다

- 증상: 예외 원문이 `st.error`에 보인다.
- 원인: 응답 전체를 `st.write`했다.
- 해결: `error.message`만 보여 준다. `requestId`는 캡션으로 남긴다.

## ⑥ 직접 해보기

1. `page_params(0, 80, "")`의 결과가 `page=1`, `limit=50`인지 단위 테스트로 확인한다.
2. 목록에 이전·다음 버튼을 붙여 `meta.totalPages` 끝에서 다음 버튼이 사라지는지 확인한다.
3. `/api-docs`를 눌러 고정 경로가 문서에 있는지 보고, 문서가 없으면 오류 상자만 나오는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 경로가 `API_PREFIX`와 `PATHS`에만 있다.
- [ ] 수정은 PATCH, 이름에 동사가 없다.
- [ ] `page`는 1부터, `limit`은 1~50, `sort`는 허용된 세 값이다.
- [ ] 이전·다음은 `meta.totalPages`로 계산한다.
- [ ] 오류 화면은 `error.code`, `error.message`, `error.fields`, `error.requestId`만 사용한다.
- [ ] OpenAPI `/api-docs`와 고정 경로를 대조하는 화면이 있다.

## ⑧ 다음 단계

계약이 한 파일에 모였으면, study15는 그 계약으로 반복되는 조회를 캐시하고 느린 작업을 측정한다.
