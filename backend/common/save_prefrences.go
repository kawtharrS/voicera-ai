package common

import (
	"encoding/json"
	"net/http"

	"voicera-backend/data"
	"voicera-backend/helpers"
)

func SavePreferences(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req SavePreferenceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{
			Ok: false, Message: "Invalid request body",
		})
		return
	}

	userID, _, _, err := GetUserInfo(r)
	if err == nil {
		req.UserID = int64(userID)
	}

	if req.UserID == 0 || req.Preference == "" {
		writeJSON(w, http.StatusBadRequest, apiResponse{
			Ok: false, Message: "user_id and preference are required",
		})
		return
	}
	if _, err := data.SaveUserPreference(
		req.UserID,
		req.Language,
		req.Tone,
		req.Name,
		req.Preference,
	); err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{
			Ok: false, Message: "failed to save preference: " + err.Error(),
		})
		return
	}

	writeJSON(w, http.StatusCreated, apiResponse{
		Ok:      true,
		Message: "Preferences saved successfully",
	})
}
