# studyFinal. 심화까지 묶은 게시판

## ① 목표

midpoint의 로그인 게시판에 DB 선택, 메일·첨부, 발췌 기반 AI 요약, Docker·자동 테스트, 보안 점검을 더해 Streamlit 한 앱으로 서비스를 닫는다.

## ② 📖 이론

### 왜 쓰는지

기초 조립은 공통 API만 호출했다. 심화 단원은 그 옆에 직접 DB, 통계, 외부 메일, 알림 조각, 문서 요약을 각각 만들었다. 최종 문서는 그 부품을 한 입구의 메뉴로 합치고, 배포와 테스트가 같은 저장소를 가리키게 하는 통합 설명서다.

### 핵심 개념

화면은 여전히 재실행과 `st.session_state.token`을 쓴다. 글의 원본은 `POST_SOURCE`로 고른다. `api`는 스펙 v1이고 `local`은 `DATABASE_URL`의 SQLite·MariaDB·PostgreSQL·MongoDB다. AI는 상세 본문을 발췌로 삼아 study18의 스트리밍을 호출한다. 비밀은 환경변수와 시크릿 파일에만 있다.

### 비유

midpoint가 계산대라면 최종 앱은 그 계산대에 창고 열쇠 함, 엽서함, 낭독대, 출고 저울을 붙인 매장이다. 손님은 메뉴만 보고, 열쇠와 모델 키는 매장 서랍에 남는다.

## ③ 🛠️ 실기

### 기능 목록

- midpoint의 가입, 로그인, 목록, 상세, 작성, 본인 수정, 본인 삭제, 로그아웃.
- `POST_SOURCE=api|local`. local은 `DATABASE_URL`로 SQLite, MariaDB, PostgreSQL, MongoDB를 바꾼다.
- 가입 성공 후 안내 메일은 시크릿이 있을 때만 SMTP로 보낸다.
- 작성 화면에서 10MB 이하 텍스트 첨부를 `data/uploads`에 저장한다.
- 통계 메뉴는 pandas 표와 선 차트다.
- 상세의 "요약" 버튼은 본문 발췌가 있을 때만 `st.write_stream`으로 답한다.
- 알림 메뉴는 5초 fragment로 새 글 제목을 쌓는다.
- `pytest`는 API를 mock으로 대체하고, GitHub Actions와 Dockerfile이 그 테스트를 전제로 한다.
- 보안 점검: 토큰은 세션만, 사용자 본문은 텍스트 출력, 비밀번호는 API에 원문으로만 보내고 로컬 사용자 파일에는 해시만, 로그에 비밀 없음.

### 폴더 구조

```text
final/
├── app.py
├── pages/
│   ├── list_page.py
│   ├── detail_page.py
│   ├── write_page.py
│   ├── dashboard_page.py
│   ├── live_page.py
│   └── ai_page.py
├── lib/
│   ├── settings.py
│   ├── contract.py
│   ├── api_client.py
│   ├── auth_api.py
│   ├── validate.py
│   ├── ui.py
│   ├── db.py
│   ├── source.py
│   ├── stats.py
│   ├── external.py
│   ├── cache_layer.py
│   └── doc_ai.py
├── mcp_server.py
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

`pages`와 `lib`의 개별 파일은 study5부터 study18의 최종 코드를 이 폴더에 모은다. 새로 붙는 접합부만 아래에 전체로 적는다.

### 구현 순서

1. midpoint 폴더를 `final/`로 복사하고 study9 테스트가 통과하는지 확인한다.
2. `lib/contract.py`의 `PATHS`로 클라이언트의 경로 리터럴을 교체한다.
3. `lib/db.py`와 `lib/source.py`를 넣어 `POST_SOURCE=local`일 때 SQLite 목록이 보이는지 확인한 뒤 URL만 PostgreSQL 또는 MariaDB, MongoDB로 바꿔 본다.
4. 작성 페이지에 업로더와 가입 직후 `send_signup_mail`을 연결한다. 시크릿 없이 연습 문장이 나오는 상태를 기본으로 한다.
5. 통계, 알림, AI 페이지를 `st.navigation`에 등록한다.
6. 상세에 요약 버튼을 넣어 발췌가 없을 때 `찾을 수 없습니다`가 나오는지 확인한다.
7. 공개 목록을 캐시한다면 작성 성공 직후 `cached_public_posts.clear()`를 호출한다. 알림 fragment에는 캐시를 넣지 않는다.
8. `pytest -q`와 Docker 빌드, study16 점검표, 아래 보안 점검을 순서대로 수행한다.

### 전체 코드

`lib/source.py`

```python
import os

from lib.api_client import create_post, list_posts
from lib.db import PostView, insert_local_post, list_local_posts


def use_local() -> bool:
    return os.getenv("POST_SOURCE", "api") == "local"


def load_cards(page: int, q: str) -> list[dict]:
    if use_local():
        rows = list_local_posts()
        if q:
            rows = [row for row in rows if q.lower() in row.title.lower() or q.lower() in row.body.lower()]
        return [{"id": row.id, "title": row.title, "body": row.body, "author": None} for row in rows]
    payload = list_posts(page, q)
    return list(payload.get("data") or [])


def save_card(title: str, body: str) -> dict:
    if use_local():
        saved: PostView = insert_local_post(title, body)
        return {"id": saved.id, "title": saved.title, "body": saved.body}
    created = create_post(title, body, [])
    return created.get("data") or {}
```

`pages/detail_page.py`에 추가하는 요약 버튼:

```python
from lib.doc_ai import search_excerpts, stream_answer

body = data.get("body") or ""
if body and st.button("본문 요약"):
    excerpts = search_excerpts(body, body[:200])
    st.write_stream(stream_answer("다섯 줄 안으로 요약하세요.", excerpts))
```

`app.py`의 메뉴:

```python
pages = [
    st.Page("pages/list_page.py", title="목록", icon="📋", default=True),
    st.Page("pages/detail_page.py", title="상세", icon="📄"),
    st.Page("pages/write_page.py", title="작성", icon="✍️"),
    st.Page("pages/dashboard_page.py", title="통계", icon="📈"),
    st.Page("pages/live_page.py", title="알림", icon="🔔"),
    st.Page("pages/ai_page.py", title="문서", icon="📄"),
]
page = st.navigation(pages)
page.run()
```

`.env.example`

```text
APP_ENV=development
API_BASE_URL=http://localhost:8000
POST_SOURCE=api
DATABASE_URL=sqlite:///data/board.db
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
```

### 줄별 설명

- `use_local`: `POST_SOURCE`가 `local`일 때만 직접 DB다. 기본값은 API라서 midpoint 동작이 유지된다.
- `load_cards`: 로컬은 `PostView`를 화면 딕셔너리로 바꾸고, API는 `data` 배열을 그대로 둔다. 검색어는 로컬에서 제목·본문 포함으로 거른다.
- `save_card`: 작성 페이지가 호출하는 유일한 저장 함수다. 로컬은 해시된 비밀번호와 무관한 글 삽입이고, API는 Bearer가 필요한 `create_post`다.
- 요약 버튼: 본문 줄을 발췌로 삼는다. 발췌 점수가 0이면 `stream_answer`가 `찾을 수 없습니다`를 내보낸다.
- 메뉴 여섯 개: 기초 CRUD와 심화 화면이 한 `st.navigation`에 있다.
- `.env.example`: 키의 자리는 보여 주고 값은 비우거나 로컬 기본값만 둔다. `AI_API_KEY`는 빈 칸이다.

### 보안 점검

- 토큰과 API 키를 `st.write`로 출력하지 않는다.
- 사용자 본문에 `unsafe_allow_html=True`를 주지 않는다.
- 가입 API의 비밀번호는 원문, 로컬 사용자 저장만 `hash_password`를 거친다.
- 작성자 버튼과 별도로 403 `error.message`를 표시한다.
- `data/uploads` 저장 이름은 `Path(name).name`만 사용한다.
- CI와 이미지에 `.env`, `secrets.toml`, DB 파일이 없다.

## ④ 🔗 연동 포인트

### 연동 구성도

```text
브라우저 ──WebSocket── Streamlit final/
                         ├─ session token ── Bearer ── 공통 API /api ── API의 DB
                         ├─ POST_SOURCE=local ── DATABASE_URL ── SQLite | MariaDB | PostgreSQL | MongoDB
                         ├─ SMTP 시크릿 ── 가입 안내 메일
                         ├─ data/uploads ── 첨부·문서
                         ├─ AI_BASE_URL + AI_API_KEY ── 발췌 프롬프트 스트리밍
                         └─ mcp_server.py find_excerpts ── 같은 발췌 함수
```

Docker는 이 프로세스만 담고, DB와 모델 서버와 SMTP는 환경변수로 가리킨다. GitHub Actions는 mock 테스트만 실행한다.

### 배포 체크리스트

- [ ] `POST_SOURCE`와 `DATABASE_URL`이 의도한 조합이다. API 모드면 DB 비밀번호가 이 앱에 없다.
- [ ] `APP_ENV=production`, `API_BASE_URL`은 운영 HTTPS다.
- [ ] `AI_API_KEY`와 SMTP·OIDC 비밀이 호스트 비밀에만 있다.
- [ ] `pytest -q`가 CI에서 통과했다.
- [ ] 이미지에 `.env`와 `secrets.toml`, `data/*.db`가 없다.
- [ ] HTTPS 도메인에서 로그인, 목록, 작성, 본인 삭제, 403이 동작한다.
- [ ] 통계 차트, 5초 알림, 요약 스트림이 배포 주소에서 열린다. 모델 키가 없으면 발췌 폴백만 보여도 된다.
- [ ] 백업이 컨테이너 밖에 있다.
- [ ] 로그에 토큰, 비밀번호, DB URL 전체가 없다.
- [ ] 업로드 10MB 초과가 거절된다.

## ⑤ 오류 노트

### local로 바꿨는데 목록이 401이다

- 증상: DB를 쓰는데 인증 오류가 나온다.
- 원인: `load_cards`가 아니라 페이지가 아직 `list_posts`를 직접 호출한다.
- 해결: 목록·작성 페이지의 저장과 조회를 `source.py`로 모은다. 상세의 수정·삭제는 API 모드에만 버튼을 두거나, 로컬 분기에 SQLAlchemy 삭제를 같은 파일에 추가한다.

### 요약 버튼이 본문과 다른 문서를 읽는다

- 증상: 상세 요약이 업로드 문서 내용이다.
- 원인: `ai_page`의 세션 텍스트를 상세가 재사용했다.
- 해결: 상세는 `data["body"]`만 `search_excerpts`에 넘긴다.

### 배포 후 알림만 멈춘다

- 증상: 목록은 갱신되는데 5초 알림이 고정이다.
- 원인: 프록시가 WebSocket 업그레이드를 끊는다.
- 해결: 업그레이드 헤더를 전달하고, 알림 경로에는 캐시를 넣지 않는다.

## ⑥ 직접 해보기

1. `POST_SOURCE=api`로 midpoint 점검표를 한 번 수행한다.
2. `POST_SOURCE=local`과 SQLite로 전환해 같은 작성 폼으로 저장한 뒤, URL만 PostgreSQL 또는 MongoDB로 바꿔 화면 코드를 수정하지 않고 저장이 되는지 확인한다.
3. 상세에서 본문에 있는 단어와 없는 단어로 요약을 눌러 발췌 번호와 `찾을 수 없습니다`를 각각 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 기능 목록의 CRUD, DB 전환, 메일, 첨부, 통계, 알림, AI, 테스트, Docker가 한 앱에 연결되어 있다.
- [ ] 기본 `POST_SOURCE=api`는 공통 스펙 v1을 유지한다.
- [ ] 연동 구성도의 비밀은 환경변수 또는 시크릿에만 있다.
- [ ] 구현 순서를 1번부터 8번까지 수행했다.
- [ ] 배포 체크리스트와 보안 점검을 배포 대상 또는 로컬 Docker에 대해 기록했다.
- [ ] 회고에 남은 운영 항목을 적었다.

## 최종 회고

이 서비스의 경계는 Streamlit 프로세스 하나다. 글의 원본은 API 또는 `DATABASE_URL` 중 하나이고, 모델과 메일은 키가 있을 때만 밖으로 나간다. 키가 없을 때의 폴백(발췌 문장, 메일 연습 문장)을 남겨 두었으므로 학습 환경에서도 화면 경로는 끝까지 간다. 공인 인증서, 실제 결제 승인, OIDC 공급자 검수, 외부 모니터링 알림은 호스트와 계정이 준비된 뒤에 같은 점검표를 다시 실행하면 된다. 그 항목을 코드 안에 가짜 성공으로 채우지 않는다.

## ⑧ 다음 단계

이 문서로 Streamlit 학습 경로의 조립이 끝난다. 같은 앱을 운영 호스트에 올릴 때는 study16 점검표와 이 배포 체크리스트를 함께 읽고, 비밀 값만 호스트에 채운 뒤 로그인부터 요약까지 한 번 수행한다.
