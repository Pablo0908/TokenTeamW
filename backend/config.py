import os
from dotenv import load_dotenv

load_dotenv()


def _cors_origins():
    raw = os.getenv("CORS_ORIGINS", "")
    explicit = [o.strip() for o in raw.split(",") if o.strip()]
    if explicit:
        return explicit
    # Fall back to local Vite + whatever FRONTEND_URL points at.
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    front = os.getenv("FRONTEND_URL", "").strip()
    if front and front not in origins:
        origins.append(front)
    return origins


class Config:
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-change-me")
    SECRET_KEY = os.getenv("SECRET_KEY", JWT_SECRET)
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "8"))

    # Atlas SRV URI. Accept ATLAS_URI as an alias for the team's older .env naming.
    MONGO_URI = os.getenv("MONGO_URI") or os.getenv("ATLAS_URI")
    DB_NAME = os.getenv("DB_NAME", "beeworking")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = _cors_origins()
