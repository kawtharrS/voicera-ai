from colorama import Fore, Style
from .router_agent import RouterAgent
from .router_state import GraphState

class RouterNodes:
    def __init__(self):
        self.agent = RouterAgent()

    def route_query(self, state: GraphState) -> GraphState:
        """Route the user query to the appropriate agent."""
        print(Fore.YELLOW + "Routing query..." + Style.RESET_ALL)
        query = state.get("query", "")
        student_id = state.get("student_id")
        prefs = state.get("user_preferences") or {}
        messages = state.get("messages", [])
        is_first = False
        if not messages or len(messages) <= 1:
            is_first = True
        print(Fore.CYAN + f"Is first message: {is_first}" + Style.RESET_ALL)
        print(Fore.CYAN + f"Student ID: {student_id}" + Style.RESET_ALL)
        result = self.agent.route(query, prefs)
        category = result.category.value
        print(Fore.GREEN + f"Query routed to: {category}" + Style.RESET_ALL)
        return {
            "category": category,
            "is_first_message": is_first
        }
            

