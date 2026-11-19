# study15. 성능과 캐시

## ① 목표

공개 목록 조회는 `st.cache_data`로, DB 엔진과 API 세션처럼 재사용 연결은 `st.cache_resource`로 나누고, 걸린 시간을 화면에 남겨 개선 전후를 비교한다.

## ② 📖 이론

### 왜 쓰는지

재실행 모델은 검색 버튼을 누르지 않아도 스크립트 전체를 다시 실행한다. 매번 `GET /api/posts`와 DB 연결을 열면 같은 결과를 기다리는 시간이 길어진다. 캐시는 "같은 입력의 결과를 잠시 기억"하는 장치다. 기억하면 안 되는 값(방금 쓴 글, 다른 사용자의 비공개 데이터)은 키와 만료 시간을 설계해야 한다.

### 핵심 개념

- **`st.cache_data`**: 반환값을 직렬화해 저장하고, 꺼낼 때 복사본을 준다. DataFrame, 목록 JSON처럼 데이터에 쓴다. `ttl` 초가 지나면 다시 계산한다.
- **`st.cache_resource`**: 엔진, HTTP 세션, Mongo 클라이언트처럼 하나여야 하는 자원을 저장한다. 복사하지 않는다. 반환 객체를 함부로 닫지 않는다.
- **키**: 함수 인자가 캐시 키다. 사용자마다 달라야 하는 결과는 사용자 id를 인자에 넣는다. 함수 안에서 `st.session_state`를 몰래 읽으면 키가 되지 않아 다른 방문자의 결과가 섞일 수 있다.
- **무효화**: 글을 만든 직후 `cached_public_posts.clear()`로 공개 목록 캐시를 비운다.
- **측정**: `time.perf_counter`로 호출 전후를 재서 캡션에 남긴다. 첫 호출과 둘째 호출의 차이를 본다.
- **긴 작업**: 한 번의 재실행 안에서 끝날 일은 `st.spinner`로 감싼다. 재실행과 무관하게 뒤에서 돌릴 작업은 스크립트 스레드에 상태를 쓰지 않고, study17처럼 결과 파일을 나중에 읽는다.

### 비유

`st.cache_data`는 방금 복사해 둔 장부 사본이다. 손님이 사본에 낙서해도 원본 기억은 그대로다. `st.cache_resource`는 창고 열쇠 그 자체라서 복사하지 않고 한 개만 둔다. 새 물건이 들어오면 사본 묶음을 폐기하고(`clear`) 다음 손님이 원본을 다시 베끼게 한다.

## ③ 🛠️ 실기

### 전체 코드

`lib/cache_layer.py`

```python
import time
from typing import Callable

import requests
import streamlit as st
from sqlalchemy.engine import Engine


@st.cache_data(ttl=60, show_spinner=False)
def cached_public_posts(base_url: str, page: int, q: str) -> dict:
    response = requests.get(
        base_url.rstrip("/") + "/api/posts",
        params={"page": page, "limit": 10, "q": q, "sort": "-createdAt"},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


@st.cache_resource
def shared_http() -> requests.Session:
    session = requests.Session()
    session.headers["Content-Type"] = "application/json; charset=utf-8"
    return session


@st.cache_resource
def shared_engine(url: str) -> Engine:
    from sqlalchemy import create_engine

    return create_engine(url, pool_pre_ping=True)


def elapsed(label: str, action: Callable[[], dict]) -> dict:
    start = time.perf_counter()
    payload = action()
    seconds = time.perf_counter() - start
    st.caption(f"{label} {seconds:.3f}초")
    return payload
```

`pages/speed_page.py`

```python
import streamlit as st

from lib.cache_layer import cached_public_posts, elapsed, shared_engine, shared_http
from lib.db import database_url
from lib.settings import load_settings

st.header("캐시")
settings = load_settings()
q = st.text_input("검색", key="cache_q")

if st.button("목록 두 번 재기"):
    first = elapsed("첫 호출", lambda: cached_public_posts(settings.api_base_url, 1, q))
    second = elapsed("둘째 호출", lambda: cached_public_posts(settings.api_base_url, 1, q))
    st.write(f"글 {(len(first.get('data') or []))}건, 둘째 결과 동일: {first == second}")

if st.button("작성 후 캐시 비우기"):
    cached_public_posts.clear()
    st.success("공개 목록 캐시를 비웠습니다.")

st.caption(f"HTTP 세션 준비: {shared_http() is shared_http()}")
engine = shared_engine(database_url())
st.caption(f"DB 엔진 준비: {engine.url.get_backend_name()}")
```

측정 버튼은 API 서버가 떠 있을 때 첫 호출보다 둘째 호출의 초가 짧아야 한다. 서버가 없으면 `raise_for_status` 예외가 그 페이지에 표시되므로, 학습 중에는 예외를 `st.error`로 감싸 서버 부재와 캐시 로직을 구분한다.

### 줄별 설명

- `@st.cache_data(ttl=60)`: 같은 `base_url`, `page`, `q` 조합을 60초 기억한다. `show_spinner=False`는 호출자가 `elapsed` 캡션으로 시간을 보게 한다.
- `cached_public_posts`: 인자에 토큰이 없다. 공개 목록만 캐시한다. 비밀 헤더를 이 함수에 넣지 않는다.
- `response.raise_for_status`: 실패한 응답을 성공 데이터로 캐시하지 않기 위해 예외를 낸다. 예외는 기본적으로 캐시되지 않는다.
- `shared_http`: 프로세스 공용 `requests.Session`이다. 쿠키 단지에 사용자 토큰을 넣지 않는다. 토큰은 호출마다 헤더로 붙이는 별도 경로(study7)에 남긴다.
- `shared_http() is shared_http()`: 두 번 호출이 같은 객체이면 자원 캐시가 동작한 것이다.
- `shared_engine`: URL별로 엔진 하나다. study11의 `sql_engine`과 같은 역할이며, 이 단원에서 자원 캐시의 측정 화면에 다시 보여 준다.
- `elapsed`: 호출 전과 후의 `perf_counter` 차이를 캡션으로 남긴다.
- `cached_public_posts.clear()`: 그 함수의 데이터 캐시 전체를 비운다. 글 작성 성공 직후에 호출하면 다음 목록이 서버를 다시 읽는다.
- 엔진 캡션의 `get_backend_name()`: `sqlite`, `mysql`, `postgresql` 같은 드라이버 이름만 보여 비밀번호를 숨긴다.

작성 성공 코드의 연결 예:

```python
created = create_post(title, body, [])
cached_public_posts.clear()
st.success("작성 완료")
```

## ④ 🔗 연동 포인트

- 공개 목록 캐시의 인자는 `API_BASE_URL`, `page`, `q`다. 셋 중 하나만 달라도 다른 칸에 저장된다. study14의 `page_params`와 같은 숫자를 넘긴다.
- 작성·수정·삭제 성공 경로는 캐시 `clear`로 이어진다. 지우지 않으면 60초 동안 이전 목록이 남는다.
- DB 엔진 캐시는 study11의 `DATABASE_URL`과 같다. URL을 바꾼 뒤에는 프로세스를 다시 시작해 옛 엔진을 버린다.
- 초 단위 캡션은 study16 로그에 남길 때 상태 코드와 함께 `logging.info`로 보낼 수 있다. 본문 JSON 전체는 로그에 넣지 않는다.
- 60초로 부족하거나 과하면 `ttl`만 바꾼다. 전역 상한이 필요하면 `.streamlit/config.toml`의 서버 캐시 한도 설정을 운영 값으로 둔다.

## ⑤ 오류 노트

### 둘째 호출도 첫 호출만큼 느리다

- 증상: 두 캡션의 초가 거의 같다.
- 원인: 인자 `q`의 공백이 달라 키가 다르거나, 호출 사이에 `clear`가 있다.
- 해결: 같은 변수를 두 번 넘긴다. 버튼 핸들러 안의 `clear`를 측정 뒤로 옮긴다.

### 다른 계정으로 로그인했는데 같은 비공개 목록이 보인다

- 증상: 사용자 A의 글이 B 화면에 나온다.
- 원인: 인증이 필요한 결과를 `st.session_state`만 읽고 캐시했다.
- 해결: 공개 목록만 `cached_public_posts`에 둔다. 사용자별 데이터는 캐시 인자에 사용자 id를 넣고, 토큰 원문은 키로 쓰지 않는다.

### 캐시된 DataFrame을 고쳤더니 다음 화면도 바뀐다

- 증상: 필터로 행을 지웠는데 원본 캐시까지 줄었다.
- 원인: `st.cache_resource`에 데이터 리스트를 넣었거나, 캐시 밖에서 같은 객체를 유지한 채 수정했다.
- 해결: 표 데이터는 `st.cache_data`를 쓴다. 반환된 DataFrame을 고치기 전에 `copy()`한다.

### 엔진을 매 요청마다 `dispose`한다

- 증상: 간헐적으로 연결이 닫혀 있다는 오류가 난다.
- 원인: `cache_resource`가 돌려준 엔진을 화면 코드가 닫았다.
- 해결: 엔진의 수명은 프로세스에 맡기고, 화면은 세션을 열어 쿼리만 한다.

## ⑥ 직접 해보기

1. 같은 검색어로 두 번 재서 둘째 캡션이 더 짧은지 적는다.
2. `clear` 뒤에 다시 재서 첫 호출에 가까운 시간이 나오는지 확인한다.
3. `shared_http() is shared_http()` 캡션이 참인지 확인한다. 거짓이면 자원 함수가 인자 없이 매번 새로 만들어지는지 코드를 다시 본다.

## ⑦ ☐ 체크리스트

- [ ] `st.cache_data` / `st.cache_resource` 로 API·DB 호출 캐시
- [ ] 공개 목록 캐시 키는 베이스 URL, page, q이고 토큰은 키에 넣지 않는다.
- [ ] 작성 성공 뒤에 공개 목록 캐시를 `clear`한다.
- [ ] DB 엔진은 자원 캐시에 두고 화면에서 닫지 않는다.
- [ ] 첫 호출과 둘째 호출의 초를 캡션으로 비교했다.
- [ ] 캐시 함수 안에서 `st.session_state`를 읽지 않는다.

## ⑧ 다음 단계

캐시와 측정이 로컬에서 보이면, study16은 그 앱을 Docker와 GitHub Actions로 올리고 로그·백업 점검표를 운영 절차로 적는다.
