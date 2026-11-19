# study11. DB 확장

## ① 목표

Streamlit 앱이 SQLite, MariaDB, PostgreSQL, MongoDB 중 하나를 환경변수로 선택해 연결하고, SQLAlchemy와 Mongo 클라이언트 설정의 차이를 코드로 구분한다.

## ② 📖 이론

### 왜 쓰는지

midpoint의 글 원본은 외부 API 뒤에 있다. 사내 도구는 API 없이 앱 프로세스가 DB를 직접 읽는 경우가 많다. 드라이버와 주소만 바꾸면 화면 함수는 같은 게시글 딕셔너리를 받게 만드는 것이 이 단원의 목표다.

### 핵심 개념

- **선택 키**: `DATABASE_URL`. SQL은 SQLAlchemy 엔진, Mongo는 `mongodb://`로 시작해 PyMongo 클라이언트를 만든다.
- **엔진 수명**: `st.cache_resource`가 프로세스 안에서 엔진과 클라이언트를 한 번만 만든다. 재실행마다 연결을 새로 열지 않는다.
- **SQLAlchemy**: SQLite, MariaDB, PostgreSQL은 같은 `Post` 모델과 `Session`을 쓴다. 다른 점은 URL 스킴과 드라이버 패키지다.
- **MongoDB**: 컬렉션에 문서를 넣고 `_id`를 문자열로 바꿔 화면의 `id`와 맞춘다. 트랜잭션 대신 단일 문서 갱신을 기본으로 둔다.
- **비밀**: URL 안의 비밀번호는 `.env`와 운영 환경변수에만 둔다.

### 비유

`DATABASE_URL`은 창고 열쇠의 종류다. SQLAlchemy는 선반 규격이 같은 세 창고(SQLite 서랍, MariaDB, PostgreSQL)를 같은 라벨로 연다. MongoDB는 선반 대신 상자(`posts` 컬렉션)에 서류를 넣는 창고라서 열쇠 판독기만 따로 둔다. 계산대인 화면은 서류 양식만 받고 열쇠 종류를 모른다.

## ③ 🛠️ 실기

패키지:

```text
SQLAlchemy==2.0.44
pymysql==1.1.2
psycopg[binary]==3.2.10
pymongo==4.15.3
```

주소 예:

```text
sqlite:///data/board.db
mysql+pymysql://board:board@localhost:3306/board
postgresql+psycopg://board:board@localhost:5432/board
mongodb://localhost:27017/board
```

### 전체 코드

`lib/db.py`

```python
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import streamlit as st
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PostView:
    id: str
    title: str
    body: str


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/board.db")
    if url.startswith("sqlite:///"):
        os.makedirs("data", exist_ok=True)
    return url


@st.cache_resource
def sql_engine(url: str):
    engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return engine


@st.cache_resource
def mongo_db(url: str):
    from pymongo import MongoClient

    client = MongoClient(url, serverSelectionTimeoutMS=3000)
    return client.get_default_database()


def _use_mongo(url: str) -> bool:
    return url.startswith("mongodb://") or url.startswith("mongodb+srv://")


def list_local_posts() -> list[PostView]:
    url = database_url()
    if _use_mongo(url):
        rows = mongo_db(url)["posts"].find().sort("created_at", -1).limit(50)
        return [PostView(str(row["_id"]), row["title"], row["body"]) for row in rows]
    with Session(sql_engine(url)) as session:
        rows = session.scalars(select(Post).order_by(Post.id.desc()).limit(50))
        return [PostView(str(row.id), row.title, row.body) for row in rows]


def insert_local_post(title: str, body: str) -> PostView:
    url = database_url()
    if _use_mongo(url):
        from datetime import datetime, timezone

        result = mongo_db(url)["posts"].insert_one(
            {"title": title, "body": body, "created_at": datetime.now(timezone.utc)}
        )
        return PostView(str(result.inserted_id), title, body)
    with Session(sql_engine(url)) as session:
        row = Post(title=title, body=body)
        session.add(row)
        session.commit()
        session.refresh(row)
        return PostView(str(row.id), row.title, row.body)
```

`app.py`

```python
import os

import streamlit as st

from lib.db import insert_local_post, list_local_posts

st.set_page_config(page_title="DB 연결", layout="centered")
st.title("직접 연결한 게시글")
st.caption(os.getenv("DATABASE_URL", "sqlite:///data/board.db").split("@")[-1])

with st.form("local_new"):
    title = st.text_input("제목")
    body = st.text_area("본문")
    submitted = st.form_submit_button("저장")
if submitted and title.strip() and body.strip():
    insert_local_post(title.strip(), body.strip())
    st.success("저장했습니다.")

for post in list_local_posts():
    st.subheader(post.title)
    st.write(post.body)
    st.caption(f"id {post.id}")
```

### 줄별 설명

- `Post`: SQL 세 종류의 공통 테이블 모델이다. 정수 id와 길이 200의 제목은 스펙의 제목 길이와 맞춘다.
- `PostView`: 화면이 받는 공통 모양이다. Mongo의 ObjectId도 문자열 `id`로 통일한다.
- `database_url`: 환경변수가 없으면 SQLite 파일을 기본값으로 둔다. SQLite일 때만 `data` 폴더를 만든다.
- `sql_engine`: `create_engine`과 `create_all`을 캐시한다. `pool_pre_ping=True`는 끊긴 MariaDB·PostgreSQL 연결을 다시 확인한다.
- `mongo_db`: URL의 데이터베이스 이름을 기본 DB로 고른다. `mongodb://localhost:27017/board`의 `board`가 그 이름이다.
- `_use_mongo`: 스킴으로 갈래를 나눈다. SQL 모델은 Mongo 경로에서 생성되지 않는다.
- `list_local_posts`: 최신 50건을 `PostView` 리스트로 돌려준다.
- `insert_local_post`: SQL은 `Session.commit`, Mongo는 `insert_one`이다.
- 화면 캡션: URL의 `@` 뒤를 보여 비밀번호가 사용자 정보 앞에 있어도 계정 부분을 화면에 줄인다. SQLite 경로에는 `@`가 없어 전체 경로가 보인다. 비밀번호가 있는 URL은 로그에도 그대로 찍지 않는다.

### 설정 차이

| 항목 | SQLite | MariaDB | PostgreSQL | MongoDB |
| --- | --- | --- | --- | --- |
| URL 스킴 | `sqlite:///` | `mysql+pymysql://` | `postgresql+psycopg://` | `mongodb://` |
| 패키지 | 표준 라이브러리와 SQLAlchemy | `pymysql` | `psycopg` | `pymongo` |
| 테이블 준비 | `create_all` | `create_all` | `create_all` | 컬렉션은 첫 삽입 때 생긴다 |
| 식별자 | 정수 `id` | 정수 `id` | 정수 `id` | `_id`를 문자열로 |
| 캐시 대상 | 엔진 | 엔진 | 엔진 | MongoClient에서 얻은 DB |

화면 코드의 `insert_local_post`와 `list_local_posts` 호출은 네 URL에서 동일하다.

## ④ 🔗 연동 포인트

- midpoint가 쓰던 `API_BASE_URL` 목록과 이 단원의 로컬 목록은 둘 다 `title`, `body`, `id`를 가진다. studyFinal에서 소스를 환경변수 `POST_SOURCE=api|local`로 고른다.
- `st.cache_resource`로 둔 엔진은 study15에서 캐시를 비우는 시점(글 작성 직후)과 연결된다. 데이터 결과 캐시인 `st.cache_data`와 역할을 섞지 않는다.
- 운영의 `DATABASE_URL`은 study10 점검표의 비밀 항목에 추가된다. SQLite 파일을 컨테이너에 남길 때는 볼륨을 마운트해야 재시작 후에도 글이 남는다.
- 공통 API를 계속 쓰는 화면은 이 파일을 호출하지 않는다. 직접 연결은 사내 도구 경로다.

## ⑤ 오류 노트

### MariaDB만 `Access denied`가 난다

- 증상: SQLite는 되는데 MariaDB URL에서 인증 오류가 난다.
- 원인: URL의 사용자, 비밀번호, 데이터베이스 이름이 서버와 다르다.
- 해결: 비밀번호를 코드에 수정해 넣지 말고 `DATABASE_URL`을 바꾼 뒤 프로세스를 다시 시작한다. 엔진은 `cache_resource`라 환경변수를 바꾼 뒤에도 같은 프로세스에 옛 엔진이 남을 수 있다. 재시작이 안전하다.

### PostgreSQL에서 드라이버 모듈이 없다

- 증상: `ModuleNotFoundError: psycopg`.
- 원인: 스킴은 `postgresql+psycopg`인데 패키지가 없다.
- 해결: `psycopg`를 설치한다. SQLite는 추가 드라이버가 필요 없다.

### Mongo 경로인데 SQL 테이블 오류가 난다

- 증상: `posts` 테이블이 없다는 SQL 예외가 Mongo를 쓸 때 나온다.
- 원인: URL이 `mongodb://`로 시작하지 않아 SQL 분기로 들어갔다.
- 해결: 스킴을 확인하고 `_use_mongo` 분기를 먼저 탄다.

### SQLite 파일이 컨테이너 재시작 후 사라진다

- 증상: 저장 직후에는 보이는데 컨테이너를 다시 만들면 비어 있다.
- 원인: `data/board.db`가 컨테이너 파일 시스템에만 있다.
- 해결: 호스트 폴더를 `/app/data`에 마운트하거나, 운영에서는 MariaDB·PostgreSQL URL로 바꾼다.

## ⑥ 직접 해보기

1. 기본 SQLite로 글을 하나 저장하고 `data/board.db` 파일이 생겼는지 확인한다.
2. `DATABASE_URL`만 MariaDB 또는 PostgreSQL로 바꿔 같은 화면에서 저장과 목록이 되는지 확인한다. 서버가 없으면 오류 문장을 원인과 함께 적는다.
3. Mongo URL로 바꾼 뒤 목록의 `id`가 정수 형태가 아닌 문자열인지 화면 캡션으로 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `DATABASE_URL` 하나로 SQLite, MariaDB, PostgreSQL, MongoDB를 고른다.
- [ ] SQL 세 종류는 같은 SQLAlchemy 모델과 세션을 쓴다.
- [ ] Mongo는 컬렉션과 `_id` 문자열로 분리했다.
- [ ] 엔진과 Mongo 클라이언트는 `st.cache_resource`에 둔다.
- [ ] 화면은 `PostView`의 `id`, `title`, `body`만 사용한다.
- [ ] 비밀번호가 든 URL을 로그와 화면에 그대로 남기지 않는다.

## ⑧ 다음 단계

같은 게시글 목록을 숫자와 표로 보여 줄 차례다. study12는 pandas와 Streamlit 차트·표 위젯으로 그 목록을 대시보드에 올린다.
