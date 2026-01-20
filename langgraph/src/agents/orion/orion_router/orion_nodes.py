from colorama import Fore, Style 
from .orion_agent import OrionRouterAgent
from .orion_states import GraphState

class RouterNodes:
    def __init__(self):
        self.agent = OrionRouterAgent()

    def route_query(self, state: GraphState)-> GraphState:
        """Route the user query to the appropriate agent"""
        print(Fore.YELLOW + "Routing query ..."+ Style.RESET_ALL)
        query= state.get("query","")
        try:
            result = self.agent.route(query)
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
