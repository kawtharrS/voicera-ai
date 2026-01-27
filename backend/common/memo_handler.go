package common

import (
	"encoding/json"
	"net/http"
	"strconv"

	"voicera-backend/data"
	"voicera-backend/helpers"
)

func SaveMemoHandler(w http.ResponseWriter, r *http.Request) {

	helpers.SetHeaders(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req data.SaveMemoRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "Invalid request body"})
		return
	}

	userID, _, _, err := GetUserInfo(r)
	if err == nil {
		req.UserID = int64(userID)
	}

	if req.UserQuery == "" || req.AIQuery == "" {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "user_query and ai_query are required"})
		return
	}

	if req.UserID == 0 {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "user_id is required"})
		return
	}

	memo, err := data.SaveUserMemo(req.UserID, req.UserQuery, req.AIQuery, req.Category, req.Emotion)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "Failed to save memo: " + err.Error()})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ok":      true,
		"message": "Memo saved successfully",
		"data":    memo,
	})
}

// GetMemosHandler returns the latest memos for a given user.
// This is used by the LangGraph agents as a long-term memory fallback
// when the langmem vector store is not available.
func GetMemosHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userIDStr := r.URL.Query().Get("user_id")
	if userIDStr == "" {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "user_id is required"})
		return
	}

	limitStr := r.URL.Query().Get("limit")
	limit := 20
	if limitStr != "" {
		if v, err := strconv.Atoi(limitStr); err == nil && v > 0 {
			limit = v
		}
	}

	userID, err := strconv.ParseInt(userIDStr, 10, 64)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "invalid user_id"})
		return
	}

	memos, err := data.GetUserMemos(userID, limit)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "Failed to load memos: " + err.Error()})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ok":   true,
		"data": memos,
	})
}
