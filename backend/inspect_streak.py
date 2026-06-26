"""READ-ONLY inspection for streak testing. Makes no writes."""
import os
from datetime import datetime, timezone

import certifi
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000, tlsCAFile=certifi.where())
db = client[os.environ.get("DB_NAME", "beeworking")]

EMAIL = "pablofori09@gmail.com"

print("=== DB ===", db.name)
print("=== collections ===", sorted(db.list_collection_names()))
print("=== total users ===", db.users.count_documents({}))
print("=== total events ===", db.events.count_documents({}))
print("=== total redemptions ===", db.redemptions.count_documents({}))

user = db.users.find_one({"email": EMAIL})
if not user:
    print(f"\n!!! USER {EMAIL} NOT FOUND in {db.name}")
else:
    uid = user["_id"]
    print(f"\n=== user {EMAIL} ===")
    print("  _id:", uid)
    print("  name:", user.get("name"), user.get("lastname"))
    print("  role:", user.get("role"), " disabled:", user.get("disabled"))
    print("  redemptions:", db.redemptions.count_documents({"user_id": uid}))

    # Replicate compute_streak() exactly (badges.py:15-60)
    today = datetime.now(timezone.utc).date()
    per_day = {}
    detail = []
    for ev in db.events.find().sort("created_at", -1):
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
        detail.append((day.isoformat(), ev.get("name", "")[:30], f"{earned}/{total}", "TODAY" if day == today else ""))

    streak = 0
    for day in sorted(per_day):
        completed = per_day[day]
        if completed > 0 or day == today:
            streak += completed
        else:
            streak = 0
    print(f"\n=== CURRENT computed streak for {EMAIL}: {streak} ===")
    print("  event-days walked (day, name, earned/total, today?):")
    for d in sorted(detail):
        print("   ", d)

client.close()
