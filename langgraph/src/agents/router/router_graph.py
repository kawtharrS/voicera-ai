from langgraph.graph import END, StateGraph
from .router_state import GraphState
from .router_nodes import RouterNodes
from ..eureka.graph import ClassroomWorkflow


class RouterWorkflow:
    def __init__(self):
        workflow = StateGraph(GraphState)
        nodes = RouterNodes()

        workflow.add_node("router", nodes.route_query)
        workflow.add_node("study_agent", ClassroomWorkflow().app)

        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            lambda x: x["category"],
            {
                "study": "study_agent",
                "personal": END, # Placeholder for now
                "work": END,     # Placeholder for now
            }
        )
        
        workflow.add_edge("study_agent", END)
        
        self.app = workflow.compile()

graph = RouterWorkflow().app
