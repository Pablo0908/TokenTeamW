"""Verification — org attendee insights (Phase I): GET /orgs/<id>/insights.

Seeds an org with two events and three attendees scanning at controlled times, then
asserts new-vs-returning, retention, and KPI values, plus tier rules:
  1. staff & non-members -> 403; owner/admin -> 200; super_admin passes
  2. new vs returning: first-ever-in-window attendees counted NEW, earlier ones RETURNING
  3. retention return-rate = share of attendees who scanned across >=2 events
  4. kpi_deltas reflect the in-window scans / unique participants
  5. new-attendees acquisition series buckets first-time attendees
All fixtures cleaned up.

Usage:  python verify_attendee_insights.py
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
SUFFIX = "attinsights"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "admin", "staff", "a1", "a2", "a3", "outsider")}
    org_id = ev1 = ev2 = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "AI", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["admin"], org_id, "admin")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        ev1 = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]), json={"name": "ev1"}).get_json() or {}).get("id")
        ev2 = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]), json={"name": "ev2"}).get_json() or {}).get("id")

        now = datetime.now(timezone.utc)
        old = now - timedelta(days=60)  # before the default 30d window

        def red(uid, ev, when):
            mongo.db.redemptions.insert_one({
                "badge_id": ObjectId(), "event_id": ObjectId(ev), "user_id": ObjectId(uids[uid]),
                "org_id": ObjectId(org_id), "redeemed_at": when})

        red("a1", ev1, now)            # new, 1 event
        red("a2", ev1, now)            # new, 2 events (repeat)
        red("a2", ev2, now)
        red("a3", ev1, old)            # first-ever BEFORE window -> returning
        red("a3", ev2, now)            # ...with an in-window scan; 2 events (repeat)

        # ---- 1. tier ----
        check("staff cannot read org insights (403)",
              client.get(f"/orgs/{org_id}/insights", headers=H(tok["staff"])).status_code == 403)
        check("non-member cannot read org insights (403)",
              client.get(f"/orgs/{org_id}/insights", headers=H(tok["outsider"])).status_code == 403)
        check("super_admin passes (200)",
              client.get(f"/orgs/{org_id}/insights", headers=H(sat)).status_code == 200)

        r = client.get(f"/orgs/{org_id}/insights", headers=H(tok["owner"]))
        d = r.get_json() or {}
        check("owner reads org insights (200) with the full shape",
              r.status_code == 200 and all(k in d for k in ("kpi_deltas", "new_vs_returning", "retention")))

        # ---- 2. new vs returning ----
        nvr = d["new_vs_returning"]
        check("new vs returning = 2 new (a1,a2), 1 returning (a3)",
              nvr["new"] == 2 and nvr["returning"] == 1)

        # ---- 3. retention: a2 & a3 hit 2 events -> 2 of 3 ----
        ret = d["retention"]
        check("retention: 2 of 3 attendees returned (return_rate ~66.7%)",
              ret["attendees"] == 3 and ret["repeat"] == 2 and abs(ret["return_rate"] - 66.7) < 0.5)
        check("retention exposes per-event attendance",
              any(e["id"] == ev1 and e["attendees"] == 3 for e in ret["events"]))

        # ---- 4. kpi values (in-window: 4 scans across a1,a2,a3) ----
        kd = d["kpi_deltas"]
        check("kpi scans in window = 4", kd["scans"]["value"] == 4)
        check("kpi unique participants in window = 3", kd["participants"]["value"] == 3)

        # ---- 5. acquisition series buckets first-time attendees in window (a1,a2 = 2) ----
        check("new-attendees series sums to 2 (a1,a2 first scan in window)",
              sum(b["count"] for b in nvr.get("series", [])) == 2)

    finally:
        for e in (ev1, ev2):
            if e:
                mongo.db.badges.delete_many({"event_id": ObjectId(e)})
                mongo.db.redemptions.delete_many({"event_id": ObjectId(e)})
                mongo.db.events.delete_one({"_id": ObjectId(e)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, memberships, events, redemptions, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
