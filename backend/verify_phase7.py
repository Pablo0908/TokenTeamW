"""Verification — event visibility + org-scoped feed (Phase 7 / Phase E).

Proves:
  1. a brand-new attendee (no scans, no membership) sees an EMPTY feed
  2. after scanning in org A, that attendee's feed lists org A's PUBLIC events only
     (unlisted hidden from non-members, scan-only never listed)
  3. an org MEMBER sees public AND unlisted events (still not scan-only)
  4. scan-only events are still scannable by QR
  5. event detail is still reachable by id (deep links / announcements keep working)
  6. event_summary carries `visibility`
  7. /me/badges shows earned events regardless of visibility, and omits unearned ones
All fixtures cleaned up.

Usage:  python verify_phase7.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "visverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "scanner", "fresh")}
    org_a = None
    evs = {}
    toks = {}
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "VS", em, hash_password("TestPass1!"), role="attendee")

        org_a = org_model.create_org(f"{SUFFIX} A", f"{SUFFIX}-a", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_a, "owner")

        with app.app_context():
            for k in uids:
                toks[k] = encode_token(uids[k], "attendee")
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # Three events with distinct visibilities, each with one badge.
        for key, vis in (("pub", "public"), ("unl", "unlisted"), ("scn", "scan-only")):
            eid = (client.post(f"/orgs/{org_a}/event", headers=H(toks["owner"]),
                               json={"name": f"{SUFFIX} {key}", "visibility": vis}).get_json() or {}).get("id")
            tok = (client.post(f"/orgs/{org_a}/events/{eid}/badge", headers=H(toks["owner"]),
                               json={"name": f"{key} badge"}).get_json() or {}).get("token")
            evs[key] = {"id": eid, "token": tok, "vis": vis}

        def feed_ids(tk):
            return {e["id"] for e in (client.get("/events/", headers=H(tk)).get_json() or [])}

        # ---- 1. fresh attendee: empty feed ----
        check("brand-new attendee sees an empty feed", feed_ids(toks["fresh"]) == set())

        # ---- 2. after a scan, public-only feed for a non-member ----
        check("scanner scans the public event (200)",
              client.get(f"/redeem/{evs['pub']['id']}/{evs['pub']['token']}", headers=H(toks["scanner"])).status_code == 200)
        sfeed = feed_ids(toks["scanner"])
        check("scanner's feed lists the PUBLIC event", evs["pub"]["id"] in sfeed)
        check("scanner's feed hides the UNLISTED event (non-member)", evs["unl"]["id"] not in sfeed)
        check("scanner's feed hides the SCAN-ONLY event", evs["scn"]["id"] not in sfeed)

        # ---- 3. member sees public + unlisted ----
        ofeed = feed_ids(toks["owner"])
        check("member sees PUBLIC + UNLISTED, never SCAN-ONLY",
              evs["pub"]["id"] in ofeed and evs["unl"]["id"] in ofeed and evs["scn"]["id"] not in ofeed)

        # ---- 4. scan-only still scannable ----
        check("scan-only event is still scannable by QR (200)",
              client.get(f"/redeem/{evs['scn']['id']}/{evs['scn']['token']}", headers=H(toks["scanner"])).status_code == 200)

        # ---- 5. detail reachable by id (link/announcement) ----
        r = client.get(f"/events/{evs['unl']['id']}", headers=H(toks["scanner"]))
        det = r.get_json() or {}
        check("unlisted event detail is reachable by id (200)", r.status_code == 200)

        # ---- 6. visibility in payloads ----
        check("event detail carries visibility", det.get("visibility") == "unlisted")
        pub_entry = next((e for e in (client.get("/events/", headers=H(toks["owner"])).get_json() or [])
                          if e["id"] == evs["pub"]["id"]), {})
        check("feed entry carries visibility", pub_entry.get("visibility") == "public")

        # ---- 7. /me/badges = earned events, any visibility; unearned omitted ----
        mb = {g["event_id"] for g in (client.get("/me/badges", headers=H(toks["scanner"])).get_json() or [])}
        check("/me/badges includes earned public + scan-only events",
              evs["pub"]["id"] in mb and evs["scn"]["id"] in mb)
        check("/me/badges omits the unearned (unlisted) event", evs["unl"]["id"] not in mb)

    finally:
        for e in evs.values():
            if e.get("id"):
                mongo.db.badges.delete_many({"event_id": ObjectId(e["id"])})
                mongo.db.redemptions.delete_many({"event_id": ObjectId(e["id"])})
                mongo.db.events.delete_one({"_id": ObjectId(e["id"])})
        if org_a:
            mongo.db.audit_log.delete_many({"org_id": org_a})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_a)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_a)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, membership, events, badges, redemptions, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
