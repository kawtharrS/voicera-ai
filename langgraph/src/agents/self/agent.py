import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .structure_output import SelfAction, SelfAgentOutput
from prompts.self import SELF_PROMPT

load_dotenv()

class SelfAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.router_prompt = PromptTemplate(
            template=SELF_PROMPT,
            input_variables=["query", "preferences"]
        )
        
        self.router_runnable = (
            self.router_prompt
            | self.model.with_structured_output(SelfAgentOutput)
        )
