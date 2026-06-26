"""Create (or reuse) a test attendee and print a browser-console snippet to log in.

Usage:
    python seed_test_user.py

Paste the printed localStorage snippet into the browser DevTools console while on
http://127.0.0.1:5173, then hard-refresh (Ctrl+Shift+R) to start the session.
"""

import json
from app import create_app, mongo
from app.models.user import create_user, find_by_email
from app.utils.auth import hash_password, encode_token

TEST_EMAIL = "test.onboarding@lyfter.cc"
TEST_PASS  = "Test1234!"
TEST_NAME  = "Test"
TEST_LAST  = "Usuario"

app = create_app()

with app.app_context():
    doc = find_by_email(TEST_EMAIL)
    if doc:
        uid  = str(doc["_id"])
        role = doc.get("role", "attendee")
        user_obj = {
            "id":        uid,
            "name":      doc.get("name", TEST_NAME),
            "lastname":  doc.get("lastname", TEST_LAST),
            "email":     doc.get("email", TEST_EMAIL),
            "role":      role,
            "platform_role": doc.get("platform_role"),
            "avatar_url":    doc.get("avatar_url"),
            "preferences":   doc.get("preferences", {}),
        }
        print(f"Existing user found: {TEST_EMAIL}  id={uid}")
    else:
        uid  = create_user(TEST_NAME, TEST_LAST, TEST_EMAIL, hash_password(TEST_PASS), role="attendee")
        role = "attendee"
        user_obj = {
            "id":        uid,
            "name":      TEST_NAME,
            "lastname":  TEST_LAST,
            "email":     TEST_EMAIL,
            "role":      role,
            "platform_role": None,
            "avatar_url":    None,
            "preferences":   {},
        }
        print(f"Created test user: {TEST_EMAIL}  id={uid}")

    token = encode_token(uid, role, token_version=0)
    user_json = json.dumps(user_obj, ensure_ascii=False)

    print("\n--- Paste this into DevTools console (F12) on http://127.0.0.1:5173 ---\n")
    print(f"localStorage.setItem('token', '{token}');")
    print(f"localStorage.setItem('role',  '{role}');")
    print(f"localStorage.setItem('user',  {json.dumps(user_json)});")
    print("\n--- Then press Ctrl+Shift+R to hard-refresh ---\n")
    print(f"Credentials  →  email: {TEST_EMAIL}  |  password: {TEST_PASS}")
