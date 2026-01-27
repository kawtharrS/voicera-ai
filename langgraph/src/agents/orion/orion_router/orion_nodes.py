from colorama import Fore, Style 
from .orion_agent import OrionRouterAgent
from .orion_states import GraphState

class RouterNodes:
    def __init__(self):
        self.agent = OrionRouterAgent()

    def route_query(self, state: GraphState)-> GraphState:
        """Route the user query to the appropriate agent."""
        print(Fore.YELLOW + "Routing query ..."+ Style.RESET_ALL)
        query = state.get("query", "") or ""
        ql = query.lower()

        # Check for email-related keywords (send, reply, etc.)
        email_keywords = ["send the draft", "send draft", "send me this draft", "send this draft", "send the email", "send email", "send it", "send reply", "send the reply", "send this draft gmail"]
        has_send_keyword = any(k in ql for k in email_keywords)

        # If we have a pending email draft created by the calendar flow, route to calendar so it can send it.
        # This avoids incorrectly going into the Gmail workflow (which is inbox-driven).
        draft_id = state.get("email_draft_id")
        if draft_id and has_send_keyword:
            print(Fore.GREEN + "Detected request to send calendar-created draft; routing to calendar" + Style.RESET_ALL)
            return {"category": "calendar"}
        
        # If user is asking to send/reply and we just came from Gmail workflow, route back to Gmail
        # The Gmail workflow maintains context of created drafts
        category_from_llm = None
        if has_send_keyword:
            print(Fore.GREEN + "Detected email send/reply request; routing to gmail" + Style.RESET_ALL)
            return {"category": "gmail"}

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

    async def save_to_langmem(self, state: GraphState) -> GraphState:
        """Saves interaction and extracts facts for Orion tasks."""
        print(Fore.YELLOW + "Orion: Syncing to backend and extracting facts..." + Style.RESET_ALL)
        from ...shared_memory import shared_memory
        
        query = state.get("query", "")
        interaction = state.get("current_interaction")
        student_id = state.get("student_id")
        
        if not student_id: return state
        
        ai_response = state.get("ai_response", "")
        category = state.get("category", "work")
        
        if not ai_response:
            if isinstance(interaction, dict):
                ai_response = interaction.get("ai_response", "")
            elif interaction is not None:
                ai_response = getattr(interaction, "ai_response", "")
            
        await shared_memory.extract_and_save(
            query=query,
            ai_response=ai_response,
            user_id=student_id,
            category=f"work_{category}"
        )
        return state
