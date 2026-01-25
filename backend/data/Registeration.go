package data

import (
	"errors"
	"strings"
)

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

func UserIsValid(username, password string) bool {
	username = strings.TrimSpace(username)
	password = strings.TrimSpace(password)

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

	user, err := GetUserByEmail(email)
	if err != nil {
		return false
	}
	return checkPassword(user.Password, password)
}

func GetUserByEmail(email string) (*User, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	if email == "" {
		return nil, errors.New("email cannot be empty")
	}

	if supabaseClient != nil {
		var result []User
		_, err := supabaseClient.From("users").
			Select("*", "", false).
			Eq("email", email).
			ExecuteTo(&result)

		if err != nil {
			return nil, err
		}
		if len(result) == 0 {
			return nil, errors.New("user not found")
		}
		return &result[0], nil
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
func registerUserSupabase(name, email, hashedPassword string) error {
	var count []map[string]interface{}
	_, err := supabaseClient.From("users").
		Select("id", "count", false).
		Or("name.eq."+name+",email.eq."+email, "").
		ExecuteTo(&count)

	if err == nil && len(count) > 0 {
		return errors.New("user already exists")
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