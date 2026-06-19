import base64
import uuid
from io import BytesIO

import qrcode
from flask import current_app


def generate_badge_token() -> str:
    return str(uuid.uuid4())


def build_redeem_url(event_id: str, token: str) -> str:
    base = current_app.config["FRONTEND_URL"].rstrip("/")
    return f"{base}/redeem/{event_id}/{token}"


def generate_qr_data_url(data: str) -> str:
    """Render a scannable QR PNG for `data` and return it as a base64 data URL.

    Error correction H + a quiet-zone border so it scans reliably from print at a booth.
    """
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
