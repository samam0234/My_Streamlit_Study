API_PREFIX = "/api"

PATHS = {
    "health": "/health",
    "signup": f"{API_PREFIX}/auth/signup",
    "login": f"{API_PREFIX}/auth/login",
    "logout": f"{API_PREFIX}/auth/logout",
    "me": f"{API_PREFIX}/auth/me",
    "posts": f"{API_PREFIX}/posts",
    "post": f"{API_PREFIX}/posts/{{id}}",
    "comments": f"{API_PREFIX}/posts/{{id}}/comments",
}


def post_path(post_id: int) -> str:
    return PATHS["post"].format(id=post_id)


def clamp_limit(limit: int) -> int:
    if limit < 1:
        return 1
    if limit > 50:
        return 50
    return limit


def page_params(page: int, limit: int, q: str, sort: str = "-createdAt") -> dict:
    safe_page = page if page >= 1 else 1
    allowed = {"createdAt", "-createdAt", "-commentCount"}
    safe_sort = sort if sort in allowed else "-createdAt"
    params = {"page": safe_page, "limit": clamp_limit(limit), "sort": safe_sort}
    if q:
        params["q"] = q
    return params


ERROR_GUIDE = {
    400: "입력 또는 요청 형식 오류",
    401: "로그인 필요 또는 로그인 실패",
    403: "권한 없음",
    404: "없는 자원",
    409: "이메일 중복",
    413: "본문이 너무 큼",
    429: "호출 제한",
    500: "서버 오류",
}
