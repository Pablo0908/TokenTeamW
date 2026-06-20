import re

from flask import Blueprint, request, jsonify

from app.models import user as user_model
from app.utils.auth import jwt_required

me_bp = Blueprint("me", __name__, url_prefix="/me")

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def _profile_shape(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "lastname": user.get("lastname", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "attendee"),
        "username": user.get("username"),
        "avatar": user.get("avatar"),
        "bio": user.get("bio", ""),
        "pinned_badges": user.get("pinned_badges", []),
        "preferences": user_model.merged_preferences(user),
    }


# ── Settings (existing) ────────────────────────────────────────────────────────

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


# ── Profile ────────────────────────────────────────────────────────────────────

@me_bp.route("/profile", methods=["GET"])
@jwt_required
def get_profile(current_user):
    user = user_model.find_by_id(current_user["sub"])
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(_profile_shape(user)), 200


@me_bp.route("/profile", methods=["PATCH"])
@jwt_required
def patch_profile(current_user):
    body = request.get_json(silent=True) or {}
    uid = current_user["sub"]
    update_data = {}

    if "name" in body:
        update_data["name"] = (body["name"] or "").strip()[:60]
    if "lastname" in body:
        update_data["lastname"] = (body["lastname"] or "").strip()[:60]
    if "bio" in body:
        update_data["bio"] = (body["bio"] or "").strip()[:160]

    if "username" in body:
        username = (body["username"] or "").strip()
        if username:
            if not _USERNAME_RE.match(username):
                return jsonify({"error": "Username must be 3–20 characters: letters, numbers and underscores only."}), 400
            username = username.lower()
            existing = user_model.find_by_username(username)
            if existing and str(existing["_id"]) != uid:
                return jsonify({"error": "That username is already taken."}), 409
            update_data["username"] = username
        else:
            update_data["username"] = None

    if "avatar" in body:
        avatar = body.get("avatar")
        if avatar is not None:
            if not isinstance(avatar, str) or not avatar.startswith("data:image/"):
                return jsonify({"error": "Avatar must be an image data URL."}), 400
            if len(avatar) > 200_000:
                return jsonify({"error": "Avatar is too large (max ~150 KB)."}), 400
        update_data["avatar"] = avatar

    user_model.update_profile(uid, update_data)
    user = user_model.find_by_id(uid)
    return jsonify(_profile_shape(user)), 200


@me_bp.route("/check-username", methods=["GET"])
@jwt_required
def check_username(current_user):
    username = (request.args.get("u") or "").strip().lower()
    if not username or not _USERNAME_RE.match(username):
        return jsonify({"available": False}), 200
    existing = user_model.find_by_username(username)
    taken = bool(existing and str(existing["_id"]) != current_user["sub"])
    return jsonify({"available": not taken}), 200


@me_bp.route("/pinned-badges", methods=["PATCH"])
@jwt_required
def patch_pinned_badges(current_user):
    body = request.get_json(silent=True) or {}
    badge_ids = body.get("badge_ids", [])
    if not isinstance(badge_ids, list):
        return jsonify({"error": "badge_ids must be a list."}), 400
    pinned = [str(b) for b in badge_ids[:4]]
    user_model.update_pinned_badges(current_user["sub"], pinned)
    return jsonify({"pinned_badges": pinned}), 200
