CATEGORIZE_QUERY_PROMPT = """
Analyze the user's query and categorize it into one of the following types:
- create: create a new event to the calendar
- search: serach for event from calendar
- update: update a certain event in the user's calendar
- delete: delete an event from the user's calendar

User Query: {query}

Determine which category best fits this query.
"""

AI_RESPONSE_WRITER_PROMPT = """
You are CalendarAI, a helpful and interactive calendar assistant.
Your goal is to perform one of these actions create, search, update and delete.

User's Question and Context: {query_information}

"""

AI_RESPONSE_PROOFREADER_PROMPT = """
Review the AI response for quality and accuracy:

Student Question: {student_question}

AI Response: {ai_response}
the response should contain if the action was successful or not 
"""


CREATE_EVENT_PROMT = """
                "Extract calendar event details from the user query.\n"
                "Use the reference datetime and timezone below to resolve relative date phrases "
                "(e.g., 'today', 'tomorrow', 'yesterday', 'next Monday', 'in 2 hours') into exact datetimes.\n"
                "If the user doesn't specify a timezone, use the provided timezone.\n"
                "Return start_datetime/end_datetime in 'YYYY-MM-DD HH:MM:SS' format and an IANA timezone.\n\n"
                "Reference datetime: {reference_datetime}\n"
                "Reference timezone: {timezone}\n\n"
                "User query: {query}"
"""


SEARCH_EVENT_PROMPT = """
Extract Google Calendar search parameters from the user query.

Use the reference datetime and timezone below to resolve relative date phrases
(e.g., 'today', 'tomorrow', 'yesterday', 'next Monday', 'this week') into exact datetimes.

Return:
- min_datetime and max_datetime in 'YYYY-MM-DD HH:MM:SS'
- query (optional): free-text term to match event fields
- max_results (optional, default 10)

Reference datetime: {reference_datetime}
Reference timezone: {timezone}

User query: {query}
"""


UPDATE_EVENT_PROMPT = """
Extract Google Calendar update parameters from the user query.

IMPORTANT: Split the request into two parts:
1) Which existing event to update (the TARGET event)
2) What the new details should be (the NEW values)

Use the reference datetime and timezone below to resolve relative date phrases
(e.g., 'today', 'tomorrow', 'next Monday', 'in 2 hours') into exact datetimes.

Return (JSON fields):
- event_id (optional): if you don't know it, return null (do NOT invent placeholders)

TARGET event identification:
- target_min_datetime / target_max_datetime: a tight window around the target event time
    Example: if user says "event at 12pm today", set a window like 11:00-13:00 today.
- target_query (optional): event title keywords if present
- max_results (optional, default 10)

NEW values (what to change):
- new_summary (optional)
- new_start_datetime / new_end_datetime (optional)
- timezone (optional)
- new_location / new_description (optional)

Notes:
- If the user provides a new start time but no new end time, set new_end_datetime = new_start_datetime + 1 hour.
- Datetime format: 'YYYY-MM-DD HH:MM:SS'

Reference datetime: {reference_datetime}
Reference timezone: {timezone}

User query: {query}
"""


DELETE_EVENT_PROMPT = """
Extract Google Calendar delete parameters from the user query.

IMPORTANT: Split the request into two parts:
1) Which existing event to delete (the TARGET event)
2) How to delete it (calendar, send_updates)

Use the reference datetime and timezone below to resolve relative date phrases
+(e.g., 'today', 'tomorrow', 'next Monday', 'in 2 hours') into exact datetimes.

Return (JSON fields):
- event_id (optional): if you don't know it, return null (do NOT invent placeholders)

TARGET event identification (when event_id is null):
- target_min_datetime / target_max_datetime: a tight window around the target event time
  Example: if user says "event at 3pm tomorrow", set a window like 14:00-16:00 tomorrow.
- target_query (optional): event title keywords if present
- max_results (optional, default 10)

DELETE settings:
- calendar_id (optional, default 'primary')
- send_updates (optional): one of 'all', 'externalOnly', or 'none'

Datetime format: 'YYYY-MM-DD HH:MM:SS'

Reference datetime: {reference_datetime}
Reference timezone: {timezone}

User query: {query}
"""