from langgraph.graph import END, StateGraph
from .router_state import GraphState
from .router_nodes import RouterNodes
from .router_response_nodes import ResponseNodes
from ..eureka.graph import ClassroomWorkflow


class RouterWorkflow:
    def __init__(self):
        workflow = StateGraph(GraphState)
        router_nodes = RouterNodes()
        response_nodes = ResponseNodes()

        workflow.add_node("router", router_nodes.route_query)
        workflow.add_node("study_agent", ClassroomWorkflow().app)
        workflow.add_node("personal_agent", response_nodes.generate_personal_response)
        workflow.add_node("work_agent", response_nodes.generate_work_response)

        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            lambda x: x["category"],
            {
                "study": "study_agent",
                "personal": "personal_agent",
                "work": "work_agent",
            }
        )
        
        workflow.add_edge("study_agent", END)
        workflow.add_edge("personal_agent", END)
        workflow.add_edge("work_agent", END)
        
        self.app = workflow.compile()

graph = RouterWorkflow().app
