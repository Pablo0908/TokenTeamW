import base64
import uuid
from io import BytesIO

import qrcode
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def generate_badge_token() -> str:
    return str(uuid.uuid4())


# --- Prize-claim tokens (signed, short-lived) ---
# The claim QR shown on a completed attendee's screen carries ONLY this signed token.
# It is an assertion, not authority: a valid signature is necessary but never sufficient —
# the verifier re-checks completion and not-already-claimed server-side on every scan.
# The TTL only mitigates QR forwarding; security does NOT depend on it (the atomic
# claimed-state flip is the real defense).
CLAIM_TTL_SECONDS = 120
_CLAIM_SALT = "prize-claim"


def _claim_serializer() -> URLSafeTimedSerializer:
    # SECRET_KEY falls back to JWT_SECRET in config; create_app refuses to boot without one.
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_CLAIM_SALT)


def sign_claim_token(user_id: str, event_id: str) -> str:
    """Mint a signed, timestamped token binding (user, event). Generated live on the
    attendee's authenticated device at view time."""
    return _claim_serializer().dumps({"u": str(user_id), "e": str(event_id)})


def verify_claim_token(token: str, max_age: int = CLAIM_TTL_SECONDS):
    """Validate signature + TTL. Returns {"u","e"} on success, or None on a bad/expired/
    tampered token. Never raises — callers treat None as a denied scan."""
    if not token:
        return None
    try:
        data = _claim_serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, Exception):
        return None
    if not isinstance(data, dict) or not data.get("u") or not data.get("e"):
        return None
    return {"u": str(data["u"]), "e": str(data["e"])}


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
