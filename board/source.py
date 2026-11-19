import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from board.contract import PATHS, page_params, post_path
from board.errors import ApiError

REPO = Path(__file__).resolve().parents[1]
_loaded = False


def load_settings() -> None:
    global _loaded
    if _loaded:
        return
    if os.getenv("APP_ENV") != "production":
        load_dotenv(REPO / ".env")
    _loaded = True


def use_local() -> bool:
    load_settings()
    return os.getenv("POST_SOURCE", "local") != "api"


def api_base() -> str:
    load_settings()
    raw = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    if not raw:
        raise ApiError(0, {"error": {"code": "CONFIG", "message": "API_BASE_URL이 없습니다."}})
    return raw


def request_json(method: str, path: str, token: str = "", *, json_body: dict | None = None, params: dict | None = None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    timeout = float(os.getenv("REQUEST_TIMEOUT", "5"))
    try:
        response = requests.request(
            method,
            api_base() + path,
            headers=headers,
            json=json_body,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException:
        raise ApiError(0, {"error": {"code": "NETWORK", "message": "API 서버에 연결하지 못했습니다."}}) from None
    if response.status_code == 204:
        return None
    try:
        payload = response.json() if response.content else {}
    except ValueError:
        raise ApiError(
            response.status_code,
            {"error": {"code": "BAD_RESPONSE", "message": "JSON이 아닌 응답입니다."}},
        ) from None
    if not response.ok:
        raise ApiError(response.status_code, payload if isinstance(payload, dict) else {})
    return payload


def signup(email: str, password: str, nickname: str) -> dict:
    if use_local():
        from board.store import signup as local_signup

        return local_signup(email, password, nickname)
    return request_json(
        "POST",
        PATHS["signup"],
        json_body={"email": email, "password": password, "nickname": nickname},
    )


def login(email: str, password: str) -> dict:
    if use_local():
        from board.store import login as local_login

        return local_login(email, password)
    return request_json("POST", PATHS["login"], json_body={"email": email, "password": password})


def logout(token: str) -> None:
    if use_local():
        from board.store import logout as local_logout

        local_logout(token)
        return
    request_json("POST", PATHS["logout"], token)


def me(token: str) -> dict:
    if use_local():
        from board.store import me as local_me

        return local_me(token)
    return request_json("GET", PATHS["me"], token)


def list_posts(page: int, q: str, limit: int = 10, token: str = "") -> dict:
    if use_local():
        from board.store import list_posts as local_list

        return local_list(page, q, limit)
    return request_json("GET", PATHS["posts"], token, params=page_params(page, limit, q))


def get_post(post_id: int, token: str = "") -> dict:
    if use_local():
        from board.store import get_post as local_get

        return local_get(post_id)
    return request_json("GET", post_path(post_id), token)


def create_post(token: str, title: str, body: str, tags: list[str] | None = None) -> dict:
    if use_local():
        from board.store import create_post as local_create

        return local_create(token, title, body, tags or [])
    return request_json(
        "POST",
        PATHS["posts"],
        token,
        json_body={"title": title, "body": body, "tags": tags or []},
    )


def update_post(token: str, post_id: int, title: str, body: str) -> dict:
    if use_local():
        from board.store import update_post as local_update

        return local_update(token, post_id, title, body)
    return request_json("PATCH", post_path(post_id), token, json_body={"title": title, "body": body})


def delete_post(token: str, post_id: int) -> None:
    if use_local():
        from board.store import delete_post as local_delete

        local_delete(token, post_id)
        return
    request_json("DELETE", post_path(post_id), token)
