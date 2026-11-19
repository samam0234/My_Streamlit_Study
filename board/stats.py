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
    dates = frame["createdAt"].dropna().dt.tz_convert("UTC").dt.floor("D")
    counts = dates.value_counts().sort_index()
    counts.index = counts.index.tz_localize(None)
    aligned = counts.reindex(index, fill_value=0)
    return aligned.to_frame(name="posts")
