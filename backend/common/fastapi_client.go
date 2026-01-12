package common 

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Status string `json:"status"`
	Message string `json:"message"`
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