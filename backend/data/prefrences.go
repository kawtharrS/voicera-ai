package data

import (
	"errors"
	"fmt"
	"github.com/supabase-community/postgrest-go"
)

func GetLatestUserPreference(userID int64) (*Preference, error) {
	if supabaseClient == nil {
		return nil, errors.New("supabase client not initialized")
	}

	var prefs []Preference
	_, err := supabaseClient.From("preferences").
		Select("*", "", false).
		Eq("user_id", fmt.Sprintf("%d", userID)).
		Order("id", &postgrest.OrderOpts{Ascending: false}).
		Limit(1, "").
		ExecuteTo(&prefs)

	if err != nil || len(prefs) == 0 {
		return nil, errors.New("no preferences found")
	}

	return &prefs[0], nil
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
