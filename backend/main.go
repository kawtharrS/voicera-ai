// Package: main
// This is the entry point for the Voicera Go backend server.
// It sets up HTTP routes and starts listening on port 8080.

package main

import (
	"fmt"      // For printing messages
	"net/http" // Standard library for HTTP request/response handling

	"github.com/gorilla/mux"   // Third-party router library for flexible URL routing
	"github.com/joho/godotenv" // Load environment variables from .env file

	"voicera-backend/common" // Import handlers from the common package
	"voicera-backend/data"   // Import data package for database initialization
)

// router is a Gorilla mux Router that handles all HTTP requests
// Think of it as a "traffic director" that matches URLs to handler functions
var router = mux.NewRouter()

// main() is the function that runs when you start the server
func main() {
	// Load environment variables from .env file (must be done before using them)
	// This reads SUPABASE_URL and SUPABASE_KEY from .env
	err := godotenv.Load()
	if err != nil {
		fmt.Println("⚠️  Note: Could not load .env file (not required if using system env vars)")
	} else {
		fmt.Println("✅ Loaded .env file")
	}

	// NOW initialize Supabase after .env variables are loaded
	// This MUST happen AFTER godotenv.Load() so the environment variables are available
	data.InitSupabase()
	
	// --- SETUP ROUTES ---
	// GET / → Shows the login page
	router.HandleFunc("/", common.LoginPageHandler)

	// GET /index → Shows the user's dashboard (after login)
	router.HandleFunc("/index", common.IndexPageHandler) // GET
	// POST /login → Handles form submission from login page
	router.HandleFunc("/login", common.LoginHandler).Methods("POST")

	// GET /register → Shows the register page
	router.HandleFunc("/register", common.RegisterPageHandler).Methods("GET")
	// POST /register → Handles form submission from register page (traditional HTML form)
	router.HandleFunc("/register", common.RegisterHandler).Methods("POST")

	// --- JSON API ROUTES (for React frontend) ---
	// POST /api/register → Receives JSON from React Sign Up form and returns JSON response
	// OPTIONS /api/register → Handles CORS preflight requests (browser security check)
	router.HandleFunc("/api/register", common.RegisterAPIHandler).Methods("POST", "OPTIONS")

	// POST /api/login → Receives JSON login requests from the React frontend
	router.HandleFunc("/api/login", common.LoginAPIHandler).Methods("POST", "OPTIONS")

	// POST /logout → Clears user session/cookies
	router.HandleFunc("/logout", common.LogoutHandler).Methods("POST")

	// Register the router with the HTTP server
	http.Handle("/", router)

	// Start the HTTP server on localhost:8080
	// This line blocks and keeps the server running until you stop it
	http.ListenAndServe(":8080", nil)
}