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

func newHTTPClient(timeout time.Duration) *http.Client {
	return &http.Client{Timeout: timeout}
}

func getFastAPIURL() (string, error) {
	url := os.Getenv("FASTAPI_URL")
	if url == "" {
		return "", errors.New("FASTAPI_URL not configured")
	}
	return strings.TrimSpace(url), nil
}

func decodeJSON(body io.Reader, target interface{}) error {
	return json.NewDecoder(body).Decode(target)
}

func encodeJSON(v interface{}) ([]byte, error) {
	return json.Marshal(v)
}

func GetFastAPIHealth() (*HealthResponse, error) {
	fastAPIURL, err := getFastAPIURL()
	if err != nil {
		return nil, err
	}

	resp, err := newHTTPClient(HealthCheckTimeout).Get(fastAPIURL + "/health")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, errors.New("FastAPI health check failed")
	}

	var health HealthResponse
	if err := decodeJSON(resp.Body, &health); err != nil {
		return nil, err
	}

	return &health, nil
}

func AskAnything(query UniversalQueryRequest) (*AIResponse, error) {
	fastAPIURL, err := getFastAPIURL()
	if err != nil {
		return nil, err
	}

	body, err := encodeJSON(query)
	if err != nil {
		return nil, err
	}

	resp, err := doPostRequest(fastAPIURL+"/api/ask-anything", body, AskAnythingTimeout)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var aiResp AIResponse
	if err := decodeJSON(resp.Body, &aiResp); err != nil {
		return nil, err
	}

	fmt.Printf("FastAPI Response - Emotion: '%s', Category: '%s'\n", aiResp.Emotion, aiResp.Category)
	return &aiResp, nil
}

func doPostRequest(url string, body []byte, timeout time.Duration) (*http.Response, error) {
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := newHTTPClient(timeout).Do(req)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, string(body))
	}

	return resp, nil
}

func TTSHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	text := r.URL.Query().Get("text")
	if text == "" {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "text parameter required"})
		return
	}

	fastAPIURL, err := getFastAPIURL()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: err.Error()})
		return
	}

	requestURL := buildTTSURL(fastAPIURL, text, r.URL.Query().Get("category"), r.URL.Query().Get("voice"))
	fmt.Printf("TTS Request: %s\n", requestURL)

	if err := streamAudioFromURL(w, requestURL); err != nil {
		fmt.Printf("TTS Error: %v\n", err)
	}
}

func buildTTSURL(fastAPIURL, text, category, voice string) string {
	params := url.Values{}
	params.Add("text", text)
	if category != "" {
		params.Add("category", category)
	}
	if voice != "" {
		params.Add("voice", voice)
	}
	return fmt.Sprintf("%s/api/tts?%s", fastAPIURL, params.Encode())
}

func streamAudioFromURL(w http.ResponseWriter, requestURL string) error {
	resp, err := http.Get(requestURL)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, apiResponse{Ok: false, Message: "Failed to contact TTS service"})
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("TTS service error (%d): %s\n", resp.StatusCode, string(body))
		writeJSON(w, resp.StatusCode, apiResponse{Ok: false, Message: "TTS service error"})
		return fmt.Errorf("TTS service returned %d", resp.StatusCode)
	}

	copyAudioHeaders(w, resp)
	if _, err := io.Copy(w, resp.Body); err != nil {
		fmt.Printf("Failed to stream audio: %v\n", err)
		return err
	}

	return nil
}

func copyAudioHeaders(w http.ResponseWriter, resp *http.Response) {
	if contentType := resp.Header.Get("Content-Type"); contentType != "" {
		w.Header().Set("Content-Type", contentType)
	} else {
		w.Header().Set("Content-Type", "audio/mpeg")
	}

	for _, header := range []string{"Content-Length", "Accept-Ranges"} {
		if val := resp.Header.Get(header); val != "" {
			w.Header().Set(header, val)
		}
	}

	w.Header().Set("Content-Disposition", "inline; filename=speech.mp3")
}

func AskAnythingHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, apiResponse{Ok: false, Message: "Method not allowed"})
		return
	}

	var query UniversalQueryRequest
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "Invalid request body"})
		return
	}

	enrichQueryWithUserInfo(&query, r)

	response, err := AskAnything(query)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: fmt.Sprintf("Error: %v", err)})
		return
	}

	if response == nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "Empty response from AI service"})
		return
	}

	processQueryResponse(query, response)

	writeJSON(w, http.StatusOK, apiResponse{Ok: true, Data: response})
}

func enrichQueryWithUserInfo(query *UniversalQueryRequest, r *http.Request) {
	userID, _, _, err := GetUserInfo(r)
	if err != nil {
		return
	}

	query.StudentID = fmt.Sprintf("%d", userID)
	populateUserPreferences(query, userID)
}

func populateUserPreferences(query *UniversalQueryRequest, userID int64) {
	pref, err := data.GetLatestUserPreference(userID)
	if err != nil || pref == nil {
		return
	}

	query.Preferences = &Preferences{
		Language:   pref.Language,
		UserId:     fmt.Sprintf("%d", pref.UserID),
		Tone:       pref.Tone,
		Name:       pref.Name,
		Prefrences: pref.Preference,
	}
}

func processQueryResponse(query UniversalQueryRequest, response *AIResponse) {
	userID, err := parseUserID(query.StudentID)
	if err != nil || userID <= 0 {
		return
	}

	go func() {
		if err := saveUserMemo(userID, query.Question, response); err != nil {
			fmt.Printf("Error saving memo: %v\n", err)
			return
		}
		scheduleCheckInIfNeeded(userID, response.Emotion)
	}()
}

func parseUserID(userIDStr string) (int64, error) {
	var userID int64
	_, err := fmt.Sscanf(userIDStr, "%d", &userID)
	return userID, err
}

func saveUserMemo(userID int64, question string, response *AIResponse) error {
	memo, err := data.SaveUserMemo(
		userID,
		question,
		response.Response,
		response.Category,
		response.Emotion,
	)
	if err != nil {
		return err
	}

	fmt.Printf("Memo saved (ID: %d) - Category: %s, Emotion: %s\n", memo.ID, memo.Category, memo.Emotion)
	return nil
}

func scheduleCheckInIfNeeded(userID int64, emotion string) {
	if _, exists := BadEmotions[emotion]; !exists {
		return
	}

	fmt.Printf("Negative emotion '%s' detected for user %d. Scheduling check-in.\n", emotion, userID)
	time.AfterFunc(CheckInDelay, func() {
		sendCheckIn(userID)
	})
}

func sendCheckIn(userID int64) {
	message := "Hey, just checking in. How are you feeling now?"
	fmt.Printf("Check-in for user %d: %s\n", userID, message)
}

func AddPreferences(query Preferences) (*AIResponse, error) {
	fastAPIURL, err := getFastAPIURL()
	if err != nil {
		return nil, err
	}

	body, err := encodeJSON(query)
	if err != nil {
		return nil, err
	}

	resp, err := doPostRequest(fastAPIURL+"/api/ask-anything", body, PreferencesTimeout)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var aiResp AIResponse
	if err := decodeJSON(resp.Body, &aiResp); err != nil {
		return nil, err
	}

	return &aiResp, nil
}

func DescribeImageHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, apiResponse{Ok: false, Message: "Method not allowed"})
		return
	}

	fastAPIURL, err := getFastAPIURL()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: err.Error()})
		return
	}

	file, fileHeader, contentType, err := parseImageUpload(w, r)
	if err != nil {
		return
	}
	defer file.Close()

	fmt.Printf("Received file: %s, Content-Type: %s\n", fileHeader.Filename, contentType)

	result, err := describeImageViaAPI(fastAPIURL, file, fileHeader.Filename, contentType)
	if err != nil {
		fmt.Printf("Error describing image: %v\n", err)
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "Failed to describe image"})
		return
	}

	writeJSON(w, http.StatusOK, apiResponse{Ok: true, Data: result})
}

func parseImageUpload(w http.ResponseWriter, r *http.Request) (io.ReadCloser, *multipart.FileHeader, string, error) {
	if err := r.ParseMultipartForm(MaxUploadSize); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "failed to parse form data"})
		return nil, nil, "", err
	}

	file, fileHeader, err := r.FormFile("file")
	if err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "file field is required"})
		return nil, nil, "", err
	}

	contentType := detectContentType(fileHeader.Header.Get("Content-Type"), fileHeader.Filename)
	return file, fileHeader, contentType, nil
}

func detectContentType(headerContentType, filename string) string {
	if headerContentType != "" && headerContentType != "application/octet-stream" {
		return headerContentType
	}

	ext := strings.ToLower(filepath.Ext(filename))
	if mimeType, ok := imageContentTypeMap[ext]; ok {
		return mimeType
	}

	return "image/jpeg"
}

func describeImageViaAPI(fastAPIURL string, file io.Reader, filename, contentType string) (map[string]interface{}, error) {
	buf, writer, err := buildMultipartForm(file, filename, contentType)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", fastAPIURL+"/image/describe", buf)
	if err != nil {
		return nil, fmt.Errorf("failed to build request: %w", err)
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := newHTTPClient(ImageServiceTimeout).Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to contact image service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("image service error (%d): %s", resp.StatusCode, string(body))
	}

	var result map[string]interface{}
	if err := decodeJSON(resp.Body, &result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	fmt.Printf("Successfully received description from image service\n")
	return result, nil
}

func buildMultipartForm(file io.Reader, filename, contentType string) (*bytes.Buffer, *multipart.Writer, error) {
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	mimeHeader := textproto.MIMEHeader{}
	mimeHeader.Set("Content-Disposition", fmt.Sprintf(`form-data; name="file"; filename="%s"`, filename))
	mimeHeader.Set("Content-Type", contentType)

	part, err := writer.CreatePart(mimeHeader)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create form part: %w", err)
	}

	if _, err := io.Copy(part, file); err != nil {
		return nil, nil, fmt.Errorf("failed to copy file data: %w", err)
	}

	if err := writer.Close(); err != nil {
		return nil, nil, fmt.Errorf("failed to close writer: %w", err)
	}

	return &buf, writer, nil
}
