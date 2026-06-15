---
name: create-util
description: Add a utility or helper module for this Flask project. Use when the user asks to create a utility, add a helper function, or needs JWT, bcrypt, or QR generation logic under app/utils/.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /create-util — Create a Utility/Helper Module

Create a utility module called `$ARGUMENTS`.

Arguments passed: `$ARGUMENTS`

## Mandatory rules

- Plain Python, no TypeScript
- File: `$ARGUMENTS.py` in `app/utils/`
- Never hardcode secrets — read all keys from environment via `os.environ` or `current_app.config`
- Decorators (`@jwt_required`, `@admin_required`) live in `app/utils/auth.py` — never in route files
- QR generation helpers live in `app/utils/qr.py`

## auth.py pattern

```python
import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta, timezone


def encode_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def jwt_required(f):
    """Decorator that injects current_user dict into the route handler."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing"}), 401
        try:
            payload = decode_token(auth_header.split(" ")[1])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401
        return f(*args, current_user=payload, **kwargs)
    return decorated


def admin_required(f):
    """Decorator that enforces admin role. Must be applied after @jwt_required."""
    @wraps(f)
    def decorated(*args, current_user, **kwargs):
        if current_user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, current_user=current_user, **kwargs)
    return decorated
```

## qr.py pattern

```python
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


def generate_qr_base64(token: str) -> str:
    """Return a base64-encoded PNG QR image for the given token string."""
    img = qrcode.make(token)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
```

## bcrypt helpers (inline in auth route, not a separate util)

```python
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()  # initialized with app in app/__init__.py

# Hash: bcrypt.generate_password_hash(plain_password).decode('utf-8')
# Check: bcrypt.check_password_hash(hashed, plain_password)
```

Infer which helpers are needed from the module name: auth (JWT + decorators), qr (QR generation), or a custom domain utility.
