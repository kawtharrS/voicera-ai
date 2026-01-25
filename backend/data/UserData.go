package data

import (
	"sync"

	"github.com/supabase-community/supabase-go"
)

var (
	userMu         sync.RWMutex
	users          = map[string]User{}
	supabaseClient *supabase.Client
)
