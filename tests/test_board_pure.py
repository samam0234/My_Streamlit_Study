import os

os.environ["SEED_DEMO"] = "0"
os.environ["APP_ENV"] = "production"
os.environ["POST_SOURCE"] = "local"

from board.contract import page_params
from board.doc_ai import search_excerpts, stream_answer
from board.passwords import hash_password, verify_password
from board.validate import validate_post


def test_validate_post():
    assert "title" in validate_post("", "본문")
    assert validate_post("가" * 201, "본문")["title"] == ["1~200자로 입력하세요."]
    assert validate_post("첫 글", "안녕하세요") == {}


def test_page_params_clamps():
    params = page_params(0, 80, "")
    assert params["page"] == 1
    assert params["limit"] == 50
    assert "q" not in params


def test_password_roundtrip():
    stored = hash_password("password123")
    assert verify_password("password123", stored)
    assert not verify_password("다른값", stored)


def test_excerpts_and_missing():
    text = "첫 줄은 세션 상태를 설명합니다.\n둘째 줄은 캐시를 설명합니다."
    found = search_excerpts(text, "세션")
    assert found and found[0]["n"] == 1
    assert "".join(stream_answer("없는말", [])) == "찾을 수 없습니다"
