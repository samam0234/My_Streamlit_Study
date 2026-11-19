"""스펙 v1 연습용 API. 실행: python tools/mock_api.py"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LOCAL_DB", str(ROOT / "data" / "mock_api.db"))
os.environ.setdefault("SEED_DEMO", "1")
os.environ.setdefault("APP_ENV", "production")

from board.errors import ApiError
from board import source


def _token(header: str | None) -> str:
    if not header:
        return ""
    parts = header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return ""


class Handler(BaseHTTPRequestHandler):
    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _send(self, status: int, payload: dict | None = None, location: str | None = None) -> None:
        body = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if location:
            self.send_header("Location", location)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _fail(self, exc: ApiError) -> None:
        status = exc.status or 500
        self._send(status, exc.payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        token = _token(self.headers.get("Authorization"))
        try:
            if path == "/health":
                self._send(200, {"status": "ok"})
                return
            if path == "/api/auth/me":
                self._send(200, source.me(token))
                return
            if path == "/api/posts":
                page = int((query.get("page") or ["1"])[0])
                limit = int((query.get("limit") or ["10"])[0])
                q = (query.get("q") or [""])[0]
                self._send(200, source.list_posts(page, q, limit, token))
                return
            if path.startswith("/api/posts/"):
                post_id = int(path.split("/")[-1])
                self._send(200, source.get_post(post_id, token))
                return
        except ApiError as exc:
            self._fail(exc)
            return
        except ValueError:
            self._send(400, {"error": {"code": "BAD_REQUEST", "message": "요청을 확인하세요.", "requestId": "local"}})
            return
        self._send(404, {"error": {"code": "NOT_FOUND", "message": "없는 경로입니다.", "requestId": "local"}})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        body = self._read_json()
        token = _token(self.headers.get("Authorization"))
        try:
            if path == "/api/auth/signup":
                payload = source.signup(body.get("email", ""), body.get("password", ""), body.get("nickname", ""))
                self._send(201, payload)
                return
            if path == "/api/auth/login":
                self._send(200, source.login(body.get("email", ""), body.get("password", "")))
                return
            if path == "/api/auth/logout":
                source.logout(token)
                self._send(204, None)
                return
            if path == "/api/posts":
                created = source.create_post(token, body.get("title", ""), body.get("body", ""), body.get("tags") or [])
                post_id = created.get("data", {}).get("id")
                self._send(201, created, location=f"/api/posts/{post_id}")
                return
        except ApiError as exc:
            self._fail(exc)
            return
        self._send(404, {"error": {"code": "NOT_FOUND", "message": "없는 경로입니다.", "requestId": "local"}})

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        body = self._read_json()
        token = _token(self.headers.get("Authorization"))
        try:
            post_id = int(path.split("/")[-1])
            updated = source.update_post(token, post_id, body.get("title", ""), body.get("body", ""))
            self._send(200, updated)
        except ApiError as exc:
            self._fail(exc)
        except ValueError:
            self._send(400, {"error": {"code": "BAD_REQUEST", "message": "글 번호가 올바르지 않습니다.", "requestId": "local"}})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        token = _token(self.headers.get("Authorization"))
        try:
            post_id = int(path.split("/")[-1])
            source.delete_post(token, post_id)
            self._send(204, None)
        except ApiError as exc:
            self._fail(exc)
        except ValueError:
            self._send(400, {"error": {"code": "BAD_REQUEST", "message": "글 번호가 올바르지 않습니다.", "requestId": "local"}})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    os.environ["POST_SOURCE"] = "local"
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("mock API http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
