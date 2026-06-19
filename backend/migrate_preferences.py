"""Backfill default appearance preferences on existing users (idempotent).

The Settings panel (language / light mode / effects / saturation / contrast) persists
to a `preferences` object on each user document. New accounts get it at creation; this
script adds it to accounts created before the feature existed. The API already treats a
missing field as defaults, so this is optional — but it keeps every document the same
shape, which is convenient for queries and deploys.

Safe to run repeatedly: only users without the field are touched.

Usage:
    python migrate_preferences.py
"""

from app import create_app, mongo
from app.models.user import DEFAULT_PREFERENCES


def run():
    create_app()  # connects to Atlas, fails fast if unreachable
    result = mongo.db.users.update_many(
        {"preferences": {"$exists": False}},
        {"$set": {"preferences": dict(DEFAULT_PREFERENCES)}},
    )
    total = mongo.db.users.count_documents({})
    with_prefs = mongo.db.users.count_documents({"preferences": {"$exists": True}})
    print(f"Backfilled {result.modified_count} user(s) (matched {result.matched_count}).")
    print(f"Users with preferences: {with_prefs}/{total}.")


if __name__ == "__main__":
    run()
