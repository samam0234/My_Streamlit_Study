class ApiError(Exception):
    def __init__(self, status: int, payload: dict):
        self.status = status
        self.payload = payload if isinstance(payload, dict) else {}
        error = self.payload.get("error") or {}
        self.message = error.get("message") or f"요청 실패 ({status})"
        super().__init__(self.message)


def error_payload(code: str, message: str, fields: dict | None = None) -> dict:
    error = {"code": code, "message": message, "requestId": "local"}
    if fields:
        error["fields"] = fields
    return {"error": error}
