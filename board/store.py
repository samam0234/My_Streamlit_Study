import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from board.errors import ApiError, error_payload
from board.passwords import hash_password, verify_password
from board.validate import validate_post, validate_signup

REPO = Path(__file__).resolve().parents[1]


def db_path() -> Path:
    raw = os.getenv("LOCAL_DB", "data/board.db")
    path = Path(raw)
    if not path.is_absolute():
        path = REPO / path
    return path


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                nickname TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                tags TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (author_id) REFERENCES users(id)
            );
            """
        )
        _seed(conn)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seed(conn: sqlite3.Connection) -> None:
    if os.getenv("SEED_DEMO", "1") != "1":
        return
    count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if count:
        return
    conn.execute(
        "INSERT INTO users (email, password_hash, nickname) VALUES (?, ?, ?)",
        ("mina@example.com", hash_password("password123"), "mina"),
    )
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("mina@example.com",)).fetchone()["id"]
    stamp = _now()
    conn.execute(
        """
        INSERT INTO posts (title, body, tags, author_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("첫 글", "안녕하세요. 로컬 실습 글입니다.", json.dumps(["intro"]), user_id, stamp, stamp),
    )


def _user_public(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "email": row["email"], "nickname": row["nickname"]}


def _author(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT id, nickname FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"id": row["id"], "nickname": row["nickname"]}


def _post_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "tags": json.loads(row["tags"] or "[]"),
        "author": _author(conn, row["author_id"]),
        "commentCount": 0,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _require_user(conn: sqlite3.Connection, token: str) -> sqlite3.Row:
    if not token:
        raise ApiError(401, error_payload("UNAUTHORIZED", "로그인이 필요합니다."))
    row = conn.execute(
        """
        SELECT users.id, users.email, users.nickname
        FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    ).fetchone()
    if row is None:
        raise ApiError(401, error_payload("UNAUTHORIZED", "로그인이 필요합니다."))
    return row


def signup(email: str, password: str, nickname: str) -> dict:
    email = email.strip().lower()
    nickname = nickname.strip()
    fields = validate_signup(email, password, nickname)
    if fields:
        raise ApiError(400, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", fields))
    init_db()
    with connect() as conn:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise ApiError(409, error_payload("EMAIL_TAKEN", "이미 가입한 이메일입니다."))
        conn.execute(
            "INSERT INTO users (email, password_hash, nickname) VALUES (?, ?, ?)",
            (email, hash_password(password), nickname),
        )
        row = conn.execute("SELECT id, email, nickname FROM users WHERE email = ?", (email,)).fetchone()
        return {"data": _user_public(row)}


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            raise ApiError(401, error_payload("INVALID_CREDENTIALS", "이메일 또는 비밀번호를 확인하세요."))
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, row["id"]))
        return {"data": {"user": _user_public(row), "accessToken": token}}


def logout(token: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def me(token: str) -> dict:
    init_db()
    with connect() as conn:
        row = _require_user(conn, token)
        return {"data": _user_public(row)}


def list_posts(page: int = 1, q: str = "", limit: int = 10) -> dict:
    page = page if page >= 1 else 1
    limit = min(50, max(1, limit))
    init_db()
    with connect() as conn:
        params: list = []
        where = ""
        if q:
            where = "WHERE posts.title LIKE ? OR posts.body LIKE ?"
            like = f"%{q}%"
            params.extend([like, like])
        total = conn.execute(f"SELECT COUNT(*) AS c FROM posts {where}", params).fetchone()["c"]
        rows = conn.execute(
            f"""
            SELECT * FROM posts {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, (page - 1) * limit],
        ).fetchall()
        data = [_post_dict(conn, row) for row in rows]
    total_pages = 0 if total == 0 else (total + limit - 1) // limit
    return {
        "data": data,
        "meta": {"page": page, "limit": limit, "total": total, "totalPages": total_pages, "q": q},
    }


def get_post(post_id: int) -> dict:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            raise ApiError(404, error_payload("NOT_FOUND", "없는 글입니다."))
        return {"data": _post_dict(conn, row)}


def create_post(token: str, title: str, body: str, tags: list[str] | None = None) -> dict:
    title = title.strip()
    body = body.strip()
    fields = validate_post(title, body)
    if fields:
        raise ApiError(400, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", fields))
    init_db()
    with connect() as conn:
        user = _require_user(conn, token)
        stamp = _now()
        cur = conn.execute(
            """
            INSERT INTO posts (title, body, tags, author_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, body, json.dumps(tags or []), user["id"], stamp, stamp),
        )
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return {"data": _post_dict(conn, row)}


def update_post(token: str, post_id: int, title: str, body: str) -> dict:
    title = title.strip()
    body = body.strip()
    fields = validate_post(title, body)
    if fields:
        raise ApiError(400, error_payload("VALIDATION_ERROR", "입력값을 확인하세요.", fields))
    init_db()
    with connect() as conn:
        user = _require_user(conn, token)
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            raise ApiError(404, error_payload("NOT_FOUND", "없는 글입니다."))
        if row["author_id"] != user["id"]:
            raise ApiError(403, error_payload("FORBIDDEN", "이 글을 수정할 수 없습니다."))
        stamp = _now()
        conn.execute(
            "UPDATE posts SET title = ?, body = ?, updated_at = ? WHERE id = ?",
            (title, body, stamp, post_id),
        )
        saved = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return {"data": _post_dict(conn, saved)}


def delete_post(token: str, post_id: int) -> None:
    init_db()
    with connect() as conn:
        user = _require_user(conn, token)
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            raise ApiError(404, error_payload("NOT_FOUND", "없는 글입니다."))
        if row["author_id"] != user["id"]:
            raise ApiError(403, error_payload("FORBIDDEN", "이 글을 삭제할 수 없습니다."))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
