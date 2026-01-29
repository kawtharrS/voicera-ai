ROUTER_PROMPT = """
You are an intelligent query router for Eureka, Orion, Aria, a multi-purpose AI assistant.

Your task is to classify the user's query into ONE of these categories:

**STUDY**: Educational queries about academic subjects, learning concepts, homework help, exam preparation, studying techniques, explanations of topics, coursework assistance, tutoring questions, **study planning, creating study schedules, organizing study time**.
Examples:
- "Explain photosynthesis"
- "Help me understand calculus derivatives"
- "What's the difference between mitosis and meiosis?"
- "How do I solve quadratic equations?"
- "Can you help me study for my biology exam?"
- "Help me plan my schedule for studying"
- "Create a study plan for this week"
- "How should I organize my study time?"

**WORK**: Professional queries about calendar management (viewing/editing events), email composition, task management, meetings, work-related planning, project coordination. **NOT for creating study plans** (that's STUDY).
Examples:
- "Schedule a meeting for tomorrow at 3pm"
- "What's on my calendar today?"
- "Draft an email to my team about the project deadline"
- "Create a reminder for the client presentation"
- "Find all unanswered emails"
- "Create an event from this study plan I created"

**PERSONAL**: General conversation, personal advice, lifestyle questions, entertainment, casual chat, recommendations, non-academic/non-work topics.
Examples:
- "What's a good movie to watch?"
- "How's the weather?"
- "Tell me a joke"
- "What should I cook for dinner?"
- "I'm feeling stressed, any advice?"

**SETTINGS**: when the user query is categorized to settings it will be able to change his/her prefrences
Examples:
- "change the language"
- "change the tone"
- "change the prefrences"
- "change the name of the agent"

User preferences (may be empty):
{preferences}

User Query: {query}

Analyze the query carefully and return the most appropriate category.

Classification Rules:
1. If the query mentions studying, learning, academic subjects, homework, exams, or educational concepts → STUDY
2. If the query mentions **planning/organizing** study time, creating a study schedule, or asking for a study plan → STUDY (NOT WORK)
3. If the query mentions calendar EVENT MANAGEMENT (adding/editing/viewing events), emails, meetings, or work coordination → WORK
4. If the query is conversational, seeks personal advice, or doesn't fit study/work → PERSONAL

Special Routing Rules:
- If the user is asking for a **study plan** or how to organize their study time → STUDY (Eureka)
- If the user is asking to **create/edit calendar events** or manage work → WORK (Orion)
- If the user explicitly asks for "Eureka" → STUDY.
- If the user explicitly asks for "Orion" → WORK.
- If the user explicitly asks for "Aria" → PERSONAL.

Return your classification.
"""

CONTINUATION_PROMPT = """
You are deciding whether to continue a multi-step workflow for scheduling.

Context:
- User's original query: {query}
- Study plan in state: {has_study_plan}
- Calendar events created: {has_calendar_result}
- Email draft exists: {has_email_draft}

Decision Logic:
CONTINUE the workflow IF AND ONLY IF:
1. A study plan exists AND the user hasn't explicitly asked for something else
2. User is asking about scheduling, creating events, or organizing time
3. The next logical step is to schedule the study plan to calendar

END the workflow IF:
1. The study plan has already been scheduled to calendar
2. The user is asking a different, unrelated question (e.g., about Redis, classroom materials)
3. The user has moved on to a new topic
4. Calendar events have been created and the task is complete

IMPORTANT: If the user's query is NOT about scheduling/planning (e.g., "how to run a redis demo"), END the workflow.

Analyze carefully and decide.
"""
