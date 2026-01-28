from fastapi import APIRouter, UploadFile, File, HTTPException, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

from utils.img_txt import describe_image_bytes

router = APIRouter(prefix="/image", tags=["Image"])

@router.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    logger.info(f"Received request to describe image: {file.filename}, content_type: {file.content_type}")
    # Be lenient with content types
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Only images are supported, received {file.content_type}"
        )

    image_bytes = await file.read()
    print(f"Received image: {file.filename}, content_type: {file.content_type}, size: {len(image_bytes)} bytes")

    try:
        description = describe_image_bytes(
            image_bytes=image_bytes,
            content_type=file.content_type
        )
        print(f"Successfully described image. Description length: {len(description)}")
    except Exception as e:
        print(f"Error describing image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    return {
        "description": description
    }