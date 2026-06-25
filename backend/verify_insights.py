"""Verification — platform analytics (Phase H): GET /admin/insights (super-admin).

Seeds a throwaway org + event + two scans (today), then asserts the platform insights
endpoint reflects them and is shaped correctly, and that the tier is enforced:
  1. non-super-admin -> 403
  2. super_admin -> 200 with the full shape
  3. the throwaway org's 2 scans show in totals, scans_over_time, the org leaderboard
     (exactly 2 — brand-new org), and the event-type mix
  4. active_users reflects today's interactions
All fixtures cleaned up.

Usage:  python verify_insights.py
"""

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "insightsverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "a1", "a2")}
    org_id = ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "IN", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                             json={"name": f"{SUFFIX} ev", "event_type": "workshop"}).get_json() or {}).get("id")
        client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["owner"]), json={"started": True})
        # two distinct attendees scan one badge each -> 2 redemptions today, this org
        for who in ("a1", "a2"):
            t = (client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                             json={"name": f"b-{who}"}).get_json() or {}).get("token")
            client.get(f"/redeem/{ev_id}/{t}", headers=H(tok[who]))

        # tight range covering today
        now = datetime.now(timezone.utc)
        params = {"period": "day",
                  "start": (now - timedelta(days=1)).date().isoformat(),
                  "end": (now + timedelta(days=1)).date().isoformat()}

        # ---- 1. tier ----
        check("non-super-admin: /admin/insights -> 403",
              client.get("/admin/insights", headers=H(tok["a1"]), query_string=params).status_code == 403)

        # ---- 2 + 3 + 4. super_admin shape + reflects the seed ----
        r = client.get("/admin/insights", headers=H(sat), query_string=params)
        d = r.get_json() or {}
        check("super_admin: /admin/insights -> 200", r.status_code == 200)
        check("response has the full shape",
              all(k in d for k in ("totals", "active_users", "scans_over_time",
                                   "user_growth", "org_leaderboard", "event_type_mix")))
        check("totals.scans >= 2", (d.get("totals") or {}).get("scans", 0) >= 2)
        check("scans_over_time has data in range",
              sum(b["count"] for b in d.get("scans_over_time", [])) >= 2)
        lead = next((o for o in d.get("org_leaderboard", []) if o["id"] == org_id), None)
        check("throwaway org appears in leaderboard with exactly 2 scans, 2 people",
              bool(lead) and lead["scans"] == 2 and lead["participants"] == 2)
        check("event-type mix includes the seeded 'workshop' type",
              any(m["event_type"] == "workshop" and m["count"] >= 2 for m in d.get("event_type_mix", [])))
        check("active_users reflects today's interactions (>=1)",
              sum(b["count"] for b in d.get("active_users", [])) >= 1)

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
        print("\n  cleaned up throwaway fixtures (users, org, membership, event, badges, redemptions, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
