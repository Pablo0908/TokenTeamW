from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


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
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


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
