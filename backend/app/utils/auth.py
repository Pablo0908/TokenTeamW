from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import request, jsonify, current_app, g


# --- Passwords (bcrypt, cost factor 12) ---

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- JWT (HS256, 8h expiry) ---

def encode_token(user_id: str, role: str, token_version: int = 0) -> str:
    hours = int(current_app.config.get("JWT_EXPIRY_HOURS", 8))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        # Session-revocation version: must match the user's current token_version.
        "tv": int(token_version or 0),
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

        # Re-validate the account on EVERY request so disabling, deleting, or a
        # password change / explicit revocation takes effect immediately (not only at
        # the token's 8h expiry). The fresh doc is stashed on g for decorators/handlers.
        from app.models import user as user_model
        user = user_model.find_by_id(payload.get("sub"))
        if not user:
            return jsonify({"error": "Invalid session. Please sign in again."}), 401
        if user.get("disabled"):
            return jsonify({"error": "This account has been disabled."}), 403
        if int(payload.get("tv", 0)) != int(user.get("token_version", 0)):
            return jsonify({"error": "Your session is no longer valid. Please sign in again."}), 401
        g.current_user_doc = user
        return f(*args, current_user=payload, **kwargs)

    return decorated


def super_admin_required(f):
    """Platform tier. Gates platform-wide actions (e.g. issuing org-creation invites)
    on `platform_role == "super_admin"`, looked up fresh (not carried in the JWT)."""
    @jwt_required
    @wraps(f)
    def decorated(*args, current_user, **kwargs):
        from app.models import user as user_model
        actor = getattr(g, "current_user_doc", None) or user_model.find_by_id(current_user["sub"])
        if not user_model.is_super_admin(actor):
            return jsonify({"error": "Super admin access required."}), 403
        return f(*args, current_user=current_user, **kwargs)

    return decorated


def org_role_required(*roles):
    """Authorize against an org-scoped membership (the multi-tenant authority model).

    The JWT deliberately carries NO org claim (a user may belong to many orgs), so the
    target org is resolved per request from the route: an explicit `org_id` kwarg, else
    the org of the `event_id` / `badge_id` the route addresses. A platform `super_admin`
    (looked up fresh — also not in the JWT) passes any check; otherwise the caller must
    hold one of `roles` ("owner" / "admin" / "staff") in the resolved org.

    Defined now for the org-scoped routes that land in later phases. Existing routes
    keep using jwt_required / staff_required / admin_required unchanged.
    """
    def decorator(f):
        @jwt_required
        @wraps(f)
        def decorated(*args, current_user, **kwargs):
            # Imported lazily to avoid any import-order coupling between utils and models.
            from app.models import user as user_model
            from app.models import event as event_model
            from app.models import badge as badge_model
            from app.models import membership as membership_model

            actor = getattr(g, "current_user_doc", None) or user_model.find_by_id(current_user["sub"])
            if user_model.is_super_admin(actor):
                return f(*args, current_user=current_user, **kwargs)

            org_id = kwargs.get("org_id")
            if not org_id and kwargs.get("event_id"):
                ev = event_model.find_by_id(kwargs["event_id"])
                org_id = str(ev["org_id"]) if ev and ev.get("org_id") else None
            if not org_id and kwargs.get("badge_id"):
                badge = badge_model.find_by_id(kwargs["badge_id"])
                org_id = str(badge["org_id"]) if badge and badge.get("org_id") else None

            if not org_id:
                return jsonify({"error": "Organization could not be resolved for this request."}), 403

            if membership_model.role_in_org(current_user["sub"], org_id) not in roles:
                return jsonify({"error": "You don't have access to this organization."}), 403

            return f(*args, current_user=current_user, **kwargs)

        return decorated

    return decorator
