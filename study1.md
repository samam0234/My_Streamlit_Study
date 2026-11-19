# study1. Hello World와 기본 문법

## ① 목표

제목, 본문, 입력 위젯으로 첫 응답을 만들고, 저장할 때 서버가 스크립트를 다시 실행하는 과정을 브라우저에서 확인한다.

## ② 📖 이론

### 왜 쓰는지

환경이 준비된 뒤에는 "화면에 무엇이 그려지는가"를 먼저 고정해야 한다. Streamlit의 문법은 HTML 템플릿 문자열이 아니라 Python 함수 호출이다. `st.title`, `st.write`, `st.markdown`이 출력 함수이고, 입력 함수의 반환값이 이번 실행에서 읽은 사용자 값이다.

### 핵심 개념

- **출력 함수**: `st.title`, `st.header`, `st.write`, `st.markdown`, `st.caption`, `st.code`.
- **매직 출력**: 스크립트 맨 앞에 변수 이름만 단독으로 두면 `st.write`와 비슷하게 화면에 나온다. 학습 예제에서는 호출을 눈에 보이게 `st.write`를 쓴다.
- **입력 함수**: `st.text_input`, `st.button`, `st.selectbox`. 함수가 반환하는 값이 현재 값이다.
- **f-string**: 위젯에서 받은 값을 문장에 섞는 Python 기본 문법이다. Streamlit 전용 템플릿 기호는 없다.
- **파일 저장 시 재실행**: 개발 서버가 `app.py` 변경을 감지하면 스크립트를 처음부터 다시 실행한다. 브라우저를 직접 새로고침하지 않아도 화면이 바뀐다.
- **조작 시 재실행**: 버튼을 누르거나 선택값을 바꾸어도 스크립트가 처음부터 다시 실행된다. 이 모델의 구조는 study2에서 다룬다.

### 비유

함수 호출은 진열대에 라벨을 붙이는 일이다. `st.title`은 간판, `st.write`는 설명 카드, `st.text_input`은 주문서다. 손님이 주문서를 고치면 점원은 진열대를 일부만 고치지 않고 카드 더미를 처음부터 다시 읽는다. 그래서 카드에 적힌 순서가 화면의 순서가 된다.

## ③ 🛠️ 실기

### 전체 코드

`app.py`

```python
import streamlit as st

st.set_page_config(page_title="Hello Streamlit", layout="centered")

st.title("안녕하세요, Streamlit")
st.header("기본 출력")
st.write("이 문장은 st.write가 그립니다.")
st.markdown("**굵은 글씨**와 `코드`는 마크다운으로 씁니다.")
st.caption("보조 설명은 caption입니다.")
st.code("streamlit run app.py", language="text")

name = st.text_input("이름", value="방문자")
tool = st.selectbox("오늘 볼 것", ["출력", "입력", "버튼"])
pressed = st.button("인사하기")

message = f"{name}님, 오늘은 {tool}을 봅니다."
st.write(message)
if pressed:
    st.success(f"{name}님, 버튼을 눌렀습니다.")
```

실행은 study0과 같다.

```powershell
streamlit run app.py
```

브라우저 확인:

1. 주소가 `http://localhost:8501`인지 본다.
2. 개발자도구를 연다. Windows에서는 `F12`다.
3. Network 탭에서 `WS` 또는 필터 `streamlit`으로 소켓 연결이 유지되는지 본다. 화면 갱신은 이 연결로 전달된다.
4. `app.py`의 제목을 저장해 고친다. Network를 새로 문서 요청으로 가득 채우지 않고도 제목이 바뀌면 파일 감시 재실행이 동작한 것이다.
5. 버튼을 누른 뒤 Console에 빨간 예외가 없는지 본다. Python 예외는 터미널과 화면의 예외 상자에 함께 나타난다.

### 줄별 설명

- `import streamlit as st`: 화면 함수의 진입점이다.
- `st.set_page_config(...)`: 탭 제목을 `Hello Streamlit`으로 정하고 본문을 가운데 폭으로 둔다. 첫 `st.title`보다 위에 있다.
- `st.title(...)`: 가장 큰 제목이다. 첫 응답인지 확인하는 기준 문장이다.
- `st.header(...)`: 제목보다 한 단계 작은 구역 제목이다.
- `st.write(...)`: 일반 문장을 출력한다. 문자열 외에도 숫자, 리스트, 표를 받을 수 있다.
- `st.markdown(...)`: 마크다운을 렌더링한다. 기본값은 HTML을 실행하지 않는다.
- `st.caption(...)`: 작은 보조 문장이다.
- `st.code(...)`: 고정폭 코드 블록이다. `language="text"`는 명령어를 코드로 보여 주기만 한다.
- `name = st.text_input(...)`: 한 줄 입력을 만들고, 이번 실행의 문자열을 `name`에 담는다. `value`는 세션에 아직 값이 없을 때의 처음 값이다.
- `tool = st.selectbox(...)`: 목록 중 현재 선택 문자열을 반환한다.
- `pressed = st.button(...)`: 이번 실행이 그 버튼 클릭으로 시작되었으면 `True`다. 다음 실행에서는 다시 `False`로 시작한다.
- `message = f"..."`: Python f-string이다. 위젯 값을 문장에 넣는다.
- `st.write(message)`: 방금 만든 문장을 출력한다.
- `if pressed:`: 버튼을 누른 실행에서만 성공 메시지를 추가한다.
- `st.success(...)`: 녹색 상태 상자다.

## ④ 🔗 연동 포인트

- 개발 서버의 파일 감시와 브라우저의 WebSocket이 결과 확인 경로다. 화면이 안 바뀌면 저장 여부와 터미널의 예외를 먼저 본다.
- 개발자도구 Console의 메시지는 프론트 표시 문제, 터미널의 traceback은 Python 문제다. 둘을 같은 시각에 대조한다.
- 이 파일의 `name`, `tool`은 변수일 뿐 다음 실행에 자동으로 남길 설계가 아니다. 위젯이 자기 키로 값을 유지하는 방식은 study3에서 `key`와 `st.session_state`로 잇는다.
- 버튼이 한 번 참이 되었다가 다음 조작에서 거짓이 되는 성질은, study5에서 제출 버튼을 "이번 실행에만 참"으로 다루는 이유다.

## ⑤ 오류 노트

### 제목을 저장했는데 화면이 그대로다

- 증상: 파일을 고쳤는데 브라우저 문장이 이전이다.
- 원인: 다른 폴더의 `app.py`를 실행 중이거나, 저장이 되지 않았다.
- 해결: 터미널의 `streamlit run` 경로와 편집 파일이 같은지 확인한다. 우측 상단의 Rerun이 보이면 한 번 눌러 현재 파일을 다시 실행한다.

### 한글이 터미널에서만 깨진다

- 증상: 브라우저 한글은 정상인데 터미널 traceback의 한글이 깨진다.
- 원인: Windows 콘솔 인코딩이 Python 출력과 다르다.
- 해결: 실행 전에 `$env:PYTHONUTF8 = "1"` 과 `$env:PYTHONIOENCODING = "utf-8"` 를 설정한다. 브라우저 화면의 한글 출력과는 별개로, 로그를 읽기 위한 설정이다.

### 버튼 메시지가 바로 사라지는 것처럼 보인다

- 증상: 성공 상자가 보였다가 입력값을 바꾸는 순간 사라진다.
- 원인: `pressed`는 그 클릭으로 시작된 실행에서만 `True`다. 다른 위젯을 바꾸면 새 실행이 되고 버튼 값은 다시 `False`다.
- 해결: 이번 단원에서는 그 동작을 관찰만 한다. 클릭 사실을 다음 실행까지 남기려면 study3의 `st.session_state`에 기록한다.

## ⑥ 직접 해보기

1. `st.markdown`에 링크 한 줄을 추가하고, 개발자도구 Elements에서 그 문장이 문단으로 생겼는지 확인한다.
2. 이름을 비운 뒤에도 f-string이 오류 없이 "님"만 붙는지 보고, 빈 이름일 때 `st.warning`을 하나 추가한다.
3. Network에서 WebSocket 연결이 하나 유지되는 동안 선택값을 세 번 바꾼다. 문서 전체가 다시 다운로드되지 않고 화면 문장만 바뀌는지 본다.

## ⑦ ☐ 체크리스트

- [ ] `st.title`로 첫 화면의 제목이 보인다.
- [ ] `st.write`와 `st.markdown`의 역할을 나눠 썼다.
- [ ] `text_input`, `selectbox`, `button`의 반환값을 변수로 받았다.
- [ ] f-string으로 입력값을 문장에 넣었다.
- [ ] 파일 저장만으로 화면이 다시 그려지는 것을 확인했다.
- [ ] 브라우저 개발자도구에서 서버와의 WebSocket 연결과 Console을 열었다.
- [ ] 버튼 값이 그 클릭 실행에서만 참이라는 점을 말로 설명할 수 있다.

## ⑧ 다음 단계

출력과 입력 함수가 한 파일에서 동작하면, study2는 그 파일을 함수 단위로 나누고 위젯 조작이 스크립트 전체를 다시 실행하는 모델을 직접 확인한다.
