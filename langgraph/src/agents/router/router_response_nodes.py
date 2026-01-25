import os
from typing import Optional

from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..shared_memory import shared_memory
from .router_state import GraphState

async def _load_personal_memory(student_id: Optional[str], query: str = "") -> str:
    """Load recent personal conversation snippets for this user."""
    if not student_id:
        print(Fore.YELLOW + "[Memory] No student_id provided" + Style.RESET_ALL)
        return ""
    
    print(Fore.CYAN + f"[Memory] Loading memories for user {student_id}..." + Style.RESET_ALL)
    memory = await shared_memory.retrieve(student_id, query)
    
    if memory:
        print(Fore.GREEN + f"[Memory] Retrieved {len(memory)} chars of memory" + Style.RESET_ALL)
        print(Fore.GREEN + f"[Memory] Content: {memory[:200]}..." + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "[Memory] No memories found for user" + Style.RESET_ALL)
    
    return memory

class ResponseNodes:
    """Response generation for personal conversations."""

    def __init__(self, emotion_agent=None):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.emotion_agent = emotion_agent

    def _detect_emotion(self, query: str, prefs: dict) -> Optional[str]:
        if not self.emotion_agent or not query:
            return None

        try:
            result = self.emotion_agent.detect(query, prefs)
            emotion = getattr(result.emotion, "value", None) or str(result.emotion)
            print(Fore.MAGENTA + f"[Personal] Detected emotion: {emotion}" + Style.RESET_ALL)
            return emotion
        except Exception as e:
            print(Fore.RED + f"[Personal] Emotion detection failed: {e}" + Style.RESET_ALL)
            return None

    def build_prompt(self, prefs: dict, memory: str) -> ChatPromptTemplate:
        language = prefs.get("language", "English")
        tone = prefs.get("tone", "friendly")
        agent_name = prefs.get("name", "your assistant")
        extra = prefs.get("preference", "")

        system_parts = [
            f"You are a personal assistant named {agent_name}.",
            f"Always respond in {language}.",
            f"Use a {tone.lower()} tone.",
            "Help with everyday tasks, personal questions, lifestyle advice, and general conversation.",
            "Be warm, supportive, and conversational.",
        ]

        if extra:
            system_parts.append(f"Additional user notes: {extra}")

        if memory:
            system_parts.append(f"\nUSER HISTORY (Facts from past conversations):\n{memory}")

        system_msg = "\n".join(system_parts)

        return ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "{query}")
        ])

    async def generate_personal_response(self, state: GraphState) -> GraphState:
        print(Fore.CYAN + "Generating personal response..." + Style.RESET_ALL)

        query = state.get("query", "")
        prefs = state.get("user_preferences") or {}
        student_id = state.get("student_id")

        memory_context = await _load_personal_memory(student_id, query)
        detected_emotion = state.get("emotion") or ""

        prompt = self.build_prompt(prefs, memory_context)

        try:
            response = await self.llm.ainvoke(prompt.format(query=query))
            ai_response = response.content

            if state.get("is_first_message"):
                ai_response = f"Hi, I'm Aria! {ai_response}"

            if student_id:
                # Save to LangMem and Supabase Interaction log
                await shared_memory.extract_and_save(
                    query=query, 
                    ai_response=ai_response, 
                    user_id=student_id, 
                    category="personal", 
                    emotion=detected_emotion or ""
                )

            print(Fore.GREEN + "Personal response generated successfully" + Style.RESET_ALL)

            current_interaction = state.get("current_interaction", {})
            if isinstance(current_interaction, dict):
                current_interaction.update({
                    "ai_response": ai_response,
                    "recommendations": [],
                })

            new_state: GraphState = {
                "ai_response": ai_response,
                "current_interaction": current_interaction,
                "recommendations": [],
                "sendable": True,
            }

            if detected_emotion:
                new_state["emotion"] = detected_emotion

            return new_state

        except Exception as e:
            print(Fore.RED + f"Personal response error: {e}" + Style.RESET_ALL)
            return {
                "ai_response": "I'm here to help with personal matters. Could you tell me a bit more?",
                "recommendations": [],
                "sendable": False,
            }
