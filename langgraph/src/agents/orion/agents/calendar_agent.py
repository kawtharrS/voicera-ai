import os 
import sys 
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder
from ..structure_outputs.calendar_structure_output import *
from prompts.calendar import * 
from ...model import Model 
from ...shared_memory import shared_memory

load_dotenv()
model = Model()


class CalendarAgent():
    def __init__(self, calendar_tool=None):
        self.calendar_tool = calendar_tool

        query_category_prompt = PromptTemplate(
            template= CATEGORIZE_QUERY_PROMPT,
            input_variables=["query"]
        )
        self.categorize_query = (
            query_category_prompt 
            | model.openai_model.with_structured_output(CategorizeQueryOutput)
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

        extract_prompt = PromptTemplate(
            template=CREATE_EVENT_PROMT,
            input_variables=["query", "reference_datetime", "timezone"],
        )
        self.create_event_extractor = (
            extract_prompt |
            model.openai_model.with_structured_output(CreateEventArgs)
        )

        search_prompt = PromptTemplate(
            template=SEARCH_EVENT_PROMPT,
            input_variables=["query", "reference_datetime", "timezone"],
        )
        self.search_event_extractor = (
            search_prompt |
            model.openai_model.with_structured_output(SearchEventArgs)
        )

        update_prompt = PromptTemplate(
            template=UPDATE_EVENT_PROMPT,
            input_variables=["query", "reference_datetime", "timezone"],
        )
        self.update_event_extractor = (
            update_prompt |
            model.openai_model.with_structured_output(UpdateEventArgs)
        )

        delete_prompt = PromptTemplate(
            template=DELETE_EVENT_PROMPT,
            input_variables=["query", "reference_datetime", "timezone"],
        )
        self.delete_event_extractor = (
            delete_prompt |
            model.openai_model.with_structured_output(DeleteEventArgs)
        )
