"""Org-theming migration — normalize every org's `theme` to the white-label shape
(idempotent, reversible, counted).

Phase 1 stored `theme` as an empty `{}`. Theming now uses
`{primary, secondary, accent, logo_url}` (empty strings = fall back to platform default).
This backfills the shape on orgs missing keys, leaving any already-set values intact.

Targets the DB the backend .env points at (a DEV database here). Additive.

Usage:
    python migrate_org_theme.py            # backfill theme shape
    python migrate_org_theme.py --rollback # reset every org's theme to {}

Safe to run repeatedly.
"""

import os
import sys

from app import create_app, mongo
from app.models.organization import _THEME_SHAPE

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def _report():
    total = mongo.db.organizations.count_documents({})
    missing = sum(
        1 for o in mongo.db.organizations.find({}, {"theme": 1})
        if not isinstance(o.get("theme"), dict) or any(k not in (o.get("theme") or {}) for k in _THEME_SHAPE)
    )
    print(f"  organizations: total={total}, missing/partial theme={missing}")
    return total, missing


def forward():
    print(f"\n=== Org theme (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _report()
    changed = 0
    for o in mongo.db.organizations.find():
        theme = o.get("theme") if isinstance(o.get("theme"), dict) else {}
        merged = {**_THEME_SHAPE, **theme}
        if merged != o.get("theme"):
            mongo.db.organizations.update_one({"_id": o["_id"]}, {"$set": {"theme": merged}})
            changed += 1
    print(f"  normalized theme on {changed} org(s)")
    _total, missing = _report()
    assert missing == 0, "every org must have the full theme shape after backfill"
    print("=== FORWARD complete ===\n")


def rollback():
    print(f"\n=== Org theme (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _report()
    res = mongo.db.organizations.update_many({}, {"$set": {"theme": {}}})
    print(f"  reset theme to empty on {res.modified_count} org(s)")
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
