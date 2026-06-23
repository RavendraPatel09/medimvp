from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import socketio

from config.db import init_db
from routers import auth, listings, chats
from sockets.chat_socket import sio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

fastapi_app = FastAPI(title="MediMVP", lifespan=lifespan)

fastapi_app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

fastapi_app.include_router(auth.router, prefix="/api/auth")
fastapi_app.include_router(listings.router, prefix="/api/listings")
fastapi_app.include_router(chats.router, prefix="/api/chats")

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
