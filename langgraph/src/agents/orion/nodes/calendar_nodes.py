import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from colorama import Fore, Style
from langchain_openai import ChatOpenAI

from ..states.calendar_state import GraphState, UserInteraction
from tools.calendarTools import CalendarTool
from ..agents.calendar_agent import CalendarAgent

default_tz = "Asia/Beirut"


def _get_reference_dt() -> datetime:
    return datetime.now(ZoneInfo(default_tz))


def _greet_if_first(state: GraphState, text: str) -> str:
    return f"Hi, I'm Orion! {text}" if state.get("is_first_message") else text


class CalendarNodes:
    def __init__(self):
        self.calendar_tool = CalendarTool()
        self.agents = CalendarAgent(self.calendar_tool)

    @staticmethod
    def _get_current_interaction(state: GraphState):
        interaction = state.get("current_interaction")

        if isinstance(interaction, dict):
            return UserInteraction(**interaction), interaction.get("user_request")

        return interaction, getattr(interaction, "user_request")

    def _search_candidates(self, payload: dict):
        calendars_info = self.calendar_tool.getCalendarsInfo().invoke({})
        search_args = {
            "calendars_info": calendars_info,
            "min_datetime": payload.get("target_min_datetime"),
            "max_datetime": payload.get("target_max_datetime"),
            "query": payload.get("target_query"),
            "max_results": payload.get("max_results", 10),
        }
        return self.calendar_tool.searchEvents().invoke(search_args)

    def receive_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Receiving user query ..." + Style.RESET_ALL)

        incoming = state.get("current_interaction")
        request = (
            incoming.get("user_request")
            if isinstance(incoming, dict)
            else getattr(incoming, "user_request", "")
        )

        request = request or state.get("query", "")

        return {
            "current_interaction": UserInteraction(
                user_request=request,
                ai_response="",
                recommendations=[],
            ),
            "is_first_message": state.get("is_first_message", False),
        }

    def categorize_user_query(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Categorizing user query ..." + Style.RESET_ALL)

        interaction, query = self._get_current_interaction(state)
        result = self.agents.categorize_query.invoke({"query": query})
        category = result.category.value

        return {
            "current_interaction": interaction.model_copy(
                update={
                    "ai_response": f"Category: {category}",
                    "observation": f"Query classified as: {category}",
                }
            ),
            "query_category": category,
        }

    def route_after_categorize(self, state: GraphState) -> GraphState:
        routes = {
            "create": "create_event",
            "search": "search_event",
            "update": "update_event",
            "delete": "delete_event",
        }
        category = state.get("query_category")
        return {"route": routes.get(category, "end")}

    def create_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Creating an event ..." + Style.RESET_ALL)

        interaction, query = self._get_current_interaction(state)
        extractor = self.agents.create_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        payload.setdefault("timezone", default_tz)

        if payload.get("start_datetime") and not payload.get("end_datetime"):
            start = datetime.strptime(payload["start_datetime"], "%Y-%m-%d %H:%M:%S")
            payload["end_datetime"] = (start + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.calendar_tool.createEvent().invoke(payload)
            response = _greet_if_first(state, f"Created event: {extractor.summary}")

            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": response,
                        "observation": "Calendar event created successfully",
                    }
                ),
                "calendar_result": result,
            }
        except Exception as e:
            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": f"Failed to create event: {e}",
                        "observation": "Calendar event creation failed.",
                    }
                )
            }

    def search_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Searching for events ..." + Style.RESET_ALL)

        interaction, query = self._get_current_interaction(state)

        try:
            calendars_info = self.calendar_tool.getCalendarsInfo().invoke({})
            extractor = self.agents.search_event_extractor.invoke(
                {
                    "query": query,
                    "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                    "timezone": default_tz,
                }
            )

            payload = extractor.model_dump(exclude_none=True)
            payload["calendars_info"] = calendars_info

            result = self.calendar_tool.searchEvents().invoke(payload)
            count = len(result) if isinstance(result, list) else 0
            response = _greet_if_first(state, f"Found {count} event(s).")

            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": response,
                        "observation": "Calendar events searched successfully",
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": f"Failed to search events: {e}",
                        "observation": "Calendar event search failed.",
                    }
                )
            }

    def update_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Updating an event ..." + Style.RESET_ALL)

        interaction, query = self._get_current_interaction(state)
        extractor = self.agents.update_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        event_id = payload.get("event_id")

        if not event_id or "placeholder" in str(event_id).lower():
            candidates = self._search_candidates(payload)

            if not candidates:
                return {
                    "current_interaction": interaction.model_copy(
                        update={
                            "ai_response": "No matching events found to update.",
                            "observation": "Update failed: no matching events.",
                        }
                    )
                }

            if len(candidates) > 1:
                options = "\n".join(
                    f"- id={c['id']} | {c.get('summary')} | start={c.get('start')}"
                    for c in candidates[:5]
                )
                return {
                    "current_interaction": interaction.model_copy(
                        update={
                            "ai_response": "Multiple events match. Reply with the event_id:\n" + options,
                            "observation": "Update requires disambiguation.",
                        }
                    ),
                    "calendar_result": {"candidates": candidates},
                }

            event_id = candidates[0]["id"]

        update_payload = {
            k: v
            for k, v in {
                "event_id": event_id,
                "calendar_id": payload.get("calendar_id", "primary"),
                "summary": payload.get("new_summary"),
                "start_datetime": payload.get("new_start_datetime"),
                "end_datetime": payload.get("new_end_datetime"),
                "timezone": payload.get("timezone") or default_tz,
                "location": payload.get("new_location"),
                "description": payload.get("new_description"),
                "send_updates": payload.get("send_updates"),
            }.items()
            if v is not None
        }

        try:
            result = self.calendar_tool.updateEvent().invoke(update_payload)
            response = _greet_if_first(state, f"Updated event: {event_id}")

            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": response,
                        "observation": "Calendar event updated successfully",
                    }
                ),
                "calendar_result": result,
            }
        except Exception as e:
            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": f"Failed to update event: {e}",
                        "observation": "Calendar event update failed.",
                    }
                )
            }

    def delete_event(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Deleting an event ..." + Style.RESET_ALL)

        interaction, query = self._get_current_interaction(state)
        extractor = self.agents.delete_event_extractor.invoke(
            {
                "query": query,
                "reference_datetime": _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": default_tz,
            }
        )

        payload = extractor.model_dump(exclude_none=True)
        event_id = payload.get("event_id")

        if not event_id or "placeholder" in str(event_id).lower():
            candidates = self._search_candidates(payload)

            if not candidates:
                return {
                    "current_interaction": interaction.model_copy(
                        update={
                            "ai_response": "No matching events found to delete.",
                            "observation": "Delete failed: no matching events.",
                        }
                    )
                }

            if len(candidates) > 1:
                options = "\n".join(
                    f"- id={c['id']} | {c.get('summary')} | start={c.get('start')}"
                    for c in candidates[:5]
                )
                return {
                    "current_interaction": interaction.model_copy(
                        update={
                            "ai_response": "Multiple events match. Reply with the event_id:\n" + options,
                            "observation": "Delete requires disambiguation.",
                        }
                    ),
                    "calendar_result": {"candidates": candidates},
                }

            event_id = candidates[0]["id"]

        try:
            result = self.calendar_tool.deleteEvent().invoke(
                {
                    "event_id": event_id,
                    "calendar_id": payload.get("calendar_id", "primary"),
                    "send_updates": payload.get("send_updates"),
                }
            )

            response = _greet_if_first(state, f"Deleted event: {event_id}")

            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": response,
                        "observation": "Calendar event deleted successfully",
                    }
                ),
                "calendar_result": result,
            }

        except Exception as e:
            return {
                "current_interaction": interaction.model_copy(
                    update={
                        "ai_response": f"Failed to delete event: {e}",
                        "observation": "Calendar event deletion failed.",
                    }
                )
            }
