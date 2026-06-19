"""Create the first admin account and (optionally) clear event/badge content.

Usage:
    python seed_admin.py            # ensure the admin account + indexes exist
    python seed_admin.py --fresh    # also delete all events, badges and redemptions

Admin credentials come from .env (ADMIN_EMAIL / ADMIN_PASSWORD / ADMIN_NAME / ADMIN_LASTNAME).
Regular attendees self-register through the app; only admins are seeded here.
"""

import os
import sys

from app import create_app, mongo
from app.models import user as user_model
from app.utils.auth import hash_password


def run(fresh=False):
    create_app()  # connects to Atlas, fails fast if unreachable, ensures indexes

    if fresh:
        removed = {
            "events": mongo.db.events.delete_many({}).deleted_count,
            "badges": mongo.db.badges.delete_many({}).deleted_count,
            "redemptions": mongo.db.redemptions.delete_many({}).deleted_count,
        }
        print(f"--fresh: cleared {removed} (users were kept).")

    email = os.getenv("ADMIN_EMAIL", "admin@lyfter.cc").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    name = os.getenv("ADMIN_NAME", "Admin")
    lastname = os.getenv("ADMIN_LASTNAME", "Lyfter")

    existing = user_model.find_by_email(email)
    if existing:
        user_model.set_role(str(existing["_id"]), "admin")
        print(f"Admin already exists: {email} (role ensured = admin).")
    else:
        uid = user_model.create_user(name, lastname, email, hash_password(password), role="admin")
        print(f"Created admin {email}  (password: {password})  id={uid}")

    print(
        "State -> users:",
        mongo.db.users.count_documents({}),
        "| events:",
        mongo.db.events.count_documents({}),
        "| badges:",
        mongo.db.badges.count_documents({}),
        "| redemptions:",
        mongo.db.redemptions.count_documents({}),
    )


if __name__ == "__main__":
    run(fresh="--fresh" in sys.argv)
