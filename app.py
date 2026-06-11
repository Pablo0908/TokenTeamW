import os
import re
import io
import base64
import uuid
import qrcode
import bcrypt
import jwt

from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "changeme_at_least_32_chars_long!!")

JWT_SECRET = app.config["SECRET_KEY"]

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            os.getenv("CLIENT_URL", "*"),
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.get_database("tokenteamw")

users_col       = db["users"]
badges_col      = db["badges"]
events_col      = db["events"]
archivements_col = db["archivements"]
assistance_col  = db["assistance"]

def _create_indexes():
    users_col.create_index("email", unique=True)
    users_col.create_index("username", unique=True)
    badges_col.create_index("token", unique=True)
    assistance_col.create_index(
        [("users_id", ASCENDING), ("badges_id", ASCENDING)],
        unique=True,
    )

_create_indexes()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def success(data, status=200):
    return jsonify(data), status


def error(message, status=400, **kwargs):
    resp = {"error": message}
    resp.update(kwargs)
    return jsonify(resp), status


def valid_oid(oid):
    try:
        ObjectId(oid)
        return True
    except Exception:
        return False


def serialize(doc):
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    for k, v in list(doc.items()):
        if v.__class__.__name__ == "ObjectId":
            doc[k] = str(v)
        elif isinstance(v, list):
            doc[k] = [
                str(i) if i.__class__.__name__ == "ObjectId" else i
                for i in v
            ]
    return doc


def generar_token(user_id, email, rol, username):
    payload = {
        "userId":   str(user_id),
        "email":    email,
        "rol":      rol,
        "username": username,
        "exp":      datetime.utcnow() + timedelta(days=7),
        "iat":      datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decodificar_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def generar_qr(token_value):
    qr_img = qrcode.make(token_value)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def user_safe(doc):
    """Return serialized user without password field."""
    if doc is None:
        return None
    s = serialize(doc)
    s.pop("password", None)
    return s


def paginate_params():
    try:
        page  = max(1, int(request.args.get("page", 1)))
        limit = max(1, min(100, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        page, limit = 1, 10
    return page, limit

# ---------------------------------------------------------------------------
# Auth decorators
# ---------------------------------------------------------------------------

def verificar_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error("Token requerido", 401)
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decodificar_token(token)
        except jwt.ExpiredSignatureError:
            return error("Token inválido o expirado", 401)
        except jwt.PyJWTError:
            return error("Token inválido o expirado", 401)
        g.user = {
            "id":       payload["userId"],
            "email":    payload["email"],
            "rol":      payload["rol"],
            "username": payload["username"],
        }
        return f(*args, **kwargs)
    return wrapper


def requerir_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if g.user.get("rol") not in roles:
                return error("No tienes permisos para esta acción", 403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    return success({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

def _register(rol):
    body = request.get_json(silent=True) or {}

    username = (body.get("username") or "").strip()
    email    = (body.get("email")    or "").strip().lower()
    password = (body.get("password") or "")
    name     = (body.get("name")     or "").strip()
    lastname = (body.get("lastname") or "").strip()

    if not username:
        return error("El campo username es requerido", 400, field="username")
    if not email:
        return error("El campo email es requerido", 400, field="email")
    if not EMAIL_RE.match(email):
        return error("Formato de email inválido", 400, field="email")
    if not password:
        return error("El campo password es requerido", 400, field="password")
    if len(password) < 8:
        return error("La contraseña debe tener al menos 8 caracteres", 400, field="password")
    if not name:
        return error("El campo name es requerido", 400, field="name")
    if not lastname:
        return error("El campo lastname es requerido", 400, field="lastname")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    now = datetime.utcnow()

    doc = {
        "username":     username,
        "password":     hashed.decode(),
        "email":        email,
        "rol":          rol,
        "verification": False,
        "name":         name,
        "lastname":     lastname,
        "created_at":   now,
        "updated_at":   now,
    }

    try:
        result = users_col.insert_one(doc)
    except DuplicateKeyError as exc:
        err_str = str(exc)
        if "email" in err_str:
            return error("El email ya está registrado", 409)
        return error("El username ya está en uso", 409)

    user = users_col.find_one({"_id": result.inserted_id})
    token = generar_token(user["_id"], user["email"], user["rol"], user["username"])

    return success({
        "token": token,
        "user":  user_safe(user),
    }, 201)


@app.route("/api/auth/register", methods=["POST"])
def register():
    return _register("admin")


@app.route("/api/auth/register-assistant", methods=["POST"])
def register_assistant():
    return _register("asistente")


@app.route("/api/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email    = (body.get("email")    or "").strip().lower()
    password = (body.get("password") or "")

    if not email or not password:
        return error("Credenciales inválidas", 401)

    user = users_col.find_one({"email": email})
    if not user:
        return error("Credenciales inválidas", 401)

    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return error("Credenciales inválidas", 401)

    token = generar_token(user["_id"], user["email"], user["rol"], user["username"])
    return success({"token": token, "user": user_safe(user)})


@app.route("/api/auth/me")
@verificar_token
def me():
    user = users_col.find_one({"_id": ObjectId(g.user["id"])})
    if not user:
        return error("Usuario no encontrado", 404)
    return success(user_safe(user))

# ---------------------------------------------------------------------------
# EVENTS
# ---------------------------------------------------------------------------

@app.route("/api/events", methods=["POST"])
@verificar_token
@requerir_rol("admin")
def create_event():
    body = request.get_json(silent=True) or {}

    name        = (body.get("name")        or "").strip()
    description = (body.get("description") or "").strip()
    date_str    = body.get("date")
    prize       = (body.get("prize")       or "").strip()

    if not name:
        return error("El campo name es requerido", 400, field="name")
    if not date_str:
        return error("El campo date es requerido", 400, field="date")

    try:
        date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        date = date.replace(tzinfo=None)
    except (ValueError, TypeError):
        return error("Formato de fecha inválido", 400, field="date")

    if date <= datetime.utcnow():
        return error("La fecha debe ser futura", 400, field="date")

    now = datetime.utcnow()
    doc = {
        "name":        name,
        "description": description,
        "date":        date,
        "prize":       prize,
        "badges_id":   [],
        "created_at":  now,
        "updated_at":  now,
    }
    result = events_col.insert_one(doc)
    event = events_col.find_one({"_id": result.inserted_id})
    return success(serialize(event), 201)


@app.route("/api/events")
def list_events():
    page, limit = paginate_params()
    skip  = (page - 1) * limit
    total = events_col.count_documents({})

    pipeline = [
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from":         "badges",
                "localField":   "badges_id",
                "foreignField": "_id",
                "as":           "badges_id",
            }
        },
    ]
    docs = list(events_col.aggregate(pipeline))

    def serialize_event(doc):
        s = serialize(doc)
        s["badges_id"] = [serialize(b) for b in doc.get("badges_id", [])]
        return s

    return success({
        "data":  [serialize_event(d) for d in docs],
        "page":  page,
        "total": total,
        "pages": -(-total // limit),
    })


@app.route("/api/events/<event_id>")
def get_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    pipeline = [
        {"$match": {"_id": ObjectId(event_id)}},
        {
            "$lookup": {
                "from":         "badges",
                "localField":   "badges_id",
                "foreignField": "_id",
                "as":           "badges_id",
            }
        },
    ]
    docs = list(events_col.aggregate(pipeline))
    if not docs:
        return error("Evento no encontrado", 404)

    doc = docs[0]
    s = serialize(doc)
    s["badges_id"] = [serialize(b) for b in doc.get("badges_id", [])]
    return success(s)


@app.route("/api/events/<event_id>", methods=["PUT"])
@verificar_token
@requerir_rol("admin")
def update_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    body = request.get_json(silent=True) or {}
    update = {}

    if "name" in body:
        update["name"] = (body["name"] or "").strip()
    if "description" in body:
        update["description"] = body["description"]
    if "prize" in body:
        update["prize"] = body["prize"]
    if "date" in body:
        try:
            date = datetime.fromisoformat(str(body["date"]).replace("Z", "+00:00"))
            update["date"] = date.replace(tzinfo=None)
        except (ValueError, TypeError):
            return error("Formato de fecha inválido", 400, field="date")

    update["updated_at"] = datetime.utcnow()

    result = events_col.find_one_and_update(
        {"_id": ObjectId(event_id)},
        {"$set": update},
        return_document=True,
    )
    if not result:
        return error("Evento no encontrado", 404)

    return success(serialize(result))


@app.route("/api/events/<event_id>", methods=["DELETE"])
@verificar_token
@requerir_rol("admin")
def delete_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    result = events_col.find_one_and_delete({"_id": ObjectId(event_id)})
    if not result:
        return error("Evento no encontrado", 404)

    return success({"message": "Evento eliminado"})

# ---------------------------------------------------------------------------
# BADGES
# ---------------------------------------------------------------------------

@app.route("/api/badges", methods=["POST"])
@verificar_token
@requerir_rol("admin")
def create_badge():
    body = request.get_json(silent=True) or {}

    event_id    = (body.get("event")       or "").strip()
    name        = (body.get("name")        or "").strip()
    description = (body.get("description") or "")
    image       = (body.get("image")       or "")
    date_str    = body.get("date")

    if not event_id:
        return error("El campo event es requerido", 400, field="event")
    if not valid_oid(event_id):
        return error("ID inválido", 400, field="event")
    if not name:
        return error("El campo name es requerido", 400, field="name")

    event = events_col.find_one({"_id": ObjectId(event_id)})
    if not event:
        return error("Evento no encontrado", 404)

    date = None
    if date_str:
        try:
            date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            date = date.replace(tzinfo=None)
        except (ValueError, TypeError):
            return error("Formato de fecha inválido", 400, field="date")

    token_value = uuid.uuid4().hex
    qr_data     = generar_qr(token_value)
    now         = datetime.utcnow()

    doc = {
        "event":       ObjectId(event_id),
        "name":        name,
        "description": description,
        "image":       image,
        "token":       token_value,
        "date":        date or now,
        "qr":          qr_data,
        "created_at":  now,
        "updated_at":  now,
    }

    result = badges_col.insert_one(doc)

    events_col.update_one(
        {"_id": ObjectId(event_id)},
        {"$push": {"badges_id": result.inserted_id}},
    )

    badge = badges_col.find_one({"_id": result.inserted_id})
    return success(serialize(badge), 201)


@app.route("/api/badges")
@verificar_token
def list_badges():
    page, limit = paginate_params()
    skip  = (page - 1) * limit
    total = badges_col.count_documents({})

    pipeline = [
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from":         "events",
                "localField":   "event",
                "foreignField": "_id",
                "as":           "event_data",
            }
        },
        {"$addFields": {"event_data": {"$arrayElemAt": ["$event_data", 0]}}},
    ]
    docs = list(badges_col.aggregate(pipeline))

    def serialize_badge(doc):
        s = serialize(doc)
        ed = doc.get("event_data")
        s["event_data"] = serialize(ed) if ed else None
        return s

    return success({
        "data":  [serialize_badge(d) for d in docs],
        "page":  page,
        "total": total,
        "pages": -(-total // limit),
    })


@app.route("/api/badges/<badge_id>")
@verificar_token
def get_badge(badge_id):
    if not valid_oid(badge_id):
        return error("ID inválido", 400)

    pipeline = [
        {"$match": {"_id": ObjectId(badge_id)}},
        {
            "$lookup": {
                "from":         "events",
                "localField":   "event",
                "foreignField": "_id",
                "as":           "event_data",
            }
        },
        {"$addFields": {"event_data": {"$arrayElemAt": ["$event_data", 0]}}},
    ]
    docs = list(badges_col.aggregate(pipeline))
    if not docs:
        return error("Badge no encontrado", 404)

    doc = docs[0]
    s = serialize(doc)
    s["event_data"] = serialize(doc.get("event_data"))
    return success(s)


@app.route("/api/badges/event/<event_id>")
@verificar_token
def badges_by_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    if not events_col.find_one({"_id": ObjectId(event_id)}):
        return error("Evento no encontrado", 404)

    docs = list(badges_col.find({"event": ObjectId(event_id)}))
    return success([serialize(d) for d in docs])


@app.route("/api/badges/<badge_id>", methods=["DELETE"])
@verificar_token
@requerir_rol("admin")
def delete_badge(badge_id):
    if not valid_oid(badge_id):
        return error("ID inválido", 400)

    badge = badges_col.find_one_and_delete({"_id": ObjectId(badge_id)})
    if not badge:
        return error("Badge no encontrado", 404)

    events_col.update_one(
        {"_id": badge["event"]},
        {"$pull": {"badges_id": badge["_id"]}},
    )
    return success({"message": "Badge eliminado"})

# ---------------------------------------------------------------------------
# ASSISTANCE
# ---------------------------------------------------------------------------

@app.route("/api/assistance/redeem/<token_value>", methods=["POST"])
@verificar_token
@requerir_rol("asistente")
def redeem_badge(token_value):
    badge = badges_col.find_one({"token": token_value})
    if not badge:
        return error("Badge no encontrado", 404)

    event = events_col.find_one({"_id": badge["event"]})
    if not event:
        return error("Evento no encontrado", 404)

    existing = assistance_col.find_one({
        "users_id":  ObjectId(g.user["id"]),
        "badges_id": badge["_id"],
    })
    if existing:
        return error("Ya redimiste este badge", 409)

    now = datetime.utcnow()
    doc = {
        "users_id":   ObjectId(g.user["id"]),
        "badges_id":  badge["_id"],
        "events_id":  badge["event"],
        "created_at": now,
        "updated_at": now,
    }
    result = assistance_col.insert_one(doc)

    socketio.emit("nueva_redencion", {
        "badge_id":   str(badge["_id"]),
        "badge_name": badge["name"],
        "user_id":    g.user["id"],
        "event_id":   str(badge["event"]),
        "date":       str(now),
    }, room=str(badge["event"]))

    return success({
        "assistance_id": str(result.inserted_id),
        "badge": {
            "id":          str(badge["_id"]),
            "name":        badge["name"],
            "description": badge.get("description"),
            "image":       badge.get("image"),
            "token":       badge["token"],
        },
        "event": {
            "id":    str(event["_id"]),
            "name":  event["name"],
            "date":  str(event.get("date")),
            "prize": event.get("prize"),
        },
        "date": str(now),
    }, 201)


@app.route("/api/assistance/my-badges")
@verificar_token
@requerir_rol("asistente")
def my_badges():
    pipeline = [
        {"$match": {"users_id": ObjectId(g.user["id"])}},
        {"$sort":  {"created_at": -1}},
        {
            "$lookup": {
                "from":         "badges",
                "localField":   "badges_id",
                "foreignField": "_id",
                "as":           "badge",
            }
        },
        {"$addFields": {"badge": {"$arrayElemAt": ["$badge", 0]}}},
        {
            "$lookup": {
                "from":         "events",
                "localField":   "events_id",
                "foreignField": "_id",
                "as":           "event",
            }
        },
        {"$addFields": {"event": {"$arrayElemAt": ["$event", 0]}}},
    ]
    docs = list(assistance_col.aggregate(pipeline))

    def serialize_a(doc):
        s = serialize(doc)
        s["badge"] = serialize(doc.get("badge"))
        s["event"] = serialize(doc.get("event"))
        return s

    return success([serialize_a(d) for d in docs])


@app.route("/api/assistance/event/<event_id>")
@verificar_token
@requerir_rol("admin")
def assistance_by_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    pipeline = [
        {"$match": {"events_id": ObjectId(event_id)}},
        {
            "$lookup": {
                "from":         "users",
                "localField":   "users_id",
                "foreignField": "_id",
                "as":           "user",
            }
        },
        {"$addFields": {"user": {"$arrayElemAt": ["$user", 0]}}},
        {
            "$lookup": {
                "from":         "badges",
                "localField":   "badges_id",
                "foreignField": "_id",
                "as":           "badge",
            }
        },
        {"$addFields": {"badge": {"$arrayElemAt": ["$badge", 0]}}},
    ]
    docs = list(assistance_col.aggregate(pipeline))

    def serialize_a(doc):
        s = serialize(doc)
        u = doc.get("user")
        if u:
            u_s = serialize(u)
            u_s.pop("password", None)
            s["user"] = u_s
        else:
            s["user"] = None
        s["badge"] = serialize(doc.get("badge"))
        return s

    return success([serialize_a(d) for d in docs])

# ---------------------------------------------------------------------------
# ARCHIVEMENTS
# ---------------------------------------------------------------------------

@app.route("/api/archivements", methods=["POST"])
@verificar_token
@requerir_rol("admin")
def create_archivement():
    body = request.get_json(silent=True) or {}

    events_id = (body.get("events_id") or "").strip()
    users_id  = (body.get("users_id")  or "").strip()
    date_str  = body.get("date")
    prize     = body.get("prize", "")

    if not events_id:
        return error("El campo events_id es requerido", 400, field="events_id")
    if not valid_oid(events_id):
        return error("ID inválido", 400, field="events_id")
    if not users_id:
        return error("El campo users_id es requerido", 400, field="users_id")
    if not valid_oid(users_id):
        return error("ID inválido", 400, field="users_id")

    if not events_col.find_one({"_id": ObjectId(events_id)}):
        return error("Evento no encontrado", 404)
    if not users_col.find_one({"_id": ObjectId(users_id)}):
        return error("Usuario no encontrado", 404)

    date = None
    if date_str:
        try:
            date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            date = date.replace(tzinfo=None)
        except (ValueError, TypeError):
            return error("Formato de fecha inválido", 400, field="date")

    now = datetime.utcnow()
    doc = {
        "events_id":  ObjectId(events_id),
        "users_id":   ObjectId(users_id),
        "date":       date or now,
        "prize":      prize,
        "created_at": now,
        "updated_at": now,
    }
    result = archivements_col.insert_one(doc)
    archivement = archivements_col.find_one({"_id": result.inserted_id})
    return success(serialize(archivement), 201)


@app.route("/api/archivements")
@verificar_token
@requerir_rol("admin")
def list_archivements():
    page, limit = paginate_params()
    skip  = (page - 1) * limit
    total = archivements_col.count_documents({})

    pipeline = [
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from":         "events",
                "localField":   "events_id",
                "foreignField": "_id",
                "as":           "event",
            }
        },
        {"$addFields": {"event": {"$arrayElemAt": ["$event", 0]}}},
        {
            "$lookup": {
                "from":         "users",
                "localField":   "users_id",
                "foreignField": "_id",
                "as":           "user",
            }
        },
        {"$addFields": {"user": {"$arrayElemAt": ["$user", 0]}}},
    ]
    docs = list(archivements_col.aggregate(pipeline))

    def serialize_arch(doc):
        s = serialize(doc)
        s["event"] = serialize(doc.get("event"))
        u = doc.get("user")
        if u:
            u_s = serialize(u)
            u_s.pop("password", None)
            s["user"] = u_s
        else:
            s["user"] = None
        return s

    return success({
        "data":  [serialize_arch(d) for d in docs],
        "page":  page,
        "total": total,
        "pages": -(-total // limit),
    })


@app.route("/api/archivements/user/<user_id>")
@verificar_token
def archivements_by_user(user_id):
    if not valid_oid(user_id):
        return error("ID inválido", 400)

    if g.user["rol"] == "asistente" and g.user["id"] != user_id:
        return error("No tienes permisos para esta acción", 403)

    if not users_col.find_one({"_id": ObjectId(user_id)}):
        return error("Usuario no encontrado", 404)

    docs = list(archivements_col.find({"users_id": ObjectId(user_id)}))
    return success([serialize(d) for d in docs])


@app.route("/api/archivements/event/<event_id>")
@verificar_token
@requerir_rol("admin")
def archivements_by_event(event_id):
    if not valid_oid(event_id):
        return error("ID inválido", 400)

    docs = list(archivements_col.find({"events_id": ObjectId(event_id)}))
    return success([serialize(d) for d in docs])


@app.route("/api/archivements/<arch_id>", methods=["DELETE"])
@verificar_token
@requerir_rol("admin")
def delete_archivement(arch_id):
    if not valid_oid(arch_id):
        return error("ID inválido", 400)

    result = archivements_col.find_one_and_delete({"_id": ObjectId(arch_id)})
    if not result:
        return error("Archivement no encontrado", 404)

    return success({"message": "Archivement eliminado"})

# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

@app.route("/api/users")
@verificar_token
@requerir_rol("admin")
def list_users():
    page, limit = paginate_params()
    skip  = (page - 1) * limit
    total = users_col.count_documents({})

    docs = list(users_col.find({}, {"password": 0}).skip(skip).limit(limit))
    return success({
        "data":  [serialize(d) for d in docs],
        "page":  page,
        "total": total,
        "pages": -(-total // limit),
    })


@app.route("/api/users/<user_id>")
@verificar_token
def get_user(user_id):
    if not valid_oid(user_id):
        return error("ID inválido", 400)

    if g.user["rol"] == "asistente" and g.user["id"] != user_id:
        return error("No tienes permisos para esta acción", 403)

    user = users_col.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return error("Usuario no encontrado", 404)

    return success(serialize(user))


@app.route("/api/users/<user_id>", methods=["PUT"])
@verificar_token
def update_user(user_id):
    if not valid_oid(user_id):
        return error("ID inválido", 400)

    if g.user["rol"] == "asistente" and g.user["id"] != user_id:
        return error("No tienes permisos para esta acción", 403)

    if not users_col.find_one({"_id": ObjectId(user_id)}):
        return error("Usuario no encontrado", 404)

    body = request.get_json(silent=True) or {}
    allowed = {"name", "lastname", "username"}
    update = {k: v for k, v in body.items() if k in allowed and v is not None}
    update["updated_at"] = datetime.utcnow()

    result = users_col.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update},
        return_document=True,
        projection={"password": 0},
    )
    return success(serialize(result))


@app.route("/api/users/<user_id>", methods=["DELETE"])
@verificar_token
@requerir_rol("admin")
def delete_user(user_id):
    if not valid_oid(user_id):
        return error("ID inválido", 400)

    result = users_col.find_one_and_delete({"_id": ObjectId(user_id)})
    if not result:
        return error("Usuario no encontrado", 404)

    return success({"message": "Usuario eliminado"})

# ---------------------------------------------------------------------------
# Socket.io
# ---------------------------------------------------------------------------

@socketio.on("join_event")
def on_join(data):
    event_id = (data or {}).get("eventId")
    if event_id:
        join_room(event_id)


@socketio.on("disconnect")
def on_disconnect():
    pass

# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return error("Ruta no encontrada", 404)


@app.errorhandler(405)
def method_not_allowed(_):
    return error("Método no permitido", 405)


@app.errorhandler(Exception)
def internal_error(exc):
    app.logger.exception("Error interno: %s", exc)
    return error("Error interno del servidor", 500)

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("NODE_ENV") != "production"
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
