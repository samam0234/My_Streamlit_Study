# study5. 폼, 입력, 검증

## ① 목표

작성 폼에서 값을 검증해 오류 문장을 보여주고, 제출 버튼을 잠가 중복 전송을 막은 뒤 응답 코드에 따라 성공·입력 오류·기타 오류 화면을 나눈다.

## ② 📖 이론

### 왜 쓰는지

목록과 경로가 있어도 사용자가 보내는 문자열은 비어 있거나 너무 길다. 검증은 두 겹이다. 화면은 빈 값과 길이를 먼저 살펴 불필요한 요청을 줄이고, 서버가 거절하면 그 문장을 그대로 보여 준다. 서버 검증이 최종 기준이다.

### 핵심 개념

- **폼**: `st.form`은 제출 버튼 한 번에 값을 모은다.
- **화면 검증**: 제목 1~200자, 본문 1자 이상. 실패하면 요청을 보내지 않고 `st.error`로 필드 문장을 보여 준다.
- **서버 검증**: 공통 스펙의 검증 실패는 HTTP 400, `error.code`가 `VALIDATION_ERROR`, `error.fields`에 필드별 문장 배열이 있다. 어떤 서버는 아직 422를 주기도 하므로 화면은 400과 422를 같은 입력 오류 분기로 받는다.
- **성공**: 작성 성공은 201이다. 200은 조회·수정·로그인의 성공으로 구분해 둔다.
- **중복 제출**: 저장이 진행 중이면 `st.session_state.saving`을 참으로 두고 제출 버튼을 `disabled`로 잠근다. 요청이 끝나면 반드시 거짓으로 되돌린다.
- **오류 본문**: `error.message`를 `st.error`에 넣는다. `error.fields`는 필드 이름 옆에 캡션으로 푼다.

### 비유

폼은 창구 서류다. 창구 직원이 빈 칸을 보면 서류를 뒤로 돌려주고 도장을 찍지 않는다. 도장을 찍는 동안에는 접수 버튼을 덮어 같은 서류가 두 장 들어가지 않게 한다. 본점(API)이 400이나 422로 돌려보내면 본점이 적은 사유를 창구 유리에 붙인다. 201 도장이 찍히면 접수증만 보여 준다.

## ③ 🛠️ 실기

이 단원은 API 없이도 검증 분기를 재현하도록 `SEND_MODE`를 둔다. `live`는 환경변수 `API_BASE_URL`로 POST하고, `invalid`는 400 본문을, `unprocessable`은 422 본문을, `ok`는 201 본문을 흉내 낸다. study6에서 `live`만 남긴다.

`lib/validate.py`

```python
def validate_post(title: str, body: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    if not 1 <= len(title) <= 200:
        fields["title"] = ["1~200자로 입력하세요."]
    if len(body.strip()) < 1:
        fields["body"] = ["본문을 입력하세요."]
    return fields
```

`app.py`

```python
import os

import requests
import streamlit as st

from lib.validate import validate_post

st.set_page_config(page_title="작성 폼", layout="centered")

if "saving" not in st.session_state:
    st.session_state.saving = False
if "result_code" not in st.session_state:
    st.session_state.result_code = None


def show_api_error(payload: dict) -> None:
    error = payload.get("error") or {}
    st.error(error.get("message") or "입력값을 확인하세요.")
    for name, messages in (error.get("fields") or {}).items():
        st.caption(f"{name}: {', '.join(messages)}")


def fake_response(mode: str) -> tuple[int, dict]:
    if mode == "ok":
        return 201, {"data": {"id": 1, "title": "첫 글", "body": "안녕하세요"}}
    if mode == "unprocessable":
        return 422, {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "입력값을 확인하세요.",
                "fields": {"title": ["1~200자로 입력하세요."]},
            }
        }
    return 400, {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "입력값을 확인하세요.",
            "fields": {"body": ["본문을 입력하세요."]},
        }
    }


def submit_post() -> None:
    if st.session_state.saving:
        return
    title = st.session_state.form_title.strip()
    body = st.session_state.form_body.strip()
    local_fields = validate_post(title, body)
    if local_fields:
        st.session_state.result_code = 400
        st.session_state.result_payload = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "입력값을 확인하세요.",
                "fields": local_fields,
            }
        }
        return

    st.session_state.saving = True
    mode = st.session_state.mode
    try:
        if mode == "live":
            response = requests.post(
                os.environ["API_BASE_URL"].rstrip("/") + "/api/posts",
                json={"title": title, "body": body, "tags": []},
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {st.session_state.get('token', '')}",
                },
                timeout=5,
            )
            status = response.status_code
            payload = response.json() if response.content else {}
        else:
            status, payload = fake_response(mode)
        st.session_state.result_code = status
        st.session_state.result_payload = payload
    except requests.RequestException:
        st.session_state.result_code = 0
        st.session_state.result_payload = {
            "error": {"code": "NETWORK", "message": "API 서버에 연결하지 못했습니다."}
        }
    finally:
        st.session_state.saving = False


st.title("글 작성")
st.selectbox("응답 연습", ["ok", "invalid", "unprocessable", "live"], key="mode")

with st.form("new_post"):
    st.text_input("제목", key="form_title")
    st.text_area("본문", key="form_body")
    st.form_submit_button(
        "작성",
        disabled=st.session_state.saving,
        on_click=submit_post,
    )

if st.session_state.saving:
    st.info("저장 중입니다. 버튼을 다시 누르지 않아도 됩니다.")

code = st.session_state.result_code
payload = st.session_state.get("result_payload") or {}
if code in (200, 201):
    st.success("작성 완료")
    st.write(payload.get("data", {}).get("title", ""))
elif code in (400, 422):
    show_api_error(payload)
elif code not in (None,):
    show_api_error(payload)
```

제목을 비우고 제출하면 요청 없이 400 분기의 필드 문장이 나온다. 모드를 `invalid`로 두고 정상적인 제목·본문을 제출하면 서버 400 문장이, `unprocessable`이면 422 문장이 같은 함수로 표시된다. `ok`는 201 성공 문장이다.

### 줄별 설명

- `validate_post`: 화면 검증이다. 문제 있는 필드만 딕셔너리에 남긴다. 빈 딕셔너리는 통과다.
- `saving`: 요청이 진행 중인지 세션에 적는다. 위젯보다 앞에서 초기화한다.
- `show_api_error`: `error.message`를 `st.error`에, `error.fields`를 캡션에 푼다. 키가 없는 응답도 기본 문장으로 받는다.
- `fake_response`: 연습 모드의 상태 코드와 본문이다. 본문 모양은 공통 스펙의 `error` 객체를 따른다.
- `submit_post` 첫 줄: 이미 저장 중이면 콜백이 바로 돌아간다.
- `local_fields`: 화면 검증에 걸리면 `result_code`만 400으로 남기고 네트워크를 호출하지 않는다.
- `st.session_state.saving = True`: 네트워크 직전에 잠근다. `finally`에서 거짓으로 되돌린다.
- `requests.post`: 본문 키는 `title`, `body`, `tags`다. 공통 스펙 v1의 작성 본문이다.
- `Authorization` 헤더: study3에서 만든 `token` 세션을 싣는다. 아직 로그인이 없으면 빈 Bearer가 되고 서버는 401을 줄 수 있다. 401 화면은 study7에서 로그인으로 잇는다.
- `timeout=5`: 응답이 없을 때 버튼을 무한히 잠그지 않는다.
- `code in (200, 201)`: 성공 화면이다. 작성의 스펙상 성공은 201이고, 200은 같은 성공 분기로 받아 수정 응답도 이 함수를 재사용할 수 있게 한다.
- `code in (400, 422)`: 입력 오류 화면이다. 스펙의 검증 실패는 400이고, 422는 같은 필드 오류 화면으로 받는다.
- 그 외 코드: 연결 실패(0)와 401, 403, 500도 `error.message` 상자로 보여 준다.
- `disabled=st.session_state.saving`: 잠금 플래그가 제출 버튼에 반영된다.

## ④ 🔗 연동 포인트

- 요청 URL은 `{API_BASE_URL}/api/posts`, 메서드는 POST, 성공은 201, 헤더 `Content-Type: application/json; charset=utf-8`과 `Authorization: Bearer`다.
- 응답 분기: 200·201은 성공 화면, 400·422는 필드 오류 화면, 그 외는 `error.message` 화면이다. 401은 study7에서 로그인 페이지로 `st.switch_page`할 조건이 된다.
- 작성 본문의 `body`는 스펙 필드다. 노션 Streamlit 페이지의 최소 코드 스케치는 본문 키를 `content`로 적고 있다. 이 과정은 공통 스펙 v1을 그대로 호출하므로 요청 키는 `body`로 고정한다.
- `show_api_error`는 목록·수정·삭제 실패에도 같은 모양으로 재사용한다. study6의 클라이언트가 이 함수를 가져간다.

## ⑤ 오류 노트

### 버튼을 연타하면 글이 두 번 생긴다

- 증상: 느린 서버에서 같은 글이 둘 이상 만들어진다.
- 원인: 첫 응답 전에 제출 콜백이 다시 들어왔다.
- 해결: `saving`을 요청 전에 참으로 두고 버튼 `disabled`와 콜백 첫 줄의 조기 반환을 함께 둔다. `finally`에서 잠금을 푼다.

### 서버가 HTML을 돌려주는데 JSON 파싱에서 죽는다

- 증상: `requests` 예외 대신 `JSONDecodeError`가 화면에 난다.
- 원인: 프록시나 잘못된 주소가 JSON이 아닌 본문을 200 또는 404로 준다.
- 해결: `response.content`가 있을 때만 `response.json()`을 호출하고, 디코드 실패는 연결 오류와 같은 분기로 바꿔 `error.message`만 보여 준다.

### 422만 처리하고 400 필드가 화면에 안 나온다

- 증상: 스펙을 지키는 서버의 검증 실패가 일반 오류로만 보인다.
- 원인: 분기가 422만 입력 오류로 보았다.
- 해결: 400과 422를 한 분기에서 `show_api_error`로 보낸다.

### 폼 제출 중 `st.success`를 콜백 안에서 호출했다

- 증상: 성공 상자가 간헐적으로 사라지거나 콜백 경고가 난다.
- 원인: 콜백은 본문이 그려지기 전에 실행된다.
- 해결: 콜백은 `result_code`와 `result_payload`만 기록하고, 상자는 콜백 밖의 본문에서 그린다.

## ⑥ 직접 해보기

1. 제목 201자를 넣어 화면 검증 문장 "1~200자로 입력하세요."가 나오는지 확인한다.
2. 모드를 `ok`, `invalid`, `unprocessable`로 바꿔 201, 400, 422가 서로 다른 상자로 보이는지 확인한다.
3. `timeout`을 `0.001`로 잠시 낮춰 연결 실패 분기의 문장이 `st.error`로만 보이는지 확인한 뒤 값을 5로 되돌린다.

## ⑦ ☐ 체크리스트

- [ ] `st.form`과 `st.form_submit_button`으로 제목·본문을 받았다.
- [ ] 제목 1~200자, 본문 필수 검증을 통과하기 전에는 POST하지 않는다.
- [ ] 오류는 `error.message`를 `st.error`로, 필드 문장은 캡션으로 보여 준다.
- [ ] `saving` 플래그와 `disabled`로 중복 제출을 막는다.
- [ ] 200·201은 성공 화면, 400·422는 입력 오류 화면으로 나눈다.
- [ ] 요청 JSON의 본문 키는 `body`다.

## ⑧ 다음 단계

폼이 응답 코드에 따라 화면을 바꾸면, study6은 같은 클라이언트 규칙으로 목록·상세·등록·수정·삭제를 공통 API에 연결한다.
