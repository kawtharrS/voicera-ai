package data

import (
	"errors"
	"strings"
)

var (
	ErrMissingFields       = errors.New("name, email, and password are required")
	ErrWeakPassword        = errors.New("password must be at least 6 characters")
	ErrUserNotFound        = errors.New("user not found")
	ErrUserAlreadyExists   = errors.New("user already exists")
	ErrEmptyEmail          = errors.New("email cannot be empty")
	ErrFailedHashPassword  = errors.New("failed to hash password")
)

const MinPasswordLength = 6

func normalizeEmail(email string) string {
	return strings.ToLower(strings.TrimSpace(email))
}

func normalizeName(name string) string {
	return strings.TrimSpace(name)
}

func normalizePassword(password string) string {
	return strings.TrimSpace(password)
}

func RegisterUser(name, email, password string) error {
	name = normalizeName(name)
	email = normalizeEmail(email)
	password = normalizePassword(password)

	if err := validateRegistration(name, email, password); err != nil {
		return err
	}

	hashed, err := hashPassword(password)
	if err != nil {
		return ErrFailedHashPassword
	}

	if supabaseClient != nil {
		return registerUserSupabase(name, email, hashed)
	}
	return registerUserInMemory(name, email, hashed)
}

func UserIsValid(username, password string) bool {
	username = normalizeName(username)
	password = normalizePassword(password)

	if supabaseClient != nil {
		return userIsValidSupabase(username, password)
	}
	return userIsValidInMemory(username, password)
}

func UserIsValidByEmail(email, password string) bool {
	email = normalizeEmail(email)
	password = normalizePassword(password)

	if email == "" || password == "" {
		return false
	}

	user, err := GetUserByEmail(email)
	if err != nil {
		return false
	}

	return checkPassword(user.Password, password)
}

func GetUserByEmail(email string) (*User, error) {
	email = normalizeEmail(email)

	if email == "" {
		return nil, ErrEmptyEmail
	}

	if supabaseClient != nil {
		return getUserByEmailSupabase(email)
	}
	return getUserByEmailInMemory(email)
}

func validateRegistration(name, email, password string) error {
	if name == "" || email == "" || password == "" {
		return ErrMissingFields
	}
	if len(password) < MinPasswordLength {
		return ErrWeakPassword
	}
	return nil
}

func getUserByEmailSupabase(email string) (*User, error) {
	var result []User
	_, err := supabaseClient.From("users").
		Select("*", "", false).
		Eq("email", email).
		ExecuteTo(&result)

	if err != nil {
		return nil, err
	}

	if len(result) == 0 {
		return nil, ErrUserNotFound
	}

	return &result[0], nil
}

func getUserByEmailInMemory(email string) (*User, error) {
	userMu.RLock()
	defer userMu.RUnlock()

	for _, u := range users {
		if normalizeEmail(u.Email) == email {
			return &u, nil
		}
	}

	return nil, ErrUserNotFound
}

func registerUserSupabase(name, email, hashedPassword string) error {
	var count []map[string]interface{}
	_, err := supabaseClient.From("users").
		Select("id", "count", false).
		Or("name.eq."+name+",email.eq."+email, "").
		ExecuteTo(&count)

	if err == nil && len(count) > 0 {
		return ErrUserAlreadyExists
	}

	record := map[string]interface{}{
		"name":     name,
		"email":    email,
		"password": hashedPassword,
		"role_id":  1,
	}

	_, _, err = supabaseClient.From("users").
		Insert(record, false, "", "", "").
		Execute()

	return err
}

func userIsValidSupabase(username, password string) bool {
	var result []User
	_, err := supabaseClient.From("users").
		Select("*", "", false).
		Eq("name", username).
		ExecuteTo(&result)

	if err != nil || len(result) == 0 {
		return false
	}

	return checkPassword(result[0].Password, password)
}

func registerUserInMemory(name, email, hashedPassword string) error {
	userMu.Lock()
	defer userMu.Unlock()

	if _, exists := users[name]; exists {
		return ErrUserAlreadyExists
	}

	users[name] = User{
		ID:       int64(len(users) + 1),
		Name:     name,
		Email:    email,
		Password: hashedPassword,
		RoleID:   1,
	}

	return nil
}

func userIsValidInMemory(username, password string) bool {
	userMu.RLock()
	defer userMu.RUnlock()

	user, ok := users[username]
	if !ok {
		return false
	}

	return checkPassword(user.Password, password)
}