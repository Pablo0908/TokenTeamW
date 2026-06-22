import re

from flask import Blueprint, request, jsonify

from app.models import user as user_model
from app.utils.auth import encode_token, hash_password, check_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@auth_bp.route("/register", methods=["POST"])
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
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if user_model.find_by_email(email):
        return jsonify({"error": "That email is already registered."}), 409

    # Role is forced server-side — never trust a client-sent role.
    user_id = user_model.create_user(name, lastname, email, hash_password(password), role="attendee")
    return jsonify({"message": "Account created", "user_id": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = user_model.find_by_email(email)
    if not user or not check_password(password, user.get("hashed_password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    if user.get("disabled"):
        return jsonify({"error": "This account has been disabled."}), 403

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
