// Package: data
// This package handles all database operations for user management
// Currently supports both in-memory storage (for dev/testing) and Supabase (for production)

package data

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"sync"

	"github.com/supabase-community/supabase-go"
)

// User represents a user account with login credentials
// This struct is used for in-memory storage and matches the Supabase table structure
type User struct {
	ID       string `json:"id"`       // Unique identifier (UUID from Supabase)
	Name     string `json:"name"` // Username
	Email    string `json:"email"`    // Email address
	Password string `json:"password"` // Password (in production, should be hashed!)
}

// --- IN-MEMORY STORAGE (for development/testing without Supabase) ---

var (
	// userMu protects concurrent access to the users map
	// This ensures multiple requests don't corrupt the data
	userMu sync.RWMutex
	// users is an in-memory database (not persistent across server restarts)
	// Maps username → User struct
	users = map[string]User{
		// Seed user to keep existing demo login working.
		"cihanozhan": {ID: "demo-user", Name: "cihanozhan", Email: "", Password: "1234!*."},
	}
)

// --- SUPABASE CLIENT ---

// supabaseClient is the connection to Supabase database
// Initialized when InitSupabase() is called in main.go
var supabaseClient *supabase.Client

// InitSupabase sets up the Supabase connection using environment variables
// THIS MUST BE CALLED FROM main() AFTER godotenv.Load()
// It reads SUPABASE_URL and SUPABASE_KEY from the environment
func InitSupabase() {
	// Get Supabase credentials from environment variables
	supabaseURL := os.Getenv("SUPABASE_URL")
	supabaseKey := os.Getenv("SUPABASE_KEY")

	fmt.Println("DEBUG: Supabase URL:", supabaseURL)
	fmt.Println("DEBUG: Supabase Key found:", supabaseKey != "")

	// Only initialize Supabase if both URL and Key are provided
	if supabaseURL != "" && supabaseKey != "" {
		var err error
		// Create a connection to Supabase
		// This connects to your Supabase project
		supabaseClient, err = supabase.NewClient(supabaseURL, supabaseKey, nil)
		if err != nil {
			// Print error but don't crash - fall back to in-memory storage
			fmt.Println("❌ Warning: Could not connect to Supabase:", err.Error())
			fmt.Println("⚠️  Falling back to in-memory storage")
			supabaseClient = nil
		} else {
			fmt.Println("✅ Successfully connected to Supabase")
		}
	} else {
		fmt.Println("⚠️  Supabase credentials not found in environment - using in-memory storage")
	}
}

// --- DATABASE FUNCTIONS ---

// RegisterUser creates a new user account
// If Supabase is available, saves to Supabase; otherwise uses in-memory storage
// Input: username, email, password
// Output: error if registration fails (user exists, invalid input, database error)
func RegisterUser(name, email, password string) error {
	// Trim whitespace from inputs
	name = strings.TrimSpace(name)
	email = strings.TrimSpace(email)

	// Validate required fields
	if name == "" {
		return errors.New("name is required")
	}
	if password == "" {
		return errors.New("password is required")
	}

	// Check if Supabase is available
	if supabaseClient != nil {
		// Use Supabase
		return registerUserSupabase(name, email, password)
	}

	// Fall back to in-memory storage
	return registerUserInMemory(name, email, password)
}

// registerUserInMemory saves a user to the in-memory map
// This is used when Supabase is not available
func registerUserInMemory(name, email, password string) error {
	userMu.Lock()
	defer userMu.Unlock()

	// Check if user already exists
	if _, exists := users[name]; exists {
		return errors.New("user already exists")
	}

	// Create new user and add to map
	users[name] = User{
		ID:       name, // Use username as ID in development
		Name:     name,
		Email:    email,
		Password: password,
	}
	return nil
}

// registerUserSupabase saves a user to the Supabase database
// Input: username, email, password
// Output: error if user exists or database fails
func registerUserSupabase(name, email, password string) error {
	// Check if user already exists in Supabase
	exists, err := userExistsSupabase(name)
	if err != nil {
		fmt.Println("DEBUG: Error checking if user exists:", err)
		return err
	}
	if exists {
		return errors.New("user already exists")
	}

	// Prepare the data to insert into Supabase
	// The table name should be "users" in your Supabase project
	userRecord := map[string]interface{}{
		"name": name,     // Column name in Supabase (adjust if different)
		"email":    email,    // Column name in Supabase (adjust if different)
		"password": password, // Column name in Supabase (adjust if different)
	}

	fmt.Println("DEBUG: Attempting to insert user into Supabase:", name, email)

	// Insert the user into Supabase
	// Replace "users" with your actual table name if different
	// Execute() returns 3 values: data (response body), statusCode, error
	data, statusCode, err := supabaseClient.
		From("users").
		Insert(userRecord, false, "", "", "").
		Execute()

	if err != nil {
		fmt.Println("DEBUG: Supabase insert error:", err.Error())
		fmt.Println("DEBUG: Status code:", statusCode)
		fmt.Println("DEBUG: Response data:", string(data))
		return errors.New("failed to register user: " + err.Error())
	}

	fmt.Println("DEBUG: User successfully registered in Supabase (status code:", statusCode, ")")
	return nil
}

// userExistsSupabase checks if a user already exists in Supabase
// This prevents duplicate registrations
func userExistsSupabase(name string) (bool, error) {
	fmt.Println("DEBUG: Checking if user exists in Supabase:", name)
	
	// Query Supabase for users with matching name
	data, statusCode, err := supabaseClient.
		From("users").
		Select("id", "", false).
		Eq("name", name).
		Execute()

	fmt.Println("DEBUG: Query status code:", statusCode)
	fmt.Println("DEBUG: Query response:", string(data))
	fmt.Println("DEBUG: Query error:", err)

	// If there's an error, check if it's a "not found" error (status 406)
	// Status 406 means no rows matched the filter
	if statusCode == 406 || (err != nil && strings.Contains(err.Error(), "not found")) {
		fmt.Println("DEBUG: User not found (this is OK, user doesn't exist yet)")
		return false, nil
	}

	// If there's a different error, return it
	if err != nil {
		fmt.Println("DEBUG: Error checking user:", err.Error())
		return false, err
	}

	// If status code is 200 and we got data, check if there are results
	// Empty array [] means no users found, non-empty means user exists
	responseStr := string(data)
	exists := responseStr != "[]" && responseStr != "" && statusCode == 200
	
	fmt.Println("DEBUG: User exists:", exists)
	return exists, nil
}

// UserIsValid checks if a user's password is correct
// If Supabase is available, checks against Supabase; otherwise uses in-memory storage
// Input: username and password
// Output: true if password matches, false otherwise
func UserIsValid(uName, pwd string) bool {
	// Check if Supabase is available
	if supabaseClient != nil {
		// Use Supabase
		return userIsValidSupabase(uName, pwd)
	}

	// Fall back to in-memory storage
	return userIsValidInMemory(uName, pwd)
}

// userIsValidInMemory checks password against in-memory storage
func userIsValidInMemory(uName, pwd string) bool {
	userMu.RLock()
	user, ok := users[uName]
	userMu.RUnlock()

	if !ok {
		return false
	}
	return user.Password == pwd
}

// userIsValidSupabase checks password against Supabase database
// This retrieves the user from Supabase and compares the password
func userIsValidSupabase(uName, pwd string) bool {
	var result User

	// Query Supabase for user with matching username
	// Replace "users" and "username" with your actual table/column names
	_, err := supabaseClient.
		From("users").
		Select("*", "", false).
		Eq("name", uName).
		Single().
		ExecuteTo(&result)

	// If user not found or error occurs, password is invalid
	if err != nil {
		return false
	}

	// Check if password matches
	return result.Password == pwd
}