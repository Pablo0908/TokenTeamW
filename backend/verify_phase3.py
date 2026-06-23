"""Phase 3 verification — audit pagination/filter, event_type, per-user analytics.

Drives the real HTTP surface with locally-minted JWTs and seeds throwaway fixtures
to prove:
  1. app still works (feed + scan -> completion), and event_type round-trips
  2. server-side pagination (50/page, has_more) under the tier scope
  3. search by user/event narrows results
  4. per-user analytics: activity buckets, favorite_event_type (the mode), login_count;
     tier-scoped (super_admin full + login_count; org admin scoped + no login_count;
     attendee 403)
Everything created is cleaned up.

Usage:  python verify_phase3.py
"""

from datetime import datetime, timezone

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "p3verify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    now = datetime.now(timezone.utc)
    emails = {"u": f"{SUFFIX}_user@example.invalid", "a": f"{SUFFIX}_orgadmin@example.invalid"}
    org_b_id = created_event_id = None
    e1 = e2 = None
    u_id = a_id = None
    try:
        # ---- fixtures ----
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        mongo.db.organizations.delete_many({"slug": f"{SUFFIX}-orgb"})

        u_id = user_model.create_user("Ver", "User", emails["u"], hash_password("TestPass1!"), role="attendee")
        a_id = user_model.create_user("Org", "Admin", emails["a"], hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        org_b_id = ObjectId(org_model.create_org("Verify Org B", f"{SUFFIX}-orgb", description=""))
        membership_model.add_membership(a_id, org_b_id, "admin")

        # Two org-B events of different types; U redeems workshop x2, conference x1 -> fav=workshop.
        e1 = mongo.db.events.insert_one({"name": f"{SUFFIX} E1", "event_type": "workshop", "org_id": org_b_id, "created_at": now}).inserted_id
        e2 = mongo.db.events.insert_one({"name": f"{SUFFIX} E2", "event_type": "conference", "org_id": org_b_id, "created_at": now}).inserted_id
        mongo.db.redemptions.insert_many([
            {"badge_id": ObjectId(), "event_id": e1, "user_id": ObjectId(u_id), "org_id": org_b_id, "redeemed_at": now},
            {"badge_id": ObjectId(), "event_id": e1, "user_id": ObjectId(u_id), "org_id": org_b_id, "redeemed_at": now},
            {"badge_id": ObjectId(), "event_id": e2, "user_id": ObjectId(u_id), "org_id": org_b_id, "redeemed_at": now},
        ])
        # U's audit: 3 logins (platform) + 2 org-B interactions.
        mongo.db.audit_log.insert_many(
            [{"actor_id": u_id, "actor_role": "attendee", "actor_email": emails["u"], "action": "auth.login", "org_id": None, "event_id": None, "ts": now} for _ in range(3)]
            + [{"actor_id": u_id, "actor_role": "attendee", "actor_email": emails["u"], "action": "badge.redeem", "org_id": str(org_b_id), "event_id": str(e1), "ts": now} for _ in range(2)]
        )
        # 60 bulk org-B entries (actor = org admin) to exercise pagination.
        mongo.db.audit_log.insert_many(
            [{"actor_id": a_id, "actor_role": "attendee", "actor_email": emails["a"], "action": "test.bulk", "org_id": str(org_b_id), "event_id": None, "ts": now} for _ in range(60)]
        )

        with app.app_context():
            u_tok = encode_token(u_id, "attendee")
            sa_tok = encode_token(str(super_admin["_id"]), super_admin["role"])
            a_tok = encode_token(a_id, "attendee")
        uh = {"Authorization": f"Bearer {u_tok}"}
        sah = {"Authorization": f"Bearer {sa_tok}"}
        bah = {"Authorization": f"Bearer {a_tok}"}

        # ---- 1. app still works + event_type round-trip ----
        check("GET /events/ -> 200", client.get("/events/", headers=uh).status_code == 200)
        r = client.post("/admin/event", headers=sah, json={"name": f"{SUFFIX} routed", "prize": "P3", "event_type": "hackathon"})
        created_event_id = r.get_json().get("id")
        check("create event with event_type -> 201", r.status_code == 201 and created_event_id)
        r = client.post(f"/admin/events/{created_event_id}/badge", headers=sah, json={"name": "P3 Badge"})
        token = r.get_json().get("token")
        r = client.get(f"/redeem/{created_event_id}/{token}", headers=uh)
        check("scan -> 200 completed (app works)", r.status_code == 200 and r.get_json().get("event_completed"))
        det = client.get(f"/events/{created_event_id}", headers=uh).get_json()
        check("event detail carries event_type", det.get("event_type") == "hackathon")

        # ---- 2. pagination (org-B admin, scoped) ----
        p1 = client.get("/admin/audit", headers=bah).get_json()
        total = p1["total"]
        check("page 1 = 50 entries, has_more True", len(p1["entries"]) == 50 and p1["has_more"] is True and total >= 60)
        p2 = client.get("/admin/audit?page=2", headers=bah).get_json()
        check("page 2 = remainder, has_more reflects end",
              len(p2["entries"]) == total - 50 and p2["has_more"] == (total > 100))
        check("org-B admin sees ONLY org B", all(e.get("org_id") == str(org_b_id) for e in p1["entries"] + p2["entries"]))

        # ---- 3. filter ----
        f = client.get(f"/admin/audit?q={emails['u']}", headers=sah).get_json()
        check("search by user email narrows to that actor",
              f["total"] > 0 and all(e.get("actor_id") == u_id or e.get("actor_email") == emails["u"] for e in f["entries"]))
        fe = client.get(f"/admin/audit?q={SUFFIX} E1", headers=sah).get_json()
        check("search by event name returns its entries", fe["total"] >= 2)

        # ---- 4. analytics ----
        sa_an = client.get(f"/admin/users/{u_id}/analytics?period=day", headers=sah).get_json()
        check("super_admin analytics: activity + favorite=workshop + login_count=3",
              sum(b["count"] for b in sa_an["activity"]) >= 5
              and sa_an["favorite_event_type"]["event_type"] == "workshop"
              and sa_an.get("login_count") == 3)
        b_an = client.get(f"/admin/users/{u_id}/analytics?period=day", headers=bah).get_json()
        check("org-admin analytics: scoped, favorite=workshop, NO login_count",
              "login_count" not in b_an
              and b_an["favorite_event_type"]["event_type"] == "workshop"
              and sum(x["count"] for x in b_an["activity"]) >= 2)
        check("attendee cannot read analytics (403)",
              client.get(f"/admin/users/{u_id}/analytics", headers=uh).status_code == 403)

    finally:
        if created_event_id:
            oid = ObjectId(created_event_id)
            mongo.db.redemptions.delete_many({"event_id": oid})
            mongo.db.badges.delete_many({"event_id": oid})
            mongo.db.events.delete_one({"_id": oid})
            mongo.db.audit_log.delete_many({"event_id": created_event_id})
        ids = [i for i in (u_id, a_id) if i]
        mongo.db.redemptions.delete_many({"user_id": {"$in": [ObjectId(i) for i in ids]}})
        for ev in (e1, e2):
            if ev:
                mongo.db.events.delete_one({"_id": ev})
        if org_b_id is not None:
            mongo.db.audit_log.delete_many({"org_id": str(org_b_id)})
            mongo.db.memberships.delete_many({"org_id": org_b_id})
            mongo.db.organizations.delete_one({"_id": org_b_id})
        mongo.db.audit_log.delete_many({"actor_id": {"$in": ids}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (org B, users, events, redemptions, audit rows)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
