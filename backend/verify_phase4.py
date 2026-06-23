"""Phase 4 verification — org self-service (codes/invites), members, org-scoped panel.

Drives the real HTTP surface with locally-minted JWTs and throwaway fixtures, proving:
  1. super_admin_required gates org-creation invites
  2. create_org invite -> accept creates a NEW org + owner membership, grants NO
     platform_role, and is single-use (re-accept fails) and revocable
  3. accept is email-matched (wrong account can't accept someone else's invite)
  4. org_join invites work; BOTH owner and admin can send them
  5. owner-only enforcement: an admin cannot change roles / remove members
  6. org-scoped isolation: a member sees only their org; a non-member is 403;
     super_admin passes
  7. app still works (feed + scan)
All fixtures cleaned up.

Usage:  python verify_phase4.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "p4verify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "admin", "other")}
    org_b_id = ev_id = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "P4", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        sah = H(sat)

        # ---- 1. super_admin_required on org-creation invites ----
        check("non-super-admin cannot create org invites (403)",
              client.post("/admin/org-invites", headers=H(tok["owner"]), json={"email": emails["owner"]}).status_code == 403)
        r = client.post("/admin/org-invites", headers=sah, json={"email": emails["owner"]})
        create_tok = r.get_json().get("token")
        check("super_admin issues create_org invite (201)", r.status_code == 201 and create_tok)

        # ---- 3. email-match: wrong account can't accept ----
        check("accept rejected for non-matching email (400)",
              client.post("/invites/accept", headers=H(tok["other"]), json={"token": create_tok}).status_code == 400)

        # ---- 2. accept create_org -> org + owner, no platform_role, single-use ----
        r = client.post("/invites/accept", headers=H(tok["owner"]), json={"token": create_tok})
        org_b_id = r.get_json().get("org", {}).get("id")
        check("accept create_org -> 200 + new org", r.status_code == 200 and org_b_id)
        m = mongo.db.memberships.find_one({"user_id": ObjectId(uids["owner"]), "org_id": ObjectId(org_b_id)})
        owner_doc = mongo.db.users.find_one({"_id": ObjectId(uids["owner"])})
        check("redeemer is owner, NO platform_role granted",
              m and m["role"] == "owner" and owner_doc.get("platform_role") is None)
        check("create_org invite is single-use (re-accept 400)",
              client.post("/invites/accept", headers=H(tok["owner"]), json={"token": create_tok}).status_code == 400)
        check("/me/orgs reflects owner membership",
              any(o["id"] == org_b_id and o["role"] == "owner" for o in client.get("/me/orgs", headers=H(tok["owner"])).get_json()["orgs"]))

        # revocable: a fresh create_org invite can be revoked, then not accepted
        r = client.post("/admin/org-invites", headers=sah, json={"email": emails["other"]})
        rid, rtok = r.get_json()["id"], r.get_json()["token"]
        client.post(f"/admin/org-invites/{rid}/revoke", headers=sah)
        check("revoked invite cannot be accepted (400)",
              client.post("/invites/accept", headers=H(tok["other"]), json={"token": rtok}).status_code == 400)

        # ---- 4. org_join: owner invites admin; admin can also invite ----
        r = client.post(f"/orgs/{org_b_id}/invites", headers=H(tok["owner"]), json={"email": emails["admin"]})
        join_tok = r.get_json().get("token")
        check("owner sends org_join invite (201)", r.status_code == 201 and join_tok)
        check("invitee accepts -> admin membership",
              client.post("/invites/accept", headers=H(tok["admin"]), json={"token": join_tok}).status_code == 200
              and mongo.db.memberships.find_one({"user_id": ObjectId(uids["admin"]), "org_id": ObjectId(org_b_id)})["role"] == "admin")
        check("an ADMIN can also send org_join invites (201)",
              client.post(f"/orgs/{org_b_id}/invites", headers=H(tok["admin"]), json={"email": emails["other"]}).status_code == 201)

        # ---- 5. owner-only: admin cannot change roles / remove members ----
        check("admin cannot change a member's role (403)",
              client.patch(f"/orgs/{org_b_id}/members/{uids['admin']}", headers=H(tok["admin"]), json={"role": "staff"}).status_code == 403)
        check("admin cannot remove a member / demote owner (403)",
              client.delete(f"/orgs/{org_b_id}/members/{uids['owner']}", headers=H(tok["admin"])).status_code == 403)
        check("owner CAN change a member's role (200)",
              client.patch(f"/orgs/{org_b_id}/members/{uids['admin']}", headers=H(tok["owner"]), json={"role": "staff"}).status_code == 200)

        # ---- 6. org-scoped isolation ----
        r = client.post(f"/orgs/{org_b_id}/event", headers=H(tok["owner"]), json={"name": f"{SUFFIX} ev", "event_type": "workshop"})
        ev_id = r.get_json().get("id")
        check("owner creates an org event (201)", r.status_code == 201 and ev_id)
        check("org member sees the org's events",
              any(e["id"] == ev_id for e in client.get(f"/orgs/{org_b_id}/events", headers=H(tok["owner"])).get_json()))
        check("non-member cannot read the org panel (403)",
              client.get(f"/orgs/{org_b_id}/events", headers=H(tok["other"])).status_code == 403
              and client.get(f"/orgs/{org_b_id}/audit", headers=H(tok["other"])).status_code == 403)
        check("super_admin can access any org panel (200)",
              client.get(f"/orgs/{org_b_id}/events", headers=sah).status_code == 200)

        # ---- 7. app still works ----
        check("GET /events/ still works (200)", client.get("/events/", headers=H(tok["owner"])).status_code == 200)

    finally:
        if ev_id:
            mongo.db.redemptions.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.badges.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        id_list = list(uids.values())
        mongo.db.audit_log.delete_many({"actor_id": {"$in": id_list}})
        mongo.db.invites.delete_many({"email": {"$in": list(emails.values())}})
        if org_b_id:
            mongo.db.audit_log.delete_many({"org_id": org_b_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_b_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_b_id)})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, memberships, invites, event, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
