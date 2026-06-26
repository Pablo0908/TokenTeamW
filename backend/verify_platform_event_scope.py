"""Verification — platform (super-admin-panel) events are excluded from org control panels.

Proves the "where it was created" model:
  1. POST /orgs/<org>/event (owner)   -> event with platform_event == False (org-owned)
  2. POST /admin/event (super admin)  -> event with platform_event == True  (platform-level)
  3. all_events(org_id, exclude_platform=True) drops platform events even when they carry
     the SAME org_id (the flag, not just org_id, is what hides them)
  4. GET /orgs/<org>/events lists ONLY the org-owned event, never the platform event
  5. GET /orgs/<org>/dashboard event totals exclude the platform event
All fixtures cleaned up.

Usage:  python verify_platform_event_scope.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import event as event_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "pfverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    owner_email = f"{SUFFIX}_owner@example.invalid"
    org_id = None
    owner_id = None
    super_admin = None
    created_event_ids = []

    try:
        # clean any prior fixtures
        mongo.db.users.delete_one({"email": owner_email})
        for o in mongo.db.organizations.find({"slug": f"{SUFFIX}-org"}):
            for e in mongo.db.events.find({"org_id": o["_id"]}, {"_id": 1}):
                for coll in ("badges", "redemptions", "prize_claims"):
                    mongo.db[coll].delete_many({"event_id": e["_id"]})
                mongo.db.events.delete_one({"_id": e["_id"]})
            mongo.db.memberships.delete_many({"org_id": o["_id"]})
            mongo.db.organizations.delete_one({"_id": o["_id"]})

        owner_id = user_model.create_user("Owner", "PF", owner_email, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=owner_id)
        membership_model.add_membership(owner_id, org_id, "owner")

        with app.app_context():
            owner_tok = encode_token(owner_id, "attendee", 0)
            sat = encode_token(str(super_admin["_id"]), super_admin.get("role", "attendee"),
                               super_admin.get("token_version", 0))
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # ---- 1. org-panel create -> platform_event False ----
        r = client.post(f"/orgs/{org_id}/event", json={"name": "Org Native Event"}, headers=H(owner_tok))
        check("POST /orgs/<org>/event -> 201", r.status_code == 201)
        org_ev_id = r.get_json().get("id")
        created_event_ids.append(org_ev_id)
        org_ev = event_model.find_by_id(org_ev_id)
        check("org-panel event has platform_event == False", org_ev.get("platform_event") is False)

        # ---- 2. platform create -> platform_event True ----
        r = client.post("/admin/event", json={"name": "Platform Event"}, headers=H(sat))
        check("POST /admin/event -> 201", r.status_code == 201)
        plat_ev_id = r.get_json().get("id")
        created_event_ids.append(plat_ev_id)
        plat_ev = event_model.find_by_id(plat_ev_id)
        check("platform event has platform_event == True", plat_ev.get("platform_event") is True)

        # ---- 3. model filter drops platform events even with the SAME org_id ----
        # Force a platform event INTO the test org so the test isolates the flag, not org_id.
        forced_plat_id = event_model.create_event(
            "Forced Platform In Org", "", None, None, "", "", str(super_admin["_id"]),
            org_id=org_id, platform_event=True)
        created_event_ids.append(forced_plat_id)

        all_in_org = {str(e["_id"]) for e in event_model.all_events(org_id=org_id)}
        org_only = {str(e["_id"]) for e in event_model.all_events(org_id=org_id, exclude_platform=True)}
        check("all_events(org) sees both org-native AND the same-org platform event",
              org_ev_id in all_in_org and forced_plat_id in all_in_org)
        check("all_events(org, exclude_platform) keeps org-native, drops same-org platform event",
              org_ev_id in org_only and forced_plat_id not in org_only)

        # ---- 4. HTTP org listing excludes platform events ----
        r = client.get(f"/orgs/{org_id}/events", headers=H(owner_tok))
        check("GET /orgs/<org>/events -> 200", r.status_code == 200)
        listed = {e.get("id") for e in (r.get_json() or [])}
        check("org events listing INCLUDES the org-native event", org_ev_id in listed)
        check("org events listing EXCLUDES the same-org platform event", forced_plat_id not in listed)

        # ---- 5. dashboard totals exclude platform events ----
        r = client.get(f"/orgs/{org_id}/dashboard", headers=H(owner_tok))
        check("GET /orgs/<org>/dashboard -> 200", r.status_code == 200)
        total = (r.get_json() or {}).get("events", {}).get("total")
        check("dashboard event total counts only the 1 org-native event (excludes platform)", total == 1)

    finally:
        for eid in created_event_ids:
            if not eid:
                continue
            for coll in ("badges", "redemptions", "prize_claims"):
                mongo.db[coll].delete_many({"event_id": ObjectId(eid)})
            mongo.db.events.delete_one({"_id": ObjectId(eid)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": str(org_id)})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]), "action": "event.create"})
        mongo.db.users.delete_one({"email": owner_email})
        print("\n  cleaned up throwaway fixtures (user, org, membership, events, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
