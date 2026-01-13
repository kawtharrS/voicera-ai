package common

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"time"
	"fmt"
)

type HealthResponse struct {
	Status string `json:"status"`
	Message string `json:"message"`
}

type StudentQuestion struct {
	Question string `json:"question"`
	CourseID string `json:"course_id,omitempty"`
	StudentID string `json:"student_id,omitempty"`
	ConversationHistory []string `json:"conversation_history,omitempty"`
}

type AIResponse struct {
	Question string `json:"question"`
	Response string `json:"response"`
	Recommendations  json.RawMessage `json:"recommendations"`
	Feedback string `json:"feedback"`
	Sendable bool `json:"sendable"`
	Trials int `json:"trials"`
	Observation string `json:"observation"`

}

func GetFastAPIHealth() (*HealthResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	client := http.Client{
		Timeout: 5* time.Second,
	}
	resp, err := client.Get(fastAPIURL +"/health")

	if err != nil{
		return nil, err
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, errors.New("FastAPI health check failed")
	}

	var health HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil{
		return nil, err
	}

	return &health,err
}

func AskAI(question StudentQuestion) (*AIResponse, error){
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

	if err != nil{
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _:=io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Fastapi error: %s", string(b))
	}
	var aiResp AIResponse
	if err :=json.NewDecoder(resp.Body).Decode(&aiResp); err != nil{
		return nil, err
	}
	return &aiResp, nil
}
