# Production Deployment — env & config reference

Backend: **Render** (gunicorn, always-on, HTTPS) · Frontend: **Vercel** (Vue PWA static) ·
DB: **`beeworking` — the dev database is reused for production** (decision 2026-06-26;
no separate prod DB) · Install path: **PWA**.

> Because prod shares the dev DB, the go-live hardening below is **mandatory** and must run
> as the LAST step before launch (see "Go-live hardening").

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
| `DB_NAME` | `beeworking` (dev DB reused for prod) |
| `JWT_SECRET` | *(fresh 64-hex, generated separately — not in repo)* |
| `SECRET_KEY` | *(fresh 64-hex, generated separately — not in repo)* |
| `JWT_EXPIRY_HOURS` | `8` |
| `FRONTEND_URL` | `https://<app>.vercel.app` |
| `CORS_ORIGINS` | `https://<app>.vercel.app` (prod origin ONLY — no localhost) |
| `GOOGLE_CLIENT_ID` | *(OPTIONAL)* public Google OAuth client ID — omit to ship without Google sign-in |
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
| `VITE_GOOGLE_CLIENT_ID` | *(OPTIONAL)* matches backend `GOOGLE_CLIENT_ID`; omit to hide the Google button |
| `VITE_PUBLIC_URL` | `https://<app>.vercel.app` |

- Build: `npm run build` · Output: `dist/` · Framework preset: Vite (root dir `frontend/`).

## Google Sign-In is OPTIONAL
Email/password + 2FA is the primary auth and works fully on its own. If `GOOGLE_CLIENT_ID`
(backend) / `VITE_GOOGLE_CLIENT_ID` (frontend) are left unset, the "or / Continue with
Google" block is hidden entirely (no dead button) and `/auth/google` returns 503. Add the
two vars later — no redeploy of the rest is needed beyond rebuilding the frontend — once a
(free) Google OAuth client is set up and the prod origin is an Authorized JavaScript origin.

## Production super admins (Stage 4, explicit designation only)
`santimenac23@gmail.com` and `pablofori09@gmail.com`. The dev auto-promotion is removed; no
other account is promoted.

## Go-live hardening (MANDATORY — prod reuses the dev DB)
Run these as the LAST step before launch, once testing on the shared DB has stopped:
1. **Super admins** → exactly the two owners:
   `python designate_prod_superadmins.py` (dry-run) then `--apply`.
   Demotes the 3 dev super admins (admin@lyfter.cc, valerodnav29@gmail.com, saencopra@gmail.com).
2. **Test data cleanup** — remove leftover test content, e.g. the orphan event
   `Lyfter i18n Test` (+ its 2 badges / 2 scans, all missing org_id) and any other dev fixtures.
3. **Re-run the Stage 4 audit** to confirm: exactly 2 super admins, 0 records missing org_id.
4. (Optional) reset/rotate the seed `admin@lyfter.cc` password or remove the account.
