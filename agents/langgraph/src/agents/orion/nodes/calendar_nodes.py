import os
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from colorama import Fore, Style
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..states.calendar_state import GraphState, UserInteraction
from ..structure_outputs.calendar_structure_output import CategorizeQueryOutput, CreateEventArgs
from prompts.calendar import CATEGORIZE_QUERY_PROMPT
from tools.calendarTools import CalendarTool
from tools.gmailTools import GmailTool
from ..agents.calendar_agent import CalendarAgent
from ...shared_memory import shared_memory

openai_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key = os.getenv("OPENAI_API_KEY")
)
default_tz = "Asia/Beirut"


def _get_reference_dt():
    """Return current datetime in default timezone (computed fresh each call)."""
    return datetime.now(ZoneInfo(default_tz))

def _remove_links_from_response(response: str) -> str:
    """Remove any URLs, links, or HTML links from the response."""
    response = re.sub(r'https?://\S+', '', response)
    response = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', response)
    response = re.sub(r'<[^>]+>', '', response)
    response = re.sub(r'\s+', ' ', response).strip()
    return response


class CalendarNodes:
    def __init__(self):
        self.calendar_tool = CalendarTool()
        self.gmail_tool = GmailTool()
        self.agents = CalendarAgent(self.calendar_tool)

    def _send_notification_email(self, action: str, details: str):
        """Helper to send a notification email when a calendar event is modified."""
        try:
            user_email = self.gmail_tool.get_my_email()
            if not user_email:
                print(Fore.RED + "Could not fetch user email for notification" + Style.RESET_ALL)
                return
            
            subject = f"Calendar Notification: Event {action.capitalize()}d"
            body = f"An event has been {action}d in your calendar.\n\nDetails:\n{details}\n\nBest regards,\nVoicera AI"
            
            self.gmail_tool.send_message(to=user_email, subject=subject, body=body)
            print(Fore.GREEN + f"Notification email sent to {user_email}" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Error sending notification email: {e}" + Style.RESET_ALL)

    def send_email_draft(self, state: GraphState) -> GraphState:
        """Send the previously created Gmail draft (if any)."""
        print(Fore.YELLOW + "Sending email draft..." + Style.RESET_ALL)

        interaction_model, _ = self._get_current_interaction(state)
        draft_id = state.get("email_draft_id")
        if not draft_id:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": "No email draft found to send. Please create a study-plan email summary first.",
                        "observation": "No email draft id in state.",
                    }
                )
            }

        try:
            gmail = GmailTool()
            ok = gmail.send_draft(draft_id)
            if ok:
                return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "Sent the email draft.",
                            "observation": "Email draft sent successfully.",
                        }
                    ),
                    "email_draft_id": None,
                    "calendar_result": {"email_sent": True},
                }
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": "Failed to send the email draft.",
                        "observation": "Email draft send failed.",
                    }
                )
            }
        except Exception as e:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to send the email draft: {e}",
                        "observation": "Email draft send error.",
                    }
                )
            }


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
            )
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
        interaction = state.get("current_interaction")
        q = ""
        if isinstance(interaction, dict):
            q = (interaction.get("user_request") or "").lower()
        elif interaction is not None:
            q = (getattr(interaction, "user_request", "") or "").lower()
        if state.get("email_draft_id") and any(k in q for k in ["send the email", "send draft", "send the draft", "send it", "send the summary email"]):
            return {"route": "send_email_draft"}

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
        tool =self.calendar_tool.createEvent()

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
            
            query_info = f"User asked: {query}\nAction: Create Event\nResult Data: {json.dumps(result, indent=2) if isinstance(result, dict) else result}"
            formatted_response = self.agents.ai_response_generator.invoke({
                "query_information": query_info,
                "history": []
            })

            self._send_notification_email("create", f"Summary: {extractor.summary}\nStart: {payload.get('start_datetime')}\nEnd: {payload.get('end_datetime')}")

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": _remove_links_from_response(formatted_response.response),
                        "observation": f"Calendar event created and formatted response: {extractor.summary}"
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
            count = len(result) if isinstance(result, list) else 0
            
            query_info = f"User asked: {query}\nCalendar Search Results: {json.dumps(result, indent=2)}"
            formatted_response = self.agents.ai_response_generator.invoke({
                "query_information": query_info,
                "history": []
            })

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": _remove_links_from_response(formatted_response.response),
                        "observation": f"Found {count} event(s) and formatted response.",
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
                options = "\n".join([f"- id={c.get('id')} | {c.get('summary')} | start={c.get('start')}" for c in shown])
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
            
            query_info = f"User asked: {query}\nAction: Update Event\nEvent ID: {event_id}\nResult Data: {json.dumps(result, indent=2) if isinstance(result, dict) else result}"
            formatted_response = self.agents.ai_response_generator.invoke({
                "query_information": query_info,
                "history": []
            })

            self._send_notification_email("update", f"Event ID: {event_id}\nNew Summary: {update_payload.get('summary') or 'Unchanged'}\nNew Start: {update_payload.get('start_datetime') or 'Unchanged'}")

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": formatted_response.response,
                        "observation": "Calendar event updated and formatted successfully",
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
                options = "\n".join([f"- id={c.get('id')} | {c.get('summary')} | start={c.get('start')}" for c in shown])
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
            
            query_info = f"User asked: {query}\nAction: Delete Event\nEvent ID: {event_id}\nResult Data: {result}"
            formatted_response = self.agents.ai_response_generator.invoke({
                "query_information": query_info,
                "history": []
            })

            self._send_notification_email("delete", f"Event ID: {event_id}\nAction: Deleted because of user request: {query}")

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": formatted_response.response,
                        "observation": "Calendar event deleted and formatted successfully",
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

    def create_events_from_study_plan(self, state: GraphState) -> GraphState:
        """Create multiple calendar events from a structured study plan."""
        print(Fore.YELLOW + "Creating events from study plan..." + Style.RESET_ALL)
        
        interaction_model, query = self._get_current_interaction(state)
        study_plan = state.get("study_plan")
        
        if not study_plan:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": "No study plan found. Please ask for a study plan first.",
                        "observation": "Study plan missing.",
                    }
                )
            }
        
        slots = []
        if isinstance(study_plan, dict):
            slots = study_plan.get("slots", [])
        elif hasattr(study_plan, 'slots'):
            slots = study_plan.slots
        
        if not slots:
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": "Study plan has no time slots.",
                        "observation": "No slots in study plan.",
                    }
                )
            }
        
        try:
            tool = self.calendar_tool.createEvent()
            created_events = []
            ref_dt = _get_reference_dt()
            
            day_offsets = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            }
            
            current_weekday = ref_dt.weekday()  
            
            slots = study_plan.get("slots") if isinstance(study_plan, dict) else getattr(study_plan, "slots", [])
            
            if not slots:
                 return {
                    "current_interaction": interaction_model.model_copy(
                        update={
                            "ai_response": "The study plan doesn't have any scheduled slots.",
                            "observation": "Study plan slots missing.",
                        }
                    )
                }

            for slot_data in slots:
                if isinstance(slot_data, dict):
                    day = slot_data.get("day")
                    start_time_str = slot_data.get("start_time")
                    end_time_str = slot_data.get("end_time")
                    activity = slot_data.get("activity")
                else:
                    day = slot_data.day
                    start_time_str = slot_data.start_time
                    end_time_str = slot_data.end_time
                    activity = slot_data.activity

                target_weekday = day_offsets.get(day, 0)
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7  
                
                slot_date = ref_dt + timedelta(days=days_ahead)
                
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
                
                start_dt = datetime.combine(slot_date.date(), start_time)
                end_dt = datetime.combine(slot_date.date(), end_time)
                
                event_payload = {
                    "summary": activity,
                    "start_datetime": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_datetime": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "timezone": default_tz,
                }
                
                result = tool.invoke(event_payload)
                created_events.append(f"{day} {start_time_str}-{end_time_str}: {activity}")
                print(Fore.GREEN + f"Created event: {activity}" + Style.RESET_ALL)
            
            summary_text = f"Created {len(created_events)} calendar events from your study plan:\n" + "\n".join(created_events)

            q = (query or "").lower()
            draft_id = None
            if any(k in q for k in ["email", "gmail", "mail", "email me", "email a summary", "summary email", "then email"]):
                try:
                    gmail = GmailTool()
                    to_addr = gmail.get_my_email()
                    subject = "Your study plan schedule"
                    body = summary_text
                    draft_id = gmail.create_draft_message(to=to_addr, subject=subject, body=body)
                except Exception as e:
                    print(Fore.RED + f"Failed to create email draft: {e}" + Style.RESET_ALL)
                    draft_id = None

            final_text = summary_text
            if draft_id:
                final_text += "\n\nI created a Gmail draft with this schedule summary. Say: 'send the draft' to send it."

            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": final_text,
                        "observation": f"Successfully created {len(created_events)} events." + (" Created email draft." if draft_id else ""),
                    }
                ),
                "calendar_result": {"created": created_events, "email_draft_id": draft_id},
                "email_draft_id": draft_id or state.get("email_draft_id"),
            }
        except Exception as e:
            print(Fore.RED + f"Error creating events: {e}" + Style.RESET_ALL)
            return {
                "current_interaction": interaction_model.model_copy(
                    update={
                        "ai_response": f"Failed to create calendar events: {e}",
                        "observation": "Event creation failed.",
                    }
                )
            }

    async def generate_recommendations(self, state: GraphState) -> GraphState:
        print(Fore.YELLOW + "Generating proactive recommendations..." + Style.RESET_ALL)
        
        interaction_model, query = self._get_current_interaction(state)
        student_id = state.get("student_id")
        
        memories = ""
        if student_id:
            memories = await shared_memory.retrieve(student_id, query)
        
        current_time = _get_reference_dt().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            result = self.agents.recommendation_generator.invoke({
                "query": query,
                "current_time": current_time,
                "memories": memories or "No specific patterns found yet.",
            })
            recommendations = result.recommendations
            print(Fore.GREEN + f"Generated {len(recommendations)} recommendations" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Recommendation error: {e}" + Style.RESET_ALL)
            recommendations = []
            
        return {
            "current_interaction": interaction_model.model_copy(
                update={
                    "recommendations": recommendations,
                }
            )
        }
