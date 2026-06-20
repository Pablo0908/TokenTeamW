import re

from flask import Blueprint, request, jsonify, current_app
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app import limiter
from app.models import user as user_model
from app.models import otp as otp_model
from app.utils.auth import encode_token, hash_password, check_password
from app.utils.email import send_otp

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

_PWD_UPPER   = re.compile(r"[A-Z]")
_PWD_LOWER   = re.compile(r"[a-z]")
_PWD_DIGIT   = re.compile(r"\d")
_PWD_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")


def _validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not _PWD_UPPER.search(password):
        return "Password must contain at least one uppercase letter."
    if not _PWD_LOWER.search(password):
        return "Password must contain at least one lowercase letter."
    if not _PWD_DIGIT.search(password):
        return "Password must contain at least one number."
    if not _PWD_SPECIAL.search(password):
        return "Password must contain at least one special character (!@#$…)."
    return None


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per 10 minutes")
def register():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    lastname = (body.get("lastname") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Enter a valid email address."}), 400
    pwd_error = _validate_password(password)
    if pwd_error:
        return jsonify({"error": pwd_error}), 400
    if user_model.find_by_email(email):
        return jsonify({"error": "That email is already registered."}), 409

    user_id = user_model.create_user(name, lastname, email, hash_password(password), role="attendee")
    return jsonify({"message": "Account created", "user_id": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute; 30 per hour")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = user_model.find_by_email(email)
    if not user or not check_password(password, user.get("hashed_password", "")):
        return jsonify({"error": "Invalid credentials"}), 401

    # Credentials are valid — generate and deliver a one-time code.
    code = otp_model.generate(email)
    try:
        send_otp(email, code)
    except Exception as exc:  # noqa: BLE001
        # Log the failure but don't block the user (code is in the DB; they can retry).
        import logging
        logging.getLogger(__name__).error("Failed to send OTP email to %s: %s", email, exc)

    return jsonify({"requires_2fa": True}), 200


@auth_bp.route("/google", methods=["POST"])
@limiter.limit("20 per minute")
def google_auth():
    body = request.get_json(silent=True) or {}
    credential = body.get("credential", "")

    if not credential:
        return jsonify({"error": "Google credential is required."}), 400

    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return jsonify({"error": "Google OAuth is not configured."}), 503

    try:
        info = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    except Exception:
        return jsonify({"error": "Invalid Google token."}), 401

    email = info.get("email", "").lower()
    if not email or not info.get("email_verified"):
        return jsonify({"error": "Google account email is not verified."}), 401

    user = user_model.find_by_email(email)
    if not user:
        # First-time Google sign-in: create the account automatically.
        given = info.get("given_name", "")
        family = info.get("family_name", "")
        user_id = user_model.create_user(given, family, email, hashed_password="", role="attendee")
        user = user_model.find_by_email(email)

    token = encode_token(str(user["_id"]), user["role"])
    return jsonify(
        {
            "token": token,
            "role": user["role"],
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name", ""),
                "lastname": user.get("lastname", ""),
                "email": user["email"],
                "role": user["role"],
                "preferences": user_model.merged_preferences(user),
            },
        }
    ), 200


@auth_bp.route("/verify-2fa", methods=["POST"])
@limiter.limit("10 per minute")
def verify_2fa():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    code = (body.get("code") or "").strip()

    if not email or not code:
        return jsonify({"error": "Email and code are required."}), 400

    ok, err = otp_model.verify(email, code)
    if not ok:
        return jsonify({"error": err}), 401

    user = user_model.find_by_email(email)
    if not user:
        return jsonify({"error": "User not found."}), 404

    token = encode_token(str(user["_id"]), user["role"])
    return jsonify(
        {
            "token": token,
            "role": user["role"],
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name", ""),
                "lastname": user.get("lastname", ""),
                "email": user["email"],
                "role": user["role"],
                "preferences": user_model.merged_preferences(user),
            },
        }
    ), 200
