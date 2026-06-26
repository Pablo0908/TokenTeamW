from flask import Blueprint, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import user as user_model
from app.utils.auth import jwt_required

# No url_prefix — this serves the participant collection endpoint at /me/badges.
badges_bp = Blueprint("badges", __name__)


def compute_streak(uid):
    """Streak for a participant = the number of events they have FULLY completed
    (earned every badge of the event). Each completed event adds +1, regardless of the
    event's start/end dates. Events with no badges can't be completed and don't count.

    Loads events once, then their badges and this user's redemptions in two BATCH
    queries, so the whole streak costs 3 queries instead of 2-per-event.
    """
    relevant = event_model.all_events()
    event_ids = [ev["_id"] for ev in relevant]
    badges_by_event = badge_model.map_by_events(event_ids)
    redeemed_by_event = redemption_model.redeemed_map_by_events(uid, event_ids)

    streak = 0
    for ev in relevant:
        badges = badges_by_event.get(str(ev["_id"]), [])
        total = len(badges)
        if total == 0:
            continue  # a badge-less event can't be completed
        redeemed = redeemed_by_event.get(str(ev["_id"]), {})
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        if earned >= total:
            streak += 1
    return streak


@badges_bp.route("/me/streak", methods=["GET"])
@jwt_required
def my_streak(current_user):
    """Authoritative streak for the signed-in participant (see compute_streak)."""
    return jsonify({"streak": compute_streak(current_user["sub"])}), 200


@badges_bp.route("/me/badges", methods=["GET"])
@jwt_required
def my_badges(current_user):
    uid = current_user["sub"]
    total_attendees = user_model.count_attendees()
    # "My badges" is the user's own collection: only events where they've earned at least one
    # badge (keeps it personal; org-scoped feed, P7). Derive those events from the user's
    # redemptions, then load badges + rarity counts in BATCH — a handful of queries instead of
    # 3-per-event over the whole catalog (which timed out once a user had many badges).
    redeemed_by_event = redemption_model.redeemed_map_by_events(uid)
    relevant_ids = list(redeemed_by_event.keys())
    badges_by_event = badge_model.map_by_events(relevant_ids)
    badge_counts = redemption_model.counts_by_badge_for_events(relevant_ids)
    out = []
    for ev in event_model.all_events():
        redeemed = redeemed_by_event.get(str(ev["_id"]))
        # Earned events always appear regardless of visibility.
        if not redeemed:
            continue
        badges = badges_by_event.get(str(ev["_id"]), [])
        total = len(badges)
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        out.append(
            {
                "event_id": str(ev["_id"]),
                "event": ev.get("name", ""),
                "date": event_model.fmt_date(ev.get("start_date")),
                "status": event_model.status_of(ev),
                "prize": ev.get("prize", ""),
                "badges_total": total,
                "badges_earned": earned,
                "completed": total > 0 and earned >= total,
                "badges": [
                    badge_model.public_badge(
                        b,
                        str(b["_id"]) in redeemed,
                        redeemed.get(str(b["_id"])),
                        redeemed_by=badge_counts.get(str(b["_id"]), 0),
                        total_attendees=total_attendees,
                    )
                    for b in badges
                ],
            }
        )
    return jsonify(out), 200
