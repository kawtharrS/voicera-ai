import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from colorama import Fore, Style
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from .state import GraphState, UserInteraction
from .structure_output import CategorizeQueryOutput, CreateEventArgs
from prompts.calendar import CATEGORIZE_QUERY_PROMPT
from tools.calendarTools import CalendarTool
from .agent import Agent

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key = os.getenv("OPENAI_API_KEY")
)
default_tz = "Asia/Beirut"
reference_dt = datetime.now(ZoneInfo(default_tz))

class CalendarNodes:
    def __init__(self):
        self.calendar_tool = CalendarTool()
        self.agents = Agent(self.calendar_tool)


    @staticmethod
    def _get_current_interaction(state: GraphState):
        interaction = state.get("current_interaction")
        if isinstance(interaction, dict):
            query = interaction.get("user_request")
            interaction_model = UserInteraction(**interaction)
        else:
            interaction_model = interaction
            query = getattr(interaction_model, "user_request")

        return interaction_model, query

    def receive_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Receiving user query ..." + Style.RESET_ALL)

        incoming = state.get("current_interaction")
        if isinstance(incoming, dict):
            request = incoming.get("user_request", "")
        else:
            request = getattr(incoming, "user_request", "")

        return {
            "current_interaction": UserInteraction(
                user_request=request,
                ai_response="",
                recommendations=[],
            )
        }
    
    def categorize_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Categorizing user query ..." + Style.RESET_ALL)

        interaction_model, query = self._get_current_interaction(state)

        result = self.agents.categorize_query.invoke({"query": query})
        category = result.category.value
        observation = f"Query classified as: {category}"

        return {
            "current_interaction": interaction_model.model_copy(
                update={
                    "ai_response": f"Category: {category}",
                    "observation": observation,
                }
            ),
            "query_category": category,
        }
    
    def route_after_categorize(self, state:GraphState) -> GraphState:
        category = state.get("query_category")
        if hasattr(category, "value"):
            category = category.value
        route = "create_event" if category == "create" else "end"
        return {"route":route}

    
    def create_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Creating an event ..." + Style.RESET_ALL)
        tool =self.calendar_tool.createEvent()

        interaction_model, query = self._get_current_interaction(state)

        extractor = self.agents.create_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": reference_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        payload.setdefault("timezone", default_tz)

        if not payload.get("end_datetime") and payload.get("start_datetime"):
            start_dt = datetime.strptime(payload["start_datetime"], "%Y-%m-%d %H:%M:%S")
            payload["end_datetime"] = (start_dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
      
        try:
            result = tool.invoke(payload)
            return {
                "current_interaction":interaction_model.model_copy(
                    update={
                        "ai_response":f"created event: {extractor.summary}",
                        "observation":"Calendar event created successfully"
                    }
                ),
                "calendar_result":result,
            }
        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to create event: {e}",
                        "observation": "Calendar event creation failed.",
                    }
                )
            }
        





        