"""Delete the seeded streak-test data for pablofori09@gmail.com and confirm streak == 0.

Removes only docs tagged seed_tag="streak-test-pablo" (the 6 events + their badges +
the user's redemptions). Touches nothing else.
"""
import os
from datetime import datetime, timezone

import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000, tlsCAFile=certifi.where())
db = client[os.environ.get("DB_NAME", "beeworking")]

EMAIL = "pablofori09@gmail.com"
TAG = "streak-test-pablo"

r1 = db.redemptions.delete_many({"seed_tag": TAG})
r2 = db.badges.delete_many({"seed_tag": TAG})
r3 = db.events.delete_many({"seed_tag": TAG})
print(f"deleted: {r3.deleted_count} events, {r2.deleted_count} badges, {r1.deleted_count} redemptions")

# recompute streak exactly as badges.py does
user = db.users.find_one({"email": EMAIL})
uid = user["_id"]
today = datetime.now(timezone.utc).date()
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
    if sum(1 for b in badges if str(b["_id"]) in redeemed) >= total:
        per_day[day] += 1
streak = 0
for day in sorted(per_day):
    completed = per_day[day]
    streak = streak + completed if (completed > 0 or day == today) else 0
print(f"=== streak for {EMAIL} now: {streak} ===")
client.close()
