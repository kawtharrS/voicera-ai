package common

import (
	"encoding/json"
	"net/http"
)

func FastAPIHealthHandler(w http.ResponseWriter, r *http.Request){
	health, err := GetFastAPIHealth()

	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}