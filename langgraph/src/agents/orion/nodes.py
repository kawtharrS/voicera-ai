import os

from colorama import Fore, Style
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from .state import GraphState, UserInteraction
from .structure_output import CategorizeQueryOutput
from prompts.calendar import CATEGORIZE_QUERY_PROMPT

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key = os.getenv("OPENAI_API_KEY")
)

class CalendarNodes:
    def __init__(self):
        categorize_prompt = PromptTemplate(
            template=CATEGORIZE_QUERY_PROMPT,
            input_variables=["query"],
        )
        self.categorize_query = categorize_prompt | openai_model.with_structured_output(
            CategorizeQueryOutput
        )

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

        interaction = state.get("current_interaction")
        if isinstance(interaction, dict):
            query = interaction.get("user_request", "")
            interaction_model = UserInteraction(**interaction)
        else:
            interaction_model = interaction
            query = interaction_model.user_request

        result = self.categorize_query.invoke({"query": query})
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



        