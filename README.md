# Streamlit 학습

Python 스크립트 한 파일로 데이터 대시보드와 사내 도구 화면을 만드는 Streamlit 학습 기록이다. 기준 버전은 Streamlit 1.67.0이다. 예제 코드는 각 `study` 문서 안에 있고, 이 저장소는 그 문서를 담는다.

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

## 읽는 순서

`study0.md`에서 환경을 만든 뒤 번호 순서대로 읽는다. `studyMidpoint.md`는 `study10.md` 다음에, `studyFinal.md`는 `study18.md` 다음에 읽는다.

문서의 코드를 실행할 때는 해당 단원의 파일을 빈 폴더에 복사하고, 그 단원의 `streamlit run` 명령을 사용한다. `.env`와 `.streamlit/secrets.toml`은 커밋하지 않는다.

## 저장소

GitHub: https://github.com/samam0234/My_Streamlit_Study
