from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from .router_state import GraphState

class ResponseNodes:
    """Simple response generation for work and personal categories."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def generate_personal_response(self, state: GraphState) -> GraphState:
        """Generate response for personal queries."""
        print(Fore.CYAN + "Generating personal response..." + Style.RESET_ALL)
        
        query = state.get("query", "")
        prefs = state.get("user_preferences") or {}

        language = prefs.get("language") or "English"
        tone = prefs.get("tone") or "friendly"
        agent_name = prefs.get("name") or "your assistant"
        extra = prefs.get("preference") or ""

        extra_line = f"Additional user notes: {extra}\n" if extra else ""
        system_msg = (
            f"You are a personal assistant named {agent_name}.\n"
            f"Always respond in {language}.\n"
            f"Use a {tone.lower()} tone.\n"
            f"{extra_line}"
            "Help with everyday tasks, personal questions, lifestyle advice, and general conversation.\n"
            "Be warm, supportive, and conversational while respecting these preferences."
        ).strip()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "{query}")
        ])
        
        try:
            response = self.llm.invoke(prompt.format(query=query))
            ai_response = response.content
            
            print(Fore.GREEN + f"Personal response generated" + Style.RESET_ALL)
            
            current_interaction = state.get("current_interaction", {})
            if isinstance(current_interaction, dict):
                current_interaction["ai_response"] = ai_response
                current_interaction["recommendations"] = []
            
            return {
                "ai_response": ai_response,
                "current_interaction": current_interaction,
                "recommendations": [],
                "sendable": True
            }
        except Exception as e:
            print(Fore.RED + f"Error generating personal response: {e}" + Style.RESET_ALL)
            return {
                "ai_response": "I'm here to help with personal matters. Could you provide more details?",
                "recommendations": [],
                "sendable": False
            }
    