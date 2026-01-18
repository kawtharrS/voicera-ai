import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from .router_structure_output import RouterOutput, RouteCategory
from prompts.router import ROUTER_PROMPT

load_dotenv()

class RouterAgent:
    def __init__(self):
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.router_prompt = PromptTemplate(
            template=ROUTER_PROMPT,
            input_variables=["query", "preferences"]
        )
        
        self.router_runnable = (
            self.router_prompt
            | self.model.with_structured_output(RouterOutput)
        )

    def route(self, query: str, preferences: dict | None = None) -> RouterOutput:
        """Routes the user query to the appropriate category, taking into account user preferences."""
        pref_text = ""
        if preferences:
            lang = preferences.get("language") or "unspecified"
            tone = preferences.get("tone") or "unspecified"
            name = preferences.get("name") or "the assistant"
            extra = preferences.get("preference") or ""
            pref_text = (
                f"Preferred language: {lang}\n"
                f"Preferred tone: {tone}\n"
                f"Agent name: {name}\n"
                f"Additional notes: {extra}"
            )
        return self.router_runnable.invoke({"query": query, "preferences": pref_text})
