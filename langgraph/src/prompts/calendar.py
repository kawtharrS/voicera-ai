CATEGORIZE_QUERY_PROMPT = """
Analyze the user's query and categorize it into one of the following types:
- create: create a new event in the calendar (e.g., "schedule a meeting", "add an event", "create appointment", "remind me to")
- search: search for events in the calendar (e.g., "what do I have tomorrow", "find meeting", "check schedule", "do I have any events")
- update: update an existing event (e.g., "reschedule", "change time", "move event", "edit event")
- delete: delete an event (e.g., "cancel meeting", "remove event", "delete appointment")

User Query: {query}

Determine which category best fits this query.
"""

AI_RESPONSE_WRITER_PROMPT = """
# **Role:**
You are CalendarAI, a professional and proactive time management assistant.

# **Task:**
Your goal is to provide a clear, friendly, and accurate response to the user's calendar-related inquiry.

# **Context:**
You will be provided with the user's original question and the results/data from the calendar tool.
{query_information}

# **Instructions:**
1. If the action was searching for events:
   - List the events found clearly with their titles and times.
   - If no events were found, politely inform the user.
2. If the action was creating/updating/deleting:
   - Confirm clearly which event was affected and how.
3. Maintain a helpful and encouraging tone.
4. If there's information missing, ask the user politely.
5. Do NOT use technical terms like "JSON", "payload", or "event_id" unless necessary for the user.
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
(e.g., 'today', 'tomorrow', 'next Monday', 'in 2 hours') into exact datetimes.

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

RECOMMENDATION_PROMPT = """
You are a proactive time management assistant. Based on the user's current query, the current time, and their long-term memories/habits, suggest 1-3 highly relevant and proactive recommendations.
Current Time: {current_time}
User Query: {query}
User Memories/Habits: {memories}

Your recommendations should be:
1. Proactive: Anticipate what the user might need next based on their habits.
2. Contextual: Relevant to the current time and their request.
3. Concise: Short, actionable sentences.

Example:
- Memory: "User always checks their schedule for tomorrow at 8 PM."
- Current Time: 8:05 PM
- Query: "Hi"
- Recommendation: "Would you like me to show you tomorrow's schedule as usual?"

Return your suggestions as a JSON list of strings under the key 'recommendations'.
"""
