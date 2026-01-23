import os 
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma 
from langchain_core.messages import BaseMessage
from langgraph.store.memory import InMemoryStore
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.checkpoint.memory import InMemorySaver
from ..structure_outputs.gmail_structure_output import *
from prompts.gmail import *
from langgraph.src.agents.model import Model
from ...shared_memory import shared_memory

load_dotenv()

checkpointer = InMemorySaver()
store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": "openai:text-embedding-3-small"
    }
)
namespace = ("gmail_agent_memories")
memory_tools = [
    create_manage_memory_tool(namespace),
    create_search_memory_tool(namespace)
]

model = Model()


class GmailAgent():
    def __init__(self, gmail_tool=None):
        self.gmail_tool = gmail_tool
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vectorstore = shared_memory.vectorstore
        self.conversation_history: List[BaseMessage] = []
        self.memory_tools = memory_tools
        self.store = store
        self.checkpointer = checkpointer

        categorize_email_prompt = PromptTemplate(
            template=CATEGORIZE_EMAIL_PROMPT,
            input_variables=["email"]
        )
        self.categorize_email = (
            categorize_email_prompt
            | model.openai_model.with_structured_output(CategorizeEmailOutput)
        )

        rag_query_prompt = PromptTemplate(
            template=GENERATE_RAG_QUERIES_PROMPT,
            input_variables=["email"]
        )
        self.design_rag_queries = (
            rag_query_prompt
            | model.openai_model.with_structured_output(GenerateRAGQueriesOutput)
        )

        rag_answer_prompt = PromptTemplate(
            template=GENERATE_RAG_ANSWER_PROMPT,
            input_variables=["question", "context"]
        )
        self.generate_rag_answer = (
            rag_answer_prompt
            | model.openai_model.with_structured_output(GenerateRAGAnswerOutput)
        )

        writer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EMAIL_WRITER_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{email_content}")
            ]
        )
        self.email_writer = (
            writer_prompt
            | model.openai_model.with_structured_output(EmailWriterOutput)
        )

        proofreader_prompt = PromptTemplate(
            template=EMAIL_PROOFREADER_PROMPT,
            input_variables=["initial_email", "generated_email"]
        )
        self.email_proofreader = (
            proofreader_prompt
            | model.openai_model.with_structured_output(EmailProofreaderOutput)
        )
