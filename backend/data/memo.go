package data

import (
	"errors"
	"fmt"
)

func SaveUserMemo(userID int64, userQuery, aiQuery, category, emotion string) (*UserMemo, error) {
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
	_, err := supabaseClient.From("user_memo").
		Insert(record, false, "", "", "").
		ExecuteTo(&result)

	if err != nil || len(result) == 0 {
		return nil, errors.New("failed to save memo")
	}
	return &result[0], nil
}

func GetUserMemos(userID int64, limit int) ([]UserMemo, error) {
	if supabaseClient == nil {
		return nil, errors.New("supabase client not initialized")
	}
	var memos []UserMemo
	_, err := supabaseClient.From("user_memo").
		Select("*", "", false).
		Eq("user_id", fmt.Sprintf("%d", userID)).
		Limit(limit, "").
		ExecuteTo(&memos)

	return memos, err
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
	_, err := supabaseClient.From("preferences").
		Insert(record, false, "", "", "").
		ExecuteTo(&result)

	if err != nil || len(result) == 0 {
		return nil, errors.New("failed to save preference")
	}
	return &result[0], nil
}

func registerUserInMemory(name, email, hashedPassword string) error {
	userMu.Lock()
	defer userMu.Unlock()

	if _, exists := users[name]; exists {
		return errors.New("user already exists")
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
