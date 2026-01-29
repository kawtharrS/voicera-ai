from colorama import Fore, Style
from .router_agent import RouterAgent
from .continuation_agent import ContinuationAgent
from .router_state import GraphState
from ..aria.agents.agent import EmotionAgent

class RouterNodes:
    def __init__(self):
        self.agent = RouterAgent()
        self.continuation_agent = ContinuationAgent()
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
        
        query_lower = query.lower()
        send_keywords = ["send", "send it", "send the draft", "send email", "send the email", "send this draft", "send draft"]
        if any(keyword in query_lower for keyword in send_keywords):
            category = "work"  #
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

    def determine_next_step(self, state: GraphState) -> GraphState:
        """Use LLM to intelligently decide on next workflow step."""
        print(Fore.YELLOW + "Checking for workflow continuation..." + Style.RESET_ALL)
        
        query = state.get("query", "")
        study_plan = state.get("study_plan")
        calendar_result = state.get("calendar_result")
        email_draft_id = state.get("email_draft_id")
        
        # Use LLM to decide if we should continue
        try:
            decision = self.continuation_agent.decide(
                query=query,
                has_study_plan=bool(study_plan),
                has_calendar_result=bool(calendar_result),
                has_email_draft=bool(email_draft_id)
            )
            
            if decision.decision.value == "continue":
                print(Fore.GREEN + f"Workflow continuation: {decision.reasoning}" + Style.RESET_ALL)
                
                # If we have a study plan but no calendar result, route to calendar
                if study_plan and not calendar_result:
                    return {
                        "query": "Create events from study plan and email a summary",
                        "category": "work"
                    }
                # If we have calendar result and email draft, route to send
                elif calendar_result and email_draft_id:
                    return {
                        "query": "Send the draft",
                        "category": "work"
                    }
            
            print(Fore.YELLOW + f"Workflow ended: {decision.reasoning}" + Style.RESET_ALL)
            return {}
            
        except Exception as e:
            print(Fore.RED + f"Error in continuation decision: {e}" + Style.RESET_ALL)
            return {}

    def check_continuation_condition(self, state: GraphState) -> str:
        """Condition to determine if we should loop back to the router."""
        query = state.get("query", "")
        study_plan = state.get("study_plan")
        calendar_result = state.get("calendar_result")
        email_draft_id = state.get("email_draft_id")
        
        # Use LLM to decide
        try:
            decision = self.continuation_agent.decide(
                query=query,
                has_study_plan=bool(study_plan),
                has_calendar_result=bool(calendar_result),
                has_email_draft=bool(email_draft_id)
            )
            return decision.decision.value
        except Exception as e:
            print(Fore.RED + f"Error in continuation condition: {e}" + Style.RESET_ALL)
            return "end"
            

