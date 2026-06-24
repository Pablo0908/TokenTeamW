import re
from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def search_ids(q):
    """User ids (as strings) whose email, name or lastname matches `q` (case-insensitive).
    Used to resolve an audit search term to actors over indexed identity fields."""
    rx = {"$regex": re.escape(q), "$options": "i"}
    cursor = mongo.db.users.find(
        {"$or": [{"email": rx}, {"name": rx}, {"lastname": rx}]}, {"_id": 1}
    )
    return [str(doc["_id"]) for doc in cursor]


# --- Appearance/behaviour preferences (synced to the frontend Settings panel) ---
# Stored on the user document so they follow the account across devices and survive
# redeploys (localStorage on the client is only a fast-boot cache).
DEFAULT_PREFERENCES = {
    "language": "en",
    "lightMode": False,
    "effects": True,
    "saturation": 1.0,
    "contrast": 1.0,
    # Accessibility
    "fontSize": 16,
    "dyslexiaFont": False,
    "lineSpacing": False,
    "boldText": False,
    "autoTheme": False,
    "highContrast": False,
    "colorBlind": False,
    "largeTapTargets": False,
    "focusHighlight": False,
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
            # Platform tier, separate from the org-level `role` above. None for normal
            # accounts; "super_admin" grants global authority (set deliberately, never
            # at self-registration). Kept on every new doc for shape consistency.
            "platform_role": None,
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


def set_platform_role(user_id, platform_role):
    """Set the platform tier ("super_admin" or None). Org-level `role` is untouched."""
    try:
        result = mongo.db.users.update_one(
            {"_id": _oid(user_id)}, {"$set": {"platform_role": platform_role}}
        )
        return result.matched_count > 0
    except Exception:
        return False


def is_super_admin(user_doc):
    return bool(user_doc) and user_doc.get("platform_role") == "super_admin"


def mark_announcements_seen(user_id):
    """Stamp now as the user's announcements last-seen time. Anything created after
    this is "unread" for them. Cross-device because it lives on the account."""
    try:
        mongo.db.users.update_one(
            {"_id": _oid(user_id)},
            {"$set": {"announcements_seen_at": datetime.now(timezone.utc)}},
        )
        return True
    except Exception:
        return False


def set_disabled(user_id, disabled: bool):
    try:
        result = mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": {"disabled": disabled}})
        return result.matched_count > 0
    except Exception:
        return False


def update_name(user_id, name, lastname):
    mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": {"name": name, "lastname": lastname}})


def update_avatar(user_id, avatar_url):
    field = {"avatar_url": avatar_url} if avatar_url else {"avatar_url": None}
    mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": field})


def update_password(user_id, hashed_password):
    mongo.db.users.update_one({"_id": _oid(user_id)}, {"$set": {"hashed_password": hashed_password}})


def delete_user(user_id):
    try:
        result = mongo.db.users.delete_one({"_id": _oid(user_id)})
        return result.deleted_count > 0
    except Exception:
        return False


def all_users():
    return list(mongo.db.users.find().sort("created_at", 1))


def count_attendees():
    return mongo.db.users.count_documents({"role": "attendee"})
