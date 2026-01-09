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