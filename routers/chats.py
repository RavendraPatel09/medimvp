from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from config.db import get_db
from middleware.auth import get_current_user, require_buyer

router = APIRouter()

class StartChatRequest(BaseModel):
    listing_id: int

@router.post("/start")
async def start_chat(body: StartChatRequest, db=Depends(get_db), buyer=Depends(require_buyer)):
    listing = await db.fetchrow(
        "SELECT id FROM medicine_listings WHERE id = $1", body.listing_id
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    existing = await db.fetchrow(
        "SELECT id FROM chats WHERE buyer_id = $1 AND listing_id = $2",
        buyer["id"], body.listing_id
    )
    if existing:
        return {"success": True, "chat_id": existing["id"]}

    chat = await db.fetchrow(
        "INSERT INTO chats (buyer_id, listing_id) VALUES ($1, $2) RETURNING id",
        buyer["id"], body.listing_id
    )
    return {"success": True, "chat_id": chat["id"]}

@router.get("")
async def get_my_chats(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await db.fetch(
        """
        SELECT c.*, ml.tablet_name, u.name AS buyer_name
        FROM chats c
        JOIN medicine_listings ml ON ml.id = c.listing_id
        JOIN users u ON u.id = c.buyer_id
        WHERE c.buyer_id = $1
           OR ml.seller_id = $1
        ORDER BY c.created_at DESC
        """,
        user["id"]
    )
    return {"success": True, "chats": [dict(r) for r in rows]}

@router.get("/{chat_id}/messages")
async def get_messages(chat_id: int, db=Depends(get_db), user=Depends(get_current_user)):
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
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = dict(chat)
    if user["id"] != chat["buyer_id"] and user["id"] != chat["seller_id"]:
        raise HTTPException(status_code=403, detail="You are not part of this chat")

    rows = await db.fetch(
        """
        SELECT m.*, u.name AS sender_name
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE m.chat_id = $1
        ORDER BY m.created_at ASC
        """,
        chat_id
    )
    return {"success": True, "messages": [dict(r) for r in rows]}
