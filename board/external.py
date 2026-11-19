import smtplib
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

from board.paths import REPO

MAX_BYTES = 10 * 1024 * 1024


def save_upload(name: str, data: bytes) -> Path:
    if len(data) > MAX_BYTES:
        raise ValueError("업로드는 10MB 이하만 받습니다.")
    folder = REPO / "data" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / Path(name).name
    target.write_bytes(data)
    return target


def _smtp():
    try:
        smtp = st.secrets.get("smtp")
    except Exception:
        return None
    if not smtp or "host" not in smtp:
        return None
    return smtp


def send_signup_mail(to_addr: str, nickname: str) -> str:
    body = f"{nickname}님, 가입을 확인했습니다."
    smtp = _smtp()
    if not smtp:
        return "연습 모드: " + body
    message = EmailMessage()
    message["Subject"] = "가입 안내"
    message["From"] = smtp["from_addr"]
    message["To"] = to_addr
    message.set_content(body)
    with smtplib.SMTP(smtp["host"], int(smtp["port"]), timeout=10) as client:
        client.starttls()
        client.login(smtp["user"], smtp["password"])
        client.send_message(message)
    return "가입 안내 메일을 보냈습니다."
