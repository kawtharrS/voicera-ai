package common

import (
	"encoding/json"
	"net/http"
)

func FastAPIHealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"message": "Health Check Passed",
	})
}