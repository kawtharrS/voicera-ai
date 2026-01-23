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
        
        # Determine if this is the first message in the session
        messages = state.get("messages", [])
        # If there are no messages or only 1 message (the current user query), it's the first.
        # Note: LangGraph might append the latest input to messages before calling nodes? 
        # Usually we check if we have prior history. 
        # Let's assume if messages list is empty or length 1 (just this turn), it is start.
        # But better to rely on conversation_history length if available or messages.
        
        is_first = False
        if not messages or len(messages) <= 1:
            is_first = True
            
        print(Fore.CYAN + f"Is first message: {is_first}" + Style.RESET_ALL)
        
        try:
            result = self.agent.route(query, prefs)
            category = result.category.value
            print(Fore.GREEN + f"Query routed to: {category}" + Style.RESET_ALL)
            
            return {
                "category": category,
                "is_first_message": is_first
            }
            
        except Exception as e:
            print(Fore.RED + f"Error routing query: {e}" + Style.RESET_ALL)
            return {
                "category": "personal"
            }
