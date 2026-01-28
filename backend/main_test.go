package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

func TestMain(m *testing.M) {
	// Set dummy environment variables for tests
	os.Setenv("FASTAPI_URL", "http://localhost:9999")
	os.Setenv("JWT_SECRET", "test_secret")
	// Make sure SUPABASE_URL is empty so it uses in-memory mode
	os.Setenv("SUPABASE_URL", "")

	exitCode := m.Run()
	os.Exit(exitCode)
}

func TestHealthEndpoint(t *testing.T) {
	r := SetupRouter()
	req, _ := http.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()

	r.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	expected := `{"message":"hi"}`
	// The handler might include a newline or not depending on the encoder
	// So we check if it contains the expected string
	if !bytes.Contains(rr.Body.Bytes(), []byte(expected)) {
		t.Errorf("handler returned unexpected body: got %v want %v", rr.Body.String(), expected)
	}
}

func TestAuthFlow(t *testing.T) {
	r := SetupRouter()

	// 1. Register
	regPayload := map[string]string{
		"name":            "TestUser",
		"email":           "test@example.com",
		"password":        "password123",
		"confirmPassword": "password123",
	}
	body, _ := json.Marshal(regPayload)
	req, _ := http.NewRequest("POST", "/api/register", bytes.NewBuffer(body))
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusCreated {
		t.Fatalf("Register failed: got %v want %v. Body: %s", status, http.StatusCreated, rr.Body.String())
	}

	var resp map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	token, ok := resp["token"].(string)
	if !ok || token == "" {
		t.Fatalf("No token returned in register response")
	}

	// 2. User Info
	req, _ = http.NewRequest("GET", "/api/user", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	rr = httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("UserInfo failed: got %v want %v. Body: %s", status, http.StatusOK, rr.Body.String())
	}

	// 3. Login
	loginPayload := map[string]string{
		"email":    "test@example.com",
		"password": "password123",
	}
	body, _ = json.Marshal(loginPayload)
	req, _ = http.NewRequest("POST", "/api/login", bytes.NewBuffer(body))
	rr = httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("Login failed: got %v want %v. Body: %s", status, http.StatusOK, rr.Body.String())
	}
}
