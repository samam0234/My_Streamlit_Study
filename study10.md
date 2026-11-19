# study10. 배포와 기초 정리

## ① 목표

의존성을 고정해 서버에 올리고, 도메인과 HTTPS가 맡는 역할을 구분한 뒤 기초 구간에서 만든 환경변수·API 연결을 배포 점검표로 확인한다.

## ② 📖 이론

### 왜 쓰는지

로컬 `streamlit run`은 개발자의 PC에서만 산다. 배포는 그 스크립트를 다른 프로세스에서 같은 버전으로 실행하고, 주소만 사용자에게 여는 일이다. Streamlit은 별도의 프론트 빌드 산출물 단계가 약하다. 배포 단위는 Python 패키지 목록과 소스 파일이다.

### 핵심 개념

- **의존성 고정**: `requirements.txt`의 버전을 서버가 그대로 설치한다.
- **프로세스**: `streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0`.
- **도메인**: 사람이 외우는 이름이다. DNS가 그 이름을 서버 IP로 보낸다.
- **HTTPS**: TLS가 브라우저와 그 호스트 사이를 암호화한다. 비밀번호와 토큰이 지나는 운영 주소는 HTTPS를 쓴다. 인증서는 리버스 프록시나 호스팅이 종료하는 경우가 많고, Streamlit 프로세스 자체가 8501에서 HTTP로 듣는 구성이 흔하다.
- **환경변수**: 운영의 `APP_ENV`, `API_BASE_URL`, 시크릿 파일. 이미지와 Git에 넣지 않는다.
- **배포 후 점검**: 헬스, 로그인, 목록, 작성, 삭제, 오류 문장, 비밀값 노출 여부를 순서대로 본다.

### 비유

`requirements.txt`는 포장 목록이다. 서버는 그 목록대로 도구를 챙긴 뒤 같은 조리 카드를 읽는다. 도메인은 가게 간판이고 HTTPS는 계산대와 손님 사이의 가림막이다. 창고 주소(`API_BASE_URL`)는 포장 상자 겉이 아니라 매장 열쇠함에 둔다.

## ③ 🛠️ 실기

### 전체 코드

`requirements.txt`

```text
streamlit==1.67.0
python-dotenv==1.1.1
requests==2.32.5
pytest==8.4.2
```

`Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
COPY pages ./pages
COPY lib ./lib
COPY .streamlit/config.toml ./.streamlit/config.toml
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

`.dockerignore`

```text
.venv
.env
.streamlit/secrets.toml
**/__pycache__
.pytest_cache
data
*.db
```

로컬에서 이미지를 확인하는 명령:

```powershell
docker build -t streamlit-board .
docker run --rm -p 8501:8501 -e APP_ENV=production -e API_BASE_URL=http://host.docker.internal:8000 streamlit-board
```

Windows와 Mac의 `host.docker.internal`은 컨테이너가 개발 PC의 API를 볼 때 쓰는 이름이다. 운영에서는 공개 API의 HTTPS 주소를 `API_BASE_URL`에 넣는다.

커뮤니티 클라우드나 일반 PaaS에 올릴 때는 저장소 루트의 `requirements.txt`와 `app.py`를 진입점으로 지정하고, 대시보드의 Secrets에 `API_BASE_URL`과 인증 비밀을 넣는다. `.streamlit/secrets.toml`을 커밋하지 않는다.

### 줄별 설명

- `python:3.12-slim`: 로컬 학습과 같은  major 버전의 파이썬이다.
- `pip install -r requirements.txt`: 이미지 빌드 시 버전을 고정해 설치한다.
- `COPY` 네 줄: 소스만 넣는다. `.env`는 `.dockerignore`가 제외한다.
- `EXPOSE 8501`: 문서상의 포트다. 실제 공개는 `-p`나 서비스 설정이 한다.
- `CMD`: 헤드리스와 `0.0.0.0`이 운영 기본값이다.
- `docker run -e`: 운영 환경변수를 프로세스에 주입한다. 이미지에 굽지 않는다.
- `host.docker.internal`: 개발용 API 주소다. 운영 값으로 남기지 않는다.

### 기초 구간 총정리

| 단원 | 남긴 것 |
| --- | --- |
| study0 | 가상환경, `streamlit run`, `.gitignore`, `.env` |
| study1 | 출력·입력 함수, 파일 저장 시 재실행, 개발자도구 |
| study2 | 함수·모듈, 폼, 매 상호작용의 재실행 |
| study3 | `st.session_state`의 토큰·폼, JSON 파일 |
| study4 | `pages/`와 `st.navigation`, 쿼리, 오류 화면 |
| study5 | 검증, 400·422, 중복 제출 잠금 |
| study6 | 스펙 v1 CRUD, `error.message`, `API_BASE_URL` |
| study7 | 로그인 토큰, 작성자 버튼, 해시, XSS를 텍스트로 출력 |
| study8 | `lib/settings.py`의 개발·운영 분리 |
| study9 | pytest, mock, AppTest, 오류 10가지 |

## ④ 🔗 연동 포인트

배포 환경에서 환경변수와 DB는 다음 순서로 잇는다.

1. `APP_ENV=production`을 프로세스에 넣는다.
2. `API_BASE_URL`에 운영 API의 HTTPS 원점을 넣는다. 이 앱은 DB 드라이버를 직접 열지 않으므로 DB 비밀번호는 API 서버의 환경변수에 있다.
3. Streamlit이 OAuth나 직접 DB를 갖는 단계(study11, study13)부터 `.streamlit/secrets.toml`에 해당하는 호스트 비밀 저장소를 채운다.
4. 리버스 프록시가 `example.com`의 443을 컨테이너 8501로 넘긴다. 사용자는 HTTPS 도메인만 연다.
5. 배포 뒤 아래 점검표를 순서대로 수행한다.

### 배포 후 점검표

- [ ] `APP_ENV`가 `production`이다.
- [ ] `API_BASE_URL`이 운영 HTTPS 주소이고 `localhost`가 아니다.
- [ ] 저장소와 이미지에 `.env`, `secrets.toml`, DB 파일이 없다.
- [ ] `https://도메인`으로 첫 화면이 열린다.
- [ ] 로그인 후 목록 GET이 `data`를 그린다.
- [ ] 작성 201, 검증 실패 400의 `error.message`가 화면에 나온다.
- [ ] 남의 글 삭제는 403 문장으로 끝난다.
- [ ] 터미널 로그에 토큰과 비밀번호가 없다.

## ⑤ 오류 노트

### 배포 주소가 계속 새로고침된다

- 증상: 브라우저가 하얗거나 WebSocket이 반복 실패한다.
- 원인: 프록시가 WebSocket 업그레이드를 넘기지 않거나, Streamlit의 베이스 경로와 공개 URL이 다르다.
- 해결: 프록시에서 업그레이드 헤더를 전달한다. 하위 경로에 올렸다면 서버 설정의 베이스 URL을 그 경로와 맞춘다.

### 로컬에서는 되는데 배포에서만 API 연결 실패다

- 증상: `API 서버에 연결하지 못했습니다.`
- 원인: 컨테이너 안의 `localhost`는 컨테이너 자신이다.
- 해결: `API_BASE_URL`을 API가 실제로 듣는 주소로 바꾼다. 개발 중 컨테이너에서는 `host.docker.internal`을 쓰고 운영에서는 API 도메인을 쓴다.

### HTTPS 페이지에서만 로그인 쿠키 경고가 난다

- 증상: 브라우저가 보안 쿠키를 거절했다는 메시지가 있다.
- 원인: 공개 URL은 HTTPS인데 인증 쿠키 설정이 보안 속성과 어긋나거나, 리다이렉트 URI가 `http://`로 남아 있다.
- 해결: 운영 `redirect_uri`와 공개 주소를 `https://`로 맞춘다. 이 기초 게시판의 API 토큰은 Bearer 세션이라 쿠키 문제와 별도로, OAuth를 붙인 뒤의 study13 설정에서 다시 확인한다.

## ⑥ 직접 해보기

1. `pytest -q`가 통과한 커밋에서만 Docker 이미지를 만든다.
2. 컨테이너를 `API_BASE_URL` 없이 실행해 설정 오류로 멈추는지 확인한 뒤, 환경변수를 넣고 다시 실행한다.
3. 점검표 8칸을 배포 주소 기준으로 읽고, 아직 호스트가 없으면 로컬 Docker 주소에 대해 표시만 따로 적어 둔다.

## ⑦ ☐ 체크리스트

- [ ] `requirements.txt` 버전이 로컬과 이미지에서 같다.
- [ ] Dockerfile이 `.env`와 시크릿을 복사하지 않는다.
- [ ] 운영 실행은 `headless`와 `0.0.0.0`, 포트 8501이다.
- [ ] 도메인은 이름, HTTPS는 TLS, 앱 포트는 프록시 뒤라는 점을 구분했다.
- [ ] 배포 후 점검표의 환경변수·목록·작성·403·로그를 확인했다.
- [ ] study0부터 study9까지 남긴 연결(세션 토큰, `pages/`, 스펙 v1, 설정 모듈)을 표로 말할 수 있다.

## ⑧ 다음 단계

기초 재료가 한 앱에 모였으면, studyMidpoint는 study0부터 study10까지로만 로그인과 CRUD가 되는 작은 게시판을 처음부터 조립한다.
