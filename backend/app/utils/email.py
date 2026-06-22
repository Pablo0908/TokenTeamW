import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)


def send_otp(to_email: str, code: str) -> None:
    host = os.getenv("MAIL_HOST", "")
    user = os.getenv("MAIL_USER", "")
    password = os.getenv("MAIL_PASSWORD", "")

    if not (host and user and password):
        # No SMTP config — print to console so devs can test locally without email.
        log.warning("=== 2FA OTP for %s : %s ===", to_email, code)
        return

    port = int(os.getenv("MAIL_PORT", "587"))
    from_addr = os.getenv("MAIL_FROM") or user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Lyfter code: {code}"
    msg["From"] = from_addr
    msg["To"] = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:420px;margin:0 auto;padding:32px">
      <h2 style="color:#4361EE;margin-bottom:8px">Lyfter verification</h2>
      <p style="color:#94a3b8">
        Enter this code to complete your sign-in. It expires in 10 minutes.
      </p>
      <div style="font-size:2.5rem;font-weight:700;letter-spacing:.35em;
                  color:#4361EE;background:#1A1040;border-radius:12px;
                  padding:16px 24px;display:inline-block;margin:16px 0">
        {code}
      </div>
      <p style="color:#6B7280;font-size:.85rem">
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ctx)
        smtp.login(user, password)
        smtp.sendmail(from_addr, to_email, msg.as_string())


def send_reset_email(to_email: str, code: str) -> None:
    host = os.getenv("MAIL_HOST", "")
    user = os.getenv("MAIL_USER", "")
    password = os.getenv("MAIL_PASSWORD", "")

    if not (host and user and password):
        log.warning("=== PASSWORD RESET code for %s : %s ===", to_email, code)
        return

    port = int(os.getenv("MAIL_PORT", "587"))
    from_addr = os.getenv("MAIL_FROM") or user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reset your Lyfter password: {code}"
    msg["From"] = from_addr
    msg["To"] = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:420px;margin:0 auto;padding:32px">
      <h2 style="color:#4361EE;margin-bottom:8px">Lyfter password reset</h2>
      <p style="color:#94a3b8">
        Use this code to reset your password. It expires in 10 minutes.
      </p>
      <div style="font-size:2.5rem;font-weight:700;letter-spacing:.35em;
                  color:#4361EE;background:#1A1040;border-radius:12px;
                  padding:16px 24px;display:inline-block;margin:16px 0">
        {code}
      </div>
      <p style="color:#6B7280;font-size:.85rem">
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=ctx)
        smtp.login(user, password)
        smtp.sendmail(from_addr, to_email, msg.as_string())
