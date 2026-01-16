package common

import (
	"encoding/json"
	"net/http"
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

	if req.UserQuery == "" || req.AIQuery == "" {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "user_query and ai_query are required"})
		return
	}

	if req.UserID == 0 {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "user_id is required"})
		return
	}

	memo, err := data.SaveUserMemo(req.UserID, req.UserQuery, req.AIQuery)
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

