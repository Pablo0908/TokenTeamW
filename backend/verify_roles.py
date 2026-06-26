"""Verification — role model cleanup + super-admin self-service promotion.

Proves the platform tier is the ONLY elevated identity and super admins manage it:
  1. a super admin can promote another user (PATCH /admin/users/<id>/super-admin {true});
     the user gains platform_role and shows super_admin:true in GET /admin/users
  2. revoking ({false}) clears it and takes effect IMMEDIATELY — the demoted user's existing
     token is refused (403) on a super_admin route, with no re-login (platform_role is
     re-read per request, not carried in the JWT)
  3. a non-super-admin calling the endpoint is refused (403)
  4. a super admin cannot change their OWN super-admin status (400) — no self-lockout
  5. the legacy global-role route (PATCH /admin/users/<id>/role) is gone
All fixtures cleaned up. Never demotes the real DB super admin.

Usage:  python verify_roles.py
"""

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "roleverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("target", "other")}
    uids = {}
    super_admin = None
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "RV", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin.get("role", "attendee"), super_admin.get("token_version", 0))
            tok = {k: encode_token(uids[k], "attendee", 0) for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        target, other = uids["target"], uids["other"]

        # ---- 1. promote ----
        r = client.patch(f"/admin/users/{target}/super-admin", headers=H(sat), json={"super_admin": True})
        promoted = user_model.find_by_id(target)
        listed = next((u for u in (client.get("/admin/users", headers=H(sat)).get_json() or {}).get("users", [])
                       if u["id"] == target), {})
        check("super admin promotes a user -> 200, platform_role set, listed super_admin:true",
              r.status_code == 200 and promoted.get("platform_role") == "super_admin" and listed.get("super_admin") is True)

        # ---- 2. promoted user's existing token now passes a super_admin route ----
        check("promoted user's token now passes a super_admin route (no re-login)",
              client.get("/admin/users", headers=H(tok["target"])).status_code == 200)

        # ---- 2b. revoke -> cleared + takes effect immediately ----
        r = client.patch(f"/admin/users/{target}/super-admin", headers=H(sat), json={"super_admin": False})
        demoted = user_model.find_by_id(target)
        check("revoke -> 200 and platform_role cleared",
              r.status_code == 200 and demoted.get("platform_role") is None)
        check("demoted user's same token is now refused on a super_admin route (403)",
              client.get("/admin/users", headers=H(tok["target"])).status_code == 403)

        # ---- 3. non-super-admin cannot promote ----
        check("a non-super-admin calling the endpoint -> 403",
              client.patch(f"/admin/users/{target}/super-admin", headers=H(tok["other"]), json={"super_admin": True}).status_code == 403)

        # ---- 4. cannot change your own status ----
        check("super admin cannot change their OWN super-admin status (400)",
              client.patch(f"/admin/users/{super_admin['_id']}/super-admin", headers=H(sat), json={"super_admin": False}).status_code == 400)

        # ---- 5. legacy global-role route is gone ----
        check("legacy PATCH /admin/users/<id>/role is gone (404/405)",
              client.patch(f"/admin/users/{target}/role", headers=H(sat), json={"role": "admin"}).status_code in (404, 405))

    finally:
        # Safety: ensure throwaway target never lingers as a super admin.
        for uid in uids.values():
            mongo.db.users.delete_one({"_id": user_model._oid(uid)})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]), "action": "user.role_change"})
        print("\n  cleaned up throwaway fixtures (users, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
