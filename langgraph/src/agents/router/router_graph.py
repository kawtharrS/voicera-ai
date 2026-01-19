from langgraph.graph import END, StateGraph
from .router_state import GraphState
from .router_nodes import RouterNodes
from .router_response_nodes import ResponseNodes
from ..eureka.graph import ClassroomWorkflow
from ..orion.orion_router.orion_graph import graph as orion_graph
from ..self.graph import SelfWorkflow
from ..aria.agents.agent import EmotionAgent

class RouterWorkflow:
    def __init__(self):
        workflow = StateGraph(GraphState)
        router_nodes = RouterNodes()
        response_nodes = ResponseNodes(emotion_agent=EmotionAgent())

        workflow.add_node("router", router_nodes.route_query)
        workflow.add_node("study_agent", ClassroomWorkflow().app)
        # Route personal queries to the full personal assistant, which will
        # internally detect and attach emotion without changing the tone.
        workflow.add_node("personal_agent", response_nodes.generate_personal_response)
        workflow.add_node("work_agent", orion_graph)
        workflow.add_node('setting_agent', SelfWorkflow().app)
        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            lambda x: x["category"],
            {
                "study": "study_agent",
                "personal": "personal_agent",
                "work": "work_agent",
                "setting": "setting_agent",
            }
        )
        
        workflow.add_edge("study_agent", END)
        workflow.add_edge("personal_agent", END)
        workflow.add_edge("work_agent", END)
        workflow.add_edge("setting_agent", END)
        
        self.app = workflow.compile()

graph = RouterWorkflow().app
