from langgraph.graph import END, StateGraph
from .router_state import GraphState
from .router_nodes import RouterNodes

class RouterWorkflow:
    def __init__(self):
        workflow = StateGraph(GraphState)
        nodes = RouterNodes()

        workflow.add_node("router", nodes.route_query)
        workflow.set_entry_point("router")
        
        workflow.add_edge("router", END)
        
        self.app = workflow.compile()

graph = RouterWorkflow().app
