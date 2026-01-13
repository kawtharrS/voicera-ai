package main

import (
	"fmt"     
	"net/http" 
	"log"

	"github.com/gorilla/mux"  
	"github.com/gorilla/handlers"
	"github.com/joho/godotenv"

	"voicera-backend/common" 
	"voicera-backend/data"   

)

var router = mux.NewRouter()

func main() {
	err := godotenv.Load()
	if err != nil {
		fmt.Println("Note: Could not load .env file (not required if using system env vars)")
	} else {
		fmt.Println("Loaded .env file")
	}

	data.InitSupabase()
	router.HandleFunc("api/login", common.LoginHandler).Methods("POST")
	router.HandleFunc("api/register", common.RegisterHandler).Methods("POST")
	router.HandleFunc("/api/register", common.RegisterAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/login", common.LoginAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("api/logout", common.LogoutHandler).Methods("POST")
	router.HandleFunc("/health", common.FastAPIHealthHandler).Methods("GET")
	router.HandleFunc("/api/ask", common.AskAIHandler).Methods("POST")
	router.HandleFunc("/api/tts", common.TTSHandler).Methods("GET")


	corsHandler := handlers.CORS(
		handlers.AllowedOrigins([]string{"http://localhost:5173"}),
		handlers.AllowedMethods([]string{"GET", "POST", "OPTIONS"}),
		handlers.AllowedHeaders([]string{"Content-Type", "Authorization"}),
		handlers.AllowCredentials(),
	)

	fmt.Println("Go server running on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", corsHandler(router)))
}