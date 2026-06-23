from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
import shutil
import uuid
import os
from config.db import get_db
from middleware.auth import get_current_user, require_seller

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def create_listing(
    tablet_name: str = Form(...),
    quantity: int = Form(...),
    manufacturing_date: str = Form(...),
    expiry_date: str = Form(...),
    actual_price: float = Form(...),
    selling_price: float = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    db=Depends(get_db),
    seller=Depends(require_seller)
):
    ext = image.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(image.file, f)

    listing = await db.fetchrow(
        """
        INSERT INTO medicine_listings
        (seller_id, tablet_name, quantity, manufacturing_date, expiry_date, actual_price, selling_price, description, image_filename)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
        """,
        seller["id"], tablet_name, quantity, manufacturing_date, expiry_date,
        actual_price, selling_price, description, filename
    )
    return {"success": True, "listing": dict(listing)}

@router.get("")
async def get_all_listings(db=Depends(get_db), user=Depends(get_current_user)):
    rows = await db.fetch(
        """
        SELECT ml.*, u.name AS seller_name, u.phone AS seller_phone
        FROM medicine_listings ml
        JOIN users u ON u.id = ml.seller_id
        WHERE ml.status = 'AVAILABLE'
        ORDER BY ml.created_at DESC
        """
    )
    return {"success": True, "listings": [dict(r) for r in rows]}

@router.get("/mine")
async def get_my_listings(db=Depends(get_db), seller=Depends(require_seller)):
    rows = await db.fetch(
        "SELECT * FROM medicine_listings WHERE seller_id = $1 ORDER BY created_at DESC",
        seller["id"]
    )
    return {"success": True, "listings": [dict(r) for r in rows]}
