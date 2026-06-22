import secrets
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app import mongo
from app.models import user as user_model
from app.utils.auth import jwt_required, hash_password
from app.utils.email import send_reset_email
from app.routes.auth import _validate_password

_CODE_TTL = 600
_CODE_MAX_ATTEMPTS = 5

# Current-user endpoints. /me/badges lives in badges.py; this owns /me/settings.
me_bp = Blueprint("me", __name__, url_prefix="/me")


@me_bp.route("/settings", methods=["GET"])
@jwt_required
def get_settings(current_user):
    return jsonify(user_model.get_preferences(current_user["sub"])), 200


@me_bp.route("/settings", methods=["PUT"])
@jwt_required
def put_settings(current_user):
    body = request.get_json(silent=True) or {}
    prefs = user_model.update_preferences(current_user["sub"], body)
    if prefs is None:
        return jsonify({"error": "User not found."}), 404
    return jsonify(prefs), 200


@me_bp.route("/password/send-code", methods=["POST"])
@jwt_required
def send_change_password_code(current_user):
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    user = user_model.find_by_id(current_user["sub"])
    if not user or user["email"] != email:
        return jsonify({"error": "Email does not match your account."}), 403

    code = str(secrets.randbelow(1_000_000)).zfill(6)
    mongo.db.change_pwd_codes.replace_one(
        {"user_id": current_user["sub"]},
        {
            "user_id": current_user["sub"],
            "email": email,
            "code": code,
            "attempts": 0,
            "created_at": datetime.now(timezone.utc),
        },
        upsert=True,
    )
    try:
        send_reset_email(email, code)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Failed to send change-pwd email to %s: %s", email, exc)

    return jsonify({"message": "Verification code sent."}), 200


@me_bp.route("/password", methods=["PUT"])
@jwt_required
def change_password(current_user):
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    code = (body.get("code") or "").strip()
    new_pwd = body.get("new_password") or ""

    if not email or not code or not new_pwd:
        return jsonify({"error": "Email, code and new password are required."}), 400

    user = user_model.find_by_id(current_user["sub"])
    if not user or user["email"] != email:
        return jsonify({"error": "Email does not match your account."}), 403

    doc = mongo.db.change_pwd_codes.find_one({"user_id": current_user["sub"]})
    if not doc:
        return jsonify({"error": "Code expired or not found. Request a new one."}), 400

    if doc.get("attempts", 0) >= _CODE_MAX_ATTEMPTS:
        mongo.db.change_pwd_codes.delete_one({"user_id": current_user["sub"]})
        return jsonify({"error": "Too many incorrect attempts. Request a new code."}), 400

    if doc["code"] != code:
        mongo.db.change_pwd_codes.update_one({"user_id": current_user["sub"]}, {"$inc": {"attempts": 1}})
        left = _CODE_MAX_ATTEMPTS - doc.get("attempts", 0) - 1
        return jsonify({"error": f"Incorrect code — {left} attempt(s) remaining."}), 400

    mongo.db.change_pwd_codes.delete_one({"user_id": current_user["sub"]})

    pwd_error = _validate_password(new_pwd)
    if pwd_error:
        return jsonify({"error": pwd_error}), 400

    user_model.update_password(current_user["sub"], hash_password(new_pwd))
    return jsonify({"message": "Password updated successfully."}), 200
