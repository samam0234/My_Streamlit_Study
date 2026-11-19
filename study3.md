# study3. 데이터 다루기

## ① 목표

재실행마다 초기화되는 변수와 `st.session_state`에 남는 값을 구분하고, 위젯 키로 화면과 묶은 뒤 JSON 파일에 저장한다.

## ② 📖 이론

### 왜 쓰는지

study2에서 보았듯 스크립트는 조작마다 처음부터 다시 실행된다. 함수 안의 일반 변수는 그때마다 사라진다. 로그인 토큰, 작성 중이던 폼, 좋아요 수처럼 "이번 방문 동안 유지할 값"은 `st.session_state`에 둔다. 브라우저를 닫아도 남을 값은 세션이 아니라 파일이 담당한다.

### 핵심 개념

- **지역 변수**: 한 번의 실행 안에서만 산다. 다음 재실행에서 다시 계산한다.
- **세션 상태**: `st.session_state`는 브라우저 탭의 Streamlit 세션에 붙어 있는 딕셔너리다. 재실행 사이에 유지되고, 탭을 닫거나 세션이 끊기면 사라진다.
- **초기화**: 키가 없을 때만 처음 값을 넣는다. 매 실행마다 덮어쓰면 유지가 깨진다.
- **바인딩**: `st.text_input("제목", key="draft_title")`는 위젯 값과 `st.session_state["draft_title"]`를 같은 값으로 묶는다.
- **위젯 생성 이후의 대입 금지**: 같은 실행에서 위젯을 만든 뒤에 그 `key`를 다시 대입하면 예외가 난다. 값을 바꾸는 대입은 위젯이 생기기 전이나 콜백 안에서 한다.
- **파일 저장**: 서버 디스크의 JSON이 이 단원의 로컬 저장소다. 화면은 세션을 읽고, 저장 버튼이 파일을 갱신한다.

### 비유

지역 변수는 계산용 메모지다. 손님이 버튼을 누를 때마다 메모지를 새로 꺼낸다. `st.session_state`는 그 손님 테이블에 놓인 쟁반이다. 쟁반 위 토큰과 작성 중인 메모는 같은 식사 동안 남는다. 식당이 문을 닫아도 남을 장부는 서랍 속 JSON 파일이다. 위젯의 `key`는 쟁반 칸에 붙여 둔 이름표라서, 입력 칸과 쟁반 칸이 항상 같은 내용을 가리킨다.

## ③ 🛠️ 실기

`data/` 폴더는 앱이 처음 저장할 때 만든다. `data/drafts.json`은 `.gitignore`에 넣을 로컬 파일이지만, 학습 중에는 내용을 눈으로 확인한다.

### 전체 코드

`app.py`

```python
import json
from pathlib import Path

import streamlit as st

STORE = Path("data") / "drafts.json"


def load_drafts() -> list[dict]:
    if not STORE.exists():
        return []
    return json.loads(STORE.read_text(encoding="utf-8"))


def save_drafts(rows: list[dict]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def init_state() -> None:
    if "token" not in st.session_state:
        st.session_state.token = ""
    if "drafts" not in st.session_state:
        st.session_state.drafts = load_drafts()
    if "saved_count" not in st.session_state:
        st.session_state.saved_count = 0


def remember_token() -> None:
    typed = st.session_state.token_input.strip()
    st.session_state.token = typed


def add_draft() -> None:
    title = st.session_state.draft_title.strip()
    body = st.session_state.draft_body.strip()
    if not title or not body:
        st.session_state.form_error = "제목과 본문을 입력하세요."
        return
    st.session_state.drafts.append({"title": title, "body": body})
    st.session_state.form_error = ""
    st.session_state.saved_count += 1
    save_drafts(st.session_state.drafts)


def main() -> None:
    st.set_page_config(page_title="세션과 파일", layout="centered")
    init_state()
    st.title("세션 상태와 파일")

    st.text_input("연습용 토큰", key="token_input", on_change=remember_token)
    st.caption("세션에 보관 중" if st.session_state.token else "세션에 토큰 없음")

    with st.form("draft_form", clear_on_submit=True):
        st.text_input("제목", key="draft_title")
        st.text_area("본문", key="draft_body")
        st.form_submit_button("임시 저장", on_click=add_draft)

    if st.session_state.get("form_error"):
        st.error(st.session_state.form_error)

    st.write(f"이번 세션에서 저장한 횟수: {st.session_state.saved_count}")
    st.json(st.session_state.drafts)


main()
```

실행 후 제목과 본문을 저장하고, 브라우저에서 새로고침한다. 목록은 파일에서 다시 읽혀 남고, "이번 세션에서 저장한 횟수"는 세션이 유지되면 남는다. 주소 옆의 세션을 끊는 메뉴(우측 상단의 앱 재시작이 아니라, 브라우저를 닫았다 다시 연 경우)에는 횟수가 0부터 다시 시작하고 목록은 파일 값으로 채워진다.

### 줄별 설명

- `STORE`: 서버 작업 폴더 아래 `data/drafts.json` 경로다.
- `load_drafts`: 파일이 없으면 빈 리스트를 반환한다. 첫 실행에서 예외로 앱이 죽지 않게 한다.
- `json.loads`: 파일 텍스트를 Python 리스트로 바꾼다.
- `save_drafts`: 부모 폴더를 만든 뒤 UTF-8 JSON으로 덮어쓴다. `ensure_ascii=False`는 한글을 그대로 저장한다.
- `init_state`: 키가 없을 때만 초기화한다. `token`은 로그인 토큰을 담을 자리이고, 이 단원에서는 입력 문자열을 그 자리에 남긴다. 실제 발급은 study7이다.
- `st.session_state.drafts = load_drafts()`: 세션이 처음 열릴 때 파일 내용을 쟁반에 올린다. 매 실행마다 호출하지 않으므로, 저장 전의 메모리 수정이 파일에 의해 즉시 덮이지 않는다.
- `remember_token`: `token_input` 위젯의 `on_change` 콜백이다. 위젯이 이미 값을 키에 넣은 뒤 호출되므로, 여기서 `token`이라는 다른 키에 복사한다.
- `add_draft`: 폼 제출 콜백이다. `draft_title`, `draft_body`는 위젯 키라서 콜백 시점에 세션에서 읽는다.
- `form_error`: 검증 문장을 세션에 남겨, 콜백이 끝난 뒤의 본문 실행이 `st.error`로 표시하게 한다. 콜백 안에서 `st.error`를 직접 부르지 않는 이유다.
- `clear_on_submit=True`: 제출에 성공한 폼 입력을 비운다.
- `st.form_submit_button(..., on_click=add_draft)`: 제출이 재실행과 콜백을 함께 일으킨다.
- `st.caption(...)`: `token` 키의 내용 전체가 아니라 보관 여부만 보여 준다.
- `st.json`: 세션에 올라간 초안 리스트를 화면에 묶는다.

위젯과 세션의 바인딩은 `key="draft_title"` 한 줄이다. 화면의 입력 칸을 고치면 `st.session_state.draft_title`이 같은 문자열이 된다.

## ④ 🔗 연동 포인트

- `st.session_state.token`은 study7에서 API 로그인 응답의 `accessToken`을 넣는 자리다. 이 단원은 그 칸을 만들고, 화면에 토큰 원문을 반복 출력하지 않는 습관을 들인다.
- `draft_title`과 `draft_body`는 study5 폼의 필드 이름과 같고, study6 요청 본문의 `title`, `body`로 이어진다.
- JSON 파일은 브라우저 `localStorage` 자리에 해당하는 서버 측 저장이다. Streamlit의 `requests`와 위젯은 서버에서 실행되므로, durable 저장은 서버 파일이나 이후의 DB다. study6의 API가 붙으면 이 파일 저장은 API의 POST로 교체하고, 세션에는 토큰과 작성 중 초안만 남긴다.
- 파일 경로 `data/`는 study10의 배포 점검에서 "디스크에 남길 데이터인가, 환경변수로 가리킬 DB인가"를 나누는 기준이 된다.

## ⑤ 오류 노트

### 위젯을 만든 뒤에 같은 키에 값을 넣었다

- 증상: `st.session_state.draft_title cannot be modified after the widget with key draft_title is instantiated.`
- 원인: 위젯 생성 뒤 같은 실행에서 그 키를 대입했다.
- 해결: 초기화는 위젯보다 위에서 하고, 사용자의 변경에 반응하는 대입은 `on_change` 또는 `on_click` 콜백으로 옮긴다.

### 매 실행마다 토큰을 빈 문자열로 덮어쓴다

- 증상: 입력했는데 재실행 후 토큰 보관 표시가 계속 비어 있다.
- 원인: `if "token" not in st.session_state` 없이 `st.session_state.token = ""`를 매 실행 호출했다.
- 해결: 없는 키에만 처음 값을 넣는다.

### JSON 저장 후 한글이 이스케이프된다

- 증상: 파일에 `\uXXXX`만 보인다.
- 원인: `json.dumps`의 기본 `ensure_ascii=True`다.
- 해결: `ensure_ascii=False`와 `encoding="utf-8"`을 함께 쓴다.

### 새로고침 뒤 목록이 비어 있다

- 증상: 저장 메시지는 있었는데 `data/drafts.json`이 없다.
- 원인: `streamlit run`의 작업 폴더가 프로젝트 루트가 아니라서 다른 곳에 `data/`가 생겼다.
- 해결: 터미널의 현재 폴더를 확인하고, 화면의 저장 경로를 `STORE.resolve()`로 한 번 출력해 본다.

## ⑥ 직접 해보기

1. 초안을 두 개 저장한 뒤 `data/drafts.json`을 열어 `title`과 `body` 키가 있는지 확인한다.
2. 토큰 입력 칸에 연습 문자열을 넣고 다른 위젯을 조작한다. 보관 표시가 유지되면 세션 키가 재실행을 견딘 것이다.
3. `init_state`의 조건문을 잠시 제거하고 어떤 증상이 생기는지 본 다음, 조건문을 되돌린다.

## ⑦ ☐ 체크리스트

- [ ] `st.session_state` 로 로그인 토큰·폼 상태 유지
- [ ] 지역 변수와 세션 키의 수명 차이를 예시로 설명했다.
- [ ] 위젯 `key`와 `st.session_state`가 같은 값으로 묶이는 것을 확인했다.
- [ ] 콜백에서 폼 값을 읽어 세션 리스트에 추가했다.
- [ ] 초안 리스트를 JSON 파일에 저장하고, 새 세션에서 그 파일을 다시 읽었다.
- [ ] 위젯 생성 이후에 같은 키를 대입하지 않았다.

## ⑧ 다음 단계

세션과 파일이 데이터를 지키기 시작하면, study4는 그 데이터를 어떤 주소와 페이지 파일에서 보여 줄지 경로를 나눈다.
