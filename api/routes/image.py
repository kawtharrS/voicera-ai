from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.img_txt import describe_image_bytes

router = APIRouter(prefix="/image", tags=["Image"])

@router.post("/describe")
async def describe_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(
            status_code=400,
            detail="Only PNG and JPEG images are supported"
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