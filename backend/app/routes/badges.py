from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import user as user_model
from app.utils.auth import jwt_required

# No url_prefix — this serves the participant collection endpoint at /me/badges.
badges_bp = Blueprint("badges", __name__)


def compute_streak(uid):
    """Consecutive-event-day streak for a participant.

    An "event-day" is a calendar day on which at least one badge-bearing event was
    hosted (keyed by the event's start_date). Walking those days oldest → newest:
      • completing an event (earning all of its badges) adds +1 per completed event;
      • a *past* event-day on which the user completed none of that day's events
        resets the running streak to 0 ("missed a day");
      • the current day never resets — it can only add, since it isn't over yet.

    Two events on the same day therefore can't break the streak as long as the user
    completes at least one (the day still has a completion), and completing both adds
    +2. The returned value is the running total after the most recent event-day: the
    length of the current unbroken run, measured in completed events.

    Events with no start_date (unscheduled) and events with no badges (can't be
    completed) do not participate — they never count as a breakable event-day.
    """
    today = datetime.now(timezone.utc).date()
    # day -> count of events completed that day. A day present as a key is an event-day.
    per_day = {}
    for ev in event_model.all_events():
        start = ev.get("start_date")
        if not isinstance(start, datetime):
            continue
        day = start.date()
        if day > today:
            continue  # upcoming events haven't happened yet
        badges = badge_model.find_by_event(ev["_id"])
        total = len(badges)
        if total == 0:
            continue  # a badge-less event can't be completed, so it's not an event-day
        per_day.setdefault(day, 0)
        redeemed = redemption_model.redeemed_badge_map(uid, ev["_id"])
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        if earned >= total:
            per_day[day] += 1

    streak = 0
    for day in sorted(per_day):
        completed = per_day[day]
        if completed > 0 or day == today:
            streak += completed
        else:
            streak = 0  # past event-day with no completion → streak breaks
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
    out = []
    for ev in event_model.all_events():
        badges = badge_model.find_by_event(ev["_id"])
        redeemed = redemption_model.redeemed_badge_map(uid, ev["_id"])
        badge_counts = redemption_model.counts_by_badge(ev["_id"])
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
