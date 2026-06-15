# Best Practices — Lyfter Badge App

## Backend (Flask)

### Route structure

Organize routes using Blueprints — one blueprint per domain. Never put all routes in a single file.

```python
# app/badges/routes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

badges_bp = Blueprint("badges", __name__)

@badges_bp.route("/me/badges", methods=["GET"])
@jwt_required()
def my_badges():
    user_id = get_jwt_identity()
    ...
```

Register blueprints in `app/__init__.py`:

```python
from app.badges.routes import badges_bp
app.register_blueprint(badges_bp)
```

### Error handling

Always return explicit HTTP status codes. Never return a 200 with an error message inside.

```python
# Wrong
return jsonify({"error": "Badge not found"}), 200

# Correct
return jsonify({"error": "Badge not found"}), 404
```

Standard codes to use in this project:

| Code | When to use |
|---|---|
| `200` | Successful GET or action |
| `201` | Resource created successfully |
| `400` | Invalid or missing input data |
| `401` | Missing or invalid JWT |
| `403` | Valid JWT but insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict — e.g. badge already redeemed, email already registered |
| `500` | Unexpected server error |

### Environment variables

Load all config from environment variables. Never hardcode secrets or URLs.

```python
# config.py
import os

class Config:
    MONGO_URI = os.environ["MONGO_URI"]
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
```

Use `os.environ["KEY"]` (raises `KeyError`) instead of `os.environ.get("KEY")` for required vars — the app should fail at startup if a required variable is missing, not silently at runtime.

### Input validation

Validate all data coming from the request body before touching the database.

```python
data = request.get_json()
if not data or not data.get("email") or not data.get("password"):
    return jsonify({"error": "email and password are required"}), 400
```

### No debug prints

Remove all `print()` statements before pushing. Use Python's `logging` module if you need runtime output:

```python
import logging
logging.warning("Unexpected token format: %s", token)
```

---

## Frontend (Vue.js)

### Component structure

- One component per file, one responsibility per component.
- Keep components under ~150 lines. If it grows larger, split it.
- Views (`views/`) handle routing and data fetching. Components (`components/`) are reusable and receive data via props.

```
views/MyBadgesView.vue     → fetches /me/badges, passes data down
components/BadgeCard.vue   → receives a badge as prop, renders it
```

### Consuming the API

Centralize all API calls in `src/api/index.js`. Never call `axios` directly from a component.

```js
// src/api/index.js
import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const getMyBadges = () => api.get("/me/badges")
export const redeemBadge = (eventId, token) => api.get(`/redeem/${eventId}/${token}`)
export const login = (credentials) => api.post("/auth/login", credentials)
```

### JWT handling on the client

- Store the token in `localStorage`.
- Read the token only through the API module's interceptor — never spread `localStorage.getItem("access_token")` across components.
- On logout, clear the token from storage and reset the auth store.

```js
// stores/auth.js (Pinia)
export const useAuthStore = defineStore("auth", {
  state: () => ({ token: localStorage.getItem("access_token") || null }),
  actions: {
    login(token) {
      this.token = token
      localStorage.setItem("access_token", token)
    },
    logout() {
      this.token = null
      localStorage.removeItem("access_token")
    },
  },
})
```

### Loading and error states in the UI

Every API call must handle three states: loading, success, and error. Never leave the user staring at a blank screen.

```vue
<template>
  <div v-if="loading">Loading badges...</div>
  <div v-else-if="error" class="text-error">{{ error }}</div>
  <div v-else>
    <BadgeCard v-for="badge in badges" :key="badge.badge_id" :badge="badge" />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getMyBadges } from "@/api"

const badges = ref([])
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getMyBadges()
    badges.value = res.data
  } catch (e) {
    error.value = e.response?.data?.error || "Failed to load badges"
  } finally {
    loading.value = false
  }
})
</script>
```

---

## General

### No debug output in commits

- **Backend:** no `print()` calls left in pushed code.
- **Frontend:** no `console.log()` calls left in pushed code.

### Variable and function names in English

All code identifiers — variables, functions, classes, constants — must be in English.

```python
# Wrong
evento_activo = True
def obtener_badges(usuario_id): ...

# Correct
active_event = True
def get_badges(user_id): ...
```

### Comments: only when the code doesn't explain itself

Write a comment only when there's a non-obvious constraint, a workaround, or a hidden invariant — not to describe what the code does.

```python
# Wrong — states the obvious
# Get the user id from the JWT token
user_id = get_jwt_identity()

# Correct — explains why, not what
# MongoDB ObjectId must be cast to string before JSON serialization
badge["_id"] = str(badge["_id"])
```

### One concern per function

Functions should do one thing. If a function is fetching data, validating it, and saving it all at once, split it.
