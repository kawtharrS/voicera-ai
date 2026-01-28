from agents.graph import END, StateGraph
from agents.checkpoint.memory import InMemorySaver
from agents.store.memory import InMemoryStore
from .state import GraphState
from .nodes import ClassroomNodes


class ClassroomWorkflow():
    def __init__(self):
        workflow = StateGraph(GraphState)
        nodes = ClassroomNodes()
        checkpointer = InMemorySaver()
        store = InMemoryStore()

        workflow.add_node("load_courses", nodes.load_courses)
        workflow.add_node("load_coursework", nodes.load_coursework)
        workflow.add_node("load_and_index_materials", nodes.load_and_index_materials)
        workflow.add_node("retrieve_memory", nodes.retrieve_memory)
        workflow.add_node("receive_student_query", nodes.receive_student_query)
        workflow.add_node("categorize_query", nodes.categorize_student_query)
        workflow.add_node("construct_rag_queries", nodes.construct_rag_queries)
        workflow.add_node("generate_ai_response", nodes.generate_ai_response)
        workflow.add_node("verify_ai_response", nodes.verify_ai_response)
        workflow.add_node("generate_study_plan", nodes.generate_study_plan)
        workflow.add_node("save_to_langmem", nodes.save_to_langmem)

        workflow.set_entry_point("load_courses")

        workflow.add_edge("load_courses", "load_coursework")
        workflow.add_edge("load_coursework", "load_and_index_materials")
        workflow.add_edge("load_and_index_materials", "retrieve_memory")
        workflow.add_edge("retrieve_memory", "receive_student_query")
        workflow.add_edge("receive_student_query", "categorize_query")
        workflow.add_edge("categorize_query", "construct_rag_queries")
        workflow.add_edge("construct_rag_queries", "generate_ai_response")
        workflow.add_edge("generate_ai_response", "verify_ai_response")

        workflow.add_conditional_edges(
            "verify_ai_response",
            nodes.finalize_response,
            {
                "end": "generate_study_plan",
                "rewrite": "generate_ai_response",
            },
        )

        workflow.add_edge("generate_study_plan", "save_to_langmem")
        workflow.add_edge("save_to_langmem", END)

        self.app = workflow.compile(checkpointer=checkpointer, store=store)


graph = ClassroomWorkflow().app
