"""Verification — security hardening (Phase S).

Proves per-request session validation + revocation:
  1. a valid token works
  2. disabling a user immediately rejects their existing token (403) — not only at expiry
  3. after disable bumps token_version, the old token stays invalid even once re-enabled
     (401), while a freshly-minted token works
  4. explicit revocation (bump_token_version) kills outstanding tokens (401); a new one works
  5. a deleted user's token is rejected (401)
  6. login on a disabled account is refused (403)
  7. an over-sized request body is rejected with 413 (MAX_CONTENT_LENGTH)
All fixtures cleaned up.

Usage:  python verify_security.py
"""

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model

PASS, FAIL = "PASS", "FAIL"
results = []
EMAIL = "verify_security_user@example.invalid"
PWD = "TestPass1!"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    uid = None
    try:
        mongo.db.users.delete_one({"email": EMAIL})
        uid = user_model.create_user("Sec", "User", EMAIL, hash_password(PWD), role="attendee")

        def tok():
            u = user_model.find_by_id(uid)
            with app.app_context():
                return encode_token(uid, u.get("role", "attendee"), u.get("token_version", 0))

        def hit(token):
            return client.get("/me/settings", headers={"Authorization": f"Bearer {token}"}).status_code

        t0 = tok()
        check("valid token -> 200", hit(t0) == 200)

        # ---- disable: existing token rejected immediately ----
        user_model.set_disabled(uid, True)
        check("disabled user's existing token -> 403", hit(t0) == 403)

        # ---- re-enable: old token still invalid (disable bumped token_version) ----
        user_model.set_disabled(uid, False)
        check("old token after re-enable -> 401 (revoked by version bump)", hit(t0) == 401)
        t1 = tok()
        check("freshly minted token -> 200", hit(t1) == 200)

        # ---- explicit revocation ----
        user_model.bump_token_version(uid)
        check("revocation: previous token -> 401", hit(t1) == 401)
        t2 = tok()
        check("post-revocation fresh token -> 200", hit(t2) == 200)

        # ---- deleted user ----
        user_model.delete_user(uid)
        check("deleted user's token -> 401", hit(t2) == 401)
        uid = None  # already deleted

        # ---- login on a disabled account ----
        mongo.db.users.delete_one({"email": EMAIL})
        uid = user_model.create_user("Sec", "User", EMAIL, hash_password(PWD), role="attendee")
        user_model.set_disabled(uid, True)
        r = client.post("/auth/login", json={"email": EMAIL, "password": PWD})
        check("login on disabled account -> 403", r.status_code == 403)

        # ---- request size cap ----
        big = b'{"x":"' + b"a" * (3 * 1024 * 1024 + 50) + b'"}'
        r = client.post("/auth/login", data=big, content_type="application/json")
        check("over-sized body -> 413", r.status_code == 413)

    finally:
        mongo.db.users.delete_one({"email": EMAIL})
        if uid:
            mongo.db.audit_log.delete_many({"actor_id": str(uid)})
        print("\n  cleaned up throwaway user")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
