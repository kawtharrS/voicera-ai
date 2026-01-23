import os
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from prompts.memory import FACT_EXTRACTION_PROMPT
from .model import Model

load_dotenv()
model = Model()
MEMORY_DB_NAME = "user_memory_store"
COLLECTION_NAME = "user_memories"


base_path = Path(__file__).parent.parent.parent
class SharedMemoryManager:
    _instance = None

    #ensures that only one instance of the class can exist
    def __new__(cls): 
        if cls._instance is None:
            cls._instance = super(SharedMemoryManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        memory_db_path = str(base_path / MEMORY_DB_NAME)
        
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=memory_db_path,
            embedding_function=self.embeddings
        )
        
        self.openai_model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"),
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def extract_and_save(self, query: str, user_id: str) -> None:
        if not query or not user_id:
            return

        fact_extraction_prompt = PromptTemplate(
            template=FACT_EXTRACTION_PROMPT,
            input_variables=["query"],
        )

        chain = fact_extraction_prompt | self.openai_model | StrOutputParser()
        facts = chain.invoke({"query": query}).strip()

        if facts and facts != "NO FACTS":
            self.vectorstore.add_texts(
                texts=[facts],
                metadatas=[{
                    "user_id": str(user_id),
                    "timestamp": str(time.time()),                        
                    "original_query": query
                    }],
                    ids=[str(uuid.uuid4())]
                )

    def retrieve(self, user_id: str, query: str = "", k: int = 5) -> str:
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
                unique_memories = list(dict.fromkeys(memories))
                return "\n".join(unique_memories)
            return ""
        except Exception: 
            return ""

shared_memory = SharedMemoryManager()
