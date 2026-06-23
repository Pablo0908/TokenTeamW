import certifi
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException

from config import Config


# Module-level so routes can import it with: from app import limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per day", "60 per hour"],
    storage_uri="memory://",
)


class _Mongo:
    """Tiny holder so models can do `from app import mongo` then `mongo.db.users`.

    Using raw PyMongo (not flask-pymongo) keeps DB selection explicit and avoids
    compatibility surprises on bleeding-edge Python with the newest driver.
    """

    client = None
    db = None


mongo = _Mongo()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("MONGO_URI"):
        raise RuntimeError("MONGO_URI is not set. Copy .env.example to .env and fill in your Atlas URI.")

    if not app.config.get("JWT_SECRET"):
        raise RuntimeError(
            "JWT_SECRET is not set. Generate one with "
            '`python -c "import secrets; print(secrets.token_hex(32))"` and put it in .env. '
            "Refusing to start with an insecure/blank signing key."
        )

    limiter.init_app(app)

    # Mobile clients call from the browser — an explicit CORS allow-list is mandatory.
    CORS(
        app,
        resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    )

    # Connect to Atlas and fail fast — never silently fall back to a local instance.
    mongo.client = MongoClient(
        app.config["MONGO_URI"],
        serverSelectionTimeoutMS=8000,
        tlsCAFile=certifi.where(),
    )
    try:
        mongo.client.admin.command("ping")
    except Exception as exc:  # noqa: BLE001 — surface a clear, actionable message and abort startup
        raise RuntimeError(
            "Could not connect to MongoDB Atlas. Verify MONGO_URI and that this machine's IP "
            f"is in the Atlas Network Access allow-list. Original error: {exc}"
        ) from exc
    mongo.db = mongo.client[app.config["DB_NAME"]]

    # Indexes are created once at startup (not per-request).
    from app.models import user, event, badge, redemption, otp, audit, organization, membership, invite, announcement

    user.create_indexes()
    event.create_indexes()
    badge.create_indexes()
    redemption.create_indexes()
    otp.create_indexes()
    audit.create_indexes()
    organization.create_indexes()
    membership.create_indexes()
    invite.create_indexes()
    announcement.create_indexes()
    mongo.db.reset_codes.create_index("created_at", expireAfterSeconds=600)
    mongo.db.reset_codes.create_index("email", unique=True)
    mongo.db.change_pwd_codes.create_index("created_at", expireAfterSeconds=600)
    mongo.db.change_pwd_codes.create_index("user_id", unique=True)

    from app.routes.auth import auth_bp
    from app.routes.events import events_bp
    from app.routes.badges import badges_bp
    from app.routes.redemptions import redemptions_bp
    from app.routes.admin import admin_bp
    from app.routes.share import share_bp
    from app.routes.me import me_bp
    from app.routes.orgs import orgs_bp
    from app.routes.announcements import announcements_bp

    for blueprint in (auth_bp, events_bp, badges_bp, redemptions_bp, admin_bp, share_bp, me_bp, orgs_bp, announcements_bp):
        app.register_blueprint(blueprint)

    @app.route("/health")
    def health():
        # Keepalive ping target for Render's free tier.
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def handle_exception(exc):
        if isinstance(exc, HTTPException):
            return jsonify({"error": exc.description}), exc.code
        app.logger.exception("Unhandled error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500

    return app
