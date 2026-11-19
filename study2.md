# study2. 핵심 구조

## ① 목표

Streamlit 앱을 함수와 페이지 모듈로 나누고, 인자·반환값·콜백으로 서로 값을 주고받는 구조와 재실행 모델을 코드로 확인한다.

## ② 📖 이론

### 왜 쓰는지

한 파일에 출력을 이어 붙이면 데모는 빨리 끝나지만, 화면이 길어지면 어떤 함수가 어떤 값을 만드는지 찾기 어려워진다. Streamlit의 기본 단위는 클래스 계층이 아니라 **함수**다. 화면 조각은 함수, 화면 파일은 모듈, `streamlit run`에 넣는 파일이 앱의 입구다.

### 핵심 개념

- **앱 입구**: `streamlit run app.py`의 `app.py`. 공통 제목과 어떤 화면 함수를 부를지를 정한다.
- **화면 함수**: `def show_board(posts: list[dict]) -> None`처럼 인자를 받아 `st.` 함수를 호출한다.
- **모듈**: `lib/cards.py`처럼 함수를 모아 둔 파일. `from lib.cards import post_card`로 부른다.
- **재실행**: 위젯 조작, 버튼, 파일 저장은 스크립트를 첫 줄부터 다시 실행한다. 지역 변수는 매 실행마다 다시 만들어진다.
- **폼**: `st.form` 안의 입력은 제출 버튼을 누르기 전까지 재실행을 일으키지 않는다. 제출 순간에 한 번 재실행된다.
- **값 전달**: 함수 인자와 반환값이 기본이다. 클릭 순간에 서버 함수를 실행하려면 `on_click` 콜백을 쓴다.

### 비유

앱 입구는 안내 데스크다. 안내 데스크는 매 손님 조작마다 업무 일지를 첫 장부터 다시 읽는다. 게시글 카드 함수는 도장이다. 안내 데스크가 게시글 딕셔너리를 건네면 도장이 제목과 본문을 찍는다. 폼은 여러 칸을 모았다가 제출 도장을 찍는 순간에만 안내 데스크를 다시 호출하는 서류철이다.

## ③ 🛠️ 실기

폴더:

```text
app.py
lib/cards.py
```

`lib`이 패키지로 인식되도록 `lib/__init__.py`는 빈 파일로 둔다.

### 전체 코드

`lib/cards.py`

```python
import streamlit as st


def post_card(post: dict) -> None:
    """게시글 하나를 화면에 그린다."""
    st.subheader(post["title"])
    st.write(post["body"])
    st.caption("태그: " + ", ".join(post["tags"]))


def count_label(posts: list[dict], label: str) -> str:
    """화면 밖에 써먹을 문장을 만들어 반환한다."""
    return f"{label} {len(posts)}건"
```

`app.py`

```python
import streamlit as st

from lib.cards import count_label, post_card

st.set_page_config(page_title="구조", layout="centered")

POSTS = [
    {"title": "첫 글", "body": "안녕하세요", "tags": ["intro"]},
    {"title": "둘째 글", "body": "재실행을 봅니다", "tags": ["rerun"]},
]


def on_ping() -> None:
    st.toast("콜백이 버튼 처리 중에 실행되었습니다.")


def show_controls() -> str | None:
    st.text_input("검색어", key="keyword")
    kind = st.selectbox("보기", ["전체", "태그 있음"], key="kind")
    st.button("신호", on_click=on_ping)
    with st.form("filter_form"):
        note = st.text_input("메모")
        submitted = st.form_submit_button("메모 적용")
    if submitted:
        return note
    st.caption(f"현재 보기: {kind}")
    return None


def main() -> None:
    st.title("함수로 나눈 화면")
    note = show_controls()
    st.write(count_label(POSTS, "샘플"))
    keyword = st.session_state.get("keyword", "")
    for post in POSTS:
        if keyword and keyword not in post["title"]:
            continue
        post_card(post)
    if note:
        st.info(f"폼에서 받은 메모: {note}")


main()
```

실행:

```powershell
streamlit run app.py
```

검색어를 한 글자씩 입력해 본다. 글자가 바뀔 때마다 제목 필터가 다시 계산되면, 입력이 스크립트 재실행을 일으킨 것이다. 폼의 메모 칸은 입력 도중 아래 목록이 다시 그려지지 않고, "메모 적용"을 누른 실행에서만 `note`가 생긴다.

### 줄별 설명

`lib/cards.py`

- `post_card(post)`: 게시글 딕셔너리를 인자로 받는 화면 함수다. 반환값은 없다. 그리는 일이 함수의 역할이다.
- `st.subheader`, `st.write`, `st.caption`: 인자로 받은 제목, 본문, 태그만 출력한다. 데이터 목록은 이 함수가 소유하지 않는다.
- `count_label(...)`: 화면 함수와 달리 문자열을 반환한다. 호출한 쪽이 어디에 쓸지 결정한다.

`app.py`

- `from lib.cards import ...`: 다른 모듈의 함수를 이름으로 불러온다.
- `POSTS`: 이번 단원의 고정 샘플이다. 재실행마다 같은 리스트가 다시 만들어진다.
- `on_ping`: 버튼의 `on_click`에 넘기는 콜백이다. 본문이 다시 실행되기 전에 호출된다.
- `st.toast`: 잠깐 보이는 알림이다. 콜백이 실제로 불렸는지 확인하는 표시다.
- `show_controls`: 입력 위젯을 한 함수에 모으고, 폼이 제출됐으면 메모 문자열을, 아니면 `None`을 반환한다.
- `st.text_input(..., key="keyword")`: 위젯을 세션 키 `keyword`에 묶는다. 반환값을 변수에 담지 않아도 다음 줄들이 `st.session_state`로 읽을 수 있다. 키의 자세한 수명은 study3에서 다룬다.
- `st.selectbox(..., key="kind")`: 선택값을 `kind` 키에 둔다. 여기 반환값은 이 함수 안에서만 쓴다.
- `st.button(..., on_click=on_ping)`: 클릭한 실행에서 `on_ping`을 부른다.
- `with st.form("filter_form"):`: 이름을 가진 폼이다. 안의 `text_input`은 제출 전 재실행을 일으키지 않는다.
- `st.form_submit_button`: 폼 안에서 재실행을 일으키는 버튼이다. 일반 `st.button`은 폼 안에 두지 않는다.
- `main`: 입구 함수다. 컨트롤 함수의 반환값과 카드 함수 호출을 순서대로 배치한다.
- `for post in POSTS`: 데이터는 반복에서 꺼내고, 그리기는 `post_card(post)`에 맡긴다.
- `main()`: 스크립트의 마지막에서 입구를 한 번 호출한다. 재실행되면 이 호출도 처음부터 다시 일어난다.

## ④ 🔗 연동 포인트

- `post_card`의 인자 모양(`title`, `body`, `tags`)은 study6에서 API 응답의 `data` 객체와 맞출 이름이다. 화면 함수는 API를 모르고, 딕셔너리만 받는다.
- `count_label`처럼 문자열을 반환하는 함수는 이후 메일 본문이나 로그 한 줄을 만들 때도 같은 방식으로 재사용한다.
- 폼 제출이 "한 번의 재실행"이라는 점은 study5에서 검증과 중복 제출 방지를 그 한 번의 실행 안에 넣는 이유다.
- 모듈을 `lib`로 나눈 경계는 study8에서 API 클라이언트와 화면 함수를 더 크게 가를 때 그대로 확장한다.

## ⑤ 오류 노트

### 같은 위젯을 키 없이 두 번 그렸다

- 증상: `DuplicateWidgetID` 또는 같은 라벨의 위젯이 충돌한다는 예외.
- 원인: 재실행 모델에서 Streamlit은 위젯을 라벨과 생성 순서로 구분한다. 같은 함수를 루프에서 키 없이 부르면 식별자가 겹친다.
- 해결: 반복 안의 입력 위젯에는 `key=f"title_{post_id}"`처럼 고유 키를 준다. 출력 전용인 `post_card`는 입력이 없으므로 키가 필요 없다.

### 폼 안의 일반 버튼이 기대와 다르게 동작한다

- 증상: 폼 안에 `st.button`을 두었더니 제출과 따로 놀거나 예외가 난다.
- 원인: 폼의 제출은 `st.form_submit_button`만 담당한다.
- 해결: 폼 안에는 제출 버튼만 두고, 즉시 실행 버튼은 폼 밖에 둔다.

### import 오류 `lib`를 찾을 수 없음

- 증상: `ModuleNotFoundError: No module named 'lib'`.
- 원인: `streamlit run`의 작업 폴더가 `app.py`가 있는 루트가 아니거나, `lib/__init__.py` 없이 실행 환경이 패키지를 못 본다.
- 해결: 프로젝트 루트에서 `streamlit run app.py`를 실행하고 `lib/__init__.py`를 둔다.

## ⑥ 직접 해보기

1. `post_card`에 인자 `show_tags: bool = True`를 추가하고, 호출부에서 `False`를 넘겨 태그가 사라지는지 확인한다.
2. 검색어를 입력하는 동안 터미널에 재실행 로그가 반복되는지 보고, 같은 입력을 폼 안으로 옮긴 뒤 제출 전에 로그가 조용한지 비교한다.
3. `count_label`의 반환값을 `st.metric("글", len(POSTS))`의 옆 문장으로 한 번 더 써 본다. 그리는 함수와 값을 만드는 함수가 나뉘어 있는지 말한다.

## ⑦ ☐ 체크리스트

- [ ] 위젯(text_input, button, selectbox, form)과 "매 상호작용마다 스크립트 재실행" 모델 이해
- [ ] 화면 조각은 함수, 묶음은 모듈, 입구는 `app.py`라는 점을 코드로 나눴다.
- [ ] 함수 인자로 게시글을 넘기고, 반환값으로 문장을 돌려받았다.
- [ ] `on_click` 콜백이 버튼 처리 중에 실행되는 것을 `st.toast`로 보았다.
- [ ] 폼은 제출 버튼에서만 재실행된다는 점을 입력 실험으로 확인했다.
- [ ] 반복 위젯에 고유 `key`가 필요한 이유를 오류 노트와 연결해 말할 수 있다.

## ⑧ 다음 단계

함수로 값을 넘기는 구조가 생겼으면, study3은 재실행마다 사라지는 지역 변수와 달리 세션에 남는 상태, 그리고 그 상태를 위젯·파일과 묶는 방법을 다룬다.
