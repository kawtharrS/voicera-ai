package common

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"voicera-backend/data"
	"voicera-backend/helpers"
)

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

	converted := &HealthResponse{
		Status:  health.Status,
		Message: health.Message,
	}
	return converted, err
}

func AskAnything(query UniversalQueryRequest) (*AIResponse, error) {
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
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	fmt.Printf("FastAPI Response - Emotion: '%s', Category: '%s'\n", aiResp.Emotion, aiResp.Category)

	converted := &AIResponse{
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

	fmt.Printf("Converted Response - Emotion: '%s'\n", converted.Emotion)
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
	var query UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	userID, _, _, err := GetUserInfo(r)
	if err == nil {
		query.StudentID = fmt.Sprintf("%d", userID)

		if pref, pErr := data.GetLatestUserPreference(int64(userID)); pErr == nil && pref != nil {
			query.Preferences = &Preferences{
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

			ScheduleCheckInIfNeeded(userID, response.Emotion)
		}()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

var BadEmotions = map[string]bool{
	"sad":        true,
	"angry":      true,
	"anxious":    true,
	"frustrated": true,
	"stressed":   true,
	"depressed":  true,
	"lonely":     true,
	"unhappy":    true,
}

func ScheduleCheckInIfNeeded(userID int64, emotion string) {
	if _, exists := BadEmotions[emotion]; exists {
		fmt.Printf("Negative emotion '%s' detected for user %d. Scheduling check-in in 30 minutes.\n", emotion, userID)

		time.AfterFunc(30*time.Minute, func() {
			CheckInAction(userID)
		})
	}
}

func CheckInAction(userID int64) {
	message := "Hey, just checking in. How are you feeling now?"
	fmt.Printf("mess: %s\n", message)
}

func addPrefrences(query Preferences) (*AIResponse, error) {
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
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("FastAPI error: %s", string(b))
	}

	var aiResp AIResponse
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}
	converted := &AIResponse{
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

func DescribeImageHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := r.ParseMultipartForm(10 << 20); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "failed to parse form data"})
		return
	}

	file, fileHeader, err := r.FormFile("file")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "file field is required"})
		return
	}
	defer file.Close()

	contentType := fileHeader.Header.Get("Content-Type")

	if contentType == "" || contentType == "application/octet-stream" {
		ext := strings.ToLower(filepath.Ext(fileHeader.Filename))
		switch ext {
		case ".jpg", ".jpeg", ".jfif":
			contentType = "image/jpeg"
		case ".png":
			contentType = "image/png"
		case ".gif":
			contentType = "image/gif"
		case ".webp":
			contentType = "image/webp"
		case ".bmp":
			contentType = "image/bmp"
		case ".tif", ".tiff":
			contentType = "image/tiff"
		case ".heic", ".heif":
			contentType = "image/heic"
		case ".avif":
			contentType = "image/avif"
		case ".ico":
			contentType = "image/x-icon"
		case ".svg":
			contentType = "image/svg+xml"
		default:
			contentType = "image/jpeg"
		}
	}

	fmt.Printf("Received file: %s, Content-Type: %s\n", fileHeader.Filename, contentType)

	fastAPIURL := os.Getenv("FASTAPI_URL")
	if fastAPIURL == "" {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "FASTAPI_URL not configured"})
		return
	}

	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	mimeHeader := textproto.MIMEHeader{}
	mimeHeader.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file"; filename="%s"`, fileHeader.Filename))
	mimeHeader.Set("Content-Type", contentType)

	part, err := writer.CreatePart(mimeHeader)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "failed to create form file"})
		return
	}

	if _, err := io.Copy(part, file); err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "failed to read uploaded file"})
		return
	}

	if err := writer.Close(); err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "failed to finalize form data"})
		return
	}

	req, err := http.NewRequest(
		"POST",
		fastAPIURL+"/image/describe",
		&buf,
	)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "failed to build upstream request"})
		return
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Error contacting image service: %v\n", err)
		writeJSON(w, http.StatusBadGateway, apiResponse{Ok: false, Message: fmt.Sprintf("error contacting image service: %v", err)})
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("Image service returned error (%d): %s\n", resp.StatusCode, string(body))
		writeJSON(w, resp.StatusCode, apiResponse{Ok: false, Message: fmt.Sprintf("image service error: %s", string(body))})
		return
	}

	fmt.Printf("Successfully received description from image service\n")
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if _, err := io.Copy(w, resp.Body); err != nil {
		fmt.Printf("failed to stream image description response: %v\n", err)
	}
}
