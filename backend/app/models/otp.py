import secrets
from datetime import datetime, timezone

from app import mongo

OTP_TTL_SECONDS = 600   # 10 minutes
MAX_ATTEMPTS    = 5


def create_indexes():
    # TTL index: MongoDB deletes the doc automatically after OTP_TTL_SECONDS.
    mongo.db.otp_codes.create_index("created_at", expireAfterSeconds=OTP_TTL_SECONDS)
    mongo.db.otp_codes.create_index("email", unique=True)


def generate(email: str) -> str:
    code = str(secrets.randbelow(1_000_000)).zfill(6)
    mongo.db.otp_codes.replace_one(
        {"email": email},
        {"email": email, "code": code, "attempts": 0, "created_at": datetime.now(timezone.utc)},
        upsert=True,
    )
    return code


def verify(email: str, code: str):
    """Returns (ok: bool, error_message: str | None)."""
    doc = mongo.db.otp_codes.find_one({"email": email})
    if not doc:
        return False, "Code expired or not found. Please sign in again."

    if doc.get("attempts", 0) >= MAX_ATTEMPTS:
        mongo.db.otp_codes.delete_one({"email": email})
        return False, "Too many incorrect attempts. Please sign in again."

    if doc["code"] != code:
        mongo.db.otp_codes.update_one({"email": email}, {"$inc": {"attempts": 1}})
        left = MAX_ATTEMPTS - doc.get("attempts", 0) - 1
        return False, f"Incorrect code — {left} attempt(s) remaining."

    mongo.db.otp_codes.delete_one({"email": email})
    return True, None
