import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

ROOT = Path(__file__).resolve().parents[2]
DB_FILE = ROOT / "data" / "study11.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE.as_posix()}")


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


@st.cache_resource
def engine(url: str):
    eng = create_engine(url, pool_pre_ping=True)
    if url.startswith("sqlite"):
        Base.metadata.create_all(eng)
    else:
        Base.metadata.create_all(eng)
    return eng


st.set_page_config(page_title="DB 연결", layout="centered")
st.title("직접 연결한 게시글")
st.caption(URL.split("@")[-1])
eng = engine(URL)
with st.form("local_new"):
    title = st.text_input("제목")
    body = st.text_area("본문")
    submitted = st.form_submit_button("저장")
if submitted and title.strip() and body.strip():
    with Session(eng) as session:
        session.add(Post(title=title.strip(), body=body.strip()))
        session.commit()
    st.success("저장했습니다.")
with Session(eng) as session:
    rows = session.scalars(select(Post).order_by(Post.id.desc()).limit(50)).all()
for row in rows:
    st.subheader(row.title)
    st.write(row.body)
    st.caption(f"id {row.id}")
st.caption("MariaDB는 mysql+pymysql:// , PostgreSQL은 postgresql+psycopg:// , MongoDB는 study11.md의 분기를 사용합니다.")
