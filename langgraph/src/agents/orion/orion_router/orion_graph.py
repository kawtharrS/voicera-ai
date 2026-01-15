from langgraph.graph import END, StateGraph 
from .orion_states import GraphState
from .orion_nodes import RouterNodes
from ..graphs.calendar_graph import CalendarWorkflow 
from ..graphs.gmail_graph import GmailWorkflow

class RouterWorkflow:
    def __init__(self):
        workflow = StateGraph(GraphState)
        router_nodes = RouterNodes()

        workflow.add_node("orion_router", router_nodes.route_query)
        workflow.add_node("gmail_router",GmailWorkflow().app)
        workflow.add_node("calendar_router",CalendarWorkflow().app)

        workflow.set_entry_point("orion_router")

        workflow.add_conditional_edges(
            "orion_router",
            lambda x:x["category"],
            {
                "gmail":"gmail_agent",
                "calendar":"calendar_agent"
            }
        )

        workflow.add_edge("gmail_edge", END)
        workflow.add_edge("calendar_agent", END)

        self.app = workflow.compile()

graph = RouterWorkflow().app
        