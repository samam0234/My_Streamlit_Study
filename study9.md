# study9. 테스트와 디버깅

## ① 목표

검증 함수의 단위 테스트와 AppTest 요청 흐름을 작성하고, API 호출은 가짜로 바꾸며, 로그와 자주 나는 오류를 읽어 고친다.

## ② 📖 이론

### 왜 쓰는지

화면을 손으로만 확인하면 폼 조건을 하나 바꿀 때마다 가입과 삭제를 다시 눌러야 한다. 단위 테스트는 화면 없이 함수의 입출력을 고정한다. AppTest는 Streamlit이 제공하는 앱 실행기다. `requests`는 테스트에서 가짜 함수로 바꿔, 공통 API 서버가 꺼져 있어도 성공·400·401 분기를 재현한다.

### 핵심 개념

- **단위 테스트**: `pytest`가 `validate_post`, `hash_password`를 직접 호출한다.
- **앱 테스트**: `streamlit.testing.v1.AppTest`가 스크립트를 실행하고 버튼 클릭 뒤의 제목·오류 상자를 읽는다.
- **가짜 API**: `unittest.mock.patch`가 `lib.api_client.requests.request`를 대체한다. 가짜 응답은 스펙과 같은 `data` / `error` JSON이다.
- **로그**: 터미널의 Streamlit 로그와 `logging` 로거. 예외 원문은 화면의 `error.message`가 아니라 서버 로그에만 남긴다.
- **디버거**: IDE에서 `streamlit run` 대신 `python -m streamlit run app.py`를 디버그 구성으로 실행하고 `lib/api_client.py`에 중단점을 둔다.

### 비유

단위 테스트는 저울 추로 저울만 검사하는 일이다. AppTest는 계산대 리허설이다. 창고 직원 대신 대본(mock)을 읽혀도 계산대가 거절 전표를 제대로 붙이는지 볼 수 있다. 로그는 주방 안의 기록지라서 손님 유리창에 원문을 붙이지 않는다.

## ③ 🛠️ 실기

`requirements.txt`에 테스트 도구를 추가한다.

```text
pytest==8.4.2
```

### 전체 코드

`tests/test_validate.py`

```python
from lib.validate import validate_post


def test_empty_title():
    fields = validate_post("", "본문")
    assert "title" in fields


def test_long_title():
    fields = validate_post("가" * 201, "본문")
    assert fields["title"] == ["1~200자로 입력하세요."]


def test_ok():
    assert validate_post("첫 글", "안녕하세요") == {}
```

`tests/test_api_client.py`

```python
from unittest.mock import Mock, patch

import pytest

from lib.api_client import ApiError, list_posts


def test_list_posts_reads_data(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_BASE_URL", "http://api.test")
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.content = b"{}"
    response.json.return_value = {
        "data": [{"id": 1, "title": "첫 글", "body": "안녕하세요"}],
        "meta": {"page": 1, "limit": 10, "total": 1, "totalPages": 1, "q": ""},
    }
    with patch("lib.api_client.requests.request", return_value=response) as called:
        payload = list_posts(1, "")
    assert payload["data"][0]["title"] == "첫 글"
    assert called.call_args.args[0] == "GET"
    assert called.call_args.args[1] == "http://api.test/api/posts"


def test_list_posts_error_message(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_BASE_URL", "http://api.test")
    response = Mock()
    response.status_code = 401
    response.ok = False
    response.content = b"{}"
    response.json.return_value = {"error": {"code": "UNAUTHORIZED", "message": "로그인이 필요합니다."}}
    with patch("lib.api_client.requests.request", return_value=response):
        with pytest.raises(ApiError) as caught:
            list_posts(1, "")
    assert caught.value.message == "로그인이 필요합니다."
```

`tests/test_app.py`

```python
from streamlit.testing.v1 import AppTest


def test_home_title():
    at = AppTest.from_file("app.py", default_timeout=15)
    at.run()
    assert at.title[0].value == "게시판"
```

제목 단언은 입구 `app.py`의 `st.title` 문장과 맞춘다. 입구 제목이 "멀티페이지"이면 그 문자열로 고친다. 테스트는 네트워크를 열지 않아야 하므로, 목록 페이지의 `list_posts`가 렌더 즉시 호출되지 않거나 위 패치가 적용된 진입점을 테스트한다. 목록을 즉시 호출하는 스크립트는 아래처럼 패치한 뒤 AppTest를 돌린다.

```python
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def test_list_shows_error_message():
    with patch("pages.list_page.list_posts", side_effect=ApiError(401, {"error": {"message": "로그인이 필요합니다."}})):
        at = AppTest.from_file("pages/list_page.py", default_timeout=15)
        at.run()
    assert any("로그인이 필요합니다." in item.value for item in at.error)
```

`pages/list_page.py`가 모듈 로드 시 `render()`를 호출하면 AppTest가 그 호출을 실행한다. `ApiError` import는 테스트 파일 상단에 둔다.

로그 설정 `lib/logging_config.py`:

```python
import logging


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def log_api_failure(status: int, request_id: str) -> None:
    logging.getLogger("board.api").info("api_failure status=%s request_id=%s", status, request_id)
```

`request_id`는 응답 JSON의 `error.requestId` 또는 헤더 `X-Request-Id`다. 스택 원문은 이 로그에만 남기고 화면에는 `error.message`만 보낸다.

실행:

```powershell
pytest -q
```

디버깅 순서:

1. 터미널에 traceback이 있으면 마지막 파일과 줄 번호부터 연다.
2. 화면의 빨간 상자 문장과 터미널 예외가 같은 시각인지 본다.
3. 브라우저 Console에 프론트 오류가 있는지도 함께 본다.
4. API 문제면 서버 로그의 `requestId`와 화면을 대조한다. 화면에는 그 id를 캡션으로만 보여 줘도 된다.

### 줄별 설명

- `test_empty_title`: 빈 제목이 `title` 키를 만드는지 본다. 위젯이 필요 없다.
- `test_long_title`: 201자가 스펙 문장과 같은 리스트를 만드는지 본다.
- `test_ok`: 정상 입력은 빈 딕셔너리다. 화면이 POST를 허용하는 조건과 같다.
- `monkeypatch.setenv`: 테스트 프로세스의 환경변수다. `APP_ENV=production`이라 `.env`의 개발 주소가 끼어들지 않는다.
- `patch("lib.api_client.requests.request")`: 클라이언트가 참조하는 `requests.request`만 가짜다. 진짜 소켓은 열리지 않는다.
- `call_args.args`: 첫 인자가 메서드, 둘째가 베이스 URL과 경로를 붙인 주소인지 확인한다.
- `pytest.raises(ApiError)`: 401 JSON의 `message`가 예외 속성에 남는지 본다.
- `AppTest.from_file`: 스크립트를 Streamlit 테스트 런타임에서 실행한다.
- `at.error`: 화면에 올라온 `st.error` 목록이다.
- `log_api_failure`: 상태 코드와 요청 id만 남긴다. 토큰, 비밀번호, 본문 전체를 포맷 문자열에 넣지 않는다.

## ④ 🔗 연동 포인트

- 가짜 응답의 `data`·`meta`·`error.message`는 공통 스펙 v1과 같은 키여야 한다. 테스트가 다른 모양을 허용하면 화면이 실서버에서만 깨진다.
- `API_BASE_URL=http://api.test`는 존재하지 않는 호스트여도 된다. 패치가 소켓 연결보다 먼저 가로채기 때문이다.
- CI인 study16은 이 `pytest -q`를 그대로 실행한다. 테스트가 진짜 DB나 진짜 API 키를 요구하면 그 단계는 실패한다.
- 디버그 중단점은 `request_json`의 `raise ApiError` 줄에 두면 상태 코드와 payload를 그 자리에서 본다.

## ⑤ 오류 노트

### 자주 나는 오류 10가지

1. 증상: `DuplicateWidgetID`. 원인: 반복 위젯에 고유 `key`가 없다. 해결: id가 들어간 키를 준다.
2. 증상: 위젯 생성 후 session_state 수정 예외. 원인: 위젯과 같은 키를 본문에서 대입했다. 해결: 초기화는 위젯 앞, 변경은 콜백으로 옮긴다.
3. 증상: 폼이 제출되지 않는다. 원인: 폼 안에 `st.button`만 있다. 해결: `st.form_submit_button`을 둔다.
4. 증상: `ModuleNotFoundError: lib`. 원인: 테스트 작업 폴더가 루트가 아니다. 해결: 루트에서 `pytest`를 실행한다.
5. 증상: 테스트가 진짜 `localhost:8000`에 접속하다 실패한다. 원인: 패치 경로가 `requests.request`가 아니라 사용하지 않는 위치다. 해결: `lib.api_client.requests.request`를 패치한다.
6. 증상: `StreamlitSecretNotFoundError`. 원인: 대괄호로 `st.secrets`를 읽었다. 해결: 없는 값을 허용하는 자리만 `.get`을 쓴다.
7. 증상: `Port 8501 is already in use`. 원인: 이전 서버가 살아 있다. 해결: 그 프로세스를 종료한다.
8. 증상: `JSONDecodeError`. 원인: HTML 오류 페이지를 JSON으로 읽었다. 해결: `response.json`을 `try`로 감싸 `BAD_RESPONSE`로 바꾼다.
9. 증상: 쿼리 `id`에서 `ValueError`. 원인: 정수가 아닌 문자열을 `int`에 넣었다. 해결: `isdigit` 검사 후 `st.stop`한다.
10. 증상: 버튼 값이 다음 클릭까지 참으로 남았다고 착각한다. 원인: `st.button`의 참은 그 실행 한 번이다. 해결: 유지할 값은 `st.session_state`에 적는다.

### pytest가 앱을 수집하다 서버가 뜬다

- 증상: 테스트 수집 중에 브라우저가 열린다.
- 원인: 테스트가 `streamlit run`을 호출했다.
- 해결: 테스트는 `AppTest`와 함수 호출만 사용한다.

## ⑥ 직접 해보기

1. `validate_post`의 본문 최소 길이를 일부러 2로 바꾼 뒤 `pytest -q`가 실패하는지 보고, 테스트를 고치지 말고 함수를 되돌린다.
2. 가짜 응답의 `message`를 다른 문장으로 바꿔 단언이 그 문장을 따라가는지 확인한다.
3. `log_api_failure`에 토큰 변수를 넣어 보는 실수를 주석으로만 적고, 실제 호출에는 상태 코드와 request id만 남긴다.

## ⑦ ☐ 체크리스트

- [ ] `validate_post` 단위 테스트가 빈 제목, 긴 제목, 정상 입력을 가른다.
- [ ] `requests.request`를 패치해 목록 성공과 401 문장을 검증했다.
- [ ] AppTest로 스크립트를 실행해 오류 상자 문장을 확인했다.
- [ ] 테스트가 진짜 API와 진짜 DB 없이 끝난다.
- [ ] 로그에는 상태 코드와 `requestId`만 남기고 비밀값은 남기지 않는다.
- [ ] 자주 나는 오류 10개의 증상과 해결을 파일에서 찾을 수 있다.

## ⑧ 다음 단계

테스트가 가짜 API로 돌아간다면, study10은 같은 앱을 빌드·배포하면서 환경변수와 DB 연결이 운영에서 이어지는지 점검표로 마무리한다.
