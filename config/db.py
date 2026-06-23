import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))
    await create_tables()
    print("PostgreSQL connected successfully")

async def get_db():
    async with pool.acquire() as conn:
        yield conn

async def create_tables():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('BUYER', 'SELLER')),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS medicine_listings (
                id SERIAL PRIMARY KEY,
                seller_id INTEGER REFERENCES users(id),
                tablet_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                manufacturing_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                actual_price NUMERIC(10,2) NOT NULL,
                selling_price NUMERIC(10,2) NOT NULL,
                description TEXT,
                image_filename TEXT,
                status TEXT DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'SOLD')),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id SERIAL PRIMARY KEY,
                buyer_id INTEGER REFERENCES users(id),
                listing_id INTEGER REFERENCES medicine_listings(id),
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (buyer_id, listing_id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                chat_id INTEGER REFERENCES chats(id),
                sender_id INTEGER REFERENCES users(id),
                message_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
