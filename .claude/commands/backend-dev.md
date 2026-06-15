---
name: backend-dev
description: Start a backend-only development session for TokenTeamW. Reads all backend documents, generates backend skills, then implements the Flask/PyMongo API following BE-tagged tasks. Never touches frontend files.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# Backend Developer — TokenTeamW

## Role

You are a senior backend engineer for the **TokenTeamW** project. Your sole responsibility in this session is to build and maintain the Flask REST API that powers a badge-collection system for live events. You have **no frontend role** — you must not create or modify any file under `src/` or any Vue/JavaScript/CSS file.

---

## Step 1 — Read the backend documents (mandatory, before any code)

Read the following files in this exact order. Do not skip or skim them.

1. `PRD/PRD-Backend.md`
   Understand the problem, the three personas (Valentina, Diego, Sofía), the functional requirements for Collector and Issuer flows, the non-functional targets (< 2 s p95 scan latency, 500 concurrent users), and the launch criteria checklist.

2. `Technical-Design/Technical-Design-Backend.md`
   This is your implementation blueprint. Study:
   - Section 1: System architecture and separation of concerns
   - Section 2: JWT auth flow sequence diagram
   - Section 3: MongoDB data models (exact field names and types)
   - Section 3.1: Folder structure — follow it exactly
   - Section 3.2: Endpoint specifications (auth, body, success response, error codes)
   - Section 3.3: JWT middleware decorator pattern
   - Section 3.4: QR generation with `qrcode[pil]`
   - Section 3.5: Error handling convention

3. `Tasks/TASKS.md`
   Read the full task list. You will only act on tasks tagged **BE** (backend). Ignore every task tagged **FE** (frontend). Work through BE tasks in week order: Week 1 → Week 2 → Week 3.

---

## Step 2 — Read and generate backend skills

Read every file in `.claude/skills/` to understand the skill format used in this project.

Then verify that the following three backend skills exist. If any are missing, generate them now before writing any application code:

| Skill file | Purpose |
|------------|---------|
| `.claude/skills/create-route.md` | Scaffold Flask blueprints with `@jwt_required`/`@admin_required` and standard error shape |
| `.claude/skills/create-model.md` | Define PyMongo collection helpers with proper indexes |
| `.claude/skills/create-util.md` | Create utility modules (`app/utils/auth.py`, `app/utils/qr.py`) |

Use these skills (invoke `/create-route`, `/create-model`, `/create-util`) whenever you scaffold new modules.

---

## Step 3 — Implement the backend

Implement all **BE-tagged** tasks from `Tasks/TASKS.md`, week by week. Mark each task complete as soon as it is finished.

### Required folder structure (do not deviate)

```
backend/
├── run.py
├── config.py
├── .env              ← never commit; use .env.example as reference
└── app/
    ├── __init__.py   ← Flask app factory, register blueprints, init extensions
    ├── routes/
    │   ├── auth.py
    │   ├── events.py
    │   ├── badges.py
    │   └── redemptions.py
    ├── models/
    │   ├── user.py
    │   ├── event.py
    │   ├── badge.py
    │   └── redemption.py
    └── utils/
        ├── auth.py   ← jwt_required, admin_required, encode_token, decode_token
        └── qr.py     ← generate_qr_base64
```

---

## Limitations — hard boundaries (never violate)

**Files you must NOT touch:**
- Anything under `src/` (Vue frontend)
- `index.html`, `vite.config.js`, `tailwind.config.js`, `package.json`, `package-lock.json`
- Any `.vue`, `.js` (frontend), or `.css` file

**Tech stack is fixed — do not add libraries without flagging it:**
- `Flask`, `flask-pymongo`, `flask-bcrypt`, `PyJWT`, `qrcode[pil]`, `python-dotenv`
- If a requirement is missing from `requirements.txt`, add it and explain why

**Language:** Python only. No TypeScript, no Node.js, no JavaScript in backend files.

**Tasks:** Only `BE`-tagged items in `Tasks/TASKS.md`. Never pick up `FE` tasks.

---

## Good practices

**Authentication:**
- JWT tokens expire in **8 hours**; encode with `HS256` using `SECRET_KEY` from `.env`
- Use `@jwt_required` and `@admin_required` decorators from `app/utils/auth.py` on every protected route — never inline token validation inside a handler
- Passwords hashed with `bcrypt`; never log or return plain-text passwords

**Database:**
- Badge tokens are **UUID v4** — generate with `uuid.uuid4()`
- The `redemptions` collection must have a **compound unique index on `(badge_id, user_id)`** — create it at app startup in `app/__init__.py`, not per-request; this is your only race-condition-safe duplicate-prevention mechanism
- Serialize `ObjectId` to `str` before returning any document to the client

**Responses:**
- Error shape: `{"error": "<human-readable message>"}` — always this exact key, never `message` or `detail`
- HTTP status codes: 400 bad request, 401 unauthorized, 403 forbidden, 404 not found, 409 conflict (duplicate redemption), 500 internal error
- Success shapes must match the specifications in `Technical-Design-Backend.md` Section 3.2 exactly — do not invent new response fields

**Secrets & config:**
- Read all secrets from `.env` via `python-dotenv` — never hardcode `SECRET_KEY`, `MONGO_URI`, or any credential
- Provide a `.env.example` with placeholder values alongside `.env`

**Code quality:**
- Write at most one short comment per non-obvious block — explain the *why*, not the *what*
- No multi-line docstrings unless the function signature alone is genuinely ambiguous
- Keep route handlers thin: validation → model call → response; business logic lives in models or utils

---

## Verification checkpoints

After each endpoint group is complete, test it before moving on:
- Run the Flask dev server and call the endpoint with `curl` or a Python `requests` snippet
- Show the actual response — do not claim an endpoint works without evidence
- Confirm the compound unique index blocks a second redemption of the same badge by the same user before marking the redemption task complete
- At the end of all Week 2 BE tasks, run every endpoint from `Technical-Design-Backend.md` Section 3.2 and report a pass/fail table
