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
        """Constructs the email writer input including user preferences and specific query instructions."""
        language = prefs.get("language") or "English"
        tone = prefs.get("tone") or "professional"
        agent_name = prefs.get("name") or "your assistant"
        extra = prefs.get("preference") or ""
        
        user_query = state.get("query", "")

        extra_line = f"\n- Additional notes: {extra}" if extra else ""
        prefs_block = (
            "\n\nUSER PREFERENCES:\n"
            f"- Preferred language: {language}\n"
            f"- Preferred tone: {tone}\n"
            f"- Agent name: {agent_name}"
            f"{extra_line}\n"
        )
        
        instruction_block = f"\n\nUSER SPECIFIC INSTRUCTION FOR THIS EMAIL:\n{user_query}\n" if user_query else ""

        base = f"Category: {state.get('email_category')}\n\nEmail:\nSubject: {current_email.subject}\n\n{current_email.body}\n\nRetrieved Information:\n{state.get('retrieved_documents', '')}"
        return base + instruction_block + prefs_block

    def load_emails(self, state: GraphState) -> GraphState:
        """Load unanswered emails from Gmail inbox or send/retrieve existing drafts."""
        query = state.get("query", "").lower()
        print(Fore.CYAN + f"[load_emails] Received query: '{query}'" + Style.RESET_ALL)
        
        retrieve_keywords = ["show drafts", "list drafts", "what drafts", "get drafts", "my drafts", "see drafts"]
        if any(k in query for k in retrieve_keywords):
            print(Fore.YELLOW + "User requesting to retrieve drafts..." + Style.RESET_ALL)
            return {
                "emails": [],
                "is_processing": False,
                "retrieving_drafts": True,
                "ai_response": "Retrieving your drafts...",
                "current_interaction": EmailInteraction(ai_response="Retrieving your drafts...")
            }
        
        has_send_draft_keyword = "send draft" in query or "send the draft" in query
        
        if has_send_draft_keyword:
            print(Fore.YELLOW + "User requesting to send existing draft(s)..." + Style.RESET_ALL)
            return {
                "emails": [],
                "is_processing": False,
                "sending_drafts": True,
                "ai_response": "Sending your drafted email replies...",
                "current_interaction": EmailInteraction(ai_response="Sending your drafted email replies...")
            }
        
        is_specific_reply = any(k in query for k in ["reply", "respond", "email to", "email from", "email for"])
        
        # Check if user wants to send a completely NEW email
        send_to_keywords = ["send an email to", "send email to", "message to", "write to", "send an email for", "send email for", "email to", "send to", "mail to"]
        is_new_email_request = any(k in query for k in send_to_keywords)
        has_email_address = "@" in query
        is_sending_verb = any(v in query for v in ["send", "write", "draft", "prepare", "compose"])
        
        if is_new_email_request or (has_email_address and is_sending_verb):
            print(Fore.YELLOW + "User requesting to send a new email..." + Style.RESET_ALL)
            return {
                "emails": [],
                "is_processing": True,
                "sending_new_email": True,
                "ai_response": "Extracting details for your new email...",
                "current_interaction": EmailInteraction(ai_response="Extracting details for your new email...")
            }

        is_empty_query = not query or query.strip() == ""
        
        print(Fore.YELLOW + f"Loading emails from inbox (inclusive={is_specific_reply})..." + Style.RESET_ALL)
        try:
            unanswered_emails = self.gmail_tool.fetch_unanswered_emails(max_results=10, include_drafted=is_specific_reply)
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
            print(Fore.GREEN + f"Loaded {len(emails)} email(s)" + Style.RESET_ALL)
            
            if not emails:
                msg = "I couldn't find any unanswered emails in your inbox."
                if not is_specific_reply:
                    msg = "I couldn't find any new unanswered emails from the last 7 days. (Note: I skip emails that already have drafts unless you ask me to 'reply' to a specific one)."
                
                return {
                    "emails": [],
                    "is_processing": False,
                    "ai_response": msg,
                    "current_interaction": EmailInteraction(ai_response=msg)
                }
                
            return {
                "emails": emails,
                "is_processing": True
            }
        except Exception as e:
            print(Fore.RED + f"Error loading emails: {e}" + Style.RESET_ALL)
            return {
                "emails": [],
                "is_processing": False,
                "ai_response": f"I encountered an error while fetching your emails: {str(e)}"
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
                "current_email": None,
                "ai_response": "I've checked all your recent emails. There's nothing else that needs attention right now."
            }
        current_email = emails[-1] if emails else None
        if not current_email:
            return {"email_category": "unrelated"}

        try:
            result = self.agents.categorize_email.invoke({
                "email": f"Subject: {current_email.subject}\n\n{current_email.body}",
                "query": state.get("query", "")
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
            if not hasattr(self.agents, 'vectorstore') or self.agents.vectorstore is None:
                print(Fore.YELLOW + "Vectorstore not available, skipping RAG retrieval" + Style.RESET_ALL)
                return {"retrieved_documents": ""}
                
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
        query = state.get("query", "").lower()
        
        confirmation_keywords = [
            "send it", "send the email", "send this", "yes", "go ahead", 
            "do it", "approve", "confirm", "send now", "send an email", "send email",
            "accept", "accepting"
        ]
        
        has_send_intent = any(k in query for k in confirmation_keywords) or (
            "send" in query.split() and not any(n in query for n in ["don't", "do not", "not", "cancel", "stop"])
        )
        
        if not user_approved and has_send_intent:
            user_approved = True
            
        current_email = state.get("current_email")
        new_details = state.get("new_email_details")
        
        subject = current_email.subject if current_email else (new_details.get("subject") if new_details else "Unknown")
        print(Fore.YELLOW + f"Processing confirmation for: {subject}" + Style.RESET_ALL)
        
        if user_approved:
            print(Fore.GREEN + "Approving email for sending" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "No clear approval found, defaulting to draft for review" + Style.RESET_ALL)
        
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
            error_msg = "Could not send email - missing email details."
            return {
                "retrieved_documents": "", 
                "trials": 0,
                "ai_response": error_msg,
                "current_interaction": {"ai_response": error_msg}
            }

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
            
            response_msg = f"I've successfully sent a reply to {current_email.sender}."
            
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "generated_email": "",
                "trials": 0,
                "email_category": None,
                "rag_queries": [],
                "sendable": False,
                "ai_response": response_msg,
                "current_interaction": {"ai_response": response_msg}
            }
        except Exception as e:
            print(Fore.RED + f"Error sending email: {e}" + Style.RESET_ALL)
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            error_msg = f"Failed to send email: {str(e)}"
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "trials": 0,
                "ai_response": error_msg,
                "current_interaction": {"ai_response": error_msg}
            }

    def create_draft(self, state: GraphState) -> GraphState:
        """Create draft for human review."""
        print(Fore.YELLOW + "Creating draft for human review..." + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        new_details = state.get("new_email_details")
        generated_email = state.get("generated_email", "")
        
        if not generated_email or (not current_email and not new_details):
            return {
                "retrieved_documents": "", 
                "trials": 0,
                "ai_response": "Could not create draft - missing email details.",
                "current_interaction": {"ai_response": "Could not create draft - missing email details."}
            }

        try:
            if current_email:
                email_dict = {
                    "id": current_email.id,
                    "threadId": current_email.thread_id,
                    "messageId": current_email.message_id,
                    "sender": current_email.sender,
                    "subject": current_email.subject,
                    "body": current_email.body
                }
                self.gmail_tool.create_draft_reply(email_dict, generated_email)
                recipient = current_email.sender
                response_msg = f"I've created a draft reply to the email from {recipient}. Please review it in Gmail before sending."
            else:
                self.gmail_tool.create_draft_message(
                    to=new_details["recipient"],
                    subject=new_details["subject"],
                    body=new_details["body"]
                )
                recipient = new_details["recipient"]
                response_msg = f"I've created a draft email for {recipient}. Please review it in Gmail before sending."
                
            print(Fore.GREEN + f"Draft created for {recipient}" + Style.RESET_ALL)
            
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != (current_email.id if current_email else None)]
            
            return {
                "emails": remaining_emails,
                "current_email": None,
                "new_email_details": None,
                "retrieved_documents": "",
                "generated_email": "",
                "trials": 0,
                "email_category": None,
                "rag_queries": [],
                "sendable": False,
                "ai_response": response_msg,
                "current_interaction": {"ai_response": response_msg}
            }
        except Exception as e:
            print(Fore.RED + f"Error creating draft: {e}" + Style.RESET_ALL)
            emails = state.get("emails", [])
            remaining_emails = [e for e in emails if e.id != current_email.id]
            error_msg = f"Failed to create draft: {str(e)}"
            return {
                "emails": remaining_emails,
                "current_email": None,
                "retrieved_documents": "",
                "trials": 0,
                "ai_response": error_msg,
                "current_interaction": {"ai_response": error_msg}
            }

    def extract_new_details(self, state: GraphState) -> GraphState:
        """Extract recipient, subject, and body for a new email."""
        print(Fore.YELLOW + "Extracting new email details..." + Style.RESET_ALL)
        query = state.get("query", "")
        
        try:
            result = self.agents.extract_new_email_details.invoke({"query": query})
            print(Fore.GREEN + f"Extracted: To={result.recipient}, Sub={result.subject}" + Style.RESET_ALL)
            
            summary = f"I've prepared a new email for {result.recipient}.\nSubject: {result.subject}\n\nBody:\n{result.body}"
            
            return {
                "new_email_details": {
                    "recipient": result.recipient,
                    "subject": result.subject,
                    "body": result.body
                },
                "generated_email": result.body, # For verification if needed
                "ai_response": summary + "\n\nShould I send it?",
                "current_interaction": EmailInteraction(ai_response=summary + "\n\nShould I send it?")
            }
        except Exception as e:
            print(Fore.RED + f"Error extracting email details: {e}" + Style.RESET_ALL)
            return {
                "ai_response": f"I couldn't extract the email details: {str(e)}",
                "current_interaction": EmailInteraction(ai_response=f"I couldn't extract the email details: {str(e)}")
            }

    def send_new_email(self, state: GraphState) -> GraphState:
        """Send a completely new email."""
        print(Fore.YELLOW + "Sending new email..." + Style.RESET_ALL)
        details = state.get("new_email_details")
        
        if not details:
            return {"ai_response": "No email details found to send."}
            
        try:
            self.gmail_tool.send_message(
                to=details["recipient"],
                subject=details["subject"],
                body=details["body"]
            )
            print(Fore.GREEN + "New email sent successfully" + Style.RESET_ALL)
            
            response_msg = f"I've successfully sent your email to {details['recipient']}."
            return {
                "ai_response": response_msg,
                "current_interaction": {"ai_response": response_msg},
                "new_email_details": None,
                "sending_new_email": False
            }
        except Exception as e:
            print(Fore.RED + f"Error sending new email: {e}" + Style.RESET_ALL)
            return {"ai_response": f"Failed to send email: {str(e)}"}

    def skip_email(self, state: GraphState) -> GraphState:
        """Skip unrelated email."""
        print(Fore.YELLOW + "Skipping unrelated email" + Style.RESET_ALL)
        
        current_email = state.get("current_email")
        
        emails = state.get("emails", [])
        remaining_emails = [e for e in emails if e.id != current_email.id]
        
        response_msg = f"Skipped email from {current_email.sender if current_email else 'unknown'} as it doesn't require my assistance."
        
        return {
            "emails": remaining_emails,
            "current_email": None,
            "retrieved_documents": "",
            "generated_email": "",
            "trials": 0,
            "email_category": None,
            "rag_queries": [],
            "sendable": False,
            "ai_response": response_msg,
            "current_interaction": {"ai_response": response_msg}
        }
    
    def retrieve_drafts(self, state: GraphState) -> GraphState:
        """Retrieve and list all available draft emails."""
        print(Fore.YELLOW + "Retrieving available draft emails..." + Style.RESET_ALL)
        
        try:
            drafts = self.gmail_tool.fetch_draft_replies()
            
            if not drafts:
                response_msg = "You have no draft emails."
                return {
                    "ai_response": response_msg,
                    "current_interaction": EmailInteraction(ai_response=response_msg),
                    "available_drafts": []
                }
            
            draft_list = []
            for i, draft in enumerate(drafts, 1):
                draft_id = draft.get("id")
                thread_id = draft.get("threadId")
                
                try:
                    message = self.gmail_tool.service.users().messages().get(
                        userId="me", 
                        id=draft_id, 
                        format="full"
                    ).execute()
                    
                    payload = message.get('payload', {})
                    headers = {header["name"].lower(): header["value"] 
                              for header in payload.get("headers", [])}
                    
                    subject = headers.get("subject", "[No Subject]")
                    to = headers.get("to", "[No Recipient]")
                    
                    draft_info = {
                        "number": i,
                        "id": draft_id,
                        "subject": subject,
                        "to": to
                    }
                    draft_list.append(draft_info)
                except Exception as e:
                    print(Fore.YELLOW + f"Could not retrieve details for draft {draft_id}: {e}" + Style.RESET_ALL)
                    draft_list.append({
                        "number": i,
                        "id": draft_id,
                        "subject": "[Details unavailable]",
                        "to": "[Details unavailable]"
                    })
            
            draft_text = f"You have {len(draft_list)} draft(s):\n\n"
            for draft in draft_list:
                draft_text += f"Draft #{draft['number']}:\n"
                draft_text += f"  To: {draft['to']}\n"
                draft_text += f"  Subject: {draft['subject']}\n\n"
            
            draft_text += "Say 'send draft 1' to send the first draft, or 'send draft 2' for the second, etc."
            
            print(Fore.GREEN + f"Retrieved {len(draft_list)} draft(s)" + Style.RESET_ALL)
            
            return {
                "ai_response": draft_text,
                "current_interaction": EmailInteraction(ai_response=draft_text),
                "available_drafts": draft_list
            }
        except Exception as e:
            error_msg = f"Error retrieving drafts: {str(e)}"
            print(Fore.RED + error_msg + Style.RESET_ALL)
            return {
                "ai_response": error_msg,
                "current_interaction": EmailInteraction(ai_response=error_msg),
                "available_drafts": []
            }
    
    def send_all_drafts(self, state: GraphState) -> GraphState:
        """Send the most recent drafted email, or all if user specifies."""
        print(Fore.YELLOW + "Sending Gmail draft email..." + Style.RESET_ALL)
        
        try:
            drafts = self.gmail_tool.fetch_draft_replies()
            
            if not drafts:
                response_msg = "No draft emails found to send."
                return {
                    "ai_response": response_msg,
                    "current_interaction": EmailInteraction(ai_response=response_msg)
                }
            
            query = state.get("query", "").lower()
            available_drafts = state.get("available_drafts", [])
            print(Fore.CYAN + f"Query for send decision: '{query}'" + Style.RESET_ALL)
            
            send_all = any(k in query for k in ["send all", "send them all", "send all drafts"])
            
            draft_number = None
            for word in query.split():
                if word.isdigit():
                    draft_number = int(word)
                    break
            
            if send_all:
                sent_count = 0
                for draft in drafts:
                    try:
                        draft_id = draft.get("id")
                        self.gmail_tool.send_draft(draft_id)
                        sent_count += 1
                        print(Fore.GREEN + f"Sent draft {draft_id}" + Style.RESET_ALL)
                    except Exception as e:
                        print(Fore.RED + f"Failed to send draft: {e}" + Style.RESET_ALL)
                
                response_msg = f"Successfully sent {sent_count} drafted email(s)."
            elif draft_number is not None and draft_number > 0 and draft_number <= len(drafts):
                draft_id = drafts[draft_number - 1].get("id")
                self.gmail_tool.send_draft(draft_id)
                print(Fore.GREEN + f"Sent draft #{draft_number} ({draft_id})" + Style.RESET_ALL)
                response_msg = f"Successfully sent draft #{draft_number}."
            elif draft_number is not None:
                response_msg = f"Draft #{draft_number} not found. You have {len(drafts)} draft(s)."
            else:
                draft_id = drafts[0].get("id")
                self.gmail_tool.send_draft(draft_id)
                print(Fore.GREEN + f"Sent most recent draft {draft_id}" + Style.RESET_ALL)
                response_msg = f"Successfully sent the most recent draft email."
            
            print(Fore.GREEN + response_msg + Style.RESET_ALL)
            
            return {
                "ai_response": response_msg,
                "current_interaction": EmailInteraction(ai_response=response_msg),
                "emails": [],
                "is_processing": False
            }
        except Exception as e:
            error_msg = f"Error sending draft: {str(e)}"
            print(Fore.RED + error_msg + Style.RESET_ALL)
            return {
                "ai_response": error_msg,
                "current_interaction": EmailInteraction(ai_response=error_msg)
            }
