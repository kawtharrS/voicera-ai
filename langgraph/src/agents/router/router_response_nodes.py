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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly personal assistant. Help with everyday tasks, 
            personal questions, lifestyle advice, and general conversation. 
            Be warm, supportive, and conversational."""),
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
    
    def generate_work_response(self, state: GraphState) -> GraphState:
        """Generate response for work-related queries."""
        print(Fore.YELLOW + "Generating work response..." + Style.RESET_ALL)
        
        query = state.get("query", "")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional work assistant. Help with work-related tasks,
            professional communication, productivity, career advice, and workplace matters.
            Be professional, concise, and action-oriented."""),
            ("human", "{query}")
        ])
        
        try:
            response = self.llm.invoke(prompt.format(query=query))
            ai_response = response.content
            
            print(Fore.GREEN + f"Work response generated" + Style.RESET_ALL)
            
            # Update current_interaction if it exists
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
            print(Fore.RED + f"Error generating work response: {e}" + Style.RESET_ALL)
            return {
                "ai_response": "I'm here to help with work matters. What do you need assistance with?",
                "recommendations": [],
                "sendable": False
            }
