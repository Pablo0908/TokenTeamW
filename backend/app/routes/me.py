from flask import Blueprint, request, jsonify

from app.models import user as user_model
from app.utils.auth import jwt_required

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
