import os
import sys
from pathlib import Path
from typing import List, Optional  
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document 
from langgraph.src.agents.model import Model
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from .structure_output import *
from ..shared_memory import shared_memory
from prompts.classroom import *

load_dotenv()

model = Model()


class Agent():
    def __init__(self, classroom_tool=None): 
        self.classroom_tool = classroom_tool
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        db_path = str(Path(__file__).parent.parent.parent / "vectorstore")

        self.vectorstore = Chroma(
            persist_directory=db_path, 
            embedding_function=embeddings
        )
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

        self.conversation_history: List[BaseMessage] = []

        query_category_prompt = PromptTemplate(
            template=CATEGORIZE_QUERY_PROMPT, 
            input_variables=["query"]
        )

        self.categorize_query = (
            query_category_prompt | 
            model.openai_model.with_structured_output(CategorizeQueryOutput)
        )

        generate_rag_prompt = PromptTemplate(
            template=GENERATE_RAG_QUERIES_PROMPT, 
            input_variables=["query"]
        )

        self.design_rag_queries = (
            generate_rag_prompt | 
            model.openai_model.with_structured_output(RAGQueriesOutput)
        )

        qa_prompt = ChatPromptTemplate.from_template(GENERATE_RAG_ANSWER_PROMPT)

        self.generate_rag_answer = (
            {"context": retriever, "question": RunnablePassthrough()} 
            | qa_prompt
            | model.openai_model
            | StrOutputParser()  

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
            model.openai_model.with_structured_output(AIResponseOutput)
        )

        proofreader_prompt = PromptTemplate(
            template=AI_RESPONSE_PROOFREADER_PROMPT, 
            input_variables=["student_question", "ai_response"]
        )
        self.response_proofreader = (
            proofreader_prompt | 
            model.openai_model.with_structured_output(ProofReaderOutput)
        )
    
    def extract_and_save_to_langmem(self, query: str, student_id: str) -> None:
        shared_memory.extract_and_save(query, student_id)

    def retrieve_from_langmem(self, student_id: str, query: str = "") -> str:
        return shared_memory.retrieve(student_id, query)
        
    def add_to_history(self, role: str, content: str) -> None:
        if role == "user":
            self.conversation_history.append(HumanMessage(content=content))
        elif role == "assistant":
            self.conversation_history.append(AIMessage(content=content))

    def get_history(self, k: int = 5) -> List[BaseMessage]:
        return self.conversation_history[-k:]
    
    def clear_history(self) -> None:
        self.conversation_history = []
