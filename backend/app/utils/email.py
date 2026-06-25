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


def send_invite_email(to_email: str, token: str, invite_type: str = "org_join",
                      org_name: str = None, inviter: str = None) -> None:
    """Email an invitation, reusing the same SMTP account as the 2FA OTP. The link lands
    on the in-app accept screen (which honors ?token=). Config-gated like send_otp: with no
    MAIL_* set, the link is logged to the console so dev still works."""
    host = os.getenv("MAIL_HOST", "")
    user = os.getenv("MAIL_USER", "")
    password = os.getenv("MAIL_PASSWORD", "")

    frontend = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")
    link = f"{frontend}/invites?token={token}"

    if invite_type == "create_org":
        subject = "You're invited to create an organization on Lyfter"
        intro = "You've been invited to create and run your own organization on Lyfter."
    else:
        subject = f"You're invited to join {org_name or 'an organization'} on Lyfter"
        intro = f"You've been invited to join {org_name or 'an organization'} on Lyfter."
    if inviter:
        intro += f" (invited by {inviter})"

    if not (host and user and password):
        log.warning("=== INVITE (%s) for %s : %s ===", invite_type, to_email, link)
        return

    port = int(os.getenv("MAIL_PORT", "587"))
    from_addr = os.getenv("MAIL_FROM") or user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:460px;margin:0 auto;padding:32px">
      <h2 style="color:#4361EE;margin-bottom:8px">Lyfter invitation</h2>
      <p style="color:#94a3b8">{intro}</p>
      <p style="margin:20px 0">
        <a href="{link}" style="background:#4361EE;color:#fff;text-decoration:none;
           border-radius:10px;padding:12px 22px;display:inline-block;font-weight:600">
          Accept invitation
        </a>
      </p>
      <p style="color:#6B7280;font-size:.85rem">
        Sign in with <strong>{to_email}</strong> to accept. This invitation expires in 14 days.
        If the button doesn't work, paste this link into your browser:<br>{link}
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
