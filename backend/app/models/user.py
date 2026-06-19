from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# --- Appearance/behaviour preferences (synced to the frontend Settings panel) ---
# Stored on the user document so they follow the account across devices and survive
# redeploys (localStorage on the client is only a fast-boot cache).
DEFAULT_PREFERENCES = {
    "language": "en",
    "lightMode": False,
    "effects": True,
    "saturation": 1.0,
    "contrast": 1.0,
}

_LANGUAGES = ("en", "es")
_SATURATION = (0.5, 1.5)
_CONTRAST = (0.8, 1.2)


def _clamp(value, lo, hi, fallback):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if v != v:  # NaN
        return fallback
    return max(lo, min(hi, v))


def sanitize_preferences(raw, base=None):
    """Whitelist + validate client-supplied preferences: unknown keys are dropped,
    out-of-range numbers clamped, types coerced. `base` patches onto existing prefs
    so a partial PUT only changes the keys it sends. Never trust the client."""
    result = dict(DEFAULT_PREFERENCES)
    if isinstance(base, dict):
        for k in DEFAULT_PREFERENCES:
            if k in base:
                result[k] = base[k]
    if isinstance(raw, dict):
        if raw.get("language") in _LANGUAGES:
            result["language"] = raw["language"]
        if "lightMode" in raw:
            result["lightMode"] = bool(raw["lightMode"])
        if "effects" in raw:
            result["effects"] = bool(raw["effects"])
        if "saturation" in raw:
            result["saturation"] = _clamp(raw["saturation"], *_SATURATION, result["saturation"])
        if "contrast" in raw:
            result["contrast"] = _clamp(raw["contrast"], *_CONTRAST, result["contrast"])
    return result


def merged_preferences(user_doc):
    """Stored prefs merged onto the defaults — so older users missing the field (or
    missing a single key) still return a complete, valid object."""
    return sanitize_preferences(user_doc.get("preferences") if isinstance(user_doc, dict) else None)


def create_indexes():
    mongo.db.users.create_index("email", unique=True)


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create_user(name, lastname, email, password_hash, role="attendee"):
    result = mongo.db.users.insert_one(
        {
            "name": name,
            "lastname": lastname,
            "email": email.lower(),
            "hashed_password": password_hash,
            "role": role,
            "preferences": dict(DEFAULT_PREFERENCES),
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def get_preferences(user_id):
    return merged_preferences(find_by_id(user_id))


def update_preferences(user_id, raw):
    """Apply a (partial) preferences patch. Returns the saved prefs, or None if the
    user doesn't exist."""
    user = find_by_id(user_id)
    if not user:
        return None
    prefs = sanitize_preferences(raw, base=user.get("preferences"))
    mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": {"preferences": prefs}})
    return prefs


def find_by_email(email):
    return mongo.db.users.find_one({"email": email.lower()})


def find_by_id(user_id):
    try:
        return mongo.db.users.find_one({"_id": _oid(user_id)})
    except Exception:
        return None


def set_role(user_id, role):
    try:
        result = mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": {"role": role}})
        return result.matched_count > 0
    except Exception:
        return False


def all_users():
    return list(mongo.db.users.find().sort("created_at", 1))


def count_attendees():
    return mongo.db.users.count_documents({"role": "attendee"})
