package data

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"sync"
	"github.com/supabase-community/supabase-go"
)

type User struct {
	ID       int    `json:"id"`      
	Name     string `json:"name"`    
	Email    string `json:"email"`    
	Password string `json:"password"` 
}

var (

	userMu sync.RWMutex
	users = map[string]User{
		"cihanozhan": {ID: 1, Name: "cihanozhan", Email: "", Password: "1234!*."},
	}
)


var supabaseClient *supabase.Client


func InitSupabase() {
	supabaseURL := os.Getenv("SUPABASE_URL")
	supabaseKey := os.Getenv("SUPABASE_KEY")

	fmt.Println("Supabase URL:", supabaseURL)
	fmt.Println("Supabase Key found:", supabaseKey != "")

	if supabaseURL != "" && supabaseKey != "" {
		var err error
		supabaseClient, err = supabase.NewClient(supabaseURL, supabaseKey, nil)
		if err != nil {
			fmt.Println("Warning: Could not connect to Supabase:", err.Error())
			fmt.Println("Falling back to in-memory storage")
			supabaseClient = nil
		} else {
			fmt.Println("Successfully connected to Supabase")
		}
	} else {
		fmt.Println("Supabase credentials not found in environment - using in-memory storage")
	}
}


func RegisterUser(name, email, password string) error {
	name = strings.TrimSpace(name)
	email = strings.ToLower(strings.TrimSpace(email))

	if name == "" {
		return errors.New("name is required")
	}
	if email == "" {
		return errors.New("email is required")
	}
	if password == "" {
		return errors.New("password is required")
	}

	if supabaseClient != nil {
		return registerUserSupabase(name, email, password)
	}

	return registerUserInMemory(name, email, password)
}

func registerUserInMemory(name, email, password string) error {
	userMu.Lock()
	defer userMu.Unlock()

	if _, exists := users[name]; exists {
		return errors.New("user already exists")
	}

	users[name] = User{
		ID:       len(users) + 1, 
		Name:     name,
		Email:    email,
		Password: password,
	}
	fmt.Printf("DEBUG: Registered user in memory - Name: %s, Email: %s\n", name, email)
	return nil
}

func registerUserSupabase(name, email, password string) error {
	exists, err := userExistsSupabase(name, email)
	if err != nil {
		fmt.Println("Error checking if user exists:", err)
		return err
	}
	if exists {
		return errors.New("user already exists")
	}


	userRecord := map[string]interface{}{
		"name":     name,
		"email":    email,
		"password": password,
	}

	fmt.Printf("DAttempting to insert user into Supabase: %s (%s)\n", name, email)

	_, _, err = supabaseClient.
		From("users").
		Insert(userRecord, false, "", "", "").
		Execute()

	if err != nil {
		fmt.Println("Supabase insert error:", err.Error())
		return errors.New("failed to register user: " + err.Error())
	}

	fmt.Println("User successfully registered in Supabase")
	return nil
}

func userExistsSupabase(name, email string) (bool, error) {
	fmt.Printf("Checking if user exists in Supabase - Name: %s, Email: %s\n", name, email)

	data, statusCode, err := supabaseClient.
		From("users").
		Select("id", "", false).
		Or("name.eq."+name+",email.eq."+email, "").
		Execute()

	if err != nil {
		if statusCode == 406 {
			fmt.Println("User not found (this is OK)")
			return false, nil
		}
		fmt.Println("Error checking user:", err.Error())
		return false, err
	}

	responseStr := string(data)
	exists := responseStr != "[]" && responseStr != "" && statusCode == 200

	fmt.Printf("User exists: %v\n", exists)
	return exists, nil
}

func UserIsValid(uName, pwd string) bool {
	if supabaseClient != nil {
		return userIsValidSupabase(uName, pwd)
	}

	return userIsValidInMemory(uName, pwd)
}

func UserIsValidByEmail(email, pwd string) bool {
	email = strings.ToLower(strings.TrimSpace(email))
	if email == "" {
		fmt.Println("UserIsValidByEmail - Empty email provided")
		return false
	}

	fmt.Printf("UserIsValidByEmail called with email: %s\n", email)

	if supabaseClient != nil {
		fmt.Println("Using Supabase for validation")
		return userIsValidByEmailSupabase(email, pwd)
	}

	fmt.Println("Using in-memory storage for validation")
	return userIsValidInMemoryByEmail(email, pwd)
}

func userIsValidInMemoryByEmail(email, pwd string) bool {
	email = strings.ToLower(strings.TrimSpace(email))
	fmt.Printf("DEBUG: Checking in-memory storage for email: %s\n", email)

	userMu.RLock()
	defer userMu.RUnlock()

	for _, u := range users {
		if strings.ToLower(u.Email) == email {
			fmt.Printf("DEBUG: Found user! Password match? %v\n", u.Password == pwd)
			return u.Password == pwd
		}
	}

	fmt.Println("DEBUG: User not found in in-memory storage")
	return false
}

func userIsValidByEmailSupabase(email, pwd string) bool {
	email = strings.ToLower(strings.TrimSpace(email))
	fmt.Printf("DEBUG: userIsValidByEmailSupabase - Email: %s\n", email)

	var result User

	_, err := supabaseClient.
		From("users").
		Select("*", "", false).
		Eq("email", email).
		Single().
		ExecuteTo(&result)

	if err != nil {
		fmt.Printf("Supabase query failed: %v\n", err)
		data, statusCode, _ := supabaseClient.
			From("users").
			Select("*", "", false).
			Eq("email", email).
			Single().
			Execute()
		fmt.Printf("Raw query - Status: %d, Data: %s\n", statusCode, string(data))
		return false
	}

	fmt.Printf("Retrieved user - ID: %d, Name: %s, Email: %s\n",
		result.ID, result.Name, result.Email)
	fmt.Printf("Password match? %v (Stored: %s, Provided: %s)\n",
		result.Password == pwd, result.Password, pwd)

	return result.Password == pwd
}

func userIsValidInMemory(uName, pwd string) bool {
	userMu.RLock()
	user, ok := users[uName]
	userMu.RUnlock()

	if !ok {
		fmt.Printf("User %s not found in in-memory storage\n", uName)
		return false
	}

	fmt.Printf("Found user %s. Password match? %v\n", uName, user.Password == pwd)
	return user.Password == pwd
}


func userIsValidSupabase(uName, pwd string) bool {
	var result User

	_, err := supabaseClient.
		From("users").
		Select("*", "", false).
		Eq("name", uName).
		Single().
		ExecuteTo(&result)

	if err != nil {
		fmt.Printf("DEBUG: Supabase query for user %s failed: %v\n", uName, err)
		return false
	}

	fmt.Printf("DEBUG: Retrieved user %s. Password match? %v\n", uName, result.Password == pwd)
	return result.Password == pwd
}