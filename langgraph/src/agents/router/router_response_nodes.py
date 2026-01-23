from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import logging
import os
from typing import Optional, List
from ..shared_memory import shared_memory
from .router_state import GraphState
from supabase import Client

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def _load_personal_memory(student_id: Optional[str]) -> str:
    """Load recent personal conversation snippets from SharedMemory for this user."""
    return shared_memory.retrieve(student_id)


class ResponseNodes:
    """Simple response generation for work and personal categories.

    For PERSONAL queries we also perform emotion detection (via Aria's
    EmotionAgent) as a side channel and attach it to the graph state so it
    can be saved in the DB, without forcing the assistant to say it out loud.
    """
    
    def __init__(self, emotion_agent=None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.emotion_agent = emotion_agent
    
    def generate_personal_response(self, state: GraphState) -> GraphState:
        """Generate response for personal queries, with Supabase-backed memory.

        If an EmotionAgent is provided, we run it on the user's query and
        attach the detected emotion to the state, but we do not echo it
        explicitly in the reply.
        """
        print(Fore.CYAN + "Generating personal response..." + Style.RESET_ALL)
        
        query = state.get("query", "")
        prefs = state.get("user_preferences") or {}
        student_id = state.get("student_id")

        # Load long-term conversation memory from Supabase (if available).
        memory_context = _load_personal_memory(student_id)

        language = prefs.get("language") or "English"
        tone = prefs.get("tone") or "friendly"
        agent_name = prefs.get("name") or "your assistant"
        extra = prefs.get("preference") or ""

        extra_line = f"Additional user notes: {extra}\n" if extra else ""
        memory_line = f"\n\nUSER HISTORY:\n{memory_context}\n" if memory_context else ""

        system_msg = (
            f"You are a personal assistant named {agent_name}.\n"
            f"Always respond in {language}.\n"
            f"Use a {tone.lower()} tone.\n"
            f"{extra_line}"
            f"{memory_line}"
            "Help with everyday tasks, personal questions, lifestyle advice, and general conversation.\n"
            "When the user asks about themselves (for example, their name), use the USER HISTORY "
            "section above to answer consistently across conversations.\n"
            "Be warm, supportive, and conversational while respecting these preferences."
        ).strip()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "{query}")
        ])
        
        try:
            # Optional: detect emotion as a side channel
            detected_emotion_value = None
            if self.emotion_agent is not None and query:
                try:
                    emo_result = self.emotion_agent.detect(query, prefs)
                    detected_emotion_value = getattr(emo_result.emotion, "value", None) or str(emo_result.emotion)
                    print(Fore.MAGENTA + f"[Personal] Detected emotion: {detected_emotion_value}" + Style.RESET_ALL)
                except Exception as e:
                    print(Fore.RED + f"[Personal] Emotion detection error: {e}" + Style.RESET_ALL)

            response = self.llm.invoke(prompt.format(query=query))
            ai_response = response.content
            
            # Prepend greeting for Aria if first message
            if state.get("is_first_message"):
                ai_response = f"Hi, I'm Aria! {ai_response}"
            
            # Save new interaction to shared memory
            if student_id:
                # We save the interaction to memory so it can be recalled later
                shared_memory.extract_and_save(query, student_id)
            
            print(Fore.GREEN + f"Personal response generated" + Style.RESET_ALL)
            
            current_interaction = state.get("current_interaction", {})
            if isinstance(current_interaction, dict):
                current_interaction["ai_response"] = ai_response
                current_interaction["recommendations"] = []
            
            # Build the new state, including emotion if we have it
            new_state: GraphState = {
                "ai_response": ai_response,
                "current_interaction": current_interaction,
                "recommendations": [],
                "sendable": True,
            }
            if detected_emotion_value:
                new_state["emotion"] = detected_emotion_value
            
            return new_state
        except Exception as e:
            print(Fore.RED + f"Error generating personal response: {e}" + Style.RESET_ALL)
            return {
                "ai_response": "I'm here to help with personal matters. Could you provide more details?",
                "recommendations": [],
                "sendable": False
            }
    
