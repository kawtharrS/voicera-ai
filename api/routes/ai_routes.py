from fastapi import APIRouter
from models import StudentQuestion, AIResponse
from services.ai_service import process_question

router = APIRouter()

@router.post("/ask-anything", response_model=AIResponse)
async def ask_anything(query: StudentQuestion):
    return await process_question(query)
