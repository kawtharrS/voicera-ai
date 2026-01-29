import os
import httpx
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

load_dotenv()

class SharedMemoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedMemoryManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.backend_url = os.getenv("BACKEND_URL")

    async def extract_and_save(
        self,
        query: str,
        user_id: str,
        ai_response: str = "",
        category: str = "general",
        emotion: str = ""
    ) -> None:
        if not user_id or not query:
            return

        if not self.backend_url:
            print("Backend URL not set, skipping save")
            return

        sync_data = {
            "user_id": int(user_id) if str(user_id).isdigit() else 1,
            "user_query": query,
            "ai_query": ai_response,
            "category": category,
            "emotion": emotion
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.backend_url}/api/save-memo",
                    json=sync_data,
                    timeout=5.0
                )
            print(f"Saved interaction for user {user_id} to backend")
        except Exception as e:
            print(f"Backend save failed: {e}")

    async def retrieve(self, user_id: str) -> str:
        """Retrieve long-term memories for a user via the Go backend /api/memos endpoint."""
        if not user_id:
            return ""

        if not self.backend_url:
            print("Backend URL not set, skipping retrieval")
            return ""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.backend_url}/api/memos",
                    params={"user_id": user_id, "limit": 50},
                    timeout=5.0,
                )

            if resp.status_code != 200:
                print(f"backend memos fetch failed with status {resp.status_code}")
                return ""

            payload = resp.json()
            memos = payload.get("data") or []
            if not isinstance(memos, list) or not memos:
                return ""

            lines = []
            for memo in memos:
                user_q = memo.get("user_query") or ""
                ai_q = memo.get("ai_query") or ""
                category = memo.get("category") or ""
                emotion = memo.get("emotion") or ""
                parts = []
                if user_q:
                    parts.append(f"User: {user_q}")
                if ai_q:
                    parts.append(f"AI: {ai_q}")
                if category:
                    parts.append(f"Category: {category}")
                if emotion:
                    parts.append(f"Emotion: {emotion}")
                if parts:
                    lines.append(" | ".join(parts))

            if not lines:
                return ""

            result = "\n".join(lines)
            return result
        except Exception as e:
            print(f"backend retrieval failed: {e}")
            return ""

    def is_ready(self) -> bool:
        return self.backend_url is not None


shared_memory = SharedMemoryManager()
