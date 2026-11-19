# study17. 실시간과 확장

## ① 목표

Streamlit의 브라우저 연결과 `st.fragment`로 알림을 주기적으로 갱신하고, 업로드한 파일을 크기 제한 안에서 처리한다.

## ② 📖 이론

### 왜 쓰는지

게시판은 새로고침 없이도 새 글 알림이 보이면 도구답다. Streamlit 브라우저는 이미 서버와 WebSocket으로 연결되어 있고, 서버가 보낸 화면 변경을 그 연결로 받는다. 앱 코드가 별도의 소켓 서버를 열지 않아도, 일정 간격으로 조각만 다시 실행해 알림 목록을 갱신할 수 있다.

### 핵심 개념

- **기본 연결**: 브라우저와 Streamlit 서버의 WebSocket이 화면 갱신 통로다. 개발자도구의 WS 항목이 그 연결이다.
- **조각 재실행**: `@st.fragment(run_every="5s")`가 붙은 함수만 5초마다 다시 실행된다. 페이지 전체가 아니라 그 함수의 위젯만 갱신된다.
- **알림**: 마지막에 본 글 id를 세션에 두고, 목록의 더 큰 id가 있으면 `st.toast`와 알림 리스트에 제목을 남긴다.
- **파일 처리**: `st.file_uploader`의 바이트를 읽어 줄 수와 문자 수를 계산한다. 10MB를 넘기면 처리하지 않는다. 처리 결과는 세션에 요약만 남긴다.

### 비유

WebSocket은 계산대와 손님 사이의 벨선이다. `st.fragment`는 가게 전체를 다시 세지 않고 안내판 하나만 5초마다 다시 적는 타이머다. 파일 처리는 접수함의 서류를 세는 일이고, 너무 두꺼운 서류는 세지 않고 돌려보낸다.

## ③ 🛠️ 실기

### 전체 코드

`pages/live_page.py`

```python
import streamlit as st

from lib.api_client import ApiError, list_posts
from lib.external import MAX_BYTES

if "seen_id" not in st.session_state:
    st.session_state.seen_id = 0
if "notices" not in st.session_state:
    st.session_state.notices = []


@st.fragment(run_every="5s")
def notice_board() -> None:
    try:
        payload = list_posts(1, "")
    except ApiError as exc:
        st.caption(exc.message)
        return
    fresh = []
    newest = st.session_state.seen_id
    for post in payload.get("data") or []:
        post_id = int(post["id"])
        if post_id > st.session_state.seen_id:
            fresh.append(post["title"])
        if post_id > newest:
            newest = post_id
    if fresh:
        st.session_state.seen_id = newest
        st.session_state.notices = (fresh + st.session_state.notices)[:10]
        st.toast(f"새 글 {len(fresh)}건")
    st.write("알림")
    for title in st.session_state.notices:
        st.caption(title)


def describe_file(name: str, data: bytes) -> str:
    if len(data) > MAX_BYTES:
        raise ValueError("10MB 이하만 처리합니다.")
    text = data.decode("utf-8", errors="replace")
    return f"{name}: {len(data)}바이트, {len(text.splitlines())}줄"


st.header("알림과 파일")
notice_board()

upload = st.file_uploader("텍스트 확인", type=["txt", "md"])
if upload is not None:
    try:
        summary = describe_file(upload.name, upload.getvalue())
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success(summary)
```

첫 실행에서 기존 글이 모두 알림으로 뜨지 않게 하려면, 페이지를 연 직후 한 번 최신 id만 기록하는 버튼을 둔다.

```python
if st.button("현재 글을 읽음으로 표시"):
    st.session_state.seen_id = max(
        [int(post["id"]) for post in (list_posts(1, "").get("data") or [])] or [0]
    )
    st.session_state.notices = []
```

### 줄별 설명

- `seen_id`: 이 세션이 이미 인지한 글 id의 최댓값이다.
- `notices`: 최근에 발견한 제목이다. 10개를 넘으면 앞쪽만 남긴다.
- `@st.fragment(run_every="5s")`: 이 함수만 5초마다 재실행된다. 파일 업로더가 있는 아래 코드는 그 주기에 다시 열리지 않는다.
- `list_posts(1, "")`: 공개 목록의 첫 페이지를 알림의 원본으로 삼는다. 실패하면 캡션에 `error.message`만 남긴다.
- `post_id > seen_id`: 정수 id가 커진 글을 새 글로 본다. Mongo의 문자열 id를 이 비교에 넣지 않는다. 직접 DB 경로를 쓸 때는 시각 문자열 비교로 함수를 따로 둔다.
- `st.toast`: 조각이 새 글을 발견한 실행에서만 짧은 알림을 띄운다.
- `describe_file`: 바이트 길이와 줄 수를 반환한다. UTF-8이 아니면 대체 문자로 읽어 처리를 중단하지 않되, 크기 초과는 예외다.
- `upload.getvalue()`: 서버가 받은 파일 전체다. 10MB 제한은 `MAX_BYTES`와 같다.
- 읽음 버튼: 현재 최댓값으로 `seen_id`를 올려 과거 글이 알림으로 반복되지 않게 한다.

브라우저 개발자도구의 WS 연결은 study1에서 연 그 소켓이다. 5초마다 문서 전체를 다시 받지 않고 조각의 출력만 바뀌면 fragment가 WebSocket 갱신을 탄 것이다.

## ④ 🔗 연동 포인트

- 알림의 원본은 `GET /api/posts`다. study15 캐시를 이 조각에 쓰면 5초 주기와 `ttl` 중 긴 쪽만큼 알림이 늦어진다. 알림 경로는 캐시하지 않은 `list_posts`를 쓴다.
- 파일 요약 문자열은 study18이 문서 바이트를 읽기 전에 "받을 수 있는 파일인가"를 가르는 1차 결과다.
- `seen_id`는 세션 수명이다. 사용자 계정에 영구히 남기려면 `me.id`와 마지막 id를 API나 DB에 저장하는 필드를 나중에 추가한다.
- 배포 환경의 프록시가 WebSocket 업그레이드를 막으면 fragment 갱신도 멈춘다. study10의 프록시 점검과 같은 항목이다.

## ⑤ 오류 노트

### 5초마다 페이지 전체가 깜박인다

- 증상: 업로더가 초기화되고 스크롤이 위로 간다.
- 원인: `run_every`를 페이지 전체가 아니라 fragment가 아닌 루프와 `time.sleep`으로 구현했다.
- 해결: 갱신할 함수에만 `@st.fragment(run_every="5s")`를 붙이고 `sleep`으로 스크립트를 붙잡지 않는다.

### 알림이 같은 제목을 계속 쌓는다

- 증상: 새 글이 없는데 5초마다 토스트가 뜬다.
- 원인: `seen_id`를 갱신하기 전에 비교만 하고 저장하지 않았다.
- 해결: 발견한 실행에서 `seen_id`를 `newest`로 올린다.

### 큰 파일을 읽다 프로세스가 느려진다

- 증상: 업로더에 큰 파일을 넣은 뒤 다른 조작이 늦다.
- 원인: 제한 전에 `decode`를 했다.
- 해결: `len(data)`를 먼저 보고 10MB를 넘으면 디코드하지 않는다.

### WebSocket이 끊긴 뒤 알림이 멈춘다

- 증상: 캡션이 과거 시각에 고정된다.
- 원인: 프록시 유휴 시간이나 서버 재시작으로 소켓이 닫혔다.
- 해결: 브라우저를 한 번 새로고침해 세션을 다시 연결한다. 프록시의 업그레이드 헤더와 유휴 시간을 WebSocket에 맞게 늘린다.

## ⑥ 직접 해보기

1. 읽음 버튼을 누른 뒤 다른 세션에서 글을 하나 작성하고, 5초 안에 토스트가 오는지 본다. API가 없으면 캡션의 연결 오류가 조각 안에만 있는지 확인한다.
2. 개발자도구에서 조각이 갱신되는 동안 문서 요청이 폭주하지 않는지 Network로 본다.
3. 빈 텍스트 파일과 여러 줄 파일을 올려 바이트 수와 줄 수가 맞는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 브라우저와 서버의 WebSocket이 화면 갱신 통로라는 점을 개발자도구로 확인했다.
- [ ] 알림은 `@st.fragment(run_every="5s")` 안에서만 다시 읽는다.
- [ ] `seen_id`보다 큰 id만 알림에 쌓인다.
- [ ] 파일은 10MB를 넘기면 디코드하지 않는다.
- [ ] 알림 목록 조회에는 공개 목록 캐시를 끼우지 않는다.

## ⑧ 다음 단계

파일 크기와 알림이 준비되었으면, study18은 업로드한 문서를 요약하고 발췌를 근거로 질문에 답하는 AI 호출과 MCP 도구를 붙인다.
