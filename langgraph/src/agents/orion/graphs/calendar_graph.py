from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from ..states.calendar_state import GraphState
from ..nodes.calendar_nodes import CalendarNodes

class CalendarWorkflow():
    def __init__(self):
        workflow = StateGraph(GraphState)
        nodes = CalendarNodes()
        checkpointer = InMemorySaver()  
        store = InMemoryStore()  
 
        workflow.add_node("receive_user_query", nodes.receive_user_query)
        workflow.add_node("categorize_user_query", nodes.categorize_user_query)
        workflow.add_node("route_after_categorize", nodes.route_after_categorize)
        workflow.add_node("create_event", nodes.create_event)
        workflow.add_node("create_events_from_study_plan", nodes.create_events_from_study_plan)
        workflow.add_node("send_email_draft", nodes.send_email_draft)
        workflow.add_node("search_event", nodes.search_event)
        workflow.add_node("update_event", nodes.update_event)
        workflow.add_node("delete_event", nodes.delete_event)
        workflow.add_node("generate_recommendations", nodes.generate_recommendations)

        workflow.set_entry_point("receive_user_query")
        workflow.add_edge("receive_user_query", "categorize_user_query")
        workflow.add_edge("categorize_user_query", "route_after_categorize")

        def pick_route(state:GraphState)->str:
            route = state.get("route", "end")

            interaction = state.get("current_interaction")
            query = ""
            if isinstance(interaction, dict):
                query = (interaction.get("user_request", "") or "").lower()
            elif interaction:
                query = (getattr(interaction, "user_request", "") or "").lower()

            if state.get("email_draft_id") and any(k in query for k in ["send the draft", "send draft", "send the email", "send email", "send it"]):
                return "send_email_draft"

            if route == "create_event" and state.get("study_plan"):
                if any(keyword in query for keyword in ["create all", "create events", "add all", "study plan", "schedule plan", "several events", "multiple events"]):
                    return "create_events_from_study_plan"

            return route
        
        workflow.add_conditional_edges(
            "route_after_categorize",
            pick_route,
            {
                "create_event":"create_event",
                "create_events_from_study_plan":"create_events_from_study_plan",
                "send_email_draft":"send_email_draft",
                "search_event":"search_event",
                "update_event":"update_event",
                "delete_event":"delete_event",
                "end" : "generate_recommendations"
            }
        )
        workflow.add_edge("create_event", "generate_recommendations")
        workflow.add_edge("create_events_from_study_plan", "generate_recommendations")
        workflow.add_edge("send_email_draft", "generate_recommendations")
        workflow.add_edge("search_event", "generate_recommendations")
        workflow.add_edge("update_event", "generate_recommendations")
        workflow.add_edge("delete_event", "generate_recommendations")
        workflow.add_edge("generate_recommendations", END)

        self.app = workflow.compile(checkpointer=checkpointer, store=store)

graph = CalendarWorkflow().app
