import os

import pytest

from board.errors import ApiError
from board import store


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_DB", str(tmp_path / "board.db"))
    monkeypatch.setenv("SEED_DEMO", "0")
    monkeypatch.setenv("POST_SOURCE", "local")
    monkeypatch.setenv("APP_ENV", "production")
    store.init_db()
    return tmp_path


def test_signup_login_and_owner_delete(db):
    created = store.signup("mina@example.com", "password123", "mina")
    assert created["data"]["nickname"] == "mina"
    with pytest.raises(ApiError) as dup:
        store.signup("mina@example.com", "password123", "mina")
    assert dup.value.status == 409

    logged = store.login("mina@example.com", "password123")
    token = logged["data"]["accessToken"]
    assert store.me(token)["data"]["email"] == "mina@example.com"

    with pytest.raises(ApiError) as bad:
        store.login("mina@example.com", "wrong-password")
    assert bad.value.status == 401

    post = store.create_post(token, "첫 글", "안녕하세요", ["intro"])
    post_id = post["data"]["id"]
    listed = store.list_posts(1, "첫")
    assert listed["meta"]["total"] == 1
    assert listed["data"][0]["body"] == "안녕하세요"

    other = store.signup("other@example.com", "password123", "other")
    assert other["data"]["id"] != created["data"]["id"]
    other_token = store.login("other@example.com", "password123")["data"]["accessToken"]
    with pytest.raises(ApiError) as forbidden:
        store.delete_post(other_token, post_id)
    assert forbidden.value.status == 403

    store.delete_post(token, post_id)
    with pytest.raises(ApiError) as missing:
        store.get_post(post_id)
    assert missing.value.status == 404


def test_create_requires_login(db):
    with pytest.raises(ApiError) as exc:
        store.create_post("", "제목", "본문", [])
    assert exc.value.status == 401
