# Voicera API - Postman Testing Guide

## Overview

This guide covers testing all endpoints for the Voicera API including Calendar (Orion) and Gmail agents.

---

## 1. Health Check

### Endpoint

```
GET http://localhost:8000/health
```

### Description

Verifies that the API is running.

### Response

```json
{
  "status": "healthy",
  "message": "Voicera ClassroomAI API is running"
}
```

---

## 2. Calendar Agent (Orion) Endpoints

### 2.1 Test Calendar Categorization Only

**Endpoint**

```
POST http://localhost:8000/orion/test-receive-categorize
```

**Description**
Tests the calendar query categorization without executing calendar operations.

**Request Body (JSON)**

```json
{
  "user_request": "create an event tomorrow at 3pm called meeting",
  "thread_id": "calendar_test_1"
}
```

**Categories**

- `create` - Create new calendar event
- `search` - Search for events
- `update` - Update existing event
- `delete` - Delete an event

**Example Requests**

```json
// CREATE
{
  "user_request": "schedule a meeting tomorrow at 2pm"
}

// SEARCH
{
  "user_request": "show me all events this week"
}

// UPDATE
{
  "user_request": "change my 3pm meeting tomorrow to 4pm"
}

// DELETE
{
  "user_request": "delete the event at 2pm today"
}
```

**Response**

```json
{
  "user_request": "create an event tomorrow at 3pm called meeting",
  "category": "create",
  "observation": "Query classified as: create"
}
```

---

### 2.2 Run Full Calendar Workflow

**Endpoint**

```
POST http://localhost:8000/orion/run
```

**Description**
Executes the complete calendar workflow: receive → categorize → route → execute action.

**Request Body (JSON)**

```json
{
  "user_request": "create an event tomorrow at 3pm called team meeting",
  "thread_id": "calendar_full_test_1"
}
```

**Response**

```json
{
  "user_request": "create an event tomorrow at 3pm called team meeting",
  "category": "create",
  "route": "create_event",
  "ai_response": "created event: team meeting",
  "observation": "Calendar event created successfully",
  "calendar_result": {
    "id": "event_id_123",
    "summary": "team meeting",
    "start": "2026-01-11T15:00:00"
  }
}
```

---

## 3. Gmail Agent Endpoints

### 3.1 Test Email Categorization Only

**Endpoint**

```
POST http://localhost:8000/gmail/test-categorize
```

**Description**
Tests email categorization without generating responses.

**Request Body (JSON)**

```json
{
  "email_subject": "Help with calculus homework",
  "email_body": "Can you explain integration? I'm having trouble understanding the concept of definite integrals."
}
```

**Categories**

- `study` - Study/educational content (uses RAG retrieval)
- `work` - Work-related topics (direct AI response)
- `general` - General feedback/opinions (direct AI response)
- `unrelated` - Irrelevant emails (skipped)

**Example Requests**

```json
// STUDY
{
  "email_subject": "Question about Python loops",
  "email_body": "Hi, I'm confused about how for loops work in Python. Can you help explain?"
}

// WORK
{
  "email_subject": "Project deadline update",
  "email_body": "The Q1 project deadline has been moved to next Friday. Please update your schedules."
}

// GENERAL
{
  "email_subject": "Great job on the presentation",
  "email_body": "I really enjoyed your presentation today. The examples were very clear and helpful!"
}

// UNRELATED
{
  "email_subject": "Buy now - 50% off",
  "email_body": "Limited time offer! Click here to get 50% off everything in our store."
}
```

**Response**

```json
{
  "email_subject": "Help with calculus homework",
  "email_body": "Can you explain integration? I'm having trouble understanding the concept of definite integrals.",
  "category": "study",
  "observation": "Email categorized as: study"
}
```

---

### 3.2 Run Full Gmail Workflow

**Endpoint**

```
POST http://localhost:8000/gmail/run
```

**Description**
Executes the complete email workflow: categorize → route → RAG (if study) → generate → verify → send/draft.

**Request Body (JSON)**

```json
{
  "email_subject": "Help with calculus homework",
  "email_body": "Can you explain integration? I'm having trouble understanding the concept of definite integrals.",
  "sender": "student@example.com",
  "thread_id": "gmail_test_1"
}
```

**Response**

```json
{
  "email_subject": "Help with calculus homework",
  "email_category": "study",
  "generated_email": "Dear Student,\n\nThank you for your question about integration. ...",
  "sendable": true,
  "trials": 1,
  "observation": "Email processed - Category: study, Sendable: true"
}
```

---

## Postman Setup Instructions

### Step 1: Create Collection

1. Open Postman
2. Click **Collections** → **Create New Collection**
3. Name it `Voicera API`
4. Click **Create**

### Step 2: Create Environment (Optional but Recommended)

1. Click **Environments** → **Create New Environment**
2. Name it `Local Development`
3. Add variable:
   - Key: `base_url`
   - Value: `http://localhost:8000`
4. Save

### Step 3: Add Health Check Request

1. Create new request: **GET** {{base_url}}/health
2. Send to verify API is running

### Step 4: Add Calendar Endpoints

#### 4.1 Categorize Calendar Query

1. Create new request: **POST** {{base_url}}/orion/test-receive-categorize
2. Body → raw → JSON
3. Copy request body from section 2.1
4. Send

#### 4.2 Run Full Calendar Workflow

1. Create new request: **POST** {{base_url}}/orion/run
2. Body → raw → JSON
3. Copy request body from section 2.2
4. Send

### Step 5: Add Gmail Endpoints

#### 5.1 Categorize Email

1. Create new request: **POST** {{base_url}}/gmail/test-categorize
2. Body → raw → JSON
3. Copy request body from section 3.1
4. Send

#### 5.2 Run Full Gmail Workflow

1. Create new request: **POST** {{base_url}}/gmail/run
2. Body → raw → JSON
3. Copy request body from section 3.2
4. Send

---

## Testing Scenarios

### Scenario 1: Complete Study Email Flow

**Goal**: Test RAG retrieval for study questions

```json
{
  "email_subject": "Explanation of Machine Learning basics",
  "email_body": "What is supervised learning and how does it differ from unsupervised learning? Can you provide examples?",
  "sender": "student@university.edu",
  "thread_id": "study_scenario_1"
}
```

**Expected**:

- Category: `study`
- Generated response uses RAG knowledge base
- Sendable: `true` (if knowledge base has relevant info)

---

### Scenario 2: Work Email Flow

**Goal**: Test direct AI response for work-related emails

```json
{
  "email_subject": "Meeting rescheduled",
  "email_body": "The team meeting originally scheduled for Friday has been moved to Monday at 10am. Please update your calendars.",
  "sender": "manager@company.com",
  "thread_id": "work_scenario_1"
}
```

**Expected**:

- Category: `work`
- Generated response (no RAG)
- Sendable: `true`

---

### Scenario 3: General Feedback

**Goal**: Test personalized response generation

```json
{
  "email_subject": "Feedback on course materials",
  "email_body": "The course materials were very well organized. I appreciated the clear explanations and the additional resources provided.",
  "sender": "student@university.edu",
  "thread_id": "general_scenario_1"
}
```

**Expected**:

- Category: `general`
- Generated thank you response
- Sendable: `true`

---

### Scenario 4: Unrelated Email

**Goal**: Test filtering of irrelevant emails

```json
{
  "email_subject": "Free credit card offer",
  "email_body": "Apply now for our premium credit card with 0% APR for 12 months!",
  "sender": "offer@creditcompany.com",
  "thread_id": "unrelated_scenario_1"
}
```

**Expected**:

- Category: `unrelated`
- Email is skipped
- Not processed further

---

## Troubleshooting

### Issue: "Module not found" error

**Solution**: Ensure the API is running with proper path setup:

```bash
cd C:\Users\user\Desktop\Voicera\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Issue: Gmail endpoints fail

**Solution**: Ensure Gmail credentials are set up:

- Place `credentials.json` in langgraph/src/tools/
- First run will prompt for OAuth authentication

### Issue: RAG not returning results

**Solution**: Ensure vectorstore is populated:

- Knowledge base documents should be in the vectorstore
- Run `rebuild_vectorstore.py` if needed

### Issue: Response takes too long

**Solution**:

- First requests are slower (model loading)
- Subsequent requests are faster
- For study emails with RAG, allow 10-15 seconds

---

## Quick Reference: cURL Commands

```bash
# Health Check
curl http://localhost:8000/health

# Calendar Test
curl -X POST http://localhost:8000/orion/test-receive-categorize \
  -H "Content-Type: application/json" \
  -d '{"user_request": "create meeting tomorrow"}'

# Gmail Test
curl -X POST http://localhost:8000/gmail/test-categorize \
  -H "Content-Type: application/json" \
  -d '{"email_subject": "Homework help", "email_body": "Can you explain this?"}'

# Gmail Full
curl -X POST http://localhost:8000/gmail/run \
  -H "Content-Type: application/json" \
  -d '{"email_subject": "Study question", "email_body": "What is...", "sender": "student@example.com"}'
```

---

## Additional Notes

- All timestamps use UTC
- Email categories are case-sensitive in responses
- The `thread_id` is optional but recommended for tracking
- RAG responses depend on knowledge base content
- Maximum 3 rewrite attempts before flagging for human review
