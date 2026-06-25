"""Verification — invite emails (Phase E).

Proves both invite-create routes dispatch an email (reusing the 2FA account) AND keep the
in-app accept working:
  1. POST /admin/org-invites emails the invitee (type create_org, correct email + token)
  2. POST /orgs/<id>/invites emails the invitee (type org_join, with the org name)
  3. the emailed token still accepts in-app (race-safe, email-bound)
  4. the real sender's console-fallback path doesn't error when MAIL_* is unset
All fixtures cleaned up.

Usage:  python verify_invites_email.py
"""

from bson import ObjectId

from app import create_app, mongo
import app.routes.orgs as orgs_routes
from app.utils import email as email_util
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "inviteemail"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "invitee1", "invitee2")}
    org_id = None
    super_admin = None
    uids = {}

    # Capture outgoing invite emails instead of sending.
    sent = []
    orig = orgs_routes.send_invite_email
    orgs_routes.send_invite_email = lambda to_email, token, invite_type="org_join", org_name=None, inviter=None: \
        sent.append({"to": to_email, "token": token, "type": invite_type, "org_name": org_name, "inviter": inviter})

    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        mongo.db.invites.delete_many({"email": {"$in": list(emails.values())}})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "IE", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"], super_admin.get("token_version", 0))
            owner_tok = encode_token(uids["owner"], "attendee", 0)
            inv1_tok = encode_token(uids["invitee1"], "attendee", 0)
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # ---- 1. create_org invite emails the invitee ----
        r = client.post("/admin/org-invites", headers=H(sat), json={"email": emails["invitee1"]})
        token1 = (r.get_json() or {}).get("token")
        last = sent[-1] if sent else {}
        check("org-creation invite emailed (create_org, right email + token)",
              r.status_code == 201 and last.get("type") == "create_org"
              and last.get("to") == emails["invitee1"] and last.get("token") == token1)

        # ---- 2. org_join invite emails the invitee with the org name ----
        r = client.post(f"/orgs/{org_id}/invites", headers=H(owner_tok), json={"email": emails["invitee2"]})
        last = sent[-1] if sent else {}
        check("org-join invite emailed (org_join, with org name)",
              r.status_code == 201 and last.get("type") == "org_join"
              and last.get("to") == emails["invitee2"] and last.get("org_name") == f"{SUFFIX} Org")

        # ---- 3. the emailed token still accepts in-app ----
        r = client.post("/invites/accept", headers=H(inv1_tok), json={"token": token1})
        body = r.get_json() or {}
        check("emailed token accepts in-app -> creates org", r.status_code == 200 and body.get("type") == "create_org")

        # ---- 4. real sender console-fallback doesn't raise when MAIL_* unset ----
        ok = True
        try:
            email_util.send_invite_email("nobody@example.invalid", "tok", "org_join", org_name="X")
        except Exception:
            ok = False
        check("real send_invite_email console-fallback does not raise", ok)

    finally:
        orgs_routes.send_invite_email = orig
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        # The accepted create_org invite spun up a new org owned by invitee1 — clean it.
        for o in mongo.db.organizations.find({"created_by": ObjectId(uids["invitee1"])}) if uids.get("invitee1") else []:
            mongo.db.memberships.delete_many({"org_id": o["_id"]})
            mongo.db.organizations.delete_one({"_id": o["_id"]})
        mongo.db.invites.delete_many({"email": {"$in": list(emails.values())}})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, invites, memberships, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
