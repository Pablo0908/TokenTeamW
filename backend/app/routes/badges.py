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
    # Only past/today events participate. Load them once, then their badges and this user's
    # redemptions in two more BATCH queries — so the whole streak costs 3 queries instead of
    # 2-per-event (the per-event form timed out for users with many event-days).
    relevant = [
        ev for ev in event_model.all_events()
        if isinstance(ev.get("start_date"), datetime) and ev["start_date"].date() <= today
    ]
    event_ids = [ev["_id"] for ev in relevant]
    badges_by_event = badge_model.map_by_events(event_ids)
    redeemed_by_event = redemption_model.redeemed_map_by_events(uid, event_ids)

    # day -> count of events completed that day. A day present as a key is an event-day.
    per_day = {}
    for ev in relevant:
        badges = badges_by_event.get(str(ev["_id"]), [])
        total = len(badges)
        if total == 0:
            continue  # a badge-less event can't be completed, so it's not an event-day
        day = ev["start_date"].date()
        per_day.setdefault(day, 0)
        redeemed = redeemed_by_event.get(str(ev["_id"]), {})
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
