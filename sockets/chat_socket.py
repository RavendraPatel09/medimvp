import socketio
import jwt
import os
from config.db import pool

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

def get_user_from_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None

@sio.event
async def connect(sid, environ, auth):
    if not auth or not auth.get("token"):
        await sio.emit("error_message", {"error": "No token provided"}, to=sid)
        return False

    user = get_user_from_token(auth["token"])
    if not user:
        await sio.emit("error_message", {"error": "Invalid token"}, to=sid)
        return False

    await sio.save_session(sid, {"user_id": user["id"], "role": user["role"]})

@sio.event
async def join_chat(sid, data):
    session = await sio.get_session(sid)
    chat_id = data.get("chat_id")
    if not chat_id:
        await sio.emit("error_message", {"error": "chat_id required"}, to=sid)
        return

    async with pool.acquire() as db:
        chat = await db.fetchrow(
            """
            SELECT c.*, ml.seller_id
            FROM chats c
            JOIN medicine_listings ml ON ml.id = c.listing_id
            WHERE c.id = $1
            """,
            chat_id
        )

    if not chat:
        await sio.emit("error_message", {"error": "Chat not found"}, to=sid)
        return

    chat = dict(chat)
    user_id = session["user_id"]

    if user_id != chat["buyer_id"] and user_id != chat["seller_id"]:
        await sio.emit("error_message", {"error": "Access denied"}, to=sid)
        return

    await sio.enter_room(sid, f"chat_{chat_id}")

@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    chat_id = data.get("chat_id")
    message_text = data.get("message_text", "").strip()

    if not chat_id or not message_text:
        await sio.emit("error_message", {"error": "chat_id and message_text are required"}, to=sid)
        return

    user_id = session["user_id"]

    async with pool.acquire() as db:
        chat = await db.fetchrow(
            """
            SELECT c.*, ml.seller_id
            FROM chats c
            JOIN medicine_listings ml ON ml.id = c.listing_id
            WHERE c.id = $1
            """,
            chat_id
        )

        if not chat:
            await sio.emit("error_message", {"error": "Chat not found"}, to=sid)
            return

        chat = dict(chat)
        if user_id != chat["buyer_id"] and user_id != chat["seller_id"]:
            await sio.emit("error_message", {"error": "Access denied"}, to=sid)
            return

        message = await db.fetchrow(
            """
            INSERT INTO messages (chat_id, sender_id, message_text)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            chat_id, user_id, message_text
        )
        sender = await db.fetchrow("SELECT name FROM users WHERE id = $1", user_id)

    payload = {**dict(message), "sender_name": sender["name"]}
    payload = {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v for k, v in payload.items()}

    await sio.emit("receive_message", payload, room=f"chat_{chat_id}")

@sio.event
async def disconnect(sid):
    pass
