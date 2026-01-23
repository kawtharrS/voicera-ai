import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from colorama import Fore, Style
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..states.calendar_state import GraphState, UserInteraction
from ..structure_outputs.calendar_structure_output import CategorizeQueryOutput, CreateEventArgs
from prompts.calendar import CATEGORIZE_QUERY_PROMPT
from tools.calendarTools import CalendarTool
from ..agents.calendar_agent import CalendarAgent

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key = os.getenv("OPENAI_API_KEY")
)
default_tz = "Asia/Beirut"


def _get_reference_dt():
    """Return current datetime in default timezone (computed fresh each call)."""
    return datetime.now(ZoneInfo(default_tz))


class CalendarNodes:
    def __init__(self):
        self.calendar_tool = CalendarTool()
        self.agents = CalendarAgent(self.calendar_tool)


    @staticmethod
    def _get_current_interaction(state: GraphState):
        interaction = state.get("current_interaction")
        if isinstance(interaction, dict):
            query = interaction.get("user_request")
            interaction_model = UserInteraction(**interaction)
        else:
            interaction_model = interaction
            query = getattr(interaction_model, "user_request")

        return interaction_model, query

    def receive_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Receiving user query ..." + Style.RESET_ALL)

        incoming = state.get("current_interaction")
        request = ""
        if isinstance(incoming, dict):
            request = incoming.get("user_request") or incoming.get("student_question", "")
        elif incoming is not None:
            request = getattr(incoming, "user_request", getattr(incoming, "student_question", ""))
        
        if not request:
            request = state.get("query", "")

        return {
            "current_interaction": UserInteraction(
                user_request=request,
                ai_response="",
                recommendations=[],
            ),
            # Preserve is_first_message if routed from parent
            "is_first_message": state.get("is_first_message", False) 
        }
    
    def categorize_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Categorizing user query ..." + Style.RESET_ALL)

        interaction_model, query = self._get_current_interaction(state)

        result = self.agents.categorize_query.invoke({"query": query})
        category = result.category.value
        observation = f"Query classified as: {category}"

        return {
            "current_interaction": interaction_model.model_copy(
                update={
                    "ai_response": f"Category: {category}",
                    "observation": observation,
                }
            ),
            "query_category": category,
        }
    
    def route_after_categorize(self, state:GraphState) -> GraphState:
        category = state.get("query_category")
        if hasattr(category, "value"):
            category = category.value
        if category == "create":
            route = "create_event"
        elif category == "search":
            route = "search_event"
        elif category == "update":
            route = "update_event"
        elif category == "delete":
            route = "delete_event"
        else:
            route = "end"
        return {"route":route}

    
    def create_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Creating an event ..." + Style.RESET_ALL)
        tool = self.calendar_tool.createEvent()

        interaction_model, query = self._get_current_interaction(state)

        extractor = self.agents.create_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        payload.setdefault("timezone", default_tz)

        if not payload.get("end_datetime") and payload.get("start_datetime"):
            start_dt = datetime.strptime(payload["start_datetime"], "%Y-%m-%d %H:%M:%S")
            payload["end_datetime"] = (start_dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = tool.invoke(payload)

            # ❗ Correct: assign response_text BEFORE returning dict
            response_text = f"created event: {extractor.summary}"
            if state.get("is_first_message"):
                response_text = f"Hi, I'm Orion! {response_text}"

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": response_text,
                        "observation": "Calendar event created successfully"
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to create event: {e}",
                        "observation": "Calendar event creation failed.",
                    }
                )
            }

    def search_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Searching for events ..." + Style.RESET_ALL)

        interaction_model, query = self._get_current_interaction(state)
        try:
            calendars_info = self.calendar_tool.getCalendarsInfo().invoke({})
        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to read calendars: {e}",
                        "observation": "Calendar calendars_info fetch failed.",
                    }
                )
            }

        extractor = self.agents.search_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        payload["calendars_info"] = calendars_info

        tool = self.calendar_tool.searchEvents()
        try:
            result = tool.invoke(payload)

            # ✅ Assign before return
            count = len(result) if isinstance(result, list) else 0
            response_text = f"Found {count} event(s)."
            if state.get("is_first_message"):
                response_text = f"Hi, I'm Orion! {response_text}"

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": response_text,
                        "observation": "Calendar events searched successfully",
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to search events: {e}",
                        "observation": "Calendar event search failed.",
                    }
                )
            }

    def update_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Updating an event ..." + Style.RESET_ALL)

        interaction_model, query = self._get_current_interaction(state)

        extractor = self.agents.update_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        event_id = payload.get("event_id")

        if not event_id or (isinstance(event_id, str) and "placeholder" in event_id.lower()):
            try:
                calendars_info = self.calendar_tool.getCalendarsInfo().invoke({})
                search_args = {
                    "calendars_info": calendars_info,
                    "min_datetime": payload.get("target_min_datetime"),
                    "max_datetime": payload.get("target_max_datetime"),
                    "query": payload.get("target_query"),
                    "max_results": payload.get("max_results", 10),
                }

                candidates = self.calendar_tool.searchEvents().invoke(search_args)
            except Exception as e:
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": f"Search for target event failed: {e}",
                            "observation": "Update failed: search error.",
                        }
                    )
                }

            if not isinstance(candidates, list) or len(candidates) == 0:
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "No matching events found to update.",
                            "observation": "Update failed: no matching events.",
                        }
                    ),
                    "calendar_result": {"candidates": []},
                }

            if len(candidates) > 1:
                shown = candidates[:5]
                options = "\n".join(
                    [f"- id={c.get('id')} | {c.get('summary')} | start={c.get('start')}" for c in shown]
                )
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "Multiple events match. Reply with the event_id:\n" + options,
                            "observation": "Update requires disambiguation.",
                        }
                    ),
                    "calendar_result": {"candidates": candidates},
                }

            event_id = candidates[0].get("id")

        update_payload = {
            "event_id": event_id,
            "calendar_id": payload.get("calendar_id", "primary"),
            "summary": payload.get("new_summary"),
            "start_datetime": payload.get("new_start_datetime"),
            "end_datetime": payload.get("new_end_datetime"),
            "timezone": payload.get("timezone"),
            "location": payload.get("new_location"),
            "description": payload.get("new_description"),
            "send_updates": payload.get("send_updates"),
        }
        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        if update_payload.get("start_datetime") and not update_payload.get("end_datetime"):
            try:
                start_dt = datetime.strptime(update_payload["start_datetime"], "%Y-%m-%d %H:%M:%S")
                update_payload["end_datetime"] = (start_dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        if (update_payload.get("start_datetime") or update_payload.get("end_datetime")) and not update_payload.get("timezone"):
            update_payload["timezone"] = default_tz

        try:
            tool = self.calendar_tool.updateEvent()
            result = tool.invoke(update_payload)

            # ✅ Correct: compute response_text BEFORE returning
            response_text = f"Updated event: {event_id}"
            if state.get("is_first_message"):
                response_text = f"Hi, I'm Orion! {response_text}"

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": response_text,
                        "observation": "Calendar event updated successfully",
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to update event: {e}",
                        "observation": "Calendar event update failed.",
                    }
                )
            }



    def delete_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Deleting an event ..." + Style.RESET_ALL)

        interaction_model, query = self._get_current_interaction(state)

        extractor = self.agents.delete_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )
        payload = extractor.model_dump(exclude_none=True)

        event_id = payload.get("event_id")
        if not event_id or (isinstance(event_id, str) and "placeholder" in event_id.lower()):
            try:
                calendars_info = self.calendar_tool.getCalendarsInfo().invoke({})
                search_args = {
                    "calendars_info": calendars_info,
                    "min_datetime": payload.get("target_min_datetime"),
                    "max_datetime": payload.get("target_max_datetime"),
                    "query": payload.get("target_query"),
                    "max_results": payload.get("max_results", 10),
                }

                candidates = self.calendar_tool.searchEvents().invoke(search_args)
            except Exception as e:
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": f"Search for target event failed: {e}",
                            "observation": "Delete failed: search error.",
                        }
                    )
                }

            if not isinstance(candidates, list) or len(candidates) == 0:
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "No matching events found to delete.",
                            "observation": "Delete failed: no matching events.",
                        }
                    ),
                    "calendar_result": {"candidates": []},
                }

            if len(candidates) > 1:
                shown = candidates[:5]
                options = "\n".join(
                    [f"- id={c.get('id')} | {c.get('summary')} | start={c.get('start')}" for c in shown]
                )
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "Multiple events match. Reply with the event_id:\n" + options,
                            "observation": "Delete requires disambiguation.",
                        }
                    ),
                    "calendar_result": {"candidates": candidates},
                }

            event_id = candidates[0].get("id")

        delete_payload = {
            "event_id": event_id,
            "calendar_id": payload.get("calendar_id", "primary"),
            "send_updates": payload.get("send_updates"),
        }
        delete_payload = {k: v for k, v in delete_payload.items() if v is not None}

        try:
            tool = self.calendar_tool.deleteEvent()
            result = tool.invoke(delete_payload)

            # ✅ Compute response_text before return
            response_text = f"Deleted event: {event_id}"
            if state.get("is_first_message"):
                response_text = f"Hi, I'm Orion! {response_text}"

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": response_text,
                        "observation": "Calendar event deleted successfully",
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to delete event: {e}",
                        "observation": "Calendar event deletion failed.",
                    }
                )
            }
