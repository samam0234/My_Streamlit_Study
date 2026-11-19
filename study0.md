# study0. 환경 설정

기준 버전은 Streamlit 1.67.0(2026-11-05 릴리스)이다. 이후 패치 버전이 깔려도 이 단원의 명령과 폴더 이름은 같다. `streamlit version` 출력으로 설치본을 확인한다.

## ① 목표

가상환경에 Streamlit을 설치하고, 프로젝트 폴더에서 개발 서버를 띄워 첫 화면까지 연다.

## ② 📖 이론

### 왜 쓰는지

Streamlit은 Python 스크립트 한 파일로 데이터 대시보드와 사내 도구 화면을 만든다. 화면 코드와 데이터 처리가 같은 프로세스에서 실행되므로, 집계 결과를 확인하는 도구를 빨리 붙일 때 실용적이다. 기업용 공개 메인 서비스의 자리와는 역할이 다르고, 사내 도구·데이터 확인·데모 화면에 잘 맞는다.

### 핵심 개념

- **스크립트**: `streamlit run`에 넘기는 Python 파일. 위에서 아래로 실행되며 그 실행이 화면이 된다.
- **개발 서버**: 기본 주소는 `http://localhost:8501`. 파일을 저장하면 서버가 스크립트를 다시 실행하고 브라우저가 따라 갱신된다.
- **위젯**: 입력 칸, 버튼처럼 사용자의 조작을 받는 함수.
- **세션**: 브라우저 탭과 서버가 연결을 유지하는 동안의 사용자 한 명 분. 값은 `st.session_state`에 둔다. 자세한 사용은 study3.
- **페이지**: 화면 단위. 여러 파일로 나누는 방법은 study4.
- **시크릿**: API 주소, 비밀번호처럼 저장소에 올리면 안 되는 값. `.env`와 `.streamlit/secrets.toml`에 둔다.

### 비유

스크립트는 조리 카드이고, `streamlit run`은 그 카드를 처음부터 다시 읽는 주방이다. 손님이 버튼을 누르거나 카드를 고치면 주방은 카드를 첫 줄부터 다시 읽는다. 접시(브라우저)에는 이번 읽기의 결과가 올라간다. 소금 단지는 조리 카드에 적지 않고 선반(환경변수)에 둔다.

## ③ 🛠️ 실기

### 설치와 확인 순서

PowerShell에서 프로젝트 루트로 이동한 뒤 아래 순서대로 실행한다.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install "streamlit==1.67.0"
streamlit version
```

macOS와 Linux에서는 활성화 명령만 `source .venv/bin/activate`로 바꾼다.

`python --version`은 3.11 이상을 확인한다. 3.12에서 이 저장소의 예제를 맞췄다. `python -m venv .venv`는 프로젝트 안에만 패키지를 넣는 가상환경을 만든다. `Activate.ps1` 실행 후 프롬프트에 `(.venv)`가 보여야 한다. 실행 정책 오류가 나면 현재 사용자에 대해 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 적용한다. `pip install "streamlit==1.67.0"`이 이 단원의 설치 명령이다. `streamlit version`은 설치된 Streamlit 버전을 출력한다.

에디터에는 다음 확장을 둔다.

- Python (Microsoft): 인터프리터를 `.venv`로 지정한다.
- Pylance: 함수 인자와 반환 타입을 편집 중에 보여 준다.
- Ruff: 저장 시 기본 스타일을 맞춘다.

Streamlit 전용 언어 서버는 필요 없다. 화면 확인은 브라우저가 담당한다.

### 폴더 구조

```text
Streamlit/
├── app.py
├── pages/                  # study4에서 화면 파일을 넣는다
├── lib/                    # study8에서 공통 함수를 넣는다
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml        # Git에 올리지 않는다
├── .env                    # Git에 올리지 않는다
├── .env.example
├── .gitignore
├── requirements.txt
└── study0.md
```

### 전체 코드

`requirements.txt`

```text
streamlit==1.67.0
python-dotenv==1.1.1
```

`.gitignore`

```gitignore
.venv/
__pycache__/
.pytest_cache/
.env
.streamlit/secrets.toml
*.db
.streamlit/cache/
```

`.env.example`

```text
API_BASE_URL=http://localhost:8000
```

`.env`는 `.env.example`을 복사해 만든다. 로컬 값만 적고 커밋하지 않는다.

`.streamlit/config.toml`

```toml
[server]
port = 8501
headless = false
fileWatcherType = "auto"

[browser]
gatherUsageStats = false
```

`.streamlit/secrets.toml` (예시. 파일 자체는 커밋하지 않는다)

```toml
API_BASE_URL = "http://localhost:8000"
```

`app.py`

```python
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Streamlit 실습", layout="centered")
st.title("Streamlit 첫 화면")
st.write("개발 서버가 이 스크립트를 위에서 아래로 실행했습니다.")

api_base = os.getenv("API_BASE_URL", "")
secret_base = st.secrets.get("API_BASE_URL", "")
st.caption(f"환경변수 API_BASE_URL 설정됨: {bool(api_base)}")
st.caption(f"secrets API_BASE_URL 설정됨: {bool(secret_base)}")
st.caption(f"작업 폴더: {Path.cwd()}")
```

개발 서버:

```powershell
streamlit run app.py
```

브라우저가 `http://localhost:8501`을 연다. 제목 "Streamlit 첫 화면"이 보이면 설치와 실행이 끝난 것이다. 끝난 서버는 터미널에서 `Ctrl+C`로 중지한다.

Git 저장소를 새로 만들 때:

```powershell
git init
git add .gitignore .env.example requirements.txt app.py .streamlit/config.toml
git status
```

`.env`와 `.streamlit/secrets.toml`이 스테이징 목록에 없으면 `.gitignore`가 동작하는 것이다.

### 줄별 설명

`app.py`

- `import os`: 환경변수를 읽는다.
- `from pathlib import Path`: 현재 작업 폴더를 화면에 안전한 경로 문자열로 보여 준다.
- `import streamlit as st`: Streamlit 함수를 `st.`로 호출한다.
- `from dotenv import load_dotenv`: `.env` 파일을 프로세스 환경변수로 올린다. Streamlit은 `.env`를 자동으로 읽지 않는다.
- `load_dotenv()`: 프로젝트 루트의 `.env`를 찾는다. 파일이 없어도 예외 없이 지나간다.
- `st.set_page_config(...)`: 브라우저 탭 제목과 본문 폭을 정한다. 다른 `st.` 출력보다 먼저 호출한다.
- `st.title(...)`: 페이지의 큰 제목이다.
- `st.write(...)`: 문장, 숫자, 표 등을 화면에 쓴다.
- `os.getenv("API_BASE_URL", "")`: `.env`에 넣은 주소를 읽는다. 없으면 빈 문자열이다.
- `st.secrets.get(...)`: `.streamlit/secrets.toml`의 같은 키를 읽는다. 시크릿 파일이 없으면 빈 값을 돌려 첫 실행이 멈추지 않게 한다.
- `st.caption(...)`: 값 자체가 아니라 "설정되어 있는가"만 표시한다. 주소 전체를 화면에 반복해서 두지 않는다.
- `Path.cwd()`: `streamlit run`을 실행한 폴더다. 이후 파일 저장 위치의 기준이 된다.

`config.toml`의 `port`는 8501, `headless = false`는 개발 중 브라우저를 연다. `gatherUsageStats = false`는 사용 통계 전송을 끈다.

## ④ 🔗 연동 포인트

이 단원에서 만든 폴더와 환경변수가 다음 단계의 연결점이다.

- Git 저장소는 학습 문서와 `app.py`만 추적한다. `.gitignore`가 `.venv`, `.env`, `secrets.toml`, 로컬 DB 파일을 제외한다.
- `API_BASE_URL`은 study6에서 게시판 API의 베이스 주소가 된다. 코드에 `http://localhost:8000`을 직접 고정하지 않고, 이 환경변수에서 읽는다.
- `.streamlit/secrets.toml`은 비밀번호, OAuth 클라이언트 비밀, DB URL을 두는 자리다. study7과 study11에서 같은 파일을 확장한다.
- 개발 서버를 띄운 상태가 study1의 자동 새로고침과 브라우저 개발자도구 확인의 출발점이다.

## ⑤ 오류 노트

### `streamlit`을 찾을 수 없음

- 증상: `streamlit : 'streamlit' 용어가 cmdlet 이름이 아닙니다` 또는 `command not found`.
- 원인: 가상환경이 꺼져 있거나, 전역 Python에만 패키지가 없다.
- 해결: `.\.venv\Scripts\Activate.ps1` 후 `python -m streamlit version`으로 다시 확인한다. 모듈로 실행되면 그 인터프리터에 설치된 것이다.

### 포트 8501이 이미 사용 중

- 증상: `Port 8501 is already in use`.
- 원인: 이전에 띄운 `streamlit run`이 남아 있다.
- 해결: 그 터미널에서 `Ctrl+C`로 중지한다. 다른 포트가 필요하면 `streamlit run app.py --server.port 8502`로 실행하고, 이후 OAuth 콜백 주소를 쓸 때는 이 포트를 같이 맞춘다.

### `set_page_config`를 두 번 호출하거나 너무 늦게 호출

- 증상: `set_page_config() can only be called once` 또는 호출 순서 오류.
- 원인: `st.title` 뒤에 설정을 두었거나, 저장 중 스크립트가 설정을 두 번 만났다.
- 해결: `set_page_config`를 import와 `load_dotenv()` 다음, 첫 출력 함수 앞에 한 번만 둔다.

### 시크릿 파일 없음

- 증상: `StreamlitSecretNotFoundError`.
- 원인: `st.secrets["API_BASE_URL"]`처럼 대괄호로 읽었는데 toml 파일이 없다.
- 해결: 없는 설정도 화면이 떠야 하는 첫 실행은 `st.secrets.get("API_BASE_URL", "")`를 쓴다. 운영에서 반드시 필요한 값은 예시 파일만 저장소에 두고, 실제 toml은 서버에만 둔다.

## ⑥ 직접 해보기

1. 가상환경을 지운 뒤 `study0`의 명령만 보고 다시 설치하고 `streamlit version` 출력을 메모한다.
2. `app.py`의 제목 문장을 바꾼 뒤 저장한다. 브라우저를 수동으로 새로고침하지 않아도 제목이 바뀌는지 확인한다.
3. `.env`를 일부러 커밋 대상에 넣지 않았는지 `git status`로 확인한다. 목록에 `.env`가 보이면 `.gitignore` 규칙을 고친다.

## ⑦ ☐ 체크리스트

- [ ] Python 3.11 이상을 `python --version`으로 확인했다.
- [ ] `.venv`를 만들고 활성화한 뒤 그 환경에 패키지를 설치했다.
- [ ] `pip install streamlit` → `streamlit run app.py` 로 첫 화면
- [ ] `streamlit version`으로 1.67 계열인지 확인했다.
- [ ] `app.py`, `pages/`, `lib/`, `.streamlit/`, `requirements.txt` 자리를 만들었다.
- [ ] Python, Pylance, Ruff 확장을 설치하고 인터프리터를 `.venv`로 지정했다.
- [ ] `.gitignore`에 `.venv/`, `.env`, `.streamlit/secrets.toml`, `*.db`가 있다.
- [ ] `.env.example`을 복사해 `.env`를 만들었고, Git 상태에 `.env`가 보이지 않는다.
- [ ] 스크립트, 재실행, 위젯, 세션, 시크릿이라는 용어를 한 줄씩 설명할 수 있다.

## ⑧ 다음 단계

첫 화면이 브라우저에 뜬 상태에서, study1은 그 화면에 기본 출력과 입력 위젯을 올리고 개발자도구로 서버와의 연결을 확인한다.
