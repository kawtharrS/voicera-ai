import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langmem import create_memory_store_manager
from langgraph.store.memory import InMemoryStore
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
        self.memory_enabled = False
        self.memory_manager = None
        self.backend_url = os.getenv("BACKEND_URL")
        
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
            print(f"[LangMem] Save failed: {e}")

    async def retrieve(self, user_id: str, query: str = "") -> str:
        if not user_id or not self.memory_enabled or self.memory_manager is None:
            return ""

        try:
            config = RunnableConfig(configurable={"user_id": str(user_id)})
            memories = await self.memory_manager.asearch(
                query=query or "general memories",
                config=config,
            )
            
            if not memories:
                return ""
            
            memory_texts = []
            for item in memories:
                if isinstance(item, str):
                    memory_texts.append(item)
                elif hasattr(item, 'value'):
                    memory_texts.append(str(item.value))
                elif hasattr(item, 'content'):
                    memory_texts.append(str(item.content))
                else:
                    memory_texts.append(str(item))
            
            if memory_texts:
                result = "\n".join(memory_texts)
                print(f"Retrieved {len(memory_texts)} items for user {user_id}")
                return result
            
            return ""
        except Exception as e:
            print(f"[MemoryRetrieve] Failed: {e}")
            return ""

    def is_ready(self) -> bool:
        return self.memory_enabled and self.memory_manager is not None


shared_memory = SharedMemoryManager()