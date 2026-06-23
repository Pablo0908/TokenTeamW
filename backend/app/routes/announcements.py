from flask import Blueprint, request, jsonify

from app.models import announcement as ann_model
from app.models import event as event_model
from app.utils.auth import jwt_required, admin_required

ann_bp = Blueprint("announcements", __name__)


def _serialize(ann):
    event_id = ann.get("event_id")
    event_name = ""
    if event_id:
        ev = event_model.find_by_id(event_id)
        event_name = ev.get("name", "") if ev else ""
    return {
        "id": str(ann["_id"]),
        "title": ann.get("title", ""),
        "body": ann.get("body", ""),
        "event_id": str(event_id) if event_id else None,
        "event_name": event_name,
        "created_at": ann["created_at"].isoformat() if ann.get("created_at") else None,
        "updated_at": ann["updated_at"].isoformat() if ann.get("updated_at") else None,
    }


@ann_bp.route("/announcements", methods=["GET"])
@jwt_required
def list_announcements(current_user):
    return jsonify([_serialize(a) for a in ann_model.all_announcements()]), 200


@ann_bp.route("/admin/announcements", methods=["POST"])
@admin_required
def create_announcement(current_user):
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required."}), 400
    ann_body = (body.get("body") or "").strip()
    event_id = (body.get("event_id") or "").strip() or None
    if event_id and not event_model.find_by_id(event_id):
        return jsonify({"error": "Event not found."}), 404
    ann_id = ann_model.create(title, ann_body, event_id, current_user["sub"])
    return jsonify(_serialize(ann_model.find_by_id(ann_id))), 201


@ann_bp.route("/admin/announcements/<ann_id>", methods=["PUT"])
@admin_required
def update_announcement(current_user, ann_id):
    if not ann_model.find_by_id(ann_id):
        return jsonify({"error": "Announcement not found."}), 404
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required."}), 400
    ann_body = (body.get("body") or "").strip()
    event_id = (body.get("event_id") or "").strip() or None
    if event_id and not event_model.find_by_id(event_id):
        return jsonify({"error": "Event not found."}), 404
    ann_model.update(ann_id, title, ann_body, event_id)
    return jsonify(_serialize(ann_model.find_by_id(ann_id))), 200


@ann_bp.route("/admin/announcements/<ann_id>", methods=["DELETE"])
@admin_required
def delete_announcement(current_user, ann_id):
    if not ann_model.find_by_id(ann_id):
        return jsonify({"error": "Announcement not found."}), 404
    ann_model.delete(ann_id)
    return jsonify({"deleted": True}), 200
