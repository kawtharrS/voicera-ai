import traceback
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing main...")
    from main import app
    print("Importing TestClient...")
    from fastapi.testclient import TestClient
    print("Creating client...")
    client = TestClient(app)
    print("Sending request...")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
except Exception as e:
    traceback.print_exc()
