# Streamlit 학습

Python 스크립트 한 파일로 데이터 대시보드와 사내 도구 화면을 만드는 Streamlit 학습 기록이다. 기준 버전은 Streamlit 1.67.0이다. 설명은 `study*.md`에 있고, 실행 코드는 `demo/`, `midpoint/`, `project/`에 있다. 이 환경은 Python 3.10이라 설치 버전은 Streamlit 1.65.0이다. Python 3.11 이상에서는 문서의 1.67도 설치할 수 있다.

노션 페이지: [Streamlit](https://app.notion.com/p/40bd7dec5e2e8153a9aded435174ecbf)

공통으로 호출하는 게시판 계약은 [HTTP · REST · API 설계](https://app.notion.com/p/3d6d7dec5e2e8139adbfd36dd506c65e)의 `/api` 스펙 v1이다. 작성 본문의 키는 `body`다.

## 문서

| 파일 | 내용 |
| --- | --- |
| `study0.md` | 설치, 폴더, 개발 서버, Git, `.env` |
| `study1.md` | 첫 화면, 기본 출력과 입력 |
| `study2.md` | 함수와 모듈, 재실행 모델 |
| `study3.md` | `st.session_state`, JSON 파일 |
| `study4.md` | `pages/` 라우팅, 쿼리, 오류 화면 |
| `study5.md` | 폼, 검증, 400·422 |
| `study6.md` | 스펙 v1 CRUD |
| `study7.md` | 로그인, 해시, XSS·CSRF·CORS |
| `study8.md` | 폴더와 개발·운영 설정 |
| `study9.md` | pytest, AppTest, mock |
| `study10.md` | Docker, HTTPS, 기초 점검 |
| `studyMidpoint.md` | 기초만으로 만드는 작은 게시판 |
| `study11.md` | SQLite, MariaDB, PostgreSQL, MongoDB |
| `study12.md` | pandas 대시보드 |
| `study13.md` | 업로드, 메일, 결제 링크, OIDC |
| `study14.md` | REST 계약, OpenAPI, 페이지 |
| `study15.md` | `st.cache_data`, `st.cache_resource` |
| `study16.md` | GitHub Actions, 로그, 백업 |
| `study17.md` | fragment 알림, 파일 처리 |
| `study18.md` | 발췌 기반 AI, MCP, DocuForge 흐름 |
| `studyFinal.md` | 심화까지 묶은 게시판 |

## 실행

저장소 루트에서 설치한다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

기본값은 `POST_SOURCE=local`이다. 글과 계정은 `data/board.db`에 저장된다. 연습 계정은 `mina@example.com` / `password123`이다.

```powershell
streamlit run demo/study1/app.py
streamlit run midpoint/app.py
streamlit run project/app.py
pytest -q
```

| 실습 | 명령 |
| --- | --- |
| study0 | `streamlit run demo/study0/app.py` |
| study1 | `streamlit run demo/study1/app.py` |
| study2 | `streamlit run demo/study2/app.py` |
| study3 | `streamlit run demo/study3/app.py` |
| study4 | `streamlit run demo/study4/app.py` |
| study5 | `streamlit run demo/study5/app.py` |
| study6~10, midpoint | `streamlit run midpoint/app.py` |
| study11 | `streamlit run demo/study11/app.py` |
| study12 | `streamlit run demo/study12/app.py` |
| study13~17, final | `streamlit run project/app.py` |
| study18 | `streamlit run demo/study18/app.py` |
| API 연습 서버 | `python tools/mock_api.py` |

API 모드로 바꾸려면 `.env`의 `POST_SOURCE=api`로 두고 mock 서버를 먼저 띄운다. 테스트는 `pytest -q`다.

## 읽는 순서

`study0.md`에서 환경을 만든 뒤 번호 순서대로 읽는다. `studyMidpoint.md`는 `study10.md` 다음에, `studyFinal.md`는 `study18.md` 다음에 읽는다.

각 단원은 위 표의 명령으로 실행한다. `.env`와 `.streamlit/secrets.toml`은 커밋하지 않는다.

## 저장소

GitHub: https://github.com/samam0234/My_Streamlit_Study
