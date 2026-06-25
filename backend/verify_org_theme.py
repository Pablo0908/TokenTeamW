"""Verification — per-org theming (Phase T).

Proves an org owner can set a brand theme that persists, is sanitized, and is exposed
everywhere the UI needs it; and that the tier rules hold:
  1. owner sets a valid theme -> 200, persisted
  2. theme appears in GET /orgs/<id>, GET /me/orgs, and event payloads (org.theme)
  3. invalid hex / bad logo URL are sanitized to "" (fall back to platform default)
  4. staff and non-members cannot edit the org (403); super_admin can
All fixtures cleaned up.

Usage:  python verify_org_theme.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "themeverify"
GOOD = {"primary": "#ff0000", "secondary": "#00ff00", "accent": "#0000ff", "logo_url": "https://example.com/logo.png"}


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "staff", "other")}
    org_id = ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "TH", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"], super_admin.get("token_version", 0))
            tok = {k: encode_token(uids[k], "attendee", 0) for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]), json={"name": "Themed ev"}).get_json() or {}).get("id")

        # ---- 1. owner sets a valid theme ----
        r = client.patch(f"/orgs/{org_id}", headers=H(tok["owner"]), json={"theme": GOOD})
        body = r.get_json() or {}
        check("owner sets valid theme -> 200 + echoed", r.status_code == 200 and body.get("theme", {}).get("primary") == "#ff0000")

        # ---- 2. exposed in GET /orgs, /me/orgs, event payload ----
        g = (client.get(f"/orgs/{org_id}", headers=H(tok["owner"])).get_json() or {}).get("theme", {})
        check("GET /orgs/<id> returns the theme", g.get("primary") == "#ff0000" and g.get("logo_url") == GOOD["logo_url"])
        me = client.get("/me/orgs", headers=H(tok["owner"])).get_json() or {}
        mine = next((o for o in me.get("orgs", []) if o["id"] == org_id), {})
        check("/me/orgs carries the theme", mine.get("theme", {}).get("accent") == "#0000ff")
        ev = client.get(f"/events/{ev_id}", headers=H(tok["owner"])).get_json() or {}
        check("event payload carries org.theme", (ev.get("org") or {}).get("theme", {}).get("primary") == "#ff0000")

        # ---- 3. sanitization ----
        r = client.patch(f"/orgs/{org_id}", headers=H(tok["owner"]),
                         json={"theme": {"primary": "zzz", "secondary": "#abcdef", "logo_url": "ftp://nope/x"}})
        th = (r.get_json() or {}).get("theme", {})
        check("invalid hex -> '' , valid kept, bad logo scheme -> ''",
              th.get("primary") == "" and th.get("secondary") == "#abcdef" and th.get("logo_url") == "")

        # ---- 4. tier ----
        check("staff cannot edit the org (403)",
              client.patch(f"/orgs/{org_id}", headers=H(tok["staff"]), json={"theme": GOOD}).status_code == 403)
        check("non-member cannot edit the org (403)",
              client.patch(f"/orgs/{org_id}", headers=H(tok["other"]), json={"theme": GOOD}).status_code == 403)
        check("super_admin can edit the org theme (200)",
              client.patch(f"/orgs/{org_id}", headers=H(sat), json={"theme": GOOD}).status_code == 200)

    finally:
        if ev_id:
            mongo.db.badges.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, membership, event, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
