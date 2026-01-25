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
