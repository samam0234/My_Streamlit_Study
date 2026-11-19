# study4. 라우팅과 요청 처리

## ① 목표

`pages/` 폴더와 `st.navigation`으로 화면을 나누고, 쿼리 파라미터·페이지 이동·없는 주소 처리를 한 앱에서 연결한다.

## ② 📖 이론

### 왜 쓰는지

게시판은 목록, 상세, 작성 화면이 서로 다른 주소여야 새로고침과 공유가 된다. Streamlit은 서버가 스크립트를 실행해 화면을 만들므로, 주소의 쿼리와 현재 페이지 파일이 "이번 요청에서 무엇을 그릴지"를 결정한다.

### 핵심 개념

- **pages 폴더**: 화면 파일을 `pages/`에 둔다. 노션 학습 목표의 멀티페이지 자리이다.
- **명시적 라우터**: `st.Page`로 각 파일을 등록하고 `st.navigation`이 현재 페이지를 고른 뒤 `page.run()`이 그 파일을 실행한다. 입구 파일은 매 재실행마다 공통 틀로 다시 실행된다.
- **쿼리 파라미터**: `st.query_params`는 URL의 `?id=1&page=2`를 문자열로 읽고 쓴다. 숫자는 직접 변환한다.
- **페이지 이동**: `st.switch_page`가 등록된 페이지 파일로 이동한다. 상세의 id는 이동 전에 `st.query_params["id"]`에 넣는다.
- **오류 화면**: 숫자가 아닌 id, 목록에 없는 id는 본문 대신 `st.error`를 보여주고 `st.stop()`으로 나머지 그리기를 멈춘다.
- **경로를 맞추는 단위**: 화면 파일 이름과 API 경로를 한 표로 적는다. 화면의 `id` 쿼리는 API의 `/api/posts/{id}`와 같은 식별자를 가리킨다.

### 비유

`app.py`는 건물 로비이고 `pages/`의 파일은 방이다. 로비는 방문할 때마다 안내판을 다시 세운 뒤, 손님이 고른 방의 스크립트만 실행한다. 주소의 `?id=3`은 방 문 앞에 붙인 쪽지다. 쪽지가 숫자가 아니거나 없는 방이면 로비는 오류 안내만 붙이고 방 안 업무를 진행하지 않는다.

## ③ 🛠️ 실기

`st.navigation`을 쓰면 `pages/` 자동 탐색과 동시에 쓰지 않는다. 파일은 `pages/`에 두고, 등록은 `app.py`의 `st.Page`만 담당한다.

```text
app.py
pages/list_page.py
pages/detail_page.py
pages/missing_page.py
```

### 전체 코드

`pages/list_page.py`

```python
import streamlit as st

POSTS = [
    {"id": 1, "title": "첫 글"},
    {"id": 2, "title": "둘째 글"},
]


def render() -> None:
    st.header("목록")
    page = st.query_params.get("page", "1")
    st.caption(f"목록 페이지 번호: {page}")
    for post in POSTS:
        if st.button(post["title"], key=f"open_{post['id']}"):
            st.query_params["id"] = str(post["id"])
            st.switch_page("pages/detail_page.py")


render()
```

`pages/detail_page.py`

```python
import streamlit as st

POSTS = {
    1: {"title": "첫 글", "body": "안녕하세요"},
    2: {"title": "둘째 글", "body": "경로를 확인합니다"},
}


def render() -> None:
    raw_id = st.query_params.get("id")
    if raw_id is None or not str(raw_id).isdigit():
        st.error("글 번호가 올바르지 않습니다.")
        if st.button("목록으로"):
            st.query_params.clear()
            st.switch_page("pages/list_page.py")
        st.stop()

    post = POSTS.get(int(raw_id))
    if post is None:
        st.error("없는 글입니다.")
        st.stop()

    st.header(post["title"])
    st.write(post["body"])
    st.caption("이 id는 이후 GET /api/posts/{id} 의 경로 값과 같습니다.")


render()
```

`pages/missing_page.py`

```python
import streamlit as st


def render() -> None:
    st.header("오류")
    st.error("요청한 화면을 찾지 못했습니다.")
    st.write("주소와 메뉴를 다시 확인하세요.")


render()
```

`app.py`

```python
import streamlit as st

st.set_page_config(page_title="경로", layout="centered")

pages = [
    st.Page("pages/list_page.py", title="목록", icon="📋", default=True),
    st.Page("pages/detail_page.py", title="상세", icon="📄"),
    st.Page("pages/missing_page.py", title="오류", icon="⚠️"),
]

st.title("멀티페이지")
page = st.navigation(pages)
page.run()
```

실행:

```powershell
streamlit run app.py
```

목록에서 "첫 글"을 누르면 주소에 `id=1`이 생기고 상세 페이지가 열린다. 주소의 `id`를 `abc`로 바꿔 본다. 상세 스크립트가 오류 문장을 보여주고 본문은 그리지 않아야 한다.

### 줄별 설명

`app.py`

- `st.Page(...)`: `pages/` 안의 파일 하나와 메뉴 제목, 아이콘을 묶는다. `default=True`인 파일이 첫 화면이다.
- `st.navigation(pages)`: 사이드바 메뉴와 현재 페이지 객체를 만든다. 이 호출이 입구의 라우터다.
- `page.run()`: 현재 페이지 파일을 실행한다. 이 줄이 없으면 메뉴만 있고 방 스크립트는 돌지 않는다.
- 제목 `st.title`은 `page.run()` 앞에 있어 모든 페이지의 공통 틀이 된다.

`pages/list_page.py`

- `st.query_params.get("page", "1")`: 쿼리가 없으면 문자열 `"1"`이다. 값은 항상 문자열이거나 없으면 기본값이다.
- `st.button(..., key=f"open_{post['id']}")`: 반복 버튼의 키를 id로 고유하게 만든다.
- `st.query_params["id"] = str(post["id"])`: 이동 전에 상세가 읽을 쪽지를 주소에 쓴다.
- `st.switch_page("pages/detail_page.py")`: 등록된 페이지 파일로 이동하며 재실행된다.

`pages/detail_page.py`

- `raw_id is None or not str(raw_id).isdigit()`: 없는 id와 숫자가 아닌 id를 오류 화면으로 보낸다.
- `st.query_params.clear()`: 잘못된 쪽지를 지우고 목록으로 돌아간다.
- `st.stop()`: 이후의 `st.header`가 실행되지 않게 스크립트를 멈춘다. 예외를 일부러 일으키지 않는다.
- `POSTS.get(int(raw_id))`: 숫자로 바꾼 뒤에만 샘플 딕셔너리를 찾는다.
- 캡션의 경로는 화면 id와 API 경로 자리표시자를 같은 값으로 맞추라는 메모다.

`pages/missing_page.py`

- 메뉴에서 직접 여는 오류 안내 페이지다. 상세의 `st.stop()` 분기와 함께 "오류 화면" 역할을 나눈다.

## ④ 🔗 연동 포인트

- 화면 쿼리 `page`는 study6 목록 요청의 `GET /api/posts?page=`와 같은 이름이다. 기본값 1, 1부터 센다.
- 화면 쿼리 `id`는 `GET /api/posts/{id}`의 경로 변수다. 프론트 파일 경로와 백엔드 경로를 아래처럼 맞춘다.

| 화면 파일 | 화면에서 읽는 값 | API |
| --- | --- | --- |
| `pages/list_page.py` | `page` | `GET /api/posts?page&limit&q&sort` |
| `pages/detail_page.py` | `id` | `GET /api/posts/{id}` |
| 작성 폼 (study5) | 없음 | `POST /api/posts` |

- `st.switch_page`는 같은 앱 안의 이동이다. 외부 API 서버의 주소는 환경변수 `API_BASE_URL`로 두고 페이지 이동과 섞지 않는다.
- 오류 화면의 문장은 study6에서 API가 404 `NOT_FOUND`를 돌려줄 때 `error.message`를 표시하는 자리와 같다.

## ⑤ 오류 노트

### 메뉴에 페이지가 두 벌로 보인다

- 증상: `pages/` 파일을 만들었더니 자동 메뉴와 `st.navigation` 메뉴가 겹친다.
- 원인: 자동 탐색과 `st.navigation`을 함께 썼다.
- 해결: 입구에서 `st.navigation`과 `page.run()`만 사용한다. 페이지 파일은 `pages/`에 두되 자동 탐색에 맡기지 않는다.

### `switch_page`가 파일을 못 찾는다

- 증상: `Could not find page` 류의 예외.
- 원인: `st.Page`에 등록한 경로와 `st.switch_page`에 넘긴 문자열이 다르다.
- 해결: 두 곳 모두 `pages/detail_page.py`처럼 프로젝트 루트 기준의 같은 문자열을 쓴다.

### id를 숫자로 바로 변환하다가 죽는다

- 증상: `ValueError: invalid literal for int()`.
- 원인: 쿼리는 문자열이고 `abc`가 들어올 수 있다.
- 해결: `isdigit()`으로 걸러 `st.error`와 `st.stop()`을 먼저 실행한다.

### 상세에 들어왔는데 id가 비어 있다

- 증상: 메뉴의 "상세"를 직접 누르면 글 번호 오류가 난다.
- 원인: 메뉴 이동은 `id` 쿼리를 만들지 않는다.
- 해결: 상세는 `id`가 있을 때만 본문을 그린다. 목록 버튼을 통해서만 `id`를 채운다. 이 동작이 오류 처리의 정상 경로다.

## ⑥ 직접 해보기

1. 주소에 `?page=3`을 붙여 목록 캡션의 번호가 3으로 바뀌는지 확인한다.
2. `id`를 99로 바꿔 없는 글 분기가 본문 제목보다 먼저 보이는지 확인한다.
3. 목록 버튼으로 상세에 들어간 뒤 브라우저 뒤로 가기를 눌러 목록 쿼리가 어떻게 되는지 주소창으로 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 멀티페이지(`pages/` 폴더) 구성
- [ ] `st.Page`와 `st.navigation`, `page.run()`으로 입구와 페이지 파일을 나눴다.
- [ ] `st.query_params`로 `page`와 `id`를 읽고, 이동 전에 `id`를 썼다.
- [ ] `st.switch_page`로 목록과 상세를 오갔다.
- [ ] 숫자가 아닌 id와 없는 id에 `st.error`와 `st.stop()`을 썼다.
- [ ] 화면 쿼리 이름과 `/api/posts`, `/api/posts/{id}`의 자리를 표로 맞췄다.

## ⑧ 다음 단계

주소와 화면 파일이 나뉘었으면, study5는 상세와 같은 앱 안에서 사용자가 입력하는 폼을 검증하고 서버 응답 코드에 따라 화면을 바꾼다.
