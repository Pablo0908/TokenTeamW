# TokenTeamW — Backend

Backend for **TokenTeamW**, a digital badge system for **Lyfter Fest 2026** (Costa Rica, November 2026).

Built with **Flask + MongoDB Atlas**.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Flask |
| Database | MongoDB Atlas (pymongo) |
| Auth | JWT (PyJWT) |
| Password hashing | bcrypt |
| QR generation | qrcode + Pillow |
| Real-time | Flask-SocketIO |
| CORS | Flask-CORS |

---

## Project Structure

```
TokenTeamW/
├── app.py              # Entire backend (single file)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd TokenTeamW
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority
JWT_SECRET=your_super_secret_key_at_least_32_characters_long
JWT_EXPIRES_IN=7d
PORT=5000
CLIENT_URL=http://localhost:3000
NODE_ENV=development
```

> `JWT_SECRET` must be at least 32 characters long.

### 5. Run the server

```bash
python app.py
```

The API will be available at `http://localhost:5000`.

---

## MongoDB Indexes

The following indexes are created automatically on startup:

| Collection | Field(s) | Type |
|------------|----------|------|
| `users` | `email` | unique |
| `users` | `username` | unique |
| `badges` | `token` | unique |
| `assistance` | `(users_id, badges_id)` | unique |

---

## API Reference

All endpoints are prefixed with `/api`.

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | Public | Server status |

---

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register admin user |
| POST | `/auth/register-assistant` | Public | Register assistant user |
| POST | `/auth/login` | Public | Login, returns JWT |
| GET | `/auth/me` | Token | Current user profile |

**Register / Register Assistant**
```json
{
  "username": "jdoe",
  "email": "jdoe@example.com",
  "password": "secret1234",
  "name": "John",
  "lastname": "Doe"
}
```

**Login**
```json
{
  "email": "jdoe@example.com",
  "password": "secret1234"
}
```

**Response (register / login)**
```json
{
  "token": "<jwt>",
  "user": {
    "id": "...",
    "username": "jdoe",
    "email": "jdoe@example.com",
    "name": "John",
    "lastname": "Doe",
    "rol": "admin",
    "verification": false
  }
}
```

---

### Events

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/events` | Admin | Create event |
| GET | `/events` | Public | List events (paginated) |
| GET | `/events/:id` | Public | Get event by ID |
| PUT | `/events/:id` | Admin | Update event |
| DELETE | `/events/:id` | Admin | Delete event |

**Create / Update body**
```json
{
  "name": "Lyfter Fest 2026",
  "description": "Annual company event",
  "date": "2026-11-15T09:00:00",
  "prize": "Exclusive Lyfter merch"
}
```

**List query params:** `?page=1&limit=10`

---

### Badges

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/badges` | Admin | Create badge (auto-generates token + QR) |
| GET | `/badges` | Token | List badges (paginated) |
| GET | `/badges/:id` | Token | Get badge by ID |
| GET | `/badges/event/:eventId` | Token | Badges for a specific event |
| DELETE | `/badges/:id` | Admin | Delete badge |

**Create body**
```json
{
  "event": "<event_id>",
  "name": "Opening Keynote",
  "description": "Attended the opening session",
  "image": "https://cdn.example.com/badge.png",
  "date": "2026-11-15T09:00:00"
}
```

**Response includes:**
- `token` — UUID hex used for QR redemption
- `qr` — `data:image/png;base64,...` ready to render in `<img src>`

---

### Assistance (Badge Redemption)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/assistance/redeem/:token` | Asistente | Redeem badge by QR token |
| GET | `/assistance/my-badges` | Asistente | Badges redeemed by current user |
| GET | `/assistance/event/:eventId` | Admin | All redemptions for an event |

**Redeem response `201`**
```json
{
  "assistance_id": "...",
  "badge": { "id", "name", "description", "image", "token" },
  "event": { "id", "name", "date", "prize" },
  "date": "..."
}
```

> Redeeming the same badge twice returns `409 "Ya redimiste este badge"`.

---

### Archivements

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/archivements` | Admin | Create archivement |
| GET | `/archivements` | Admin | List all (paginated) |
| GET | `/archivements/user/:userId` | Token | Archivements for a user |
| GET | `/archivements/event/:eventId` | Admin | Archivements for an event |
| DELETE | `/archivements/:id` | Admin | Delete archivement |

**Create body**
```json
{
  "events_id": "<event_id>",
  "users_id": "<user_id>",
  "date": "2026-11-15T18:00:00",
  "prize": "Golden Badge"
}
```

> Assistants can only view their own archivements.

---

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users` | Admin | List all users (paginated) |
| GET | `/users/:id` | Token | Get user by ID |
| PUT | `/users/:id` | Token | Update name, lastname, username |
| DELETE | `/users/:id` | Admin | Delete user |

> Assistants can only view and edit their own profile. `password` is never returned.

---

## Authentication

All protected endpoints require the header:

```
Authorization: Bearer <token>
```

### Roles

| Role | Access |
|------|--------|
| `admin` | Full access to all endpoints |
| `asistente` | Can redeem badges, view own profile and archivements |

---

## Real-time (Socket.io)

Connect to the server with Socket.io and join an event room to receive live redemption events.

**Join a room**
```js
socket.emit('join_event', { eventId: '<event_id>' })
```

**Listen for redemptions**
```js
socket.on('nueva_redencion', (data) => {
  // data: { badge_id, badge_name, user_id, event_id, date }
})
```

---

## Error Responses

All errors return JSON:

```json
{ "error": "Descriptive message" }
```

| Code | Meaning |
|------|---------|
| 400 | Validation error / bad input |
| 401 | Missing or invalid token |
| 403 | Insufficient role permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate email, username, or badge redemption) |
| 500 | Internal server error |

---

## Production

```bash
gunicorn -k eventlet -w 1 app:app
```

> Use `-w 1` with eventlet/gevent workers — Socket.io requires a single worker or a message queue (Redis) for multi-worker deployments.

Set `NODE_ENV=production` in `.env` to disable debug mode.
