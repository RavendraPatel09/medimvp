import os
import jwt
from fastapi import Depends, HTTPException, Header
from config.db import get_db

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: str = Header(...), db=Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user = await db.fetchrow("SELECT * FROM users WHERE id = $1", payload["id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(user)

def require_seller(user=Depends(get_current_user)):
    if user["role"] != "SELLER":
        raise HTTPException(status_code=403, detail="Only sellers can do this")
    return user

def require_buyer(user=Depends(get_current_user)):
    if user["role"] != "BUYER":
        raise HTTPException(status_code=403, detail="Only buyers can do this")
    return user
