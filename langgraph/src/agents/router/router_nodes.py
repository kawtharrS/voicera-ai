from colorama import Fore, Style
from .router_agent import RouterAgent
from .router_state import GraphState
from ..aria.agents.agent import EmotionAgent

class RouterNodes:
    def __init__(self):
        self.agent = RouterAgent()
        self.emotion_agent = EmotionAgent()

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
        
        # Check if user is trying to send an email draft from previous Gmail workflow
        query_lower = query.lower()
        send_keywords = ["send", "send it", "send the draft", "send email", "send the email", "send this draft", "send draft"]
        if any(keyword in query_lower for keyword in send_keywords):
            # If coming from Gmail workflow context, route back to Gmail for sending
            category = "work"  # Work includes email operations
            print(Fore.GREEN + f"Query routed to: {category} (email send detected)" + Style.RESET_ALL)
        else:
            result = self.agent.route(query, prefs)
            category = result.category.value
            print(Fore.GREEN + f"Query routed to: {category}" + Style.RESET_ALL)
        
        print(Fore.YELLOW + "Detecting emotion..." + Style.RESET_ALL)
        emotion_result = self.emotion_agent.detect(query, prefs)
        emotion = emotion_result.emotion.value if hasattr(emotion_result.emotion, 'value') else str(emotion_result.emotion)
        
        print(Fore.GREEN + f"Emotion detected: {emotion}" + Style.RESET_ALL)
        
        return {
            "category": category,
            "emotion": emotion,
            "is_first_message": is_first
        }
            

