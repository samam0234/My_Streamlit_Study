# study12. 프론트와 UI 연동

## ① 목표

게시글 목록을 pandas DataFrame으로 만들고 `st.dataframe`과 `st.line_chart`로 통계 대시보드를 그리며, 필터 상태는 세션에, 조건 입력은 폼에 둔다.

## ② 📖 이론

### 왜 쓰는지

목록 화면은 글을 읽는 자리이고, 대시보드는 같은 글을 날짜별 개수로 보는 자리다. Streamlit은 표와 차트를 함수로 그린다. pandas는 그 함수에 넘길 표를 만드는 도구다.

### 핵심 개념

- **표**: `pandas.DataFrame`이 열 이름을 가진 표다. `st.dataframe`이 그 표를 스크롤 가능한 격자로 보여 준다.
- **차트**: `st.line_chart`는 인덱스를 가로축, 숫자 열을 세로축으로 그린다. 날짜별 글 수에 맞다.
- **상태**: 선택한 기간(7일, 30일)은 `st.session_state.range_days`에 둔다. 재실행 후에도 같은 필터가 남는다.
- **폼**: 기간과 태그 조건을 `st.form`에 모아 제출 한 번에 필터를 적용한다. 슬라이더를 드래그하는 동안 차트가 반복 계산되지 않는다.
- **화면 전용 라이브러리**: 추가 격자가 필요하면 `st.column_config`로 열 형식을 지정한다. 차트 꾸미기가 더 필요하면 `plotly` 그림을 `st.plotly_chart`에 넘긴다. 상태 저장소와 폼 런타임은 Streamlit의 세션과 폼이 담당한다.

### 비유

DataFrame은 모눈 장부다. `st.dataframe`은 장부를 유리 진열장에 넣는 일이고, `st.line_chart`는 장부의 날짜 열만 떼어 벽 그래프에 옮기는 일이다. 폼은 장부를 몇 일치 볼지 적는 신청서라서, 신청서를 내기 전에는 벽 그래프를 다시 그리지 않는다.

## ③ 🛠️ 실기

`pandas`를 requirements에 추가한다.

```text
pandas==2.3.3
```

### 전체 코드

`lib/stats.py`

```python
from datetime import datetime, timedelta, timezone

import pandas as pd


def posts_frame(posts: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(posts, columns=["id", "title", "createdAt", "commentCount"])
    if frame.empty:
        return frame
    frame["createdAt"] = pd.to_datetime(frame["createdAt"], utc=True, errors="coerce")
    frame["commentCount"] = pd.to_numeric(frame["commentCount"], errors="coerce").fillna(0)
    return frame


def daily_counts(frame: pd.DataFrame, days: int, today: datetime | None = None) -> pd.DataFrame:
    today = today or datetime.now(timezone.utc)
    start = (today - timedelta(days=days - 1)).date()
    index = pd.date_range(start, periods=days, freq="D")
    if frame.empty or "createdAt" not in frame:
        return pd.DataFrame({"posts": 0}, index=index)
    dates = frame["createdAt"].dt.tz_convert("UTC").dt.floor("D")
    counts = dates.value_counts().sort_index()
    counts.index = counts.index.tz_localize(None)
    aligned = counts.reindex(index, fill_value=0)
    return aligned.to_frame(name="posts")
```

`pages/dashboard_page.py`

```python
from datetime import datetime, timezone

import streamlit as st

from lib.api_client import ApiError, list_posts
from lib.stats import daily_counts, posts_frame
from lib.ui import show_error


def render() -> None:
    st.header("게시글 통계")
    if "range_days" not in st.session_state:
        st.session_state.range_days = 7

    with st.form("range_form"):
        days = st.selectbox("기간(일)", [7, 14, 30], index=[7, 14, 30].index(st.session_state.range_days))
        submitted = st.form_submit_button("필터 적용")
    if submitted:
        st.session_state.range_days = int(days)

    try:
        payload = list_posts(1, "")
    except ApiError as exc:
        show_error(exc)
        return

    rows = []
    for post in payload.get("data") or []:
        rows.append(
            {
                "id": post.get("id"),
                "title": post.get("title"),
                "createdAt": post.get("createdAt"),
                "commentCount": post.get("commentCount", 0),
            }
        )
    frame = posts_frame(rows)
    chart = daily_counts(frame, int(st.session_state.range_days), datetime.now(timezone.utc))
    st.metric("이번 페이지 글 수", int(len(frame)))
    st.line_chart(chart, y="posts")
    st.dataframe(frame, hide_index=True, width="stretch")


render()
```

`app.py`의 `st.navigation` 목록에 `st.Page("pages/dashboard_page.py", title="통계", icon="📈")`를 추가한다.

샘플로 API 없이 차트를 확인하려면 `posts_frame`에 아래 리스트를 넣어 함수만 호출해 본다.

```python
sample = [
    {"id": 1, "title": "첫 글", "createdAt": "2026-11-01T09:00:00Z", "commentCount": 2},
    {"id": 2, "title": "둘째 글", "createdAt": "2026-11-02T09:00:00Z", "commentCount": 0},
]
```

### 줄별 설명

- `posts_frame`: 필요한 네 열만 남긴다. 입력이 비어도 열 이름은 유지한다.
- `to_datetime(..., utc=True)`: 스펙의 ISO 8601 UTC 문자열을 시계열로 바꾼다. 깨진 값은 `NaT`가 되어 차트에서 빠진다.
- `daily_counts`: 선택한 일수만큼의 날짜 인덱스를 먼저 만든다. 글이 없는 날은 0이다. 이렇게 해야 선이 날짜를 건너뛰지 않는다.
- `tz_localize(None)`: 일 단위 인덱스와 맞추기 위해 UTC 자정 시각의 타임존 표시를 걷어 낸다. 비교 기준은 여전히 UTC 달력이다.
- `range_days` 초기화: 세션에 없을 때만 7이다.
- 폼의 `selectbox`: 제출 전에는 `st.session_state.range_days`를 바꾸지 않는다. 제출 콜백 대신 본문에서 `submitted`가 참일 때만 반영한다. 이 대입은 위젯 키가 아니라 `range_days`라서 위젯 충돌이 없다.
- `list_posts(1, "")`: 통계의 입력은 공통 API 목록의 `data`다. 이 예제는 첫 페이지를 집계한다. 전체 합계가 필요하면 `meta.totalPages`만큼 반복한다. 그 반복은 study14의 페이지 버튼과 함께 붙인다.
- `st.metric`: 표의 행 수를 숫자 칸으로 보여 준다.
- `st.line_chart(chart, y="posts")`: `posts` 열만 선으로 그린다.
- `st.dataframe(..., hide_index=True)`: 원본 글을 격자으로 보여 준다. `width="stretch"`는 부모 폭에 맞춘다.

## ④ 🔗 연동 포인트

- 차트의 원본은 `GET /api/posts`의 `createdAt`과 `commentCount`다. 필드 이름이 스펙과 같아야 `posts_frame`이 열을 찾는다.
- 필터 일수는 세션에만 있다. 주소에 남기려면 `st.query_params["days"]`에 같은 숫자를 쓴다. 목록 페이지의 `page` 쿼리와 나란히 두면 새로고침 후에도 필터가 유지된다.
- `commentCount` 열은 이후 막대 계열을 추가할 때 DataFrame에 `comments` 집계를 더하는 자리이다.
- 대시보드 페이지를 `st.navigation`에 등록하면 midpoint 앱의 메뉴에 통계가 붙는다. DB를 직접 읽는 study11 경로는 `PostView`에 `created_at`을 ISO 문자열로 넣어 같은 `posts_frame`에 넘긴다.

## ⑤ 오류 노트

### 차트는 있는데 날짜가 하루씩 밀린다

- 증상: UTC 새벽 글이 전날 칸에 들어간다.
- 원인: 타임존 없는 문자열을 로컬 시간으로 해석했다.
- 해결: `utc=True`로 파싱하고 일 단위도 UTC로 자른다.

### `st.line_chart`가 열을 못 찾는다

- 증상: 차트 자리에 예외가 나고 `posts`가 없다고 한다.
- 원인: `daily_counts`가 시리즈를 그대로 반환했다.
- 해결: `to_frame(name="posts")`로 열 이름을 만든다.

### 필터를 바꿔도 첫 화면 일수가 남는다

- 증상: 30일을 골랐는데 다시 7일이다.
- 원인: 매 실행마다 `st.session_state.range_days = 7`을 호출했다.
- 해결: 키가 없을 때만 7을 넣는다.

### 빈 목록에서 열이 없어 키 오류가 난다

- 증상: 글이 0건일 때 `createdAt` 접근이 실패한다.
- 원인: 빈 DataFrame을 열 이름 없이 만들었다.
- 해결: `columns=[...]`를 지정하고 `daily_counts`의 `empty` 분기를 먼저 반환한다.

## ⑥ 직접 해보기

1. 샘플 두 건으로 `daily_counts`를 7일로 만들어 글이 없는 날이 0인지 확인한다.
2. 폼에서 30일을 적용한 뒤 다른 페이지에 갔다가 통계로 돌아와 세션의 30일이 남는지 확인한다.
3. `st.dataframe`에서 `commentCount`가 숫자가 아닌 글이 0으로 바뀌는지, 원문에 그 값이 없을 때를 포함해 본다.

## ⑦ ☐ 체크리스트

- [ ] pandas DataFrame + `st.dataframe`, `st.line_chart` 로 게시글 통계 대시보드
- [ ] 날짜 축은 UTC ISO 문자열에서 만들고 빈 날은 0이다.
- [ ] 기간 필터는 폼 제출 때에만 `st.session_state.range_days`를 바꾼다.
- [ ] 대시보드의 입력은 목록 API의 `createdAt`, `commentCount`다.
- [ ] 빈 목록도 열 이름이 있는 표와 0으로 채운 차트로 그린다.

## ⑧ 다음 단계

표와 차트가 목록 API를 읽기 시작했다. study13은 그 앱에 메일, 파일 업로드, 결제 링크, 소셜 로그인을 연결한다.
