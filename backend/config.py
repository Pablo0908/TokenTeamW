import os
from dotenv import load_dotenv

load_dotenv()


def _cors_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    explicit = [o.strip() for o in raw.split(",") if o.strip()]
    if explicit:
        return explicit
    # Fall back to local Vite + whatever FRONTEND_URL points at. 127.0.0.1 is listed
    # first (preferred over "localhost" to avoid the IPv6/::1 stall on Windows).
    origins = ["http://127.0.0.1:5173", "http://localhost:5173"]
    front = os.getenv("FRONTEND_URL", "").strip()
    if front and front not in origins:
        origins.append(front)
    return origins


class Config:
    # No insecure fallback: an unset secret would let anyone forge admin JWTs.
    # create_app() validates this and refuses to boot if it's missing.
    JWT_SECRET = os.getenv("JWT_SECRET")
    SECRET_KEY = os.getenv("SECRET_KEY") or JWT_SECRET
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

    # Atlas SRV URI. Accept ATLAS_URI as an alias for the team's older .env naming.
    MONGO_URI = os.getenv("MONGO_URI") or os.getenv("ATLAS_URI")
    DB_NAME = os.getenv("DB_NAME", "beeworking")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    CORS_ORIGINS = _cors_origins()

    # Cap request bodies to bound abuse (covers the base64 avatar/logo uploads). 3 MB.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(3 * 1024 * 1024)))

    # Rate-limit storage. Default in-memory for dev; point at Redis in production
    # (e.g. redis://host:6379) so limits hold across workers/instances.
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # Email (2FA OTP). Leave blank in .env to log codes to the console instead of emailing.
    MAIL_HOST = os.getenv("MAIL_HOST", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USER = os.getenv("MAIL_USER", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")
