import os
from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from ..states.gmail_state import GraphState, Email, EmailInteraction
from ..structure_outputs.gmail_structure_output import CategorizeEmailOutput
from prompts.gmail import CATEGORIZE_EMAIL_PROMPT
from tools.gmailTools import GmailTool
from ..agents.gmail_agent import GmailAgent
from ...model import Model

model = Model()

class GmailNodes:
    def __init__(self):
        self.gmail_tool = GmailTool()
        self.agents = GmailAgent(self.gmail_tool)

    def _build_email_writer_input(self, state: GraphState, current_email: Email, prefs: dict) -> str:
        """Constructs the email writer input including user preferences."""
        language = prefs.get("language") or "English"
        tone = prefs.get("tone") or "professional"
        agent_name = prefs.get("name") or "your assistant"
        extra = prefs.get("preference") or ""

        extra_line = f"\n- Additional notes: {extra}" if extra else ""
        prefs_block = (
            "\n\nUSER PREFERENCES:\n"
            f"- Preferred language: {language}\n"
            f"- Preferred tone: {tone}\n"
            f"- Agent name: {agent_name}"
            f"{extra_line}\n"
        )

        base = f"Category: {state.get('email_category')}\n\nEmail:\nSubject: {current_email.subject}\n\n{current_email.body}\n\nRetrieved Information:\n{state.get('retrieved_documents', '')}"
        return base + prefs_block

    def load_emails(self, state: GraphState) -> GraphState:
        """Load unanswered emails from Gmail inbox."""
        print(Fore.YELLOW + "Loading emails from inbox..." + Style.RESET_ALL)
        try:
            unanswered_emails = self.gmail_tool.fetch_unanswered_emails(max_results=10)
            emails = [
                Email(
                    id=email.get("id"),
                    thread_id=email.get("threadId"),
                    message_id=email.get("messageId"),
                    sender=email.get("sender"),
                    subject=email.get("subject"),
                    body=email.get("body")
                )
                for email in unanswered_emails
            ]
            print(Fore.GREEN + f"Loaded {len(emails)} unanswered email(s)" + Style.RESET_ALL)
            return {
                "emails": emails,
                "is_processing": len(emails) > 0
            }
        except Exception as e:
            print(Fore.RED + f"Error loading emails: {e}" + Style.RESET_ALL)
            return {
                "emails": [],
                "is_processing": False
            }

    def check_inbox_empty(self, state: GraphState) -> str:
        """Check if there are emails to process."""
        emails = state.get("emails", [])
        return "process" if emails else "empty"

    def categorize_email(self, state: GraphState) -> GraphState:
        """Categorize the current email."""
        print(Fore.YELLOW + "Categorizing email..." + Style.RESET_ALL)
        
        emails = state.get("emails", [])
        
        if not emails:
            print(Fore.GREEN + "All emails processed!" + Style.RESET_ALL)
            return {
                "email_category": None,
                "current_email": None
            }
        current_email = emails[-1] if emails else None
        if not current_email:
            return {"email_category": "unrelated"}

        try:
            result = self.agents.categorize_email.invoke({
                "email": f"Subject: {current_email.subject}\n\n{current_email.body}"
            })
            category = result.category.value
            print(Fore.GREEN + f"Email category: {category}" + Style.RESET_ALL)
            
            return {
                "current_email": current_email,
                "email_category": category,
                "current_interaction": EmailInteraction(email=current_email, category=category)
            }
        except Exception as e:
            print(Fore.RED + f"Error categorizing email: {e}" + Style.RESET_ALL)
            return {
                "current_email": current_email,
                "email_category": "unrelated"
            }

    def route_by_category(self, state: GraphState) -> str:
        """Route email based on category."""
        category = state.get("email_category")
        if category == "study":
            return "construct_rag_queries"
        elif category in ["work", "general"]:
            return "write_draft_email"
        else:
            return "skip_email"

    def construct_rag_queries(self, state: GraphState) -> GraphState:
        """Construct RAG queries for product inquiries."""
        print(Fore.YELLOW + "Constructing RAG queries..." + Style.RESET_ALL)
        current_email = state.get("current_email")
        if not current_email:
            return {"rag_queries": []}
        try:
            result = self.agents.design_rag_queries.invoke({
                "email": f"Subject: {current_email.subject}\n\n{current_email.body}"
            })
            print(Fore.GREEN + f"Generated {len(result.queries)} RAG queries" + Style.RESET_ALL)
            return {"rag_queries": result.queries}
        except Exception as e:
            print(Fore.RED + f"Error constructing RAG queries: {e}" + Style.RESET_ALL)
            return {"rag_queries": []}

    def retrieve_from_rag(self, state: GraphState) -> GraphState:
        """Retrieve information from RAG for each query."""
        print(Fore.YELLOW + "Retrieving information from RAG..." + Style.RESET_ALL)
        
        queries = state.get("rag_queries", [])
        if not queries:
            return {"retrieved_documents": ""}

        try:
            final_answer = ""
            for query in queries:
                results = self.agents.vectorstore.similarity_search(query, k=3)
                context = "\n".join([doc.page_content for doc in results])
                
                rag_result = self.agents.generate_rag_answer.invoke({
                    "question": query,
                    "context": context
                })
                final_answer += f"Q: {query}\nA: {rag_result.answer}\n\n"
            
            print(Fore.GREEN + "RAG retrieval complete" + Style.RESET_ALL)
            return {"retrieved_documents": final_answer}
        except Exception as e:
            print(Fore.RED + f"Error retrieving from RAG: {e}" + Style.RESET_ALL)
            return {"retrieved_documents": ""}

    def write_draft_email(self, state: GraphState) -> GraphState:
        """Write draft email response."""
        print(Fore.YELLOW + "Writing draft email..." + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        if not current_email:
            return {"generated_email": "", "trials": state.get("trials", 0) + 1}

        prefs = state.get("user_preferences") or {}

        try:
            writer_messages = state.get("writer_messages", [])
            
            draft_result = self.agents.email_writer.invoke({
                "email_content": self._build_email_writer_input(state, current_email, prefs),
                "history": writer_messages
            })
            
            email = draft_result.email
            trials = state.get("trials", 0) + 1
            writer_messages.append(f"**Draft {trials}:**\n{email}")
            
            print(Fore.GREEN + f"Draft email written (attempt {trials})" + Style.RESET_ALL)
            return {
                "generated_email": email,
                "trials": trials,
                "writer_messages": writer_messages
            }
        except Exception as e:
            print(Fore.RED + f"Error writing draft: {e}" + Style.RESET_ALL)
            return {
                "generated_email": "",
                "trials": state.get("trials", 0) + 1
            }

    def verify_email(self, state: GraphState) -> GraphState:
        """Verify generated email with proofreader agent."""
        print(Fore.YELLOW + "Verifying email quality..." + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        generated_email = state.get("generated_email", "")
        
        if not current_email or not generated_email:
            return {"sendable": False}

        try:
            review = self.agents.email_proofreader.invoke({
                "initial_email": f"Subject: {current_email.subject}\n\n{current_email.body}",
                "generated_email": generated_email
            })
            
            sendable = review.send
            
            if not sendable:
                writer_messages = state.get("writer_messages", [])
                writer_messages.append(f"**Proofreader Feedback:**\n{review.feedback}")
                print(Fore.YELLOW + f"Email needs revision: {review.feedback}" + Style.RESET_ALL)
                return {
                    "sendable": False,
                    "writer_messages": writer_messages
                }
            else:
                print(Fore.GREEN + "Email verified and ready to send" + Style.RESET_ALL)
                return {"sendable": True}
                
        except Exception as e:
            print(Fore.RED + f"Error verifying email: {e}" + Style.RESET_ALL)
            return {"sendable": False}

    def ask_confirmation(self, state: GraphState) -> GraphState:
        """Ask user for confirmation before sending (or auto-approve based on flag)."""
        user_approved = state.get("user_approved", False)
        
        current_email = state.get("current_email")
        generated_email = state.get("generated_email", "")
        
        print(Fore.YELLOW + f"Processing: {current_email.subject if current_email else 'Unknown'}" + Style.RESET_ALL)
        if user_approved:
            print(Fore.GREEN + "Auto-sending email" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "Creating draft for review" + Style.RESET_ALL)
        
        return {"user_approved": user_approved}

    def should_rewrite(self, state: GraphState) -> str:
        """Check if email should be rewritten or sent."""
        sendable = state.get("sendable", False)
        trials = state.get("trials", 0)
        max_trials = 3
        
        if sendable:
            return "send"
        elif trials < max_trials:
            print(Fore.YELLOW + f"Rewriting email (attempt {trials}/{max_trials})" + Style.RESET_ALL)
            return "rewrite"
        else:
            print(Fore.YELLOW + "Max rewrite attempts reached, flagging for human review" + Style.RESET_ALL)
            return "flag_human_review"

    def send_email(self, state: GraphState) -> GraphState:
        """Send the verified email."""
        print(Fore.YELLOW + "Sending email..." + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        generated_email = state.get("generated_email", "")
        
        if not current_email or not generated_email:
            return {"retrieved_documents": "", "trials": 0}

        try:
            email_dict = {
                "id": current_email.id,
                "threadId": current_email.thread_id,
                "messageId": current_email.message_id,
                "sender": current_email.sender,
                "subject": current_email.subject,
                "body": current_email.body
            }
            self.gmail_tool.send_reply(email_dict, generated_email)
            print(Fore.GREEN + "Email sent successfully" + Style.RESET_ALL)
            
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "generated_email": "",
                "trials": 0,
                "email_category": None,
                "rag_queries": [],
                "sendable": False
            }
        except Exception as e:
            print(Fore.RED + f"Error sending email: {e}" + Style.RESET_ALL)
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "trials": 0
            }

    def create_draft(self, state: GraphState) -> GraphState:
        """Create draft for human review."""
        print(Fore.YELLOW + "Creating draft for human review..." + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        generated_email = state.get("generated_email", "")
        
        if not current_email or not generated_email:
            return {"retrieved_documents": "", "trials": 0}

        try:
            email_dict = {
                "id": current_email.id,
                "threadId": current_email.thread_id,
                "messageId": current_email.message_id,
                "sender": current_email.sender,
                "subject": current_email.subject,
                "body": current_email.body
            }
            self.gmail_tool.create_draft_reply(email_dict, generated_email)
            print(Fore.GREEN + "Draft created for review" + Style.RESET_ALL)
            
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "generated_email": "",
                "trials": 0,
                "email_category": None,
                "rag_queries": [],
                "sendable": False
            }
        except Exception as e:
            print(Fore.RED + f"Error creating draft: {e}" + Style.RESET_ALL)
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "trials": 0
            }

    def skip_email(self, state: GraphState) -> GraphState:
        """Skip unrelated email."""
        print(Fore.YELLOW + "Skipping unrelated email" + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        
        emails = state.get("emails", [])
        remaining_emails = [e for e in emails if e.id != current_email.id]
        
        return {
            "emails": remaining_emails,
            "current_email": None,
            "retrieved_documents": "",
            "generated_email": "",
            "trials": 0,
            "email_category": None,
            "rag_queries": [],
            "sendable": False
        }
