def validate_post(title: str, body: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    if not 1 <= len(title) <= 200:
        fields["title"] = ["1~200자로 입력하세요."]
    if len(body.strip()) < 1:
        fields["body"] = ["본문을 입력하세요."]
    return fields


def validate_signup(email: str, password: str, nickname: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        fields["email"] = ["이메일 형식을 확인하세요."]
    if len(password) < 8:
        fields["password"] = ["8자 이상 입력하세요."]
    if not nickname:
        fields["nickname"] = ["닉네임을 입력하세요."]
    return fields
