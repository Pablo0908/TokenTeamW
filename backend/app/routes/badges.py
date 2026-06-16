from flask import Blueprint, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.utils.auth import jwt_required

# No url_prefix — this serves the participant collection endpoint at /me/badges.
badges_bp = Blueprint("badges", __name__)


@badges_bp.route("/me/badges", methods=["GET"])
@jwt_required
def my_badges(current_user):
    uid = current_user["sub"]
    out = []
    for ev in event_model.all_events():
        badges = badge_model.find_by_event(ev["_id"])
        redeemed = redemption_model.redeemed_badge_map(uid, ev["_id"])
        total = len(badges)
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        out.append(
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
    return jsonify(out), 200
