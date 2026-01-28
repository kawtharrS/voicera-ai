import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "voicera-langgraph")
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")

DEFAULT_MAX_TRIALS = 3
DEFAULT_STUDENT_ID = "default_student"

TTS_MODEL = "tts-1"
SPEED = 1.0
TIMEOUT = 30.0
MAX_TOKENS= 300
VOICE_MAPPING = {
    "study": "alloy",
    "work": "onyx",
    "personal": "shimmer",
    "gmail": "onyx",
    "calendar": "onyx",
}
HEADERS= {
    "Authorization": f"Bearer {Settings.OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

MODEL= "gpt-4o"
settings = Settings()
