package common

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"time"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

type StudentQuestion struct {
	Question            string                   `json:"question"`
	CourseID            string                   `json:"course_id,omitempty"`
	StudentID           string                   `json:"student_id,omitempty"`
	ConversationHistory []map[string]interface{} `json:"conversation_history,omitempty"`
}

type UniversalQueryRequest struct {
	Question            string                   `json:"question"`
	StudentID           string                   `json:"student_id,omitempty"`
	CourseID            string                   `json:"course_id,omitempty"`
	ThreadID            string                   `json:"thread_id,omitempty"`
	ConversationHistory []map[string]interface{} `json:"conversation_history,omitempty"`
}

type AIResponse struct {
	Question        string          `json:"question"`
	Response        string          `json:"response"`
	Recommendations json.RawMessage `json:"recommendations"`
	Feedback        string          `json:"feedback"`
	Sendable        bool            `json:"sendable"`
	Trials          int             `json:"trials"`
	Observation     string          `json:"observation"`
	Category        string          `json:"category,omitempty"`
}

type UniversalQueryResponse struct {
	Question        string                 `json:"question"`
	Category        string                 `json:"category"`
	Response        string                 `json:"response"`
	Recommendations []string               `json:"recommendations,omitempty"`
	Observation     string                 `json:"observation,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

func GetFastAPIHealth() (*HealthResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	client := http.Client{
		Timeout: 5 * time.Second,
	}
	resp, err := client.Get(fastAPIURL + "/health")

	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, errors.New("FastAPI health check failed")
	}

	var health HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, err
	}

	return &health, err
}

func AskAI(question StudentQuestion) (*AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(question)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/ask",
		bytes.NewBuffer(body),
	)

	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 120 * time.Second}

	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Fastapi error: %s", string(b))
	}
	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	return &aiResp, nil
}

// New: Universal query function with automatic routing
func AskAnything(query UniversalQueryRequest) (*AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(query)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/ask-anything",
		bytes.NewBuffer(body),
	)

	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 120 * time.Second}

	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	return &aiResp, nil
}

func AskAnythingSimple(question string) (*AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	encodedQuestion := url.QueryEscape(question)
	requestURL := fmt.Sprintf("%s/ask-anything-simple?question=%s", fastAPIURL, encodedQuestion)

	client := http.Client{Timeout: 120 * time.Second}
	resp, err := client.Post(requestURL, "application/json", nil)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	return &aiResp, nil
}

func TTSHandler(w http.ResponseWriter, r *http.Request) {
	text := r.URL.Query().Get("text")
	if text == "" {
		http.Error(w, "text parameter required", http.StatusBadRequest)
		return
	}

	category := r.URL.Query().Get("category")

	fastAPIURL := os.Getenv("FASTAPI_URL")
	if fastAPIURL == "" {
		http.Error(w, "FASTAPI_URL not configured", http.StatusInternalServerError)
		return
	}

	requestURL := fmt.Sprintf("%s/tts?text=%s", fastAPIURL, url.QueryEscape(text))
	if category != "" {
		requestURL = fmt.Sprintf("%s&category=%s", requestURL, url.QueryEscape(category))
	}
	fmt.Printf("TTS Request: %s\n", requestURL)

	resp, err := http.Get(requestURL)
	if err != nil {
		fmt.Printf("TTS Error: %v\n", err)
		http.Error(w, "Failed to contact TTS service", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("TTS service error (%d): %s\n", resp.StatusCode, string(body))
		http.Error(w, "TTS service error", resp.StatusCode)
		return
	}

	w.Header().Set("Content-Type", "audio/mpeg")
	w.Header().Set("Content-Disposition", "inline; filename=speech.mp3")

	_, err = io.Copy(w, resp.Body)
	if err != nil {
		fmt.Printf("Failed to stream audio: %v\n", err)
	}
}

func AskAnythingHandler(w http.ResponseWriter, r *http.Request) {
	var query UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	response, err := AskAnything(query)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func AskAnythingSimpleHandler(w http.ResponseWriter, r *http.Request) {
	question := r.URL.Query().Get("question")
	if question == "" {
		http.Error(w, "question parameter required", http.StatusBadRequest)
		return
	}

	response, err := AskAnythingSimple(question)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// AskPersonal calls the personal agent endpoint
func AskPersonal(query UniversalQueryRequest) (*AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(query)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/personal/ask",
		bytes.NewBuffer(body),
	)

	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 120 * time.Second}

	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	return &aiResp, nil
}

// AskWork calls the work agent endpoint
func AskWork(query UniversalQueryRequest) (*AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(query)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/work/ask",
		bytes.NewBuffer(body),
	)

	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 120 * time.Second}

	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	return &aiResp, nil
}

func AskPersonalHandler(w http.ResponseWriter, r *http.Request) {
	var query UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	response, err := AskPersonal(query)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func AskWorkHandler(w http.ResponseWriter, r *http.Request) {
	var query UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	response, err := AskWork(query)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
