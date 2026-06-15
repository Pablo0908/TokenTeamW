---
name: create-route
description: Scaffold a Flask blueprint for this project. Use when the user asks to create a route, add an endpoint, or needs a new Flask blueprint for auth, events, badges, or redemptions.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-route — Scaffold a Flask Blueprint

Create a Flask blueprint called `$ARGUMENTS`.

Arguments passed: `$ARGUMENTS`

## Mandatory rules

- Plain Python, no TypeScript
- File: `$ARGUMENTS.py` in `app/routes/`
- Register the blueprint in `app/__init__.py` with the appropriate URL prefix
- Use `@jwt_required` and `@admin_required` decorators from `app/utils/auth.py` — never inline token validation inside a handler
- All error responses: `jsonify({"error": "<message>"}), <status_code>`
- All success responses must match the shape in `Technical-Design/Technical-Design-Backend.md` for that endpoint

## Base pattern

```python
from flask import Blueprint, request, jsonify
from app.utils.auth import jwt_required, admin_required
from app.models.[name] import [Model]

[name]_bp = Blueprint('[name]', __name__, url_prefix='/[name]')


@[name]_bp.route('/', methods=['GET'])
@jwt_required
def list_[name](current_user):
    # implementation
    pass


@[name]_bp.route('/<id>', methods=['GET'])
@jwt_required
def get_[name](current_user, id):
    # implementation
    pass


@[name]_bp.route('/', methods=['POST'])
@jwt_required
@admin_required
def create_[name](current_user):
    # implementation
    pass
```

## Error shape convention

```python
# 400 Bad Request
return jsonify({"error": "Missing required field: email"}), 400

# 401 Unauthorized
return jsonify({"error": "Token is invalid or expired"}), 401

# 403 Forbidden
return jsonify({"error": "Admin access required"}), 403

# 404 Not Found
return jsonify({"error": "Resource not found"}), 404

# 409 Conflict
return jsonify({"error": "Badge already redeemed"}), 409

# 500 Internal Server Error
return jsonify({"error": "Internal server error"}), 500
```

Infer routes, HTTP methods, and auth requirements from the blueprint name: auth (no decorator on public routes), events, badges, redemptions.
