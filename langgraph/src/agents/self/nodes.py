import os
from typing import Optional

from colorama import Fore, Style
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from .structure_output import SelfAgentOutput, SelfAction
from  tools.prefrenceTool import PreferencesTool
from .agent import SelfAgent
from .state import SelfAgentGraphState


class SelfNodes:
    def __init__(self):
        self.router_agent = SelfAgent()
        self.preferences_tool = PreferencesTool()
        self.update_preferences_tool = self.preferences_tool.updatePreferences()

    def receive_user_query(self, state: SelfAgentGraphState) -> SelfAgentGraphState:
        print(Fore.YELLOW + "Receiving user query ..." + Style.RESET_ALL)

        query = state.get("query") or ""
        if not query:
            current = state.get("current_interaction")
            query = getattr(current, "user_request", "") if current else ""

        student_id = state.get("student_id")
        user_id: int | None = None
        if isinstance(student_id, str) and student_id.isdigit():
            try:
                user_id = int(student_id)
            except ValueError:
                user_id = None

        prefs = state.get("user_preferences") or state.get("preferences") or {}

        return {
            "current_interaction": query,
            "user_id": user_id,
            "preferences": prefs,
        }

    def run_self_agent(self, state: SelfAgentGraphState) -> SelfAgentGraphState:
        print(Fore.YELLOW + "Running SelfAgent ..." + Style.RESET_ALL)

        query = state.get("current_interaction") or state.get("query") or ""
        preferences = state.get("preferences") or {}

        result: SelfAgentOutput = self.router_agent.router_runnable.invoke({
            "query": query,
            "preferences": preferences
        })

        return {
            "current_interaction": query,
            "router_output": result
        }

    def apply_preferences(self, state: SelfAgentGraphState) -> SelfAgentGraphState:
        print(Fore.YELLOW + "Applying preferences ..." + Style.RESET_ALL)

        router_output: SelfAgentOutput = state.get("router_output")
        if not router_output:
            return state

        action = router_output.action

        if action == SelfAction.get_prefrences:
            prefs = state.get("preferences", {}) or {}
            language = prefs.get("language") or "not set"
            tone = prefs.get("tone") or "not set"
            name = prefs.get("name") or "not set"
            extra = prefs.get("preference") or "none"

            ai_response = (
                "Here are your current preferences:\n"
                f"- Language: {language}\n"
                f"- Tone: {tone}\n"
                f"- Name: {name}\n"
                f"- Additional notes: {extra}"
            )

            return {
                "preferences": prefs,
                "ai_response": ai_response,
                "recommendations": [],
                "observation": "Returned current preferences.",
                "router_output": router_output,
            }

        if action == SelfAction.updated_prefrences:
            user_id = state.get("user_id")
            if not user_id:
                msg = "I couldn't update your preferences because I don't know which user you are. Please make sure you are logged in."
                return {
                    "ai_response": msg,
                    "recommendations": [],
                    "observation": "No user_id found in state.",
                    "router_output": router_output,
                }

            payload = {
                "user_id": user_id,
                "language": router_output.language,
                "tone": router_output.tone,
                "name": router_output.name,
                "preference": router_output.preference,
            }

            payload = {k: v for k, v in payload.items() if v is not None}

            existing_prefs = state.get("preferences", {}) or {}
            updated_prefs = {**existing_prefs, **{k: v for k, v in payload.items() if k != "user_id"}}

            try:
                self.update_preferences_tool.invoke(payload)

                changed_fields = [
                    f"language → {updated_prefs.get('language')}" if "language" in payload else None,
                    f"tone → {updated_prefs.get('tone')}" if "tone" in payload else None,
                    f"name → {updated_prefs.get('name')}" if "name" in payload else None,
                    f"additional notes → {updated_prefs.get('preference')}" if "preference" in payload else None,
                ]
                changed_fields = [c for c in changed_fields if c]
                if changed_fields:
                    details = "\n- " + "\n- ".join(changed_fields)
                else:
                    details = ""

                ai_response = "I've updated your preferences." + details

                return {
                    "preferences": updated_prefs,
                    "ai_response": ai_response,
                    "recommendations": [],
                    "observation": "Preferences updated successfully.",
                    "router_output": router_output,
                }
            except Exception as e:
                msg = f"I tried to update your preferences but something went wrong: {e}"
                return {
                    "ai_response": msg,
                    "recommendations": [],
                    "observation": f"Preferences update failed: {e}",
                    "router_output": router_output,
                }

        return state
