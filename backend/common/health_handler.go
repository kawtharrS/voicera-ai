package common

import (
	"net/http"
	"voicera-backend/helpers"
)

func FastAPIHealthHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	writeJSON(w, http.StatusOK, apiResponse{
		Ok:      true,
		Message: "hi",
	})
}
