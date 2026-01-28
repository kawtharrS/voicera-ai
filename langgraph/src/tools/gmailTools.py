import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GmailTool:
    def __init__(self):
        self.service = self._get_gmail_service()

    def get_my_email(self) -> str:
        """Return the authenticated Gmail address for the current token."""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress", "")
        except Exception as e:
            print(f"Error getting Gmail profile: {e}")
            return ""

    def _get_gmail_service(self):
        """Authenticate and build Gmail API service."""
        SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        creds = None
        credentials_file = None
        token_file = None

        credentials_paths = [
            'credentials.json',
            os.path.join(os.path.dirname(__file__), 'credentials.json'),
        ]
        token_paths = [
            'token.json',
            os.path.join(os.path.dirname(__file__), 'token.json'),
        ]
        for path in credentials_paths:
            if os.path.exists(path):
                credentials_file = path
                break

        for path in token_paths:
            if os.path.exists(path):
                token_file = path
                break
        if token_file is None:
            token_file = token_paths[0]  
        if token_file and os.path.exists(token_file):
            creds = UserCredentials.from_authorized_user_file(token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_file:
                    raise FileNotFoundError(
                        "credentials.json not found in any expected location:\n"
                        + "\n".join(credentials_paths) + 
                        "\n\nSee GMAIL_API_SETUP.md for instructions on obtaining credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)

    def fetch_unanswered_emails(self, max_results: int = 50, include_drafted: bool = False) -> List[Dict]:
        """Fetch unanswered emails from the inbox."""
        try:
            recent_emails = self.fetch_recent_emails(max_results)
            if not recent_emails:
                return []
            
            threads_with_drafts = set()
            if not include_drafted:
                drafts = self.fetch_draft_replies()
                threads_with_drafts = {draft['threadId'] for draft in drafts}
            
            seen_threads = set()
            unanswered_emails = []
            
            for email in recent_emails:
                thread_id = email['threadId']
                
                if thread_id not in seen_threads and (include_drafted or thread_id not in threads_with_drafts):
                    seen_threads.add(thread_id)
                    email_info = self._get_email_info(email['id'])
                    
                    if not self._should_skip_email(email_info):
                        unanswered_emails.append(email_info)
            
            return unanswered_emails
            
        except Exception as e:
            print(f"Error fetching unanswered emails: {e}")
            return []

    def fetch_recent_emails(self, max_results: int = 50) -> List[Dict]:
        """Fetch emails from the last 7 days."""
        try:
            now = datetime.now()
            delay = now - timedelta(days=7)
            after_timestamp = int(delay.timestamp())
            before_timestamp = int(now.timestamp())
            query = f"after:{after_timestamp} before:{before_timestamp}"
            
            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            
            return results.get("messages", [])
            
        except Exception as e:
            print(f"Error fetching recent emails: {e}")
            return []

    def fetch_draft_replies(self) -> List[Dict]:
        """Fetch draft replies to find already-answered threads."""
        try:
            results = self.service.users().drafts().list(
                userId="me"
            ).execute()
            
            drafts = []
            for draft in results.get("drafts", []):
                draft_info = {
                    "id": draft["id"],
                    "threadId": draft["message"]["threadId"]
                }
                drafts.append(draft_info)
            
            return drafts
            
        except Exception as e:
            print(f"Error fetching drafts: {e}")
            return []

    def _get_email_info(self, msg_id: str) -> Dict:
        """Extract email information from message ID."""
        try:
            message = self.service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
            
            payload = message.get('payload', {})
            headers = {header["name"].lower(): header["value"] 
                      for header in payload.get("headers", [])}
            
            return {
                "id": msg_id,
                "threadId": message.get("threadId"),
                "messageId": headers.get("message-id"),
                "references": headers.get("references", ""),
                "sender": headers.get("from", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "body": self._get_email_body(payload),
            }
            
        except Exception as e:
            print(f"Error getting email info: {e}")
            return {}

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = payload['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception as e:
            print(f"Error extracting email body: {e}")
        
        return ""

    def _should_skip_email(self, email_info: Dict) -> bool:
        """Check if email should be skipped (e.g., from agency)."""
        sender = email_info.get("sender", "").lower()
        if "@yourdomain.com" in sender:  
            return True
        return False

    def send_reply(self, original_email: Dict, reply_body: str) -> bool:
        """Send a reply to the original email."""
        try:
            message = self.service.users().messages().get(
                userId="me", id=original_email['id'], format="full"
            ).execute()
            
            subject = original_email.get("subject", "")
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
            
            reply_message = self._create_message(
                sender="me",
                to=original_email.get("sender"),
                subject=subject,
                message_text=reply_body,
                thread_id=original_email.get("threadId")
            )
            
            self.service.users().messages().send(
                userId="me", body=reply_message
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error sending reply: {e}")
            return False

    def create_draft_reply(self, original_email: Dict, draft_body: str) -> bool:
        """Create a draft reply for human review."""
        try:
            subject = original_email.get("subject", "")
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"
            
            message = self._create_message(
                sender="me",
                to=original_email.get("sender"),
                subject=subject,
                message_text=draft_body
            )
            
            draft = {
                'message': message,
                'threadId': original_email.get("threadId")
            }
            
            self.service.users().drafts().create(
                userId="me", body=draft
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error creating draft: {e}")
            return False

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """Send a new outbound email (not a reply)."""
        try:
            msg = self._create_message(sender="me", to=to, subject=subject, message_text=body)
            self.service.users().messages().send(userId="me", body=msg).execute()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def create_draft_message(self, to: str, subject: str, body: str) -> Optional[str]:
        """Create a new draft email (not a reply) and return the draft ID."""
        try:
            msg = self._create_message(sender="me", to=to, subject=subject, message_text=body)
            draft = {"message": msg}
            created = self.service.users().drafts().create(userId="me", body=draft).execute()
            return created.get("id")
        except Exception as e:
            print(f"Error creating draft message: {e}")
            return None

    def send_draft(self, draft_id: str) -> bool:
        """Send an existing Gmail draft by draft ID."""
        try:
            if not draft_id:
                return False
            self.service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            return True
        except Exception as e:
            print(f"Error sending draft: {e}")
            return False

    def _create_message(self, sender: str, to: str, subject: str, 
                       message_text: str, thread_id: Optional[str] = None) -> Dict:
        """Create a message for sending or drafting."""
        message = MIMEText(message_text)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = {'raw': raw_message}
        if thread_id:
            result['threadId'] = thread_id
        
        return result
