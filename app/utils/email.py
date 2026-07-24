import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from ..core import settings

logger = logging.getLogger("app.email")


def send_email(subject: str, body: str, to: str, html: Optional[str] = None) -> None:
    if not settings.EMAIL_HOST and not settings.EMAIL_HOST_USER:
        logger.info("Email delivery skipped because SMTP settings are not configured. To=%s", to)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_HOST_USER or "no-reply@example.com"
    msg["To"] = to
    if html:
        msg.set_content(body)
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(body)

    host = settings.EMAIL_HOST or "smtp.gmail.com"
    port = settings.EMAIL_PORT or 587
    use_tls = settings.EMAIL_USE_TLS
    username = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    if use_tls:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as server:
            if username and password:
                server.login(username, password)
            server.send_message(msg)
