import requests
import os
import json
import time
import pytest

BASE_URL = "http://localhost:8080"
TIMESTAMP = int(time.time() * 1000)
TEST_NAME = f"Test User {TIMESTAMP}"
TEST_EMAIL = f"test_{TIMESTAMP}@example.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def token():
    """Register a user (or login if exists) and return the auth token."""
    print(f"\nSetting up user: {TEST_EMAIL} / {TEST_NAME}")
    payload = {
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirmPassword": TEST_PASSWORD
    }
    resp = requests.post(f"{BASE_URL}/api/register", json=payload)
    if resp.status_code == 201:
        return resp.json().get("token")
    
    if resp.status_code == 409:
        payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        resp = requests.post(f"{BASE_URL}/api/login", json=payload)
        assert resp.status_code == 200
        return resp.json().get("token")
    
    pytest.fail(f"Failed to register or login. Status: {resp.status_code} Body: {resp.text}")

@pytest.fixture(scope="module")
def user_id(token):
    """Retrieve user ID using the token."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/user", headers=headers)
    assert resp.status_code == 200
    return resp.json()["id"]


def test_health():
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    assert "hi" in resp.text

@pytest.mark.parametrize("i", range(3))
def test_register_multiple_iterations(i):
    """Stress test user registration."""
    ts = int(time.time() * 1000) + i
    payload = {
        "name": f"Stress {ts}",
        "email": f"stress_{ts}@example.com",
        "password": "password123",
        "confirmPassword": "password123"
    }
    resp = requests.post(f"{BASE_URL}/api/register", json=payload)
    assert resp.status_code == 201
    assert "token" in resp.json()

def test_login_flow():
    ts = int(time.time() * 1000) + 100
    email = f"login_{ts}@example.com"
    pwd = "password123"
    requests.post(f"{BASE_URL}/api/register", json={
        "name": f"Login User {ts}", "email": email, "password": pwd, "confirmPassword": pwd
    })
    resp = requests.post(f"{BASE_URL}/api/login", json={"email": email, "password": pwd})
    assert resp.status_code == 200
    assert "token" in resp.json()

def test_user_info(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/user", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"].lower() == TEST_EMAIL.lower()

def test_missing_auth_header():
    resp = requests.get(f"{BASE_URL}/api/user")
    assert resp.status_code == 401

def test_invalid_login():
    resp = requests.post(f"{BASE_URL}/api/login", json={"email": "fake@example.com", "password": "wrong"})
    assert resp.status_code == 401

def test_tts_simple():
    resp = requests.get(f"{BASE_URL}/api/tts?text=Test")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type") == "audio/mpeg"

def test_tts_voices():
    for voice in ["alloy", "shimmer", "echo"]:
        resp = requests.get(f"{BASE_URL}/api/tts?text=Test&voice={voice}")
        assert resp.status_code == 200

def test_image_describe():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "api", "figures", "figure-1-1.jpg")
    
    if not os.path.exists(img_path):
        pytest.skip(f"Test image not found at {img_path}")

    with open(img_path, "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        resp = requests.post(f"{BASE_URL}/api/image/describe", files=files)
    
    assert resp.status_code == 200
    assert resp.json().get("description")


def test_save_preference(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "language": "French",
        "tone": "Formal",
        "name": "Pierre",
        "preference": "I love baguettes"
    }
    resp = requests.post(f"{BASE_URL}/api/save-preference", headers=headers, json=payload)
    assert resp.status_code == 201

def test_save_memo(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "user_query": "Test query",
        "ai_query": "Test response",
        "category": "Test",
        "emotion": "Happy"
    }
    resp = requests.post(f"{BASE_URL}/api/save-memo", headers=headers, json=payload)
    assert resp.status_code == 201

def test_get_memos(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/memos?user_id={user_id}", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json().get("data"), list)


@pytest.mark.parametrize("query, expected_category", [
    ("What's on my calendar tomorrow?", "calendar"),
    ("Schedule a meeting with John next Friday", "calendar"),
    ("Do I have any free time on Monday?", "calendar"),
])
def test_agent_calendar(token, query, expected_category):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, json={"question": query})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    
    if data.get("category"):
        assert any(c in data["category"].lower() for c in ["calendar", "schedule", "meeting", "work"])

@pytest.mark.parametrize("query, expected_category", [
    ("Check my unread emails", "email"),
    ("Draft an email to mom saying hi", "email"),
    ("Send an email to boss about the report", "email"),
])
def test_agent_email(token, query, expected_category):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, json={"question": query})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    if data.get("category"):
        assert any(c in data["category"].lower() for c in ["email", "gmail", "communication"])

@pytest.mark.parametrize("query", [
    "Tell me a joke",
    "How are you?",
    "What is the meaning of life?",
    "Explain quantum physics broadly",
    "Who won the 1998 World Cup?"
])
def test_agent_general_chat(token, query):
    """Tests for Aria / Eureka handling general knowledge or chat."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, json={"question": query})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("response", "")) > 0

def test_agent_emotion_detection(token):
    """Test if negative emotion triggers check-in logic (simulated)."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, json={"question": "I am feeling very sad and lonely today."})
    assert resp.status_code == 200
    data = resp.json()
    emotion = data.get("emotion", "").lower()
    if emotion:
        assert emotion in ["sadness", "sad", "lonely", "depression", "negative", "unhappy"]


def test_eureka_rag_query(token):
    """Test Eureka's RAG/Knowledge capability."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, 
                         json={"question": "What are the key concepts of machine learning?"})
    assert resp.status_code == 200
    assert "response" in resp.json()

def test_study_plan_generation(token):
    """Test generating a study plan (Eureka capability)."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, 
                         json={"question": "Create a study plan for learning Python in 2 weeks."})
    assert resp.status_code == 200
    data = resp.json()
    assert "Python" in data.get("response", "")

def test_sequential_conversation(token):
    """Test maintaining context across 2 turns."""
    headers = {"Authorization": f"Bearer {token}"}
    
    resp1 = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, 
                          json={"question": "My name is Alice."})
    assert resp1.status_code == 200
    
    resp2 = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, 
                          json={"question": "What is my name?"})
    assert resp2.status_code == 200
    assert "Alice" in resp2.json().get("response", "")

