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
        prefs = state.get("user_preferences") or {}
        
        try:
            result = self.agent.route(query, prefs)
            category = result.category.value
            print(Fore.GREEN + f"Query routed to: {category}" + Style.RESET_ALL)
            
            return {
                "category": category
            }
            
        except Exception as e:
            print(Fore.RED + f"Error routing query: {e}" + Style.RESET_ALL)
            return {
                "category": "personal"
            }
