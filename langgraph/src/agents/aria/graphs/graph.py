from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from ..states.state import EmotionDetectionState
from ..nodes.nodes import EmotionDetectionNodes


class EmotionDetectionWorkflow:
    def __init__(self):
        workflow = StateGraph(EmotionDetectionState)
        nodes = EmotionDetectionNodes()
        checkpointer = InMemorySaver()
        store = InMemoryStore()

        workflow.add_node("receive_text", nodes.receive_text)
        workflow.add_node("detect_emotion", nodes.detect_emotion)
        workflow.add_node("track_emotion", nodes.track_emotion_history)
        workflow.add_node("continue_chat", nodes.continue_chat)

        workflow.set_entry_point("receive_text")

        workflow.add_edge("receive_text", "detect_emotion")
        workflow.add_edge("detect_emotion", "track_emotion")
        workflow.add_edge("track_emotion", "continue_chat")
        workflow.add_edge("continue_chat", END)

        self.app = workflow.compile(checkpointer=checkpointer, store=store)


graph = EmotionDetectionWorkflow().app