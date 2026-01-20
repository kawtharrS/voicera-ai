package data

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"
	"sync"

	"github.com/supabase-community/supabase-go"
	"golang.org/x/crypto/bcrypt"
)

type User struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	Email    string `json:"email"`
	Password string `json:"password"`
	RoleID   int    `json:"role_id"`
}

type UserMemo struct {
	ID        int64  `json:"id"`
	UserID    int64  `json:"user_id"`
	UserQuery string `json:"user_query"`
	AIQuery   string `json:"ai_query"`
	Category  string `json:"category"`
	Emotion   string `json:"emotion"`
}

type SaveMemoRequest struct {
	UserID    int64  `json:"user_id"`
	UserQuery string `json:"user_query"`
	AIQuery   string `json:"ai_query"`
	Category  string `json:"category"`
	Emotion   string `json:"emotion"`
}

type Preference struct {
	ID         int64  `json:"id"`
	UserID     int64  `json:"user_id"`
	Language   string `json:"language"`
	Tone       string `json:"tone"`
	Name       string `json:"name"`
	Preference string `json:"preference"`
}

var (
	userMu sync.RWMutex
	users  = map[string]User{}
)

var supabaseClient *supabase.Client

func hashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

func checkPassword(hashedPassword, password string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
	return err == nil
}

func InitSupabase() {
	supabaseURL := os.Getenv("SUPABASE_URL")
	supabaseKey := os.Getenv("SUPABASE_KEY")

	if supabaseURL == "" || supabaseKey == "" {
		fmt.Println("Supabase credentials not found — using in-memory storage")
		return
	}

	client, err := supabase.NewClient(supabaseURL, supabaseKey, nil)
	if err != nil {
		fmt.Println("Warning: Could not connect to Supabase:", err)
		return
	}

	supabaseClient = client
	fmt.Println("Successfully connected to Supabase")
}

func RegisterUser(name, email, password string) error {
	name = strings.TrimSpace(name)
	email = strings.ToLower(strings.TrimSpace(email))

	if name == "" || email == "" || password == "" {
		return errors.New("name, email, and password are required")
	}

	if len(password) < 6 {
		return errors.New("password must be at least 6 characters")
	}

	hashed, err := hashPassword(password)
	if err != nil {
		return errors.New("failed to hash password")
	}

	if supabaseClient != nil {
		return registerUserSupabase(name, email, hashed)
	}

	return registerUserInMemory(name, email, hashed)
}

func registerUserInMemory(name, email, hashedPassword string) error {
	userMu.Lock()
	defer userMu.Unlock()

	if _, exists := users[name]; exists {
		return errors.New("user already exists")
	}

	users[name] = User{
		ID:       len(users) + 1,
		Name:     name,
		Email:    email,
		Password: hashedPassword,
		RoleID:   1, // Default RoleID for new users
	}

	return nil
}

func registerUserSupabase(name, email, hashedPassword string) error {
	exists, err := userExistsSupabase(name, email)
	if err != nil {
		return err
	}
	if exists {
		return errors.New("user already exists")
	}

	record := map[string]interface{}{
		"name":     name,
		"email":    email,
		"password": hashedPassword,
		"role_id":  1, // Default RoleID for new users
	}

	_, _, err = supabaseClient.
		From("users").
		Insert(record, false, "", "", "").
		Execute()

	return nil
}

func userExistsSupabase(name, email string) (bool, error) {
	data, status, err := supabaseClient.
		From("users").
		Select("id", "", false).
		Or("name.eq."+name+",email.eq."+email, "").
		Execute()

	if err != nil {
		if status == 406 {
			return false, nil
		}
		return false, err
	}

	return string(data) != "[]" && status == 200, nil
}

func UserIsValid(username, password string) bool {
	username = strings.TrimSpace(username)
	password = strings.TrimSpace(password)

	fmt.Printf("[DEBUG] UserIsValid called with username: %s, password length: %d\n", username, len(password))

	if supabaseClient != nil {
		return userIsValidSupabase(username, password)
	}
	return userIsValidInMemory(username, password)
}

func UserIsValidByEmail(email, password string) bool {
	email = strings.ToLower(strings.TrimSpace(email))
	password = strings.TrimSpace(password)

	if email == "" || password == "" {
		return false
	}

	if supabaseClient != nil {
		user, err := GetUserByEmail(email)
		if err != nil {
			return false
		}
		isValid := checkPassword(user.Password, password)
		return isValid
	}

	return userIsValidInMemoryByEmail(email, password)
}

func userIsValidSupabase(username, password string) bool {
	var user User

	data, status, err := supabaseClient.
		From("users").
		Select("*", "", false).
		Eq("name", username).
		Single().
		Execute()

	if err != nil || status != 200 {
		fmt.Printf("[DEBUG] Supabase query error for username %s: %v (status: %d)\n", username, err, status)
		return false
	}

	var users []User
	if err := json.Unmarshal(data, &users); err != nil {
		return false
	}

	if len(users) == 0 {
		return false
	}

	user = users[0]

	isValid := checkPassword(user.Password, password)
	fmt.Printf("[DEBUG] Password comparison result for %s: %v\n", username, isValid)
	return isValid
}

func userIsValidByEmailSupabase(email, password string) bool {
	data, status, err := supabaseClient.
		From("users").
		Select("*", "", false).
		Eq("email", email).
		Single().
		Execute()

	if err != nil || status != 200 {
		return false
	}

	var users []User
	if err := json.Unmarshal(data, &users); err != nil {
		return false
	}

	if len(users) == 0 {
		return false
	}

	user := users[0]

	isValid := checkPassword(user.Password, password)
	return isValid
}

func userIsValidInMemory(username, password string) bool {
	userMu.RLock()
	defer userMu.RUnlock()

	user, ok := users[username]
	if !ok {
		return false
	}

	isValid := checkPassword(user.Password, password)
	return isValid
}

func userIsValidInMemoryByEmail(email, password string) bool {
	userMu.RLock()
	defer userMu.RUnlock()

	for _, user := range users {
		if strings.ToLower(user.Email) == email {

			isValid := checkPassword(user.Password, password)
			return isValid
		}
	}
	return false
}

func SaveUserMemo(userID int64, userQuery, aiQuery string, category string, emotion string) (*UserMemo, error) {
	if supabaseClient == nil {
		return nil, errors.New("supabase client not initialized")
	}

	record := map[string]interface{}{
		"user_id":    userID,
		"user_query": userQuery,
		"ai_query":   aiQuery,
		"category":   category,
		"emotion":    emotion,
	}

	var result []UserMemo
	_, err := supabaseClient.
		From("user_memo").
		Insert(record, false, "", "", "").
		ExecuteTo(&result)

	if err != nil || len(result) == 0 {
		return nil, errors.New("failed to save memo")
	}

	return &result[0], nil
}

func GetUserMemos(userID int64, limit int) ([]UserMemo, error) {
	var memos []UserMemo

	_, err := supabaseClient.
		From("user_memo").
		Select("*", "", false).
		Eq("user_id", fmt.Sprintf("%d", userID)).
		Limit(limit, "").
		ExecuteTo(&memos)

	return memos, err
}

func GetUserByEmail(email string) (*User, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	if email == "" {
		return nil, errors.New("email cannot be empty")
	}

	if supabaseClient != nil {
		var users []User
		data, _, err := supabaseClient.
			From("users").
			Select("*", "", false).
			Eq("email", email).
			Execute()

		if err != nil {
			return nil, err
		}

		if err := json.Unmarshal(data, &users); err != nil || len(users) == 0 {
			return nil, errors.New("user not found")
		}

		return &users[0], nil
	}

	userMu.RLock()
	defer userMu.RUnlock()
	for _, u := range users {
		if strings.ToLower(u.Email) == email {
			return &u, nil
		}
	}
	return nil, errors.New("user not found")
}

func SaveUserPreference(userID int64, language, tone, name, preference string) (*Preference, error) {
	if supabaseClient == nil {
		return nil, errors.New("supabase client not initialized")
	}

	record := map[string]interface{}{
		"user_id":    userID,
		"language":   language,
		"tone":       tone,
		"name":       name,
		"preference": preference,
	}

	var result []Preference
	_, err := supabaseClient.
		From("preferences").
		Insert(record, false, "", "", "").
		ExecuteTo(&result)

	if err != nil || len(result) == 0 {
		return nil, errors.New("failed to save preference")
	}

	return &result[0], nil
}

func GetLatestUserPreference(userID int64) (*Preference, error) {
	if supabaseClient == nil {
		return nil, errors.New("supabase client not initialized")
	}

	var prefs []Preference
	_, err := supabaseClient.
		From("preferences").
		Select("*", "", false).
		Eq("user_id", fmt.Sprintf("%d", userID)).
		ExecuteTo(&prefs)

	if err != nil || len(prefs) == 0 {
		return nil, errors.New("no preferences found")
	}

	latest := prefs[0]
	for _, p := range prefs {
		if p.ID > latest.ID {
			latest = p
		}
	}

	return &latest, nil
}
