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

var router = mux.NewRouter()

func main() {
	godotenv.Load()
	data.InitSupabase()

	router.HandleFunc("/api/register", common.RegisterAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/login", common.LoginAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/logout", common.LogoutHandler).Methods("POST")
	router.HandleFunc("/health", common.FastAPIHealthHandler).Methods("GET")
	router.HandleFunc("/api/ask-anything", common.AskAnythingHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/tts", common.TTSHandler).Methods("GET")
	router.HandleFunc("/api/image/describe", common.DescribeImageHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/save-memo", common.SaveMemoHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/memos", common.GetMemosHandler).Methods("GET", "OPTIONS")
	router.HandleFunc("/api/save-preference", common.SavePreferences).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/user", common.UserInfoHandler).Methods("GET", "OPTIONS")

	corsHandler := handlers.CORS(
		handlers.AllowedOrigins([]string{"http://localhost:5173"}),
		handlers.AllowedMethods([]string{"GET", "POST", "OPTIONS"}),
		handlers.AllowedHeaders([]string{"Content-Type", "Authorization"}),
		handlers.AllowCredentials(),
	)

	log.Fatal(http.ListenAndServe(":8080", corsHandler(router)))
}
