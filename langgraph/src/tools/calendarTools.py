from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from langchain_google_community.calendar.create_event import CalendarCreateEvent
from langchain_google_community.calendar.delete_event import CalendarDeleteEvent
from langchain_google_community.calendar.search_events import CalendarSearchEvents
from langchain_google_community.calendar.update_event import CalendarUpdateEvent
from langchain_google_community.calendar.utils import get_google_credentials


class CalendarTool:

    def __init__(
        self,
        token_file: Optional[str] = None,
        client_secrets_file: Optional[str] = None,
        scopes: Optional[list[str]] = None,
    ):
        tools_dir = Path(__file__).resolve().parent
        self._token_file = Path(token_file).expanduser().resolve() if token_file else (tools_dir / "token.json")
        self._client_secrets_file = (
            Path(client_secrets_file).expanduser().resolve() if client_secrets_file else (tools_dir / "credentials.json")
        )
        self._scopes = scopes or ["https://www.googleapis.com/auth/calendar"]

        self._api_resource = None

    def _get_api_resource(self):
        if self._api_resource is not None:
            return self._api_resource

        if not self._client_secrets_file.exists():
            raise FileNotFoundError(
                f"Google OAuth client secrets not found at '{self._client_secrets_file}'. "
                "Place credentials.json there or pass client_secrets_file=..."
            )

        os.makedirs(self._token_file.parent, exist_ok=True)
        credentials = get_google_credentials(
            token_file=str(self._token_file),
            scopes=self._scopes,
            client_secrets_file=str(self._client_secrets_file),
        )
        self._api_resource = build("calendar", "v3", credentials=credentials)
        return self._api_resource

    def createEvent(self):
        return CalendarCreateEvent(api_resource=self._get_api_resource())
    
    def searchEvents(self):
        return CalendarSearchEvents(api_resource=self._get_api_resource())
    
    def updateEvent(self):
        return CalendarUpdateEvent(api_resource=self._get_api_resource())
    
    def deleteEvent(self):
        return CalendarDeleteEvent(api_resource=self._get_api_resource())
    


    