# study18. AI 연동과 MCP

## ① 목표

업로드한 문서의 발췌만 근거로 요약과 답변을 스트리밍으로 보여주고, 같은 검색을 MCP 도구로도 호출한다.

## ② 📖 이론

### 왜 쓰는지

사내 도구는 긴 문서를 올려 요약한 뒤 "이 문서에 있는 내용만" 묻고 싶을 때가 많다. 노션의 AI 미니 프로젝트 [DocuForge](https://app.notion.com/p/40bd7dec5e2e818d9c91c6fb26dccc4c)가 그 흐름이다. DocuForge는 문서를 올리면 모델이 요약하고, 청크 검색으로 고른 발췌만 근거로 답하며, 답 끝에 `(발췌 1)`처럼 번호를 붙인다. 발췌에 없으면 "찾을 수 없습니다"라고 말한다. 이 단원은 그 흐름을 Streamlit 한 앱의 화면과 작은 MCP 도구로 재현한다. 인증 없는 공개 문서라는 점도 DocuForge MVP와 같다.

### 핵심 개념

- **프롬프트**: 시스템 역할은 "제공된 발췌 안에서만 답하고, 사용한 발췌 번호를 괄호로 적는다"이다. 발췌가 비면 모델 호출 없이 "찾을 수 없습니다"를 반환한다.
- **발췌 선택**: 질문을 공백과 조사 없이 나눈 토큰이 문장에 많이 겹칠수록 상위 문장을 고른다. 임베딩 서버가 없을 때의 학습용 검색이다.
- **스트리밍**: `st.write_stream`이 제너레이터의 문자열 조각을 타자기처럼 이어서 그린다. 키가 없으면 준비된 문장을 조각으로 나눠 같은 함수로 보여 준다.
- **모델 API**: OpenAI 호환 `POST {AI_BASE_URL}/v1/chat/completions`에 `stream: true`를 보낸다. 키는 `AI_API_KEY` 환경변수다.
- **MCP**: 모델이 부를 도구를 작은 서버로 분리한다. 도구 이름은 `search_excerpts`이고, 인자 `query`에 대한 발췌 문자열을 돌려준다. Streamlit 버튼은 그 도구와 같은 함수를 프로세스 안에서 호출하고, 표준 입출력 MCP 서버는 다른 호스트가 같은 함수를 붙잡을 수 있게 연다.

### 비유

발췌 상자는 책갈피가 꽂힌 페이지다. 모델은 그 페이지 밖에 있는 기억을 답에 섞지 않겠다고 약속한 낭독자다. `st.write_stream`은 낭독이 끝나는 것을 기다리지 않고 들리는 대로 받아 적는 속기다. MCP 도구는 낭독자에게 책갈피 페이지를 건네는 창구의 이름표다.

## ③ 🛠️ 실기

환경변수:

```text
AI_BASE_URL=http://localhost:11434
AI_API_KEY=
AI_MODEL=gemma4:12b
```

`AI_MODEL`의 예시는 DocuForge가 요약에 쓴 Ollama 모델 이름이다. 로컬에 그 모델이 없으면 키를 비워 두고 발췌 문장만 스트리밍한다. 키와 베이스 URL이 있을 때만 네트워크 호출을 한다.

### 전체 코드

`lib/doc_ai.py`

```python
import json
import os
from collections.abc import Iterator

import requests


def split_sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            chunks.append(line)
    return chunks


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
```

`mcp_server.py`

```python
from mcp.server.fastmcp import FastMCP

from lib.doc_ai import search_excerpts

mcp = FastMCP("docuforge-notes")
DOCUMENT = ""


@mcp.tool()
def find_excerpts(query: str) -> str:
    """학습 문서 발췌를 검색한다. query는 질문 문장이다."""
    rows = search_excerpts(DOCUMENT, query)
    if not rows:
        return "찾을 수 없습니다"
    return "\n".join(f"(발췌 {row['n']}) {row['text']}" for row in rows)


if __name__ == "__main__":
    mcp.run()
```

실행 전에 `pip install mcp`가 필요하다. `DOCUMENT`는 학습용으로 서버 파일 상단에서 읽게 바꿀 수 있다.

```python
from pathlib import Path

DOCUMENT = Path("data/uploads/note.txt").read_text(encoding="utf-8") if Path("data/uploads/note.txt").exists() else ""
```

`pages/ai_page.py`

```python
import streamlit as st

from lib.doc_ai import search_excerpts, stream_answer
from lib.external import MAX_BYTES

st.header("문서 요약과 질문")
st.caption("DocuForge와 같이 발췌 근거가 있을 때만 답합니다.")

if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""

upload = st.file_uploader("TXT 또는 MD", type=["txt", "md"])
if upload is not None:
    data = upload.getvalue()
    if len(data) > MAX_BYTES:
        st.error("10MB 이하만 올립니다.")
    else:
        st.session_state.doc_text = data.decode("utf-8", errors="replace")
        st.success(f"{len(st.session_state.doc_text)}자를 읽었습니다.")

text = st.session_state.doc_text
if text:
    head = "\n".join(text.splitlines()[:5])
    st.subheader("요약 카드")
    st.write_stream(stream_answer("다섯 줄 안으로 요약하세요.", search_excerpts(text, text[:200])))
    st.caption(head)

question = st.text_input("질문")
if st.button("질문하기", disabled=not text or not question.strip()):
    excerpts = search_excerpts(text, question.strip())
    st.write("근거")
    for item in excerpts:
        st.caption(f"(발췌 {item['n']}) {item['text']}")
    st.write_stream(stream_answer(question.strip(), excerpts))
```

같은 세션에서 MCP 도구 함수를 버튼으로 확인한다.

```python
from mcp_server import find_excerpts

if st.button("MCP 도구로 검색") and question.strip():
    st.code(find_excerpts(question.strip()))
```

표준 입출력으로 서버만 띄울 때는 프로젝트 루트에서 `python mcp_server.py`를 실행한다. 호스트가 이 프로세스를 MCP 클라이언트로 붙잡을 때의 명령은 `python`과 인자 `mcp_server.py`다.

### 줄별 설명

- `split_sentences`: 빈 줄을 제외한 한 줄을 발췌 1건으로 본다. DocuForge의 청크보다 단순한 학습용 단위다.
- `search_excerpts`: 질문 토큰이 줄에 들어 있는 개수를 점수로 삼아 상위 3개를 고른다. 0점 줄은 근거가 아니다.
- `build_prompt`: 시스템 문장이 발췌 밖 답변을 막는다. 사용자 메시지는 발췌 본문과 질문을 나눈다.
- `stream_answer`의 빈 발췌: 네트워크 없이 `찾을 수 없습니다`만 내보낸다.
- 키 없는 분기: 발췌 문장을 단어 단위로 `yield`해 `st.write_stream` 경로를 로컬에서 확인한다.
- `stream=True`: 호환 API의 서버 전송 이벤트를 줄 단위로 읽는다. `data: [DONE]`에서 멈춘다.
- `delta.content`: 토큰 조각이다. 빈 조각은 화면에 넘기지 않는다.
- `FastMCP`: 도구 이름을 함수 이름 `find_excerpts`로 등록한다. 독스트링이 도구 설명이다.
- `mcp.run()`: 표준 입출력으로 MCP 서버를 연다. Streamlit 프로세스와 동시에 같은 파일을 두 번 띄우지 않도록, 화면 버튼은 함수를 직접 부르고 서버 프로세스는 따로 둔다.
- `ai_page`의 크기 검사: study13·study17과 같은 10MB다.
- `st.write_stream`: 제너레이터를 받아 요약 카드와 답변을 순서대로 그린다.
- 근거 캡션: 모델 출력과 별도로, 검색이 고른 `(발췌 n)`을 먼저 보여 준다.

## ④ 🔗 연동 포인트

- 업로더와 10MB 제한은 study13의 `data/uploads` 저장과 study17의 `describe_file` 다음에 온다. 요약은 저장된 경로가 아니라 세션의 텍스트를 우선 사용한다.
- 모델 이름 `gemma4:12b`와 "발췌 번호가 있는 답"은 DocuForge의 요약·질의 동작과 맞춘다. DocuForge의 Vue·Rails·FastAPI 역할은 이 앱에서 화면, 발췌 검색, 모델 호출로 한 프로세스에 모은다.
- `AI_API_KEY`는 `.env`와 운영 비밀에만 둔다. 프롬프트 로그에 키를 찍지 않는다.
- MCP 도구 `find_excerpts`는 화면의 `search_excerpts`와 같은 점수를 쓰므로, 호스트가 도구를 불러도 발췌 번호가 화면과 같다.
- studyFinal의 게시글 본문 요약은 `stream_answer(질문, search_excerpts(본문, 질문))`를 상세 페이지 버튼에 연결하면 된다.

## ⑤ 오류 노트

### 키가 없는데 연결 오류가 난다

- 증상: 빈 `AI_API_KEY`인데 `requests` 예외가 난다.
- 원인: 베이스 URL만 있고 키 검사를 빠뜨렸다.
- 해결: `base`, `key`, `model`이 모두 있을 때만 POST한다. 아니면 발췌 문자열을 조각으로 내보낸다.

### 문서와 상관없는 답이 나온다

- 증상: 모델이 일반 상식을 답한다.
- 원인: 발췌를 프롬프트에 넣지 않았거나 시스템 문장이 없다.
- 해결: `build_prompt`의 발췌 블록을 그대로 보내고, 발췌 리스트가 비면 호출하지 않는다.

### `st.write_stream`이 한 번에만 나타난다

- 증상: 스트리밍 효과 없이 문단이 한 번 나온다.
- 원인: 제너레이터가 아니라 완성된 문자열을 넘겼다.
- 해결: 문자열을 나누는 제너레이터를 넘긴다. `st.write_stream`의 반환값을 다시 `st.write`하지 않아도 화면에는 이미 쓰여 있다.

### MCP 서버와 화면이 `DOCUMENT`를 다르게 본다

- 증상: 버튼 검색과 서버 도구의 발췌가 다르다.
- 원인: 서버의 `DOCUMENT`가 빈 문자열로 고정되어 있다.
- 해결: 서버 시작 시 `data/uploads/note.txt`를 읽고, 화면은 그 파일을 저장한 뒤 서버를 다시 시작한다.

## ⑥ 직접 해보기

1. 세 줄짜리 메모를 올리고, 그중 한 줄에만 있는 단어로 질문했을 때 `(발췌 n)`이 그 줄 번호인지 확인한다.
2. 메모에 없는 단어를 질문했을 때 출력이 `찾을 수 없습니다`인지 확인한다.
3. `python mcp_server.py`가 표준 입력 대기 상태로 뜨는지 확인하고, 화면의 "MCP 도구로 검색"이 같은 문장을 내는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 시스템 프롬프트가 발췌 밖 답변을 막고 발췌 번호를 요구한다.
- [ ] 발췌가 없으면 모델 API를 호출하지 않고 `찾을 수 없습니다`를 반환한다.
- [ ] 키가 없을 때는 발췌 문장을 `st.write_stream`으로 보여 준다.
- [ ] 키가 있을 때는 OpenAI 호환 스트리밍 응답의 `delta.content`를 이어서 보여 준다.
- [ ] MCP 도구 `find_excerpts`가 `search_excerpts`와 같은 번호 형식을 반환한다.
- [ ] DocuForge의 업로드 → 요약 카드 → 근거 질문 순서를 이 페이지에서 따라간다.
- [ ] `AI_API_KEY`를 코드와 로그에 남기지 않는다.

## ⑧ 다음 단계

발췌 근거 답변이 한 페이지에서 보이면, studyFinal은 midpoint 게시판에 DB 선택, 외부 알림, 이 AI 요약, Docker와 자동 테스트를 한 서비스로 묶는다.
