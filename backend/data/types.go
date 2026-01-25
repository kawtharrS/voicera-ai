package data

type User struct {
	ID       int64  `json:"id"`
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

type Preference struct {
	ID         int64  `json:"id"`
	UserID     int64  `json:"user_id"`
	Language   string `json:"language"`
	Tone       string `json:"tone"`
	Name       string `json:"name"`
	Preference string `json:"preference"`
}

type SaveMemoRequest struct {
	UserID    int64  `json:"user_id"`
	UserQuery string `json:"user_query"`
	AIQuery   string `json:"ai_query"`
	Category  string `json:"category"`
	Emotion   string `json:"emotion"`
}