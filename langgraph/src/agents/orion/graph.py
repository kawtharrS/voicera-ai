from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from .state import GraphState
from .nodes import CalendarNodes
from .agent import Agent

class CalendarWorkflow():
    def __init__(self):
        workflow = StateGraph(GraphState)
        agent = Agent()
        nodes = CalendarNodes()
        checkpointer = InMemorySaver()  
        store = InMemoryStore()  
 
        workflow.add_node("receive_user_query", nodes.receive_user_query)
        workflow.add_node("categorize_user_query", nodes.categorize_user_query)

        workflow.set_entry_point("receive_user_query")
        workflow.add_edge("receive_user_query", "categorize_user_query")


        self.app = workflow.compile(checkpointer=checkpointer, store=store)

graph = CalendarWorkflow().app


