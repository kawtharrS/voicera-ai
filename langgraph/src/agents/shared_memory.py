import os
import time
import uuid
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

logger = logging.getLogger(__name__)

# Constants
MEMORY_DB_NAME = "user_memory_store"
COLLECTION_NAME = "user_memories"

FACT_EXTRACTION_PROMPT = """
Analyze the following user query and extract any important personal facts, 
preferences, or context that should be remembered for future interactions.
If there are no new important facts, return "NO FACTS".

User Query: {query}

Return ONLY the extracted facts or "NO FACTS".
"""

class SharedMemoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedMemoryManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        # Path to the shared memory vector store
        # Assuming this file is in langgraph/src/agents/
        # We want to go up to langgraph/
        base_path = Path(__file__).parent.parent.parent
        memory_db_path = str(base_path / MEMORY_DB_NAME)
        
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=memory_db_path,
            embedding_function=self.embeddings
        )
        
        self.openai_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def extract_and_save(self, query: str, user_id: str) -> None:
        """Extract facts from query and save to the RAG memory store."""
        if not query or not user_id:
            return

        fact_extraction_prompt = PromptTemplate(
            template=FACT_EXTRACTION_PROMPT,
            input_variables=["query"],
        )

        chain = fact_extraction_prompt | self.openai_model | StrOutputParser()
        facts = chain.invoke({"query": query}).strip()

        if facts and facts != "NO FACTS":
            try:
                self.vectorstore.add_texts(
                    texts=[facts],
                    metadatas=[{
                        "user_id": str(user_id),
                        "timestamp": str(time.time()),
                        "original_query": query
                    }],
                    ids=[str(uuid.uuid4())]
                )
                logger.info(f"Saved memory for user {user_id}")
            except Exception as exc: 
                logger.warning("Failed to write to user memory store: %s", exc)

    def retrieve(self, user_id: str, query: str = "", k: int = 5) -> str:
        """Retrieve stored context for a user using RAG."""
        if not user_id:
            return ""

        try:
            search_query = query if query else "important facts"
            results = self.vectorstore.similarity_search(
                search_query,
                k=k,
                filter={"user_id": str(user_id)}
            )
            
            if results:
                memories = [doc.page_content for doc in results]
                # Deduplicate while preserving order
                unique_memories = list(dict.fromkeys(memories))
                return "\n".join(unique_memories)
                
            return ""

        except Exception as exc: 
            logger.warning("Error retrieving from user memory store: %s", exc)
            return ""

# Global instance
shared_memory = SharedMemoryManager()
