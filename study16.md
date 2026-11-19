# study16. 운영, CI/CD

## ① 목표

Docker 이미지와 GitHub Actions로 테스트를 자동 실행하고, 로그와 백업을 배포 전후에 점검표로 확인한다.

## ② 📖 이론

### 왜 쓰는지

한 대의 PC에서만 도는 앱은 재현이 안 된다. CI는 푸시할 때마다 같은 테스트 명령을 실행하고, 이미지는 그 테스트가 통과한 파일로 만든다. 로그는 장애 당시의 상태 코드와 요청 id를 남기고, 백업은 SQLite 파일이나 SQL 덤프를 앱 이미지 밖에 보관한다.

### 핵심 개념

- **Docker**: study10의 Dockerfile이 배포 단위다. 이 단원은 그 이미지를 CI에서 빌드하는 절차를 점검표에 넣는다.
- **GitHub Actions**: `.github/workflows/ci.yml`이 `pytest`를 실행한다. 비밀 키를 워크플로 파일에 적지 않는다.
- **로그**: 표준 출력으로 내보내고 호스트가 수집한다. 비밀번호, 토큰, `DATABASE_URL` 전체를 메시지에 넣지 않는다.
- **백업**: SQLite는 `data/board.db`를 주기적으로 복사한다. MariaDB와 PostgreSQL은 덤프 명령을 DB 서버에서 실행한다. Mongo는 컬렉션 덤프를 같은 일정에 둔다.
- **모니터링**: `/health`가 200 `{ "status": "ok" }`인지, Streamlit 프로세스가 8501을 여는지 확인한다. 이 앱은 공개 API의 헬스와 화면 프로세스를 둘 다 본다.

### 비유

CI는 출고 전 저울이고 Docker는 밀봉 상자다. 로그는 운행 일지고 백업은 상자 밖의 복사 장부다. 저울을 통과하지 않은 상자는 부두지 않고, 장부 사본을 상자 안에만 두지 않는다.

## ③ 🛠️ 실기

아래 파일과 점검표가 이 단원의 구현이다. 애플리케이션 코드는 study10 Dockerfile과 study9 테스트를 그대로 사용한다.

### 전체 코드

`.github/workflows/ci.yml`

```yaml
name: ci
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install
        run: pip install -r requirements.txt
      - name: Test
        env:
          APP_ENV: production
          API_BASE_URL: http://api.test
        run: pytest -q
```

`lib/ops_log.py`

```python
import logging

logger = logging.getLogger("board.ops")


def configure() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def record_health(ok: bool, request_id: str) -> None:
    logger.info("health ok=%s request_id=%s", ok, request_id)
```

백업 명령은 앱 이미지가 아니라 데이터를 가진 호스트에서 실행한다.

```powershell
Copy-Item data\board.db "data\backup\board-$(Get-Date -Format yyyyMMddHHmm).db"
```

SQL 서버를 쓸 때의 덤프는 그 서버의 도구로 한다.

```bash
pg_dump "$DATABASE_URL" --file "backup/board.sql"
mysqldump --single-transaction board > backup/board.sql
```

Mongo 컬렉션은 `mongodump --uri "$DATABASE_URL" --out backup/mongo`로 받는다. URI는 환경변수에서만 읽는다.

### 줄별 설명

- `on.push`와 `pull_request`: 브랜치에 올리는 순간과 검토 요청에서 같은 테스트를 돌린다.
- `actions/checkout@v4`: 저장소 파일을 러너에 받는다.
- `setup-python`의 3.12: Dockerfile의 베이스 이미지와 같은 메이저다.
- `pip install -r requirements.txt`: 로컬과 같은 버전 목록이다.
- `APP_ENV=production`: CI가 개발자 PC의 `.env`에 의존하지 않게 한다.
- `API_BASE_URL=http://api.test`: mock이 가로채는 주소다. 이 주소로 실제 트래픽이 나가면 study9의 패치가 빠진 것이다.
- `record_health`: 참·거짓과 요청 id만 남긴다.
- `Copy-Item`: SQLite 파일을 시각이 적힌 이름으로 복사한다. 원본을 덮어쓰지 않는다.
- `pg_dump`와 `mysqldump`: 서버 쪽 논리 백업이다. 앱 컨테이너가 DB 파일을 직접 복사한다고 가정하지 않는다.

## ④ 🔗 연동 포인트

- Actions의 `pytest`는 study9의 mock 테스트를 그대로 실행한다. 테스트가 진짜 DB를 요구하면 이 워크플로는 실패해야 한다.
- Docker 빌드는 테스트 잡이 성공한 뒤에만 수동 또는 보호된 브랜치에서 실행한다. 이미지 빌드 명령은 study10과 같다.
- 운영 `API_BASE_URL`과 `DATABASE_URL`은 호스트 비밀 저장소에서 컨테이너 환경변수로 주입한다. 워크플로 파일에 운영 값을 적지 않는다.
- 헬스 로그의 `requestId`는 API 오류 본문의 `error.requestId`와 같은 값을 넘겨, 화면에서 본 실패와 로그를 대조한다.
- 백업 파일은 study11에서 고른 DB 종류에 맞는 명령 하나만 스케줄에 둔다.

## ⑤ 오류 노트

### CI에서만 `API_BASE_URL이 없습니다`가 난다

- 증상: 로컬 pytest는 통과하고 Actions는 설정 예외로 실패한다.
- 원인: 로컬은 `.env`가 있고 CI에는 없다.
- 해결: 워크플로 `env`에 `APP_ENV`와 `API_BASE_URL`을 둔다. 테스트는 `.env`를 읽지 않는 분기를 사용한다.

### 이미지 로그에 접속 문자열이 찍힌다

- 증상: 컨테이너 로그에 사용자 이름과 비밀번호가 보인다.
- 원인: 엔진 URL 전체를 `logger.info`에 넘겼다.
- 해결: 드라이버 이름과 호스트 정도만 남기거나, 상태 코드와 request id만 남긴다.

### 백업 파일이 컨테이너를 지우면 함께 사라진다

- 증상: `backup/`이 이미지 재생성 후 없다.
- 원인: 백업 경로가 컨테이너 파일 시스템 안이다.
- 해결: 호스트 볼륨이나 객체 저장소로 복사한다. 점검표에서 컨테이너 밖의 파일 존재를 확인한다.

## ⑥ 직접 해보기

1. 워크플로 파일을 추가한 뒤 로컬에서 같은 환경변수로 `pytest -q`를 실행한다.
2. `record_health(True, "demo-id")`를 한 번 호출해 로그 한 줄에 비밀번호 자리가 없는지 본다.
3. SQLite를 쓰는 경우에만 복사 명령을 실행하고, 복사본 파일 크기가 0이 아닌지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `.github/workflows/ci.yml`이 Python 3.12와 `pytest -q`를 실행한다.
- [ ] CI 환경변수는 가짜 API 주소만 담고 운영 비밀이 없다.
- [ ] Dockerfile 빌드는 테스트 통과 뒤에 한다.
- [ ] 로그 형식에 토큰, 비밀번호, DB URL 전체가 없다.
- [ ] 백업 명령이 앱 이미지 밖 경로를 대상으로 한다.
- [ ] 배포 전 `/health`와 Streamlit 8501 응답을 확인하는 칸이 있다.
- [ ] 컨테이너를 지운 뒤에도 최신 백업 파일을 열 수 있다.

### 배포 전 점검

- [ ] `pytest -q`가 CI와 로컬에서 통과했다.
- [ ] 이미지에 `.env`와 `secrets.toml`이 없다.
- [ ] `APP_ENV=production`이다.
- [ ] `API_BASE_URL`이 운영 HTTPS다.
- [ ] DB를 직접 쓰면 `DATABASE_URL`이 호스트 비밀에만 있다.
- [ ] 백업 파일이 컨테이너 밖에 있다.
- [ ] 로그인, 목록, 작성, 403이 배포 주소에서 동작한다.
- [ ] 로그에 비밀값이 없다.

## ⑧ 다음 단계

출고 절차가 점검표로 남으면, study17은 떠 있는 앱에 주기적 알림과 파일 처리를 붙여 화면이 사용자의 조작 사이에도 새 정보를 읽게 한다.
