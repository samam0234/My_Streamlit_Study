# study8. 구조화와 재사용

## ① 목표

화면, API 호출, 검증, 설정을 폴더로 나누고 환경변수 한 곳에서 읽어 개발 설정과 운영 설정이 같은 코드로 갈라지게 한다.

## ② 📖 이론

### 왜 쓰는지

study6과 study7의 함수가 페이지마다 복사되면 경로 문자열이 어긋난다. 구조화는 새 기능을 추가하기 전에 같은 일을 하는 함수를 한 파일로 모으는 일이다. 설정은 코드 밖에 둔다. 개발 PC의 API 주소와 운영 서버의 API 주소가 달라도 `lib/settings.py`의 읽기 함수는 그대로다.

### 핵심 개념

- **입구**: `app.py`는 `st.navigation`과 공통 제목만 둔다.
- **화면**: `pages/`의 파일은 `lib`의 함수만 호출한다. URL 문자열을 페이지에 다시 적지 않는다.
- **클라이언트**: `lib/api_client.py`, `lib/auth_api.py`.
- **검증**: `lib/validate.py`.
- **설정**: `lib/settings.py`가 `.env`와 환경변수를 읽어 데이터 클래스로 돌려준다.
- **개발 / 운영**: 개발은 `.env`의 `APP_ENV=development`. 운영은 프로세스 환경변수 `APP_ENV=production`과 호스트가 주입하는 `API_BASE_URL`. 운영에서 `.env` 파일이 없어도 환경변수만으로 기동한다.
- **중복 제거**: 오류 표시는 `lib/ui.py`의 `show_error` 하나다.

### 비유

`lib`은 공용 창고 서랍이고 `pages`는 매장 진열이다. 진열대마다 창고 주소를 다시 써 붙이지 않는다. 주소표는 서랍 하나(`settings`)에만 있고, 매장을 개발 매장에서 운영 매장으로 옮겨도 진열대 배치 코드는 주소표를 다시 읽을 뿐이다.

## ③ 🛠️ 실기

```text
app.py
pages/list_page.py
pages/write_page.py
lib/__init__.py
lib/settings.py
lib/api_client.py
lib/auth_api.py
lib/validate.py
lib/ui.py
.streamlit/config.toml
.env.example
```

### 전체 코드

`lib/settings.py`

```python
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_env: str
    api_base_url: str
    request_timeout: float

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


def load_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development")
    if app_env != "production":
        load_dotenv()
    base = os.getenv("API_BASE_URL", "").rstrip("/")
    timeout = float(os.getenv("REQUEST_TIMEOUT", "5"))
    if not base:
        raise RuntimeError("API_BASE_URL이 없습니다.")
    return Settings(app_env=app_env, api_base_url=base, request_timeout=timeout)
```

`lib/ui.py`

```python
import streamlit as st

from lib.api_client import ApiError


def show_error(exc: ApiError) -> None:
    st.error(exc.message)
    fields = (exc.payload.get("error") or {}).get("fields") or {}
    for name, messages in fields.items():
        st.caption(f"{name}: {', '.join(messages)}")
```

`lib/api_client.py`의 `_base`와 `timeout`은 설정을 사용하도록 바뀐 부분만 전체 함수로 적는다. 나머지 메서드는 study6과 같다.

```python
from lib.settings import load_settings


def request_json(method: str, path: str, *, json_body: dict | None = None, params: dict | None = None):
    settings = load_settings()
    try:
        response = requests.request(
            method,
            settings.api_base_url + path,
            headers=_headers(),
            json=json_body,
            params=params,
            timeout=settings.request_timeout,
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
```

`pages/write_page.py`

```python
import streamlit as st

from lib.api_client import ApiError, create_post
from lib.ui import show_error
from lib.validate import validate_post


def render() -> None:
    st.header("작성")
    with st.form("new_post"):
        title = st.text_input("제목")
        body = st.text_area("본문")
        submitted = st.form_submit_button("작성")
    if not submitted:
        return
    fields = validate_post(title.strip(), body.strip())
    if fields:
        show_error(ApiError(400, {"error": {"code": "VALIDATION_ERROR", "message": "입력값을 확인하세요.", "fields": fields}}))
        return
    try:
        create_post(title.strip(), body.strip(), [])
    except ApiError as exc:
        show_error(exc)
        return
    st.success("작성 완료")


render()
```

`.env.example`

```text
APP_ENV=development
API_BASE_URL=http://localhost:8000
REQUEST_TIMEOUT=5
```

운영 프로세스에는 파일 없이 같은 키를 환경변수로 넣는다.

```powershell
$env:APP_ENV = "production"
$env:API_BASE_URL = "https://api.example.com"
$env:REQUEST_TIMEOUT = "5"
streamlit run app.py --server.headless true --server.address 0.0.0.0
```

개발 설정 파일 `.streamlit/config.toml`은 `headless = false`를 유지한다. 운영 명령의 `--server.headless true`가 그 값을 덮어 브라우저를 자동으로 열지 않는다.

### 줄별 설명

- `Settings`: 환경 이름, API 주소, 타임아웃만 담는 불변 객체다. 페이지가 `os.getenv`를 직접 부르지 않게 한다.
- `is_production`: `APP_ENV`가 `production`일 때만 참이다.
- `load_settings`: 운영이 아니면 `.env`를 읽는다. 운영은 이미 들어온 환경변수만 사용한다. 주소가 없으면 기동 시점에 `RuntimeError`로 멈추므로, 잘못된 호스트로 조용히 나가지 않는다.
- `show_error`: study5와 study6에 반복되던 캡션 루프의 단일 구현이다.
- `request_json`의 `settings.api_base_url`: 경로 `/api/posts` 앞의 호스트를 설정 객체가 공급한다.
- `settings.request_timeout`: 호출마다 숫자를 새로 적지 않는다.
- `pages/write_page.py`: 검증, 오류 표시, 작성을 각각 `lib`에 위임한다. 이 파일에는 `http://`가 없다.
- 운영 명령의 `--server.address 0.0.0.0`: 컨테이너 밖에서 8501로 접속하게 한다. 개발 PC의 기본 바인딩과 이 값만 다르다.

## ④ 🔗 연동 포인트

- 개발 `.env`의 `API_BASE_URL=http://localhost:8000`과 운영 환경변수의 `https://api.example.com`은 같은 `load_settings`를 지난다.
- 페이지가 `create_post`만 알면 study14에서 경로 규칙이 바뀌어도 수정 파일은 `lib/api_client.py` 하나다.
- `APP_ENV`는 study10 배포 점검표의 첫 항목이다. 운영 프로세스에 `production`이 보이는지 확인한다.
- study9의 테스트는 `API_BASE_URL`을 가짜 서버 주소로 넣고 `load_settings`가 그 값을 반환하는지만 보면 된다.

## ⑤ 오류 노트

### 운영에서 개발 PC의 localhost로 요청이 나간다

- 증상: 배포 앱의 오류가 연결 실패이고, 로그의 호스트가 `127.0.0.1`이다.
- 원인: 이미지 안에 `.env`가 복사되었고 `APP_ENV`가 `production`이 아니라서 `load_dotenv`가 그 파일을 읽었다.
- 해결: `.dockerignore`와 `.gitignore`에 `.env`를 둔다. 운영 프로세스의 `APP_ENV=production`을 먼저 설정한다.

### 페이지마다 오류 상자 모양이 다르다

- 증상: 한 페이지는 필드 캡션이 있고 다른 페이지는 상태 코드만 있다.
- 원인: `show_error`를 복사하면서 한쪽이 오래되었다.
- 해결: `lib/ui.py`만 남기고 페이지의 지역 함수를 지운다.

### 설정을 매 위젯 입력마다 파일에서 다시 읽고 싶지 않다

- 증상: 없음. 다만 `load_dotenv`를 렌더 함수에서 반복 호출한다.
- 원인: 호출 위치를 페이지에 두었다.
- 해결: `load_settings` 안에서만 읽고, 운영에서는 그 호출이 파일을 찾지 않는다. 요청 한 번의 수명 동안 객체를 지역 변수로 유지한다.

## ⑥ 직접 해보기

1. `.env`의 `REQUEST_TIMEOUT`을 `1`로 바꾼 뒤 서버를 끄고, 실패까지 걸리는 시간이 줄었는지 본다. 확인 후 `5`로 되돌린다.
2. `pages/write_page.py`에서 `http`를 검색해 문자열이 없는지 확인한다.
3. `APP_ENV`를 `production`으로 두고 `.env`를 잠시 다른 이름으로 옮겼을 때, 셸에 `API_BASE_URL`이 있으면 앱이 뜨고 없으면 `RuntimeError`가 나는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `app.py`, `pages/`, `lib/`로 입구·화면·공통 코드를 나눴다.
- [ ] API 주소와 타임아웃은 `lib/settings.py`만 읽는다.
- [ ] 오류 표시는 `lib/ui.show_error` 하나다.
- [ ] 개발은 `.env`, 운영은 프로세스 환경변수와 `APP_ENV=production`으로 나뉜다.
- [ ] 운영 명령에 `.env` 파일을 넣지 않는다.
- [ ] 페이지 파일에 호스트 문자열이 없다.

## ⑧ 다음 단계

폴더가 역할별로 갈라졌으면, study9는 그 순수 함수와 API 클라이언트를 테스트로 고정하고 실패 로그를 읽는 연습을 한다.
