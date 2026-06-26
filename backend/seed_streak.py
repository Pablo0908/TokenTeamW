"""Seed a >5 streak for pablofori09@gmail.com via 6 TODAY-dated completed events.

Today-dated events are safe: compute_streak() never resets on the current day
(badges.py:56), so this adds to ONLY this user's streak and cannot zero out anyone
else's. Every inserted doc carries seed_tag="streak-test-pablo" for clean teardown.
Re-running first removes the previous seed, so it stays idempotent.
"""
import os
import uuid
from datetime import datetime, timezone

import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000, tlsCAFile=certifi.where())
db = client[os.environ.get("DB_NAME", "beeworking")]

EMAIL = "pablofori09@gmail.com"
TAG = "streak-test-pablo"
N = 6  # > 5

user = db.users.find_one({"email": EMAIL})
assert user, f"user {EMAIL} not found"
uid = user["_id"]
now = datetime.now(timezone.utc)
today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)

# --- idempotent teardown of any previous run ---
old_events = [d["_id"] for d in db.events.find({"seed_tag": TAG}, {"_id": 1})]
r1 = db.redemptions.delete_many({"seed_tag": TAG})
r2 = db.badges.delete_many({"seed_tag": TAG})
r3 = db.events.delete_many({"seed_tag": TAG})
print(f"teardown: removed {r3.deleted_count} events, {r2.deleted_count} badges, {r1.deleted_count} redemptions")

# --- insert N today-dated, badge-bearing, fully-completed events ---
for i in range(1, N + 1):
    ev_id = db.events.insert_one({
        "name": f"Streak Test Event {i}",
        "description": "Seeded for streak-animation testing.",
        "start_date": today_noon,
        "end_date": today_noon,
        "location": "QA",
        "prize": "",
        "event_type": "uncategorized",
        "visibility": "public",
        "org_id": None,
        "started": True,
        "paused": False,
        "ended": False,
        "created_by": uid,
        "created_at": now,
        "seed_tag": TAG,
    }).inserted_id

    badge_id = db.badges.insert_one({
        "event_id": ev_id,
        "org_id": None,
        "name": f"Streak Test Badge {i}",
        "description": "Seeded badge.",
        "icon": "🏅",
        "color": "primary",
        "image": "",
        "token": f"streaktest-{uuid.uuid4().hex}",
        "qr_image": "",
        "created_at": now,
        "seed_tag": TAG,
    }).inserted_id

    db.redemptions.insert_one({
        "badge_id": badge_id,
        "event_id": ev_id,
        "user_id": uid,
        "org_id": None,
        "redeemed_at": now,
        "seed_tag": TAG,
    })
print(f"inserted: {N} events + {N} badges + {N} redemptions for {EMAIL}")

# --- recompute streak exactly as badges.py does ---
today = now.date()
per_day = {}
for ev in db.events.find():
    start = ev.get("start_date")
    if not isinstance(start, datetime):
        continue
    day = start.date()
    if day > today:
        continue
    badges = list(db.badges.find({"event_id": ev["_id"]}))
    total = len(badges)
    if total == 0:
        continue
    per_day.setdefault(day, 0)
    redeemed = {str(d["badge_id"]) for d in db.redemptions.find({"user_id": uid, "event_id": ev["_id"]})}
    earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
    if earned >= total:
        per_day[day] += 1
streak = 0
for day in sorted(per_day):
    completed = per_day[day]
    if completed > 0 or day == today:
        streak += completed
    else:
        streak = 0
print(f"\n=== NEW computed streak for {EMAIL}: {streak} ===")
assert streak >= N, f"expected >= {N}, got {streak}"
print("OK")
client.close()
