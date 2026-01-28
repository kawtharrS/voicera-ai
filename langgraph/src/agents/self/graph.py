from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from .state import SelfAgentGraphState
from .nodes import SelfNodes


class SelfWorkflow:
    def __init__(self):
        workflow = StateGraph(SelfAgentGraphState)
        nodes = SelfNodes()
        checkpointer = InMemorySaver()
        store = InMemoryStore()

        workflow.add_node("receive_user_query", nodes.receive_user_query)
        workflow.add_node("run_self_agent", nodes.run_self_agent)
        workflow.add_node("apply_preferences", nodes.apply_preferences)

        workflow.set_entry_point("receive_user_query")

        workflow.add_edge("receive_user_query", "run_self_agent")
        workflow.add_edge("run_self_agent", "apply_preferences")
        workflow.add_edge("apply_preferences", END)

        self.app = workflow.compile(checkpointer=checkpointer, store=store)


graph = SelfWorkflow().app
