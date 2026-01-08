from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import get_google_credentials
from googleapiclient.discovery import build
from langchain_google_community.calendar.create_event import CalendarCreateEvent
from langchain_google_community.calendar.search_events import CalendarSearchEvents
from langchain_google_community.calendar.update_event import CalendarUpdateEvent
from langchain_google_community.calendar.delete_event import CalendarDeleteEvent


class CalendarTool:

    credentials = get_google_credentials(
        token_file="token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
        client_secrets_file="credentials.json"
    )

    api_resource =build("calendar", "v3", credentials=credentials)
    toolkit = CalendarToolkit(api_resource = api_resource) 

    def createEvent():
        return CalendarCreateEvent()
    
    def searchEvents():
        return CalendarSearchEvents()
    
    def updateEvent():
        return CalendarUpdateEvent()
    
    def deleteEvent():
        return CalendarDeleteEvent()
    


    