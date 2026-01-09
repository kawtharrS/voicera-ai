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