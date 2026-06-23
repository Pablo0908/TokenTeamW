from flask import Blueprint, jsonify
from pymongo.errors import DuplicateKeyError

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import audit as audit_model
from app.utils.auth import jwt_required

redemptions_bp = Blueprint("redemptions", __name__)


@redemptions_bp.route("/redeem/<event_id>/<token>", methods=["GET"])
@jwt_required
def redeem(current_user, event_id, token):
    uid = current_user["sub"]

    # Invalid event / token and inactive event all return the same generic 403 (no info leak).
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "This badge isn’t available right now."}), 403

    badge = badge_model.find_by_token(ev["_id"], token)
    if not badge:
        return jsonify({"error": "This QR code is not a Lyfter badge."}), 403

    if event_model.compute_status(ev.get("start_date"), ev.get("end_date")) != "active":
        return jsonify({"error": "This event isn’t active right now."}), 403

    try:
        redeemed_at = redemption_model.redeem(badge["_id"], ev["_id"], uid, org_id=ev.get("org_id"))
    except DuplicateKeyError:
        return jsonify({"error": "You already have this badge."}), 409

    # Org-scoped interaction: tagged with the event's org so org admins see scans
    # within their own events (actor role/email auto-resolved by audit.log).
    audit_model.log(
        uid, "badge.redeem", f"{badge.get('name', '')} · {ev.get('name', '')}",
        org_id=ev.get("org_id"), event_id=str(ev["_id"]),
    )

    total = badge_model.count_for_event(ev["_id"])
    earned = redemption_model.count_for_event(uid, ev["_id"])
    completed = total > 0 and earned >= total

    return jsonify(
        {
            "message": "Event completed!" if completed else "Badge earned",
            "badge": badge_model.public_badge(badge, True, redeemed_at),
            "event": ev.get("name", ""),
            "event_id": str(ev["_id"]),
            "event_completed": completed,
            "prize": ev.get("prize", "") if completed else None,
            "badges_earned": earned,
            "badges_total": total,
        }
    ), 200
