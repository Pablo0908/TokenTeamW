# Production Deployment — env & config reference

Backend: **Render** (gunicorn, always-on, HTTPS) · Frontend: **Vercel** (Vue PWA static) ·
DB: **separate `beeworking_prod` database in the same Atlas cluster** · Install path: **PWA**.

> No secrets live in the repo. Set everything below in the host dashboards. Generate fresh
> production secrets — never reuse dev values.

## Deploy ordering (resolves the URL chicken-and-egg)
1. Provision `beeworking_prod` DB + run migrations (Stage 4).
2. Deploy **backend to Render** → note its URL `https://<api>.onrender.com`.
3. Deploy **frontend to Vercel** with `VITE_API_URL` = the Render URL → note `https://<app>.vercel.app`.
4. Set the backend's `FRONTEND_URL` + `CORS_ORIGINS` to the Vercel URL and redeploy backend.
5. Add the Vercel origin as an **Authorized JavaScript origin** in Google Cloud (OAuth client).
6. Confirm **Atlas Network Access** allows Render's egress (or `0.0.0.0/0` if static IPs aren't available).

## Render — backend service env vars
| Var | Value |
|---|---|
| `MONGO_URI` | `mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority` |
| `DB_NAME` | `beeworking_prod` |
| `JWT_SECRET` | *(fresh 64-hex, generated separately — not in repo)* |
| `SECRET_KEY` | *(fresh 64-hex, generated separately — not in repo)* |
| `JWT_EXPIRY_HOURS` | `8` |
| `FRONTEND_URL` | `https://<app>.vercel.app` |
| `CORS_ORIGINS` | `https://<app>.vercel.app` (prod origin ONLY — no localhost) |
| `GOOGLE_CLIENT_ID` | the public Google OAuth client ID (matches frontend) |
| `MAIL_HOST` / `MAIL_PORT` | `smtp.gmail.com` / `587` |
| `MAIL_USER` / `MAIL_PASSWORD` | the Lyfter mailbox + app password |
| `MAIL_FROM` | `Lyfter <lyfterbadges@gmail.com>` (angle brackets required) |
| `FLASK_ENV` | `production` |
| `RATELIMIT_STORAGE_URI` | `redis://<host>:6379` if >1 worker (else omit) |

- Start command: `gunicorn run:app` · Build: `pip install -r requirements.txt` (root dir `backend/`).
- `JWT_SECRET` is required — the app refuses to boot without it.

## Vercel — frontend project env vars (build-time, `VITE_*`)
| Var | Value |
|---|---|
| `VITE_API_URL` | `https://<api>.onrender.com` (the Render backend URL) |
| `VITE_USE_MOCK` | `false` |
| `VITE_GOOGLE_CLIENT_ID` | the public Google OAuth client ID (matches backend) |
| `VITE_PUBLIC_URL` | `https://<app>.vercel.app` |

- Build: `npm run build` · Output: `dist/` · Framework preset: Vite (root dir `frontend/`).

## Production super admins (Stage 4, explicit designation only)
`santimenac23@gmail.com` and `pablofori09@gmail.com` — set via `PATCH /admin/users/<id>/super-admin`
(or a one-off designation script). The dev auto-promotion is removed; no other account is promoted.
