package main

import (
	"log"
	"net/http"

	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	"github.com/joho/godotenv"

	"voicera-backend/common"
	"voicera-backend/data"
)

func main() {
	godotenv.Load()
	data.InitSupabase()

	r := SetupRouter()

	corsHandler := handlers.CORS(
		handlers.AllowedOrigins([]string{"http://localhost:5173"}),
		handlers.AllowedMethods([]string{"GET", "POST", "OPTIONS"}),
		handlers.AllowedHeaders([]string{"Content-Type", "Authorization"}),
		handlers.AllowCredentials(),
	)

	log.Fatal(http.ListenAndServe(":8080", corsHandler(r)))
}

func SetupRouter() *mux.Router {
	r := mux.NewRouter()
	r.HandleFunc("/api/register", common.RegisterAPIHandler).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/login", common.LoginAPIHandler).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/logout", common.LogoutHandler).Methods("POST")
	r.HandleFunc("/health", common.FastAPIHealthHandler).Methods("GET")
	r.HandleFunc("/api/ask-anything", common.AskAnythingHandler).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/tts", common.TTSHandler).Methods("GET")
	r.HandleFunc("/api/image/describe", common.DescribeImageHandler).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/save-memo", common.SaveMemoHandler).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/memos", common.GetMemosHandler).Methods("GET", "OPTIONS")
	r.HandleFunc("/api/save-preference", common.SavePreferences).Methods("POST", "OPTIONS")
	r.HandleFunc("/api/user", common.UserInfoHandler).Methods("GET", "OPTIONS")
	return r
}
