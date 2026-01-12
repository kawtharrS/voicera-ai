package main

import (
	"fmt"     
	"net/http" 

	"github.com/gorilla/mux"  
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
	router.HandleFunc("/login", common.LoginHandler).Methods("POST")
	router.HandleFunc("/register", common.RegisterHandler).Methods("POST")
	router.HandleFunc("/api/register", common.RegisterAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/login", common.LoginAPIHandler).Methods("POST", "OPTIONS")
	router.HandleFunc("/logout", common.LogoutHandler).Methods("POST")
	router.HandleFunc("/health", common.FastAPIHealthHandler).Methods("GET")

	http.Handle("/", router)
	fmt.Println("🚀 Go server running on http://localhost:8080")
if err := http.ListenAndServe(":8080", nil); err != nil {
	panic(err)
}

}