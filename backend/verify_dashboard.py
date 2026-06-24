"""Verification — org dashboard endpoint (Phase A).

Proves GET /orgs/<org_id>/dashboard returns coherent, tenant-scoped counts and obeys
the org tier rules:
  1. owner reads the dashboard (200) with the expected shape
  2. counts reflect a real scan: total_scans>=1, unique_participants>=1, badges>=1,
     events.total>=1, the scanned event appears in top_events, activity has a bucket
  3. read-only staff can read the dashboard (200)
  4. a non-member is refused (403)
  5. super_admin passes (200)
All fixtures cleaned up.

Usage:  python verify_dashboard.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "dashverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "staff", "attendee", "other")}
    org_id = ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "DB", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # Real activity: create event + badge (owner), then attendee scans it.
        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                             json={"name": f"{SUFFIX} ev", "event_type": "workshop"}).get_json() or {}).get("id")
        badge = client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                            json={"name": "Keynote"}).get_json() or {}
        token = badge.get("token")
        r = client.get(f"/redeem/{ev_id}/{token}", headers=H(tok["attendee"]))
        check("setup: attendee scanned a badge (redeem 200)", r.status_code == 200)

        # ---- 1 + 2. owner reads dashboard; counts reflect the scan ----
        r = client.get(f"/orgs/{org_id}/dashboard", headers=H(tok["owner"]))
        d = r.get_json() or {}
        check("owner reads dashboard (200)", r.status_code == 200)
        check("dashboard exposes the expected shape",
              all(k in d for k in ("org", "events", "unique_participants", "total_scans",
                                   "badges_minted", "top_events", "activity")))
        check("total_scans >= 1", d.get("total_scans", 0) >= 1)
        check("unique_participants >= 1", d.get("unique_participants", 0) >= 1)
        check("badges_minted >= 1", d.get("badges_minted", 0) >= 1)
        check("events.total >= 1", (d.get("events") or {}).get("total", 0) >= 1)
        check("scanned event appears in top_events",
              any(te.get("id") == ev_id and te.get("scans", 0) >= 1 for te in d.get("top_events", [])))
        check("activity has at least one bucket", len(d.get("activity", [])) >= 1)

        # ---- 3. staff can read ----
        check("staff can read the dashboard (200)",
              client.get(f"/orgs/{org_id}/dashboard", headers=H(tok["staff"])).status_code == 200)

        # ---- 4. non-member refused ----
        check("non-member cannot read the dashboard (403)",
              client.get(f"/orgs/{org_id}/dashboard", headers=H(tok["other"])).status_code == 403)

        # ---- 5. super_admin passes ----
        check("super_admin can read any org's dashboard (200)",
              client.get(f"/orgs/{org_id}/dashboard", headers=H(sat)).status_code == 200)

    finally:
        if ev_id:
            mongo.db.badges.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.redemptions.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, membership, event, badge, redemption, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
