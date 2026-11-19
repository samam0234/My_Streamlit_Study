import json
import os
from collections.abc import Iterator

import requests


def split_sentences(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def search_excerpts(text: str, query: str, top_k: int = 3) -> list[dict]:
    tokens = [token for token in query.lower().split() if token]
    scored = []
    for index, line in enumerate(split_sentences(text), start=1):
        haystack = line.lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append({"n": index, "text": line, "score": score})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def build_prompt(question: str, excerpts: list[dict]) -> list[dict]:
    sources = "\n".join(f"(발췌 {item['n']}) {item['text']}" for item in excerpts)
    return [
        {
            "role": "system",
            "content": "발췌에 있는 내용만 답하세요. 답 끝에 사용한 발췌 번호를 (발췌 n)처럼 적으세요. 발췌에 없으면 찾을 수 없습니다 라고만 답하세요.",
        },
        {"role": "user", "content": f"발췌:\n{sources}\n\n질문: {question}"},
    ]


def stream_answer(question: str, excerpts: list[dict]) -> Iterator[str]:
    if not excerpts:
        yield "찾을 수 없습니다"
        return
    base = os.getenv("AI_BASE_URL", "").rstrip("/")
    key = os.getenv("AI_API_KEY", "")
    model = os.getenv("AI_MODEL", "")
    if not base or not key or not model:
        fallback = " ".join(f"{item['text']} (발췌 {item['n']})" for item in excerpts)
        for word in fallback.split(" "):
            if word:
                yield word + " "
        return
    response = requests.post(
        base + "/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "stream": True, "messages": build_prompt(question, excerpts)},
        timeout=60,
        stream=True,
    )
    response.raise_for_status()
    for line in response.iter_lines():
        if not line or not line.startswith(b"data:"):
            continue
        data = line.removeprefix(b"data:").strip()
        if data == b"[DONE]":
            break
        payload = json.loads(data.decode("utf-8"))
        delta = payload["choices"][0].get("delta") or {}
        text = delta.get("content") or ""
        if text:
            yield text
