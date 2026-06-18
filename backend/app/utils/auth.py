from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import request, jsonify, current_app


# --- Passwords (bcrypt, cost factor 12) ---

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- JWT (HS256, 8h expiry) ---

def encode_token(user_id: str, role: str) -> str:
    hours = int(current_app.config.get("JWT_EXPIRY_HOURS", 8))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=hours),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])


# --- Decorators (inject current_user into the handler) ---

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token missing."}), 401
        try:
            payload = decode_token(auth_header.split(" ", 1)[1])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Your session has expired. Please sign in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session. Please sign in again."}), 401
        return f(*args, current_user=payload, **kwargs)

    return decorated


def admin_required(f):
    @jwt_required
    @wraps(f)
    def decorated(*args, current_user, **kwargs):
        if current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required."}), 403
        return f(*args, current_user=current_user, **kwargs)

    return decorated


def staff_required(f):
    """Admin OR assistant. Used for read-only staff views (user directory, badge
    tokens/QRs); write operations stay behind admin_required."""
    @jwt_required
    @wraps(f)
    def decorated(*args, current_user, **kwargs):
        if current_user.get("role") not in ("admin", "assistant"):
            return jsonify({"error": "Staff access required."}), 403
        return f(*args, current_user=current_user, **kwargs)

    return decorated
