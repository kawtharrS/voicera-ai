from fastapi import APIRouter, UploadFile, File, HTTPException, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from services.img_txt_service import describe_image_bytes

router = APIRouter(prefix="/image", tags=["Image"])

@router.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Only images are supported, received {file.content_type}"
        )

    image_bytes = await file.read()

    try:
        description = describe_image_bytes(
            image_bytes=image_bytes,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    return {
        "description": description
    }