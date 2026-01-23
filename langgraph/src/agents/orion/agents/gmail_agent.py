import os 
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from ..structure_outputs.gmail_structure_output import *
from prompts.gmail import *
from ...model import Model 
from ...shared_memory import shared_memory

load_dotenv()

model = Model()


class GmailAgent():
    def __init__(self, gmail_tool=None):
        self.gmail_tool = gmail_tool
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.vectorstore = shared_memory.vectorstore

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
