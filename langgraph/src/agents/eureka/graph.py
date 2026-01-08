from langgraph.graph import END, StateGraph
from .state import GraphState
from .nodes import ClassroomNodes
from .memory import MemoryHandlers
from .agent import Agent


class ClassroomWorkflow():
    def __init__(self):
        workflow = StateGraph(GraphState)
        agent = Agent()
        nodes = ClassroomNodes()
        memory = MemoryHandlers(agent)

        workflow.add_node("load_courses", nodes.load_courses)
        workflow.add_node("load_coursework", nodes.load_coursework)
        workflow.add_node("load_and_index_materials", nodes.load_and_index_materials)
        workflow.add_node("receive_student_query", memory.receive_query_with_memory)  # Use memory handler
        workflow.add_node("categorize_query", memory.categorize_with_memory)  # Use memory handler
        workflow.add_node("construct_rag_queries", nodes.construct_rag_queries)
        workflow.add_node("generate_ai_response", nodes.generate_ai_response)
        workflow.add_node("verify_ai_response", nodes.verify_ai_response)
        workflow.add_node("finalize_response", nodes.finalize_response)

        workflow.set_entry_point("load_courses")

        workflow.add_edge("load_courses", "load_coursework")
        workflow.add_edge("load_coursework", "load_and_index_materials")
        workflow.add_edge("load_and_index_materials", "receive_student_query")
        workflow.add_edge("receive_student_query", "categorize_query")
        workflow.add_edge("categorize_query", "construct_rag_queries")
        workflow.add_edge("construct_rag_queries", "generate_ai_response")
        workflow.add_edge("generate_ai_response", "verify_ai_response")

        workflow.add_conditional_edges(
            "verify_ai_response",
            nodes.finalize_response,
            {
                "end": END,         
                "rewrite": "generate_ai_response"  
            }
        )

        self.app = workflow.compile()


graph = ClassroomWorkflow().app
