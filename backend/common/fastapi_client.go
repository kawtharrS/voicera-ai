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

	"voicera-backend/data"
	"voicera-backend/types"
)

func GetFastAPIHealth() (*types.HealthResponse, error) {
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

	var health types.HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, err
	}

	converted := &types.HealthResponse{
		Status:  health.Status,
		Message: health.Message,
	}
	return converted, err
}

func AskAnything(query types.UniversalQueryRequest) (*types.AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(query)

	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/api/ask-anything",
		bytes.NewBuffer(body),
	)

	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 360 * time.Second}

	resp, err := client.Do(req)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close() // prevents memory leaks

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp types.AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	fmt.Printf("[DEBUG] FastAPI Response - Emotion: '%s', Category: '%s'\n", aiResp.Emotion, aiResp.Category)

	converted := &types.AIResponse{
		Question:        aiResp.Question,
		Response:        aiResp.Response,
		Recommendations: aiResp.Recommendations,
		Feedback:        aiResp.Feedback,
		Sendable:        aiResp.Sendable,
		Trials:          aiResp.Trials,
		Observation:     aiResp.Observation,
		Category:        aiResp.Category,
		Emotion:         aiResp.Emotion,
	}

	fmt.Printf("[DEBUG] Converted Response - Emotion: '%s'\n", converted.Emotion)
	return converted, nil
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

	requestURL := fmt.Sprintf("%s/api/tts?text=%s", fastAPIURL, url.QueryEscape(text))
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
	var query types.UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	userID, _, _, err := GetUserInfo(r)
	if err == nil {
		query.StudentID = fmt.Sprintf("%d", userID)

		if pref, pErr := data.GetLatestUserPreference(int64(userID)); pErr == nil && pref != nil {
			query.Preferences = &types.Preferences{
				Language:   pref.Language,
				UserId:     fmt.Sprintf("%d", pref.UserID),
				Tone:       pref.Tone,
				Name:       pref.Name,
				Prefrences: pref.Preference,
			}
		}
	}

	response, err := AskAnything(query)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error: %v", err), http.StatusInternalServerError)
		return
	}

	if userID > 0 && response != nil {
		go func() {
			memo, err := data.SaveUserMemo(
				int64(userID),
				query.Question,
				response.Response,
				response.Category,
				response.Emotion,
			)
			if err != nil {
				fmt.Printf("Error saving memo: %v\n", err)
			} else {
				fmt.Printf("Memo saved (ID: %d) - Category: %s, Emotion: %s\n", memo.ID, memo.Category, memo.Emotion)
			}
		}()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func addPrefrences(query types.Preferences) (*types.AIResponse, error) {
	fastAPIURL := os.Getenv("FASTAPI_URL")

	body, err := json.Marshal(query)

	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/api/ask-anything",
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
	defer resp.Body.Close() // prevents memory leaks

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp types.AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	converted := &types.AIResponse{
		Question:        aiResp.Question,
		Response:        aiResp.Response,
		Recommendations: aiResp.Recommendations,
		Feedback:        aiResp.Feedback,
		Sendable:        aiResp.Sendable,
		Trials:          aiResp.Trials,
		Observation:     aiResp.Observation,
		Category:        aiResp.Category,
		Emotion:         aiResp.Emotion,
	}
	return converted, nil
}
