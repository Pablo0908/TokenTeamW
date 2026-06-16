---
name: create-model
description: Create a PyMongo collection helper for this project. Use when the user asks to create a model, define a MongoDB collection, or add database access helpers for users, events, badges, or redemptions.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-model — Create a PyMongo Collection Helper

Create a PyMongo model helper called `$ARGUMENTS`.

Arguments passed: `$ARGUMENTS`

## Mandatory rules

- Plain Python, no TypeScript
- File: `$ARGUMENTS.py` in `app/models/`
- Never import `mongo` directly in routes — routes always call functions from this model file
- Indexes must be created at app startup (called from `app/__init__.py`), not per-request
- The `redemptions` collection requires a compound unique index on `(badge_id, user_id)` to prevent double-redemption at the database level
- Field names must match the schema in `Technical-Design/Technical-Design-Backend.md` Section 2

## Base pattern

```python
from bson import ObjectId
from datetime import datetime, timezone
from app import mongo  # PyMongo instance from app factory


def create_indexes():
    """Call once at startup to ensure indexes exist."""
    # example: mongo.db.[collection].create_index([...], unique=True)
    pass


def insert_[name](data: dict) -> str:
    """Insert a document and return its string _id."""
    result = mongo.db.[collection].insert_one({
        **data,
        "created_at": datetime.now(timezone.utc),
    })
    return str(result.inserted_id)


def find_[name]_by_id(id: str) -> dict | None:
    try:
        return mongo.db.[collection].find_one({"_id": ObjectId(id)})
    except Exception:
        return None


def find_all_[name]() -> list[dict]:
    return list(mongo.db.[collection].find())
```

## Schema reference (from Technical-Design-Backend.md)

| Collection    | Key fields |
|---------------|-----------|
| users         | name, email, hashed_password, role (admin\|participant), created_at |
| events        | name, description, start_date, end_date, prize, created_by, created_at |
| badges        | event_id, name, description, token (UUID, unique), qr_image_url, created_at |
| redemptions   | badge_id, event_id (denormalized), user_id, redeemed_at — compound unique index (badge_id, user_id) |

Infer field names and index requirements from the collection name. Always serialize `ObjectId` to `str` before returning to routes.
