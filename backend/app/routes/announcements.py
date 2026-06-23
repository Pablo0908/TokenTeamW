from flask import Blueprint, request, jsonify

from app.models import announcement as announcement_model
from app.models import event as event_model
from app.models import user as user_model
from app.models import audit as audit_model
from app.utils.auth import jwt_required, super_admin_required

# Announcements are platform-wide: readable by every authenticated user, but only a
# super_admin may create/edit/delete. The write gate is enforced server-side via
# `super_admin_required` (platform_role), never trusting the client.
announcements_bp = Blueprint("announcements", __name__, url_prefix="/announcements")


def _event_lookup(items):
    """One query for all distinct events referenced by `items` -> {id_str: event_doc},
    so we attach event metadata without a query per announcement."""
    ids = {a["event_id"] for a in items if a.get("event_id")}
    if not ids:
        return {}
    return {str(ev["_id"]): ev for ev in (event_model.find_by_id(i) for i in ids) if ev}


@announcements_bp.route("", methods=["GET"])
@announcements_bp.route("/", methods=["GET"])
@jwt_required
def list_announcements(current_user):
    """All announcements, newest first, visible to any authenticated user. Each entry
    carries an `unread` flag (created after the viewer's last-seen time) and the
    payload includes an `unread_count` to drive the home badge."""
    actor = user_model.find_by_id(current_user["sub"])
    seen_at = actor.get("announcements_seen_at") if actor else None

    items = announcement_model.list_all()
    events = _event_lookup(items)
    out = [
        announcement_model.public(a, event=events.get(str(a["event_id"])) if a.get("event_id") else None, seen_at=seen_at)
        for a in items
    ]
    unread_count = sum(1 for a in out if a["unread"])
    return jsonify({"announcements": out, "unread_count": unread_count}), 200


@announcements_bp.route("/seen", methods=["POST"])
@jwt_required
def mark_seen(current_user):
    """Mark all announcements as read for the caller (stamps last-seen = now)."""
    user_model.mark_announcements_seen(current_user["sub"])
    return jsonify({"message": "ok"}), 200


def _resolve_event_id(raw):
    """Validate an optional event_id from the request: returns (event_id|None, error).
    A blank/None value is allowed (general announcement); a non-empty value must
    resolve to a real event."""
    if not raw:
        return None, None
    if not event_model.find_by_id(raw):
        return None, "The selected event could not be found."
    return raw, None


def _maybe_enable_event(actor_id, event_id, enable_event):
    """When the 'enable event' box is ticked and an event is linked, force-start that
    event so it is scannable now. No-op otherwise. Logged for the audit trail."""
    if not (event_id and enable_event):
        return
    ev = event_model.find_by_id(event_id)
    if not ev or ev.get("started"):
        return
    event_model.set_started(event_id, True)
    audit_model.log(actor_id, "event.start", f'{ev.get("name", "")} (via announcement)',
                    org_id=ev.get("org_id"), event_id=str(ev["_id"]))


@announcements_bp.route("", methods=["POST"])
@announcements_bp.route("/", methods=["POST"])
@super_admin_required
def create_announcement(current_user):
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    text = (body.get("body") or "").strip()
    if not title:
        return jsonify({"error": "Title is required."}), 400
    if not text:
        return jsonify({"error": "Description is required."}), 400

    event_id, err = _resolve_event_id(body.get("event_id"))
    if err:
        return jsonify({"error": err}), 400

    new_id = announcement_model.create(title, text, current_user["sub"], event_id=event_id)
    audit_model.log(
        current_user["sub"], "announcement.create",
        detail=f'Posted announcement "{title}"', event_id=event_id,
    )
    # Optional convenience: enabling the linked event in the same step so an announced
    # event is immediately scannable (reduces "announced but not started" mistakes).
    _maybe_enable_event(current_user["sub"], event_id, body.get("enable_event"))
    doc = announcement_model.find_by_id(new_id)
    ev = event_model.find_by_id(event_id) if event_id else None
    return jsonify(announcement_model.public(doc, event=ev)), 201


@announcements_bp.route("/<announcement_id>", methods=["PATCH"])
@super_admin_required
def update_announcement(current_user, announcement_id):
    if not announcement_model.find_by_id(announcement_id):
        return jsonify({"error": "Announcement not found."}), 404

    body = request.get_json(silent=True) or {}
    fields = {}
    if "title" in body:
        title = (body.get("title") or "").strip()
        if not title:
            return jsonify({"error": "Title cannot be empty."}), 400
        fields["title"] = title
    if "body" in body:
        text = (body.get("body") or "").strip()
        if not text:
            return jsonify({"error": "Description cannot be empty."}), 400
        fields["body"] = text
    if "event_id" in body:
        event_id, err = _resolve_event_id(body.get("event_id"))
        if err:
            return jsonify({"error": err}), 400
        fields["event_id"] = event_id

    if not fields:
        return jsonify({"error": "Nothing to update."}), 400

    announcement_model.update(announcement_id, fields)
    audit_model.log(
        current_user["sub"], "announcement.update",
        detail=f"Edited announcement", event_id=fields.get("event_id"),
    )
    doc = announcement_model.find_by_id(announcement_id)
    # Honor the enable-event box on edit too (against the resulting linked event).
    effective_event = fields.get("event_id") if "event_id" in fields else \
        (str(doc["event_id"]) if doc.get("event_id") else None)
    _maybe_enable_event(current_user["sub"], effective_event, body.get("enable_event"))
    ev = event_model.find_by_id(doc["event_id"]) if doc.get("event_id") else None
    return jsonify(announcement_model.public(doc, event=ev)), 200


@announcements_bp.route("/<announcement_id>", methods=["DELETE"])
@super_admin_required
def delete_announcement(current_user, announcement_id):
    doc = announcement_model.find_by_id(announcement_id)
    if not doc:
        return jsonify({"error": "Announcement not found."}), 404
    announcement_model.delete(announcement_id)
    audit_model.log(
        current_user["sub"], "announcement.delete",
        detail=f'Deleted announcement "{doc.get("title", "")}"',
    )
    return jsonify({"message": "Announcement deleted."}), 200
