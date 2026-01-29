import base64
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_API_VERSION = "v1"
EMAIL_DAYS_LOOKBACK = 7
DEFAULT_MAX_RESULTS = 50
SKIP_DOMAIN = "@yourdomain.com"

CREDENTIALS_FILENAMES = ["credentials.json"]
TOKEN_FILENAME = "token.json"


class AuthenticationHandler:
    """Handles Gmail API authentication and credential management."""

    def __init__(self):
        self.token_file = self._find_token_file()
        self.credentials_file = self._find_credentials_file()

    def get_credentials(self) -> UserCredentials:
        """Get valid Gmail API credentials."""
        creds = self._load_existing_credentials()

        if not creds or not creds.valid:
            creds = self._refresh_or_authenticate(creds)

        if creds:
            self._save_credentials(creds)

        return creds

    def _load_existing_credentials(self) -> Optional[UserCredentials]:
        """Load credentials from token file if it exists."""
        if self.token_file and os.path.exists(self.token_file):
            try:
                return UserCredentials.from_authorized_user_file(self.token_file, GMAIL_SCOPES)
            except Exception as e:
                print(f"Error loading credentials: {e}")
        return None

    def _refresh_or_authenticate(self, creds: Optional[UserCredentials]) -> UserCredentials:
        """Refresh token or perform new authentication."""
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return creds
            except Exception as e:
                print(f"Error refreshing credentials: {e}")

        if not self.credentials_file:
            raise FileNotFoundError(
                f"credentials.json not found. Expected locations:\n"
                f"  - {CREDENTIALS_FILENAMES[0]}\n"
                f"  - {os.path.join(os.path.dirname(__file__), CREDENTIALS_FILENAMES[0])}\n"
                f"See GMAIL_API_SETUP.md for setup instructions."
            )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
            return creds
        except Exception as e:
            print(f"Error authenticating: {e}")
            raise

    def _save_credentials(self, creds: UserCredentials) -> None:
        """Save credentials to token file."""
        try:
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())
        except Exception as e:
            print(f"Error saving credentials: {e}")

    @staticmethod
    def _find_credentials_file() -> Optional[str]:
        """Find credentials.json in expected locations."""
        paths = [
            CREDENTIALS_FILENAMES[0],
            os.path.join(os.path.dirname(__file__), CREDENTIALS_FILENAMES[0]),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def _find_token_file() -> str:
        """Find or determine token file location."""
        paths = [
            TOKEN_FILENAME,
            os.path.join(os.path.dirname(__file__), TOKEN_FILENAME),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return paths[0]  


class EmailParser:
    """Parses email message payloads and extracts content."""

    @staticmethod
    def parse_headers(payload: Dict) -> Dict[str, str]:
        """Extract headers from message payload."""
        return {
            header["name"].lower(): header["value"]
            for header in payload.get("headers", [])
        }

    @staticmethod
    def extract_body(payload: Dict) -> str:
        """Extract email body from payload."""
        try:
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")
            else:
                data = payload.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")
        except Exception as e:
            print(f"Error extracting email body: {e}")
        return ""

    @staticmethod
    def extract_email_info(message: Dict) -> Dict:
        """Extract structured info from full message."""
        payload = message.get("payload", {})
        headers = EmailParser.parse_headers(payload)
        body = EmailParser.extract_body(payload)

        return {
            "id": message.get("id"),
            "threadId": message.get("threadId"),
            "messageId": headers.get("message-id"),
            "references": headers.get("references", ""),
            "sender": headers.get("from", "Unknown"),
            "subject": headers.get("subject", "No Subject"),
            "body": body,
        }


class MessageBuilder:
    """Constructs MIME messages for sending or drafting."""

    @staticmethod
    def create_message(
        to: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ) -> Dict:
        """Create a message suitable for sending or drafting."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        result = {"raw": raw_message}
        if thread_id:
            result["threadId"] = thread_id

        return result

    @staticmethod
    def format_subject(subject: str, is_reply: bool = False) -> str:
        """Format subject line for reply."""
        if is_reply and not subject.startswith("Re:"):
            return f"Re: {subject}"
        return subject


class GmailService:
    """Low-level Gmail API operations."""

    def __init__(self, service):
        self.service = service

    def get_profile(self) -> Dict:
        """Get authenticated user's profile."""
        try:
            return self.service.users().getProfile(userId="me").execute()
        except Exception as e:
            print(f"Error getting Gmail profile: {e}")
            return {}

    def get_message(self, message_id: str) -> Optional[Dict]:
        """Fetch a message by ID."""
        try:
            return self.service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
        except Exception as e:
            print(f"Error fetching message: {e}")
            return None

    def list_messages(self, query: str, max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict]:
        """List messages matching query."""
        try:
            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            return results.get("messages", [])
        except Exception as e:
            print(f"Error listing messages: {e}")
            return []

    def list_drafts(self) -> List[Dict]:
        """List all drafts."""
        try:
            results = self.service.users().drafts().list(userId="me").execute()
            drafts = []
            for draft in results.get("drafts", []):
                drafts.append({
                    "id": draft["id"],
                    "threadId": draft["message"]["threadId"],
                })
            return drafts
        except Exception as e:
            print(f"Error listing drafts: {e}")
            return []

    def send_message(self, message: Dict) -> bool:
        """Send a message."""
        try:
            self.service.users().messages().send(userId="me", body=message).execute()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def create_draft(self, message: Dict, thread_id: Optional[str] = None) -> Optional[str]:
        """Create a draft and return draft ID."""
        try:
            draft_body = {"message": message}
            if thread_id:
                draft_body["threadId"] = thread_id
            result = self.service.users().drafts().create(
                userId="me", body=draft_body
            ).execute()
            return result.get("id")
        except Exception as e:
            print(f"Error creating draft: {e}")
            return None

    def send_draft(self, draft_id: str) -> bool:
        """Send an existing draft."""
        try:
            self.service.users().drafts().send(
                userId="me", body={"id": draft_id}
            ).execute()
            return True
        except Exception as e:
            print(f"Error sending draft: {e}")
            return False


class GmailTool:
    """High-level Gmail operations for email management."""

    def __init__(self):
        auth = AuthenticationHandler()
        credentials = auth.get_credentials()
        service = build(
            "gmail",
            GMAIL_API_VERSION,
            credentials=credentials,
        )
        self.gmail = GmailService(service)
        self.parser = EmailParser()
        self.builder = MessageBuilder()

    def get_my_email(self) -> str:
        """Get the authenticated user's email address."""
        profile = self.gmail.get_profile()
        return profile.get("emailAddress", "")

    def fetch_recent_emails(self, max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict]:
        """Fetch emails from the last 7 days."""
        now = datetime.now()
        delay = now - timedelta(days=EMAIL_DAYS_LOOKBACK)

        query = f"after:{int(delay.timestamp())} before:{int(now.timestamp())}"
        return self.gmail.list_messages(query, max_results)

    def fetch_draft_replies(self) -> List[Dict]:
        """Fetch draft replies to identify answered threads."""
        return self.gmail.list_drafts()

    def fetch_unanswered_emails(
        self,
        max_results: int = DEFAULT_MAX_RESULTS,
        include_drafted: bool = False,
    ) -> List[Dict]:
        """Fetch unanswered emails from inbox."""
        recent_emails = self.fetch_recent_emails(max_results)
        if not recent_emails:
            return []

        answered_thread_ids = set()
        if not include_drafted:
            drafts = self.fetch_draft_replies()
            answered_thread_ids = {draft["threadId"] for draft in drafts}

        seen_threads = set()
        unanswered_emails = []

        for email_summary in recent_emails:
            thread_id = email_summary["threadId"]

            if thread_id in seen_threads or (
                not include_drafted and thread_id in answered_thread_ids
            ):
                continue

            seen_threads.add(thread_id)

            email_info = self._get_full_email(email_summary["id"])
            if email_info and not self._should_skip_email(email_info):
                unanswered_emails.append(email_info)

        return unanswered_emails

    def send_reply(self, original_email: Dict, reply_body: str) -> bool:
        """Send a reply to an email."""
        subject = self.builder.format_subject(
            original_email.get("subject", ""),
            is_reply=True,
        )

        message = self.builder.create_message(
            to=original_email.get("sender"),
            subject=subject,
            body=reply_body,
            thread_id=original_email.get("threadId"),
        )

        return self.gmail.send_message(message)

    def create_draft_reply(self, original_email: Dict, draft_body: str) -> bool:
        """Create a draft reply for review."""
        subject = self.builder.format_subject(
            original_email.get("subject", ""),
            is_reply=True,
        )

        message = self.builder.create_message(
            to=original_email.get("sender"),
            subject=subject,
            body=draft_body,
        )

        draft_id = self.gmail.create_draft(
            message,
            thread_id=original_email.get("threadId"),
        )
        return draft_id is not None

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """Send a new email."""
        message = self.builder.create_message(to=to, subject=subject, body=body)
        return self.gmail.send_message(message)

    def create_draft_message(self, to: str, subject: str, body: str) -> Optional[str]:
        """Create a draft email and return draft ID."""
        message = self.builder.create_message(to=to, subject=subject, body=body)
        return self.gmail.create_draft(message)

    def send_draft(self, draft_id: str) -> bool:
        """Send an existing draft."""
        if not draft_id:
            return False
        return self.gmail.send_draft(draft_id)

    def _get_full_email(self, message_id: str) -> Optional[Dict]:
        """Fetch and parse full email details."""
        message = self.gmail.get_message(message_id)
        if not message:
            return None
        return self.parser.extract_email_info(message)

    @staticmethod
    def _should_skip_email(email_info: Dict) -> bool:
        """Check if email should be filtered out."""
        sender = email_info.get("sender", "").lower()
        return SKIP_DOMAIN in sender