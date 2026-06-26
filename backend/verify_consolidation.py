"""Verification — /admin/* super-admin consolidation (Phase F).

Proves the legacy global-admin tier is gone from /admin/*:
  1. a non-super-admin ORG admin is refused on every globally-powerful /admin route
     (users list, event create, role/disable/delete, global badge list)
  2. the two tiered read endpoints still serve that org admin their own-org view
     (/admin/audit, /admin/users/<id>/analytics)
  3. a super_admin still passes the locked routes
All fixtures cleaned up.

Usage:  python verify_consolidation.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "consolidation"
DUMMY = str(ObjectId())  # a well-formed but nonexistent id


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    email = f"{SUFFIX}_orgadmin@example.invalid"
    org_id = created_event_id = None
    super_admin = None
    uid = None
    try:
        mongo.db.users.delete_one({"email": email})
        uid = user_model.create_user("Org", "Admin", email, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        # An ORG owner who is NOT a platform super_admin.
        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uid)
        membership_model.add_membership(uid, org_id, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            oat = encode_token(uid, "attendee")
        H = lambda t: {"Authorization": f"Bearer {t}"}
        oah, sah = H(oat), H(sat)

        # ---- 1. org admin refused on globally-powerful /admin routes ----
        check("org admin: GET /admin/users -> 403",
              client.get("/admin/users", headers=oah).status_code == 403)
        check("org admin: POST /admin/event -> 403",
              client.post("/admin/event", headers=oah, json={"name": "nope"}).status_code == 403)
        check("org admin: PATCH /admin/users/<id>/super-admin -> 403",
              client.patch(f"/admin/users/{DUMMY}/super-admin", headers=oah, json={"super_admin": True}).status_code == 403)
        check("org admin: PATCH /admin/users/<id>/disable -> 403",
              client.patch(f"/admin/users/{DUMMY}/disable", headers=oah, json={"disabled": True}).status_code == 403)
        check("org admin: DELETE /admin/users/<id> -> 403",
              client.delete(f"/admin/users/{DUMMY}", headers=oah).status_code == 403)
        check("org admin: GET /admin/events/<id>/badges -> 403",
              client.get(f"/admin/events/{DUMMY}/badges", headers=oah).status_code == 403)
        check("org admin: GET /admin/orgs -> 403",
              client.get("/admin/orgs", headers=oah).status_code == 403)

        # ---- 2. tiered reads still serve the org admin their own-org view ----
        check("org admin: GET /admin/audit -> 200 (tiered own-org)",
              client.get("/admin/audit", headers=oah).status_code == 200)
        check("org admin: GET /admin/users/<self>/analytics -> 200 (tiered)",
              client.get(f"/admin/users/{uid}/analytics", headers=oah).status_code == 200)

        # ---- 3. super_admin still passes the locked routes ----
        check("super_admin: GET /admin/users -> 200",
              client.get("/admin/users", headers=sah).status_code == 200)
        check("super_admin: GET /admin/orgs -> 200",
              client.get("/admin/orgs", headers=sah).status_code == 200)
        r = client.post("/admin/event", headers=sah, json={"name": f"{SUFFIX} ev"})
        created_event_id = (r.get_json() or {}).get("id")
        check("super_admin: POST /admin/event -> 201", r.status_code == 201 and created_event_id)

    finally:
        if created_event_id:
            mongo.db.events.delete_one({"_id": ObjectId(created_event_id)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uid:
            mongo.db.audit_log.delete_many({"actor_id": uid})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]), "action": "event.create"})
        mongo.db.users.delete_one({"email": email})
        print("\n  cleaned up throwaway fixtures (user, org, membership, event, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
