package data

import (
	"fmt"
	"os"
	"github.com/supabase-community/supabase-go"
)

func InitSupabase() {
	supabaseURL := os.Getenv("SUPABASE_URL")
	supabaseKey := os.Getenv("SUPABASE_KEY")

	if supabaseURL == "" || supabaseKey == "" {
		return
	}

	client, err := supabase.NewClient(supabaseURL, supabaseKey, nil)
	if err != nil {
		return
	}

	supabaseClient = client
	fmt.Println("Successfully connected to Supabase HTTP API")
}