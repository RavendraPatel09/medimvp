# MediMVP Backend (FastAPI + PostgreSQL)

A medicine-listing + buyer-seller chat app backend.

```
Seller uploads medicine → Buyer sees medicine → Buyer starts chat → Buyer & seller chat
```

---

## 1. Setup

### Requirements
- Python 3.10+
- PostgreSQL running locally

### Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Configure environment
```bash
cp .env.example .env
```

Fill in your values:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/medi_mvp
JWT_SECRET=replace_this_with_a_long_random_string
PORT=8000
```

### Create the database
```bash
psql -U postgres -c "CREATE DATABASE medi_mvp;"
```

Tables are created automatically when the server starts.

### Run the server
```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
PostgreSQL connected successfully
Uvicorn running on http://127.0.0.1:8000
```

---

## 2. API Reference

All responses are JSON with a `success` field.
Protected routes need: `Authorization: Bearer <token>`

### Auth

**POST `/api/auth/register`**
```json
{ "name": "Anita Kumar", "phone": "9000000002", "password": "buyer123", "role": "BUYER" }
```
`role` must be `BUYER` or `SELLER`. Returns a token + user object.

**POST `/api/auth/login`**
```json
{ "phone": "9000000002", "password": "buyer123" }
```

### Listings

**POST `/api/listings`** — seller only, `multipart/form-data`
Fields: `tablet_name`, `quantity`, `manufacturing_date`, `expiry_date`, `actual_price`, `selling_price`, `description`, `image` (file)

**GET `/api/listings`** — any logged-in user. Returns all `AVAILABLE` listings with seller info.

**GET `/api/listings/mine`** — seller only. Returns the logged-in seller's own listings.

Images are served at `http://localhost:8000/uploads/<filename>`

### Chats

**POST `/api/chats/start`** — buyer only
```json
{ "listing_id": 1 }
```

**GET `/api/chats`** — all chats the logged-in user is part of.

**GET `/api/chats/:chat_id/messages`** — full message history. Only buyer or seller of that chat can access.

### Real-time chat (Socket.IO)

Connect with the JWT token:
```js
const socket = io("http://localhost:8000", { auth: { token: jwtToken } });
```

Events:
- Emit `join_chat` with `{ chat_id }` after opening a chat screen.
- Emit `send_message` with `{ chat_id, message_text }` to send a message.
- Listen for `receive_message` to get new messages (sent to both people in the room).
- Listen for `error_message` for auth or validation errors.

---

## 3. Project Structure

```
backend/
├── main.py                  # entry point — FastAPI + Socket.IO setup
├── requirements.txt
├── .env.example
├── config/
│   └── db.py                # asyncpg connection pool + table creation
├── middleware/
│   └── auth.py              # JWT verification + role guards
├── routers/
│   ├── auth.py              # register, login
│   ├── listings.py          # create listing, browse, mine
│   └── chats.py             # start chat, list chats, messages
├── sockets/
│   └── chat_socket.py       # real-time messaging with Socket.IO
└── uploads/                 # uploaded medicine images land here
```

---

## 4. Key Decisions

- Passwords are hashed with bcrypt.
- Auth is stateless JWT — no server-side sessions.
- `chats` table has a unique constraint on `(buyer_id, listing_id)` to prevent duplicate conversations.
- Socket.IO rooms are named `chat_<id>` so messages only reach the two people in that chat.
- Tables are auto-created on startup via `asyncpg` — no migration tool needed for MVP.
- FastAPI's interactive docs are available at `http://localhost:8000/docs`.
# medimvp
