# Proactive AI Implementation Plan for Voicera

This plan outlines how to transform the current `Voicera` agents from reactive responders to proactive assistants that learn from user behavior.

## Core Concept: The Proactive Loop

To achieve proactivity, we need to close the loop between **User Action** and **Agent Memory**.

1.  **Observe & Reflect**: After every interaction, the system analyzes the conversation to extract "learnings" (preferences, recurring tasks, tone).
2.  **Store**: These learnings are saved to a long-term memory store (`langmem`).
3.  **Recall**: Before processing a new request, the system retrieves relevant context.
4.  **Anticipate**: The agent uses this context to suggest actions or format responses *before* being explicitly asked.

---

## Step 1: Verify & Enhance Shared Memory

You already have `shared_memory.py`. We need to ensure it is actively incorporated into the main flow.

**Action**: Update `api/services/ai_service.py` to:
1.  **Retrieve** memory *before* invoking the graph.
2.  **Save** the interaction *after* the graph returns.

### Proposed Code for `api/services/ai_service.py`

```python
# Import shared_memory
from agents.shared_memory import shared_memory

async def process_question(query: StudentQuestion) -> AIResponse:
    # 1. RETRIEVE context (Proactive Step)
    # Fetch long-term memories relevant to the current user
    user_id = query.student_id or DEFAULT_STUDENT_ID
    # We query for general habits or specific to the current question
    memory_context = await shared_memory.retrieve(user_id, query.question)
    
    # Prepend this memory to the student_context or a new field
    enhanced_context = f"{memory_context}\n{query.preferences or {}}"

    initial_state = {
        # ... existing fields ...
        "student_id": user_id,
        "student_context": enhanced_context, # Inject memory here
        # ...
    }

    # 2. INVOKE Graph
    result = await graph.ainvoke(initial_state, ...)

    # 3. SAVE & REFLECT (Learning Step)
    # Run this in background so it doesn't block the response to the user
    # (or await if critical)
    ai_text = extract_ai_response(result)
    await shared_memory.extract_and_save(
        query=query.question,
        user_id=user_id,
        ai_response=ai_text,
        category=result.get("category", "general"),
        emotion=extract_emotion(result)
    )

    return AIResponse(...)
```

---

## Step 2: Update Agent Prompts (The "Brain")

The agents need to *know* they have this memory.

**Action**: Modify the system prompts for `Orion` (Calendar), `Eureka`, and `Aria`.

**Example Update for `CATEGORIZE_QUERY_PROMPT` in `prompts/calendar.py`:**

```python
CATEGORIZE_QUERY_PROMPT = """
You are an intelligent calendar assistant.
User Query: {query}

User Context (Past Habits & Preferences):
{user_context}

Task:
1. User Context: Check if the user has a preferred way of doing things (e.g. "always set meetings to 30 mins").
2. Answer based on the query AND the context.
...
"""
```

By injecting `{user_context}` (which now contains the retrieved `langmem` data), the agent becomes "aware" of the user's history.

---

## Step 3: Implement "Proactive Suggestions"

To make the agent truly proactive (suggesting things effectively), you can add a `Reflector/Suggester` logic.

**Option A: In-Flow Suggestion**
In your `UserInteraction` model (in `calendar_state.py`), you already have a `recommendations` list.
Ensure the agent populates this list based on memory.

*Example*:
*   **Memory**: "User always checks their schedule for tomorrow at 8 PM."
*   **Current Time**: 8:01 PM.
*   **User**: "Hi."
*   **Agent (Proactive)**: "Hello! It's just past 8 PM. Would you like me to show you tomorrow's schedule as usual?"

**Implementation**:
In the `receive_user_query` or `categorize_user_query` node, check the `memory_context` against the current state (time, recent actions) and inject a "hidden prompt" that says: *"If the user context suggests a routine action for right now, suggest it."*

---

## Step 4: The Background Worker (True Autonomy)

For "True" proactivity (acting without a user message), you need a system heartbeat.

1.  **Scheduler**: A simple cron job (e.g., in `main.py` using `fastapi-utils` or a background loop) that runs every minute.
2.  **Check**: It queries the `SharedMemory` or `Calendar` for "Triggers" (e.g., "Remind me to X at Y").
3.  **Push**: If a trigger checks out, it pushes a notification (if you have a frontend socket) or keeps a "Pending Message" in the database that is delivered next time the user opens the app.

---

## Summary of Immediate Tasks

1.  **Modify `ai_service.py`**: Add `shared_memory.retrieve` (Start) and `shared_memory.extract_and_save` (End).
2.  **Verify `shared_memory.py`**: Ensure it works (it looks correct, relying on `langmem`).
3.  **Update Agent Prompts**: Pass the retrieved context into the LLM prompts so it uses the information.
