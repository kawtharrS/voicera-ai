import os 
import sys 
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma 
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage 
from langchain_core.documents import Document 
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.checkpoint.memory import InMemorySaver
from .structure_output import *
from prompts.calendar import * 

load_dotenv()
checkpointer = InMemorySaver()
store = InMemoryStore(
    index = {
        "dims":1536,
        "embed":"openai:text-embedding-3-small"
    }
)
namespace = ("agent_memories")
memory_tools = [
    create_manage_memory_tool(namespace),
    create_search_memory_tool(namespace)
]
openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

class Agent():
    def __init__(self, calendar_tool):
        self.calendar_tool = calendar_tool
        embeddings = OpenAIEmbeddings(openai_api_key= os.getenv("OPENAI_API_KEY"))
        db_path = str(Path(__file__).parent.parent.parent / "vectorstore")
        self.vectorstore = Chroma(
            persist_directory = db_path,
            embedding_finction= embeddings
        )
        retriever= self.vectorstore.as_retriever(search_kwargs={"k":3})
        self.conversation_history: List[BaseMessage] = []
        self.memory_tools = memory_tools 
        self.store = store
        self.checkpointer = checkpointer

        query_category_prompt = PromptTemplate(
            template= CATEGORIZE_QUERY_PROMPT,
            input_variable=["query"]
        )
        self.categorize_query = (
            query_category_prompt 
            | openai_model.with_structured_output(CategorizeQueryOutput)
        )

        writer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", AI_RESPONSE_WRITER_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{query_information}")
            ]
        )
        self.ai_response_generator = (
            writer_prompt | 
            openai_model.with_structured_output(AIResponseOutput)
        )

        proofreader_prompt = PromptTemplate(
            template=AI_RESPONSE_PROOFREADER_PROMPT, 
            input_variables=["student_question", "ai_response"]
        )
        self.response_proofreader = (
            proofreader_prompt | 
            openai_model.with_structured_output(ProofReaderOutput)
        )
    
    