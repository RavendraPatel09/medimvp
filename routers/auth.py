from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from config.db import get_db

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    role: str

class LoginRequest(BaseModel):
    phone: str
    password: str

def make_token(user_id: int, role: str):
    payload = {
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.post("/register")
async def register(body: RegisterRequest, db=Depends(get_db)):
    if body.role not in ("BUYER", "SELLER"):
        raise HTTPException(status_code=400, detail="role must be BUYER or SELLER")

    existing = await db.fetchrow("SELECT id FROM users WHERE phone = $1", body.phone)
    if existing:
        raise HTTPException(status_code=409, detail="Phone already registered")

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = await db.fetchrow(
        "INSERT INTO users (name, phone, password, role) VALUES ($1, $2, $3, $4) RETURNING id, name, phone, role",
        body.name, body.phone, hashed, body.role
    )
    user = dict(user)
    token = make_token(user["id"], user["role"])
    return {"success": True, "token": token, "user": user}

@router.post("/login")
async def login(body: LoginRequest, db=Depends(get_db)):
    user = await db.fetchrow("SELECT * FROM users WHERE phone = $1", body.phone)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    user = dict(user)
    if not bcrypt.checkpw(body.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = make_token(user["id"], user["role"])
    user.pop("password")
    return {"success": True, "token": token, "user": user}
