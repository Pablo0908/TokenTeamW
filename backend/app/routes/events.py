from flask import Blueprint, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import user as user_model
from app.utils.auth import jwt_required

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/", methods=["GET"])
@jwt_required
def list_events(current_user):
    uid = current_user["sub"]
    out = []
    for ev in event_model.all_events():
        total = badge_model.count_for_event(ev["_id"])
        earned = redemption_model.count_for_event(uid, ev["_id"])
        out.append(event_model.event_summary(ev, total, earned))
    return jsonify(out), 200


@events_bp.route("/<event_id>", methods=["GET"])
@jwt_required
def get_event(current_user, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    uid = current_user["sub"]
    badges = badge_model.find_by_event(ev["_id"])
    redeemed = redemption_model.redeemed_badge_map(uid, ev["_id"])
    badge_counts = redemption_model.counts_by_badge(ev["_id"])
    total_attendees = user_model.count_attendees()
    total = len(badges)
    earned = sum(1 for b in badges if str(b["_id"]) in redeemed)

    summary = event_model.event_summary(ev, total, earned)
    summary["badges"] = [
        badge_model.public_badge(
            b,
            str(b["_id"]) in redeemed,
            redeemed.get(str(b["_id"])),
            redeemed_by=badge_counts.get(str(b["_id"]), 0),
            total_attendees=total_attendees,
        )
        for b in badges
    ]
    return jsonify(summary), 200
