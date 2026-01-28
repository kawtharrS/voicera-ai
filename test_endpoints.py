import requests
import os
import json
import time

BASE_URL = "http://localhost:8080"
# Use a unique email and name based on timestamp (milliseconds) to avoid collisions
TIMESTAMP = int(time.time() * 1000)
TEST_NAME = f"Test User {TIMESTAMP}"
TEST_EMAIL = f"test_{TIMESTAMP}@example.com"
TEST_PASSWORD = "password123"

print(f"Starting tests with email: {TEST_EMAIL} and name: {TEST_NAME}")

def test_health():
    print("Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200
    assert "hi" in resp.text

def test_register():
    print("\nTesting /api/register...")
    payload = {
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirmPassword": TEST_PASSWORD
    }
    resp = requests.post(f"{BASE_URL}/api/register", json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 201 or resp.status_code == 409, f"Unexpected status: {resp.status_code}. Response: {resp.text}"
    return resp.json().get("token")

def test_login():
    print("\nTesting /api/login...")
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    resp = requests.post(f"{BASE_URL}/api/login", json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("token")

def test_user_info(token):
    print("\nTesting /api/user...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/user", headers=headers)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"].lower() == TEST_EMAIL.lower(), f"Expected {TEST_EMAIL}, got {data['email']}"
    return data["id"]

def test_ask_anything(token):
    print("\nTesting /api/ask-anything...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "question": "What is the capital of France?"
    }
    resp = requests.post(f"{BASE_URL}/api/ask-anything", headers=headers, json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200
    # The response should have at least some AI answer
    assert "response" in resp.json()

def test_tts():
    print("\nTesting /api/tts...")
    resp = requests.get(f"{BASE_URL}/api/tts?text=Hello world")
    print(f"Status: {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type") == "audio/mpeg"

def test_image_describe():
    print("\nTesting /api/image/describe...")
    img_path = os.path.join("api", "figures", "figure-1-1.jpg")
    if not os.path.exists(img_path):
        print(f"Warning: Test image not found at {img_path}. Skipping.")
        return

    with open(img_path, "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        resp = requests.post(f"{BASE_URL}/api/image/describe", files=files)
    
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200
    assert "description" in resp.json()

def test_save_preference(token):
    print("\nTesting /api/save-preference...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "language": "English",
        "tone": "Friendly",
        "name": "Tester",
        "preference": "I like tech news"
    }
    resp = requests.post(f"{BASE_URL}/api/save-preference", headers=headers, json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 201

def test_save_memo(token):
    print("\nTesting /api/save-memo...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "user_query": "What is 2+2?",
        "ai_query": "4",
        "category": "Math",
        "emotion": "Neutral"
    }
    resp = requests.post(f"{BASE_URL}/api/save-memo", headers=headers, json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 201

def test_get_memos(token, user_id):
    print("\nTesting /api/memos...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/memos?user_id={user_id}", headers=headers)
    print(f"Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 200
    assert "data" in resp.json()

def main():
    try:
        test_health()
        
        token = test_register()
        if not token:
            print("Registration didn't return token (maybe already exists), trying login...")
            token = test_login()
        
        user_id = test_user_info(token)
        test_ask_anything(token)
        test_tts()
        test_image_describe()
        test_save_preference(token)
        test_save_memo(token)
        test_get_memos(token, user_id)
        
        print("\n" + "="*40)
        print("SUCCESS: All endpoints verified!")
        print("="*40)
    except Exception as e:
        print("\n" + "!"*40)
        print(f"FAILURE: {e}")
        print("!"*40)
        exit(1)

if __name__ == "__main__":
    main()
