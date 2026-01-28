import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agents.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig

try:
    from langmem import create_memory_store_manager  # type: ignore
except ImportError:  # langmem is optional (and requires Python >=3.11)
    create_memory_store_manager = None  # type: ignore

load_dotenv()

class SharedMemoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedMemoryManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.memory_enabled = False
        self.memory_manager = None
        self.backend_url = os.getenv("BACKEND_URL")

        # langmem is optional and currently only supports Python >= 3.11.
        # On environments where it's not installed, we gracefully disable memory.
        if create_memory_store_manager is None:
            return

        try:
            openai_model = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL"),
                temperature=0,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )

            store = InMemoryStore(
                index={
                    "dims": 1536,
                    "embed": "openai:text-embedding-3-small",
                }
            )

            self.memory_manager = create_memory_store_manager(
                openai_model,
                namespace=("memories", "{user_id}"),
                store=store,
            )

            self.memory_enabled = self.memory_manager is not None

        except Exception as e:
            self.memory_manager = None
            self.memory_enabled = False

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

        sync_data = {
            "user_id": int(user_id) if str(user_id).isdigit() else 1,
            "user_query": query,
            "ai_query": ai_response,
            "category": category,
            "emotion": emotion
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.backend_url}/api/save-memo",
                json=sync_data,
                timeout=5.0
            )

        if not self.memory_enabled or self.memory_manager is None:
            return

        try:
            messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": ai_response}
            ]
            config = RunnableConfig(configurable={"user_id": str(user_id)})
            
            await self.memory_manager.ainvoke(
                {"messages": messages},
                config=config,
            )
            print(f"Saved interaction for user {user_id}")
        except Exception as e:
            print(f"Save failed: {e}")

    async def retrieve(self, user_id: str, query: str = "") -> str:
        """Retrieve long-term memories for a user.

        Preference order:
        1. langmem vector store (if available)
        2. Supabase-backed memos via the Go backend /api/memos endpoint
        """
        if not user_id:
            return ""

        # First try langmem vector store if configured
        if self.memory_enabled and self.memory_manager is not None:
            try:
                config = RunnableConfig(configurable={"user_id": str(user_id)})
                memories = await self.memory_manager.asearch(
                    query=query or "general memories",
                    config=config,
                )

                if memories:
                    memory_texts = []
                    for item in memories:
                        if isinstance(item, str):
                            memory_texts.append(item)
                        elif hasattr(item, "value"):
                            memory_texts.append(str(item.value))
                        elif hasattr(item, "content"):
                            memory_texts.append(str(item.content))
                        else:
                            memory_texts.append(str(item))

                    if memory_texts:
                        result = "\n".join(memory_texts)
                        print(f"Retrieved {len(memory_texts)} items for user {user_id} from langmem")
                        return result
            except Exception as e:
                print(f"[Memory] langmem retrieval failed: {e}")

        # Fallback: fetch recent memos from backend (Supabase)
        if not self.backend_url:
            return ""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.backend_url}/api/memos",
                    params={"user_id": user_id, "limit": 50},
                    timeout=5.0,
                )

            if resp.status_code != 200:
                print(f"[Memory] backend memos fetch failed with status {resp.status_code}")
                return ""

            payload = resp.json()
            memos = payload.get("data") or []
            if not isinstance(memos, list) or not memos:
                return ""

            # Each memo has user_query, ai_query, category, emotion
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
            print(f"[Memory] Retrieved {len(lines)} memos for user {user_id} from backend")
            return result
        except Exception as e:
            print(f"[Memory] backend retrieval failed: {e}")
            return ""

    def is_ready(self) -> bool:
        return self.memory_enabled and self.memory_manager is not None


shared_memory = SharedMemoryManager()