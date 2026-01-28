from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from ..states.gmail_state import GraphState
from ..nodes.gmail_nodes import GmailNodes


class GmailWorkflow():
    def __init__(self):
        workflow = StateGraph(GraphState)
        nodes = GmailNodes()
        checkpointer = InMemorySaver()  
        store = InMemoryStore()  
 
        workflow.add_node("load_emails", nodes.load_emails)
        workflow.add_node("categorize_email", nodes.categorize_email)
        workflow.add_node("construct_rag_queries", nodes.construct_rag_queries)
        workflow.add_node("retrieve_from_rag", nodes.retrieve_from_rag)
        workflow.add_node("write_draft_email", nodes.write_draft_email)
        workflow.add_node("verify_email", nodes.verify_email)
        workflow.add_node("ask_confirmation", nodes.ask_confirmation)
        workflow.add_node("send_email", nodes.send_email)
        workflow.add_node("create_draft", nodes.create_draft)
        workflow.add_node("skip_email", nodes.skip_email)
        workflow.add_node("send_all_drafts", nodes.send_all_drafts)
        workflow.add_node("retrieve_drafts", nodes.retrieve_drafts)
        workflow.add_node("extract_details", nodes.extract_new_details)
        workflow.add_node("send_new_email", nodes.send_new_email)

        workflow.set_entry_point("load_emails")

        def check_inbox_condition(state: GraphState) -> str:
            if state.get("retrieving_drafts"):
                return "retrieve_drafts"
            if state.get("sending_drafts"):
                return "send_drafts"
            if state.get("sending_new_email"):
                return "extract_details"
            emails = state.get("emails", [])
            return "categorize" if emails else "end"

        workflow.add_conditional_edges(
            "load_emails",
            check_inbox_condition,
            {
                "categorize": "categorize_email",
                "send_drafts": "send_all_drafts",
                "retrieve_drafts": "retrieve_drafts",
                "extract_details": "extract_details",
                "end": END
            }
        )

        def route_by_category(state: GraphState) -> str:
            category = state.get("email_category")
            if category is None:
                return END
            if category == "study":
                return "construct_rag_queries"
            elif category in ["work", "general"]:
                return "write_draft_email"
            else:
                return "skip_email"

        workflow.add_conditional_edges(
            "categorize_email",
            route_by_category,
            {
                "construct_rag_queries": "construct_rag_queries",
                "write_draft_email": "write_draft_email",
                "skip_email": "skip_email",
                END: END
            }
        )

        workflow.add_edge("construct_rag_queries", "retrieve_from_rag")
        workflow.add_edge("retrieve_from_rag", "write_draft_email")

        workflow.add_edge("write_draft_email", "verify_email")

        def should_rewrite(state: GraphState) -> str:
            sendable = state.get("sendable", False)
            trials = state.get("trials", 0)
            max_trials = 3
            
            if sendable:
                return "ask_confirmation"
            elif trials < max_trials:
                return "rewrite"
            else:
                return "flag_human_review"

        workflow.add_conditional_edges(
            "verify_email",
            should_rewrite,
            {
                "ask_confirmation": "ask_confirmation",
                "rewrite": "write_draft_email",
                "flag_human_review": "create_draft"
            }
        )

        def user_confirmed(state: GraphState) -> str:
            user_approved = state.get("user_approved", False)
            if user_approved:
                if state.get("new_email_details"):
                    return "send_new"
                return "send_reply"
            return "draft"

        workflow.add_conditional_edges(
            "ask_confirmation",
            user_confirmed,
            {
                "send_new": "send_new_email",
                "send_reply": "send_email",
                "draft": "create_draft"
            }
        )


        workflow.add_edge("extract_details", "ask_confirmation")
        workflow.add_edge("send_new_email", END)

        def has_more_emails(state: GraphState) -> str:
            emails = state.get("emails", [])
            return "continue" if emails else "end"

        workflow.add_conditional_edges(
            "send_email",
            has_more_emails,
            {
                "continue": "categorize_email",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "create_draft",
            has_more_emails,
            {
                "continue": "categorize_email",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "skip_email",
            has_more_emails,
            {
                "continue": "categorize_email",
                "end": END
            }
        )
        
        workflow.add_edge("send_all_drafts", END)
        workflow.add_edge("retrieve_drafts", END)

        self.app = workflow.compile(checkpointer=checkpointer, store=store)


graph = GmailWorkflow().app
