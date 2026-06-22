from flask import Blueprint, request, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import user as user_model
from app.models import audit as audit_model
from app.utils.auth import admin_required, staff_required
from app.utils.qr import generate_badge_token, build_redeem_url, generate_qr_data_url

# All admin operations live here: event/badge creation, badge stats, and user management.
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/event", methods=["POST"])
@admin_required
def create_event(current_user):
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Event name is required."}), 400

    event_id = event_model.create_event(
        name=name,
        description=(body.get("description") or "").strip(),
        start_date=event_model.parse_date(body.get("date") or body.get("start_date")),
        end_date=event_model.parse_date(body.get("end_date")),
        location=(body.get("location") or "").strip(),
        prize=(body.get("prize") or "").strip(),
        created_by=current_user["sub"],
    )
    audit_model.log(current_user["sub"], "event.create", name)
    return jsonify({"id": event_id, "name": name}), 201


@admin_bp.route("/events/<event_id>/badge", methods=["POST"])
@admin_required
def create_badge(current_user, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Badge name is required."}), 400

    # Server generates the token + QR image; the client only sends name/description/icon/color.
    token = generate_badge_token()
    qr_url = build_redeem_url(str(ev["_id"]), token)
    qr_image = generate_qr_data_url(qr_url)
    badge_id = badge_model.create_badge(
        event_id=ev["_id"],
        name=name,
        description=(body.get("description") or "").strip(),
        token=token,
        qr_image=qr_image,
        icon=(body.get("icon") or "🏅"),
        color=(body.get("color") or "primary"),
        image=(body.get("image") or "").strip(),
    )
    audit_model.log(current_user["sub"], "badge.create", f"{name} · {ev.get('name', '')}")
    return jsonify(
        {
            "id": badge_id,
            "name": name,
            "token": token,
            "qr_url": qr_url,
            "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
            "qr_image": qr_image,
        }
    ), 201


@admin_bp.route("/events/<event_id>/badges/bulk", methods=["POST"])
@admin_required
def create_badges_bulk(current_user, event_id):
    """Create many badges in one call. Accepts either an explicit list:
        {"badges": [{"name", "description?", "icon?", "color?"}, ...]}
    or a template + count (names become "<name_prefix> 1..N"):
        {"count": N, "name_prefix": "Booth", "icon?": "🏅", "color?": "primary"}
    Returns the created badges (qr generated client-side from qr_url for the print sheet)."""
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    body = request.get_json(silent=True) or {}
    specs = body.get("badges")

    if not isinstance(specs, list):
        count = body.get("count")
        prefix = (body.get("name_prefix") or body.get("name") or "").strip()
        shared = {"icon": body.get("icon", "🏅"), "color": body.get("color", "primary")}
        if isinstance(count, int) and count > 0 and prefix:
            specs = [{"name": f"{prefix} {i}", **shared} for i in range(1, count + 1)]
        else:
            return jsonify({"error": "Provide a 'badges' list, or a 'count' plus a 'name_prefix'."}), 400

    cleaned = []
    for s in specs:
        if not isinstance(s, dict):
            continue
        name = (s.get("name") or "").strip()
        if name:
            cleaned.append({**s, "name": name})

    if not cleaned:
        return jsonify({"error": "No valid badge names were provided."}), 400
    if len(cleaned) > 100:
        return jsonify({"error": "You can create at most 100 badges at once."}), 400

    created = []
    for s in cleaned:
        token = generate_badge_token()
        qr_url = build_redeem_url(str(ev["_id"]), token)
        qr_image = generate_qr_data_url(qr_url)
        badge_id = badge_model.create_badge(
            event_id=ev["_id"],
            name=s["name"],
            description=(s.get("description") or "").strip(),
            token=token,
            qr_image=qr_image,
            icon=(s.get("icon") or "🏅"),
            color=(s.get("color") or "primary"),
            image=(s.get("image") or "").strip(),
        )
        created.append(
            {
                "id": badge_id,
                "name": s["name"],
                "token": token,
                "qr_url": qr_url,
                "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
            }
        )
    audit_model.log(current_user["sub"], "badge.bulk_create", f"{len(created)} badges · {ev.get('name', '')}")
    return jsonify({"created": created, "count": len(created)}), 201


@admin_bp.route("/events/<event_id>/badges", methods=["GET"])
@staff_required
def list_badges(current_user, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    total_attendees = user_model.count_attendees()
    out = []
    for b in badge_model.find_by_event(ev["_id"]):
        token = b.get("token", "")
        # No qr_image in this list response (keeps the payload light per the mobile rule);
        # the QR is regenerated client-side from qr_url, and is also stored on each badge doc.
        out.append(
            {
                "id": str(b["_id"]),
                "name": b.get("name", ""),
                "description": b.get("description", ""),
                "icon": b.get("icon", "🏅"),
                "color": b.get("color", "primary"),
                "image": b.get("image", ""),
                "token": token,
                "qr_url": build_redeem_url(str(ev["_id"]), token),
                "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
                "redeemed_by": redemption_model.count_for_badge(b["_id"]),
                "total_attendees": total_attendees,
            }
        )
    return jsonify(out), 200


# --- User management (admin-only): track badge counts, promote/demote ---

@admin_bp.route("/users", methods=["GET"])
@staff_required
def list_users(current_user):
    counts = redemption_model.counts_by_user()
    out = []
    for u in user_model.all_users():
        uid = str(u["_id"])
        out.append(
            {
                "id": uid,
                "name": u.get("name", ""),
                "lastname": u.get("lastname", ""),
                "email": u.get("email", ""),
                "role": u.get("role", "attendee"),
                "disabled": bool(u.get("disabled", False)),
                "badges_count": counts.get(uid, 0),
                "created_at": event_model.fmt_date(u.get("created_at")),
            }
        )
    return jsonify({"users": out}), 200


@admin_bp.route("/users/<user_id>/badges", methods=["GET"])
@staff_required
def user_badges(current_user, user_id):
    user = user_model.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Same per-event grouping as /me/badges, but for the user the admin is inspecting.
    events = []
    for ev in event_model.all_events():
        badges = badge_model.find_by_event(ev["_id"])
        redeemed = redemption_model.redeemed_badge_map(user_id, ev["_id"])
        total = len(badges)
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        events.append(
            {
                "event_id": str(ev["_id"]),
                "event": ev.get("name", ""),
                "date": event_model.fmt_date(ev.get("start_date")),
                "status": event_model.compute_status(ev.get("start_date"), ev.get("end_date")),
                "prize": ev.get("prize", ""),
                "badges_total": total,
                "badges_earned": earned,
                "completed": total > 0 and earned >= total,
                "badges": [
                    badge_model.public_badge(b, str(b["_id"]) in redeemed, redeemed.get(str(b["_id"])))
                    for b in badges
                ],
            }
        )

    return jsonify(
        {
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name", ""),
                "lastname": user.get("lastname", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "attendee"),
                "badges_count": redemption_model.count_for_user(user_id),
            },
            "events": events,
        }
    ), 200


@admin_bp.route("/users/<user_id>/role", methods=["PATCH"])
@admin_required
def set_user_role(current_user, user_id):
    body = request.get_json(silent=True) or {}
    role = (body.get("role") or "").strip().lower()
    if role not in ("admin", "attendee", "assistant"):
        return jsonify({"error": "Role must be 'admin', 'assistant' or 'attendee'."}), 400
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can’t change your own role."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    user_model.set_role(user_id, role)
    audit_model.log(current_user["sub"], "user.role_change", f"{target.get('email', user_id)} → {role}")
    return jsonify({"id": user_id, "role": role}), 200


@admin_bp.route("/users/<user_id>/disable", methods=["PATCH"])
@admin_required
def toggle_disable_user(current_user, user_id):
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can't disable your own account."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    disabled = bool(body.get("disabled", True))
    user_model.set_disabled(user_id, disabled)
    action = "user.disable" if disabled else "user.enable"
    audit_model.log(current_user["sub"], action, target.get("email", user_id))
    return jsonify({"id": user_id, "disabled": disabled}), 200


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(current_user, user_id):
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can't delete your own account."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    user_model.delete_user(user_id)
    audit_model.log(current_user["sub"], "user.delete", target.get("email", user_id))
    return jsonify({"id": user_id, "deleted": True}), 200


@admin_bp.route("/audit", methods=["GET"])
@admin_required
def audit_log(current_user):
    return jsonify({"entries": audit_model.recent(150)}), 200
