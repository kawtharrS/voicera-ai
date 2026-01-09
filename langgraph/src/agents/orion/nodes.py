import os 
from colorama import Fore, Style
from typing import Optional
from langchain_openai import ChatOpenAI
from .agent import Agent 
from .state import *
from tools.calendarTools import CalendarTool
from prompts.calendar import *

openai_model = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.1, 
    openai_api_key = os.getenv("OPENAI_API_KEY")
)

class CalendarNodes:
    def __inti__(self):
        self.agents = Agent()
        self.calendar_tools = CalendarTool()

    def receive_user_query(self, state:GraphState) ->GraphState:
        print(Fore.YELLOW + "Receiving student query ..." + Style.RESET_ALL)

        incoming = state["current_interaction"]
        request = incoming.get("user_request") if isinstance(incoming, dict) else incoming.user_request

        return {"user_interaction": UserInteraction(
            user_request=request,
            ai_response="",
            recommendations=[]
        )}
    
    def categorize_user_query(self, state:GraphState)-> GraphState:
        print(Fore.YELLOW + "Categorizing user query ..." + Style.RESET_ALL)

        query = state["user_interaction"].user_request

        result = self.agents.categorize_query.invoke({"query":query})
        category = result.category.value 
        observation = f"Query classified as: {category}"

        return {"current_interaction": state["current_interaction"].model_copy(update={
            "ai_response": f"Category: {category}",
            "observation": observation
        })}  



        