from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import logging
import os
from typing import Optional, List

from supabase import create_client, Client

from .router_state import GraphState

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase_client() -> Optional[Client]:
    """Lazily initialize a Supabase client for personal-agent memory.

    Reads SUPABASE_URL and SUPABASE_KEY from the environment. If they are not
    configured or the client cannot be created, returns None and logs a warning.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        logger.warning("Supabase credentials not configured; personal long-term memory disabled.")
        return None

    try:
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized for personal-agent memory.")
    except Exception as exc:
        logger.warning("Failed to initialize Supabase client for personal agent: %s", exc)
        _supabase_client = None

    return _supabase_client


def _load_personal_memory(student_id: Optional[str]) -> str:
    """Load recent personal conversation snippets from Supabase for this user.

    Uses the `user_memo` table populated by the Go backend. Returns a short,
    human-readable summary that the LLM can use to recall facts like the
    user's name, preferences, and past questions/answers.
    """
    if not student_id:
        return ""

    client = get_supabase_client()
    if client is None:
        return ""

    try:
        user_id = int(student_id)
    except ValueError:
        logger.warning("student_id '%s' is not a valid integer; skipping Supabase memory.", student_id)
        return ""

    try:
        response = (
            client
            .table("user_memo")
            .select("user_query, ai_query")
            .eq("user_id", user_id)
            .order("id", desc=True)
            .limit(15)
            .execute()
        )

        records: List[dict] = getattr(response, "data", None) or []
        if not records:
            return ""

        snippets: List[str] = []
        for row in records:
            user_q = (row.get("user_query") or "").strip()
            ai_a = (row.get("ai_query") or "").strip()
            if not user_q and not ai_a:
                continue

            if len(user_q) > 200:
                user_q = user_q[:200] + "..."
            if len(ai_a) > 300:
                ai_a = ai_a[:300] + "..."

            snippets.append(f"Q: {user_q}\nA: {ai_a}")

        if not snippets:
            return ""

        joined = "\n\n".join(reversed(snippets))
        return (
            "Here is a summary of this user's previous conversations with you. "
            "Use it to remember their name, preferences, and important details, "
            "and to answer questions about themselves when appropriate.\n\n" + joined
        )

    except Exception as exc:  
        logger.warning("Failed to load personal Supabase memory: %s", exc)
        return ""


class ResponseNodes:
    """Simple response generation for work and personal categories."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def generate_personal_response(self, state: GraphState) -> GraphState:
        """Generate response for personal queries, with Supabase-backed memory."""
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
    
