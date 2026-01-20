import os 
from dotenv import load_dotenv 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .orion_structure_output import RouteOrion, RouterOutput
from prompts.orion_router import ROUTER_PROMPT

load_dotenv()

class OrionRouterAgent():
    def __init__(self):
        self.model = ChatOpenAI(
            model = "gpt-4o-mini", 
            temperature=0,
            openai_api_key= os.getenv("OPENAI_API_KEY")
        )

        self.router_prompt = PromptTemplate(
            template = ROUTER_PROMPT,
            inpute_variables = ["query"]
        )

        self.router_runnable = (
            self.router_prompt
            | self.model.with_structured_output(RouterOutput)
        )

    def route(self, query:str) -> RouterOutput:
        """Routes the user query to the appropriate category"""
        return self.router_runnable.invoke({"query":query})