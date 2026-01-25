package common 
import (
	"github.com/golang-jwt/jwt/v5"
	"encoding/json"
	"time"
)

type SavePreferenceRequest struct {
	UserID     int64  `json:"user_id"`
	Language   string `json:"language"`
	Tone       string `json:"tone"`
	Name       string `json:"name"`
	Preference string `json:"preference"`
}

type registerRequest struct {
	Name            string `json:"name"`
	Email           string `json:"email"`
	Password        string `json:"password"`
	ConfirmPassword string `json:"confirmPassword"`
}

type apiResponse struct {
	Ok      bool   `json:"ok"`
	Message string `json:"message"`
	Token   string `json:"token,omitempty"`
}

type UserInfoResponse struct {
	ID     int64  `json:"id"`
	Email  string `json:"email"`
	RoleID int    `json:"role_id"`
}


type Claims struct {
	UserID int64  `json:"user_id"`
	Email  string `json:"email"`
	RoleID int    `json:"role_id"`
	jwt.RegisteredClaims
}

type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

type StudentQuestion struct {
	Question            string                   `json:"question"`
	CourseID            string                   `json:"course_id,omitempty"`
	StudentID           string                   `json:"student_id,omitempty"`
	ConversationHistory []map[string]interface{} `json:"conversation_history,omitempty"`
}

type UniversalQueryRequest struct {
	Question            string                   `json:"question"`
	StudentID           string                   `json:"student_id,omitempty"`
	CourseID            string                   `json:"course_id,omitempty"`
	ThreadID            string                   `json:"thread_id,omitempty"`
	ConversationHistory []map[string]interface{} `json:"conversation_history,omitempty"`
	Preferences         *Preferences             `json:"preferences,omitempty"`
}

type AIResponse struct {
	Question        string          `json:"question"`
	Response        string          `json:"response"`
	Recommendations json.RawMessage `json:"recommendations"`
	Feedback        string          `json:"feedback"`
	Sendable        bool            `json:"sendable"`
	Trials          int             `json:"trials"`
	Observation     string          `json:"observation"`
	Category        string          `json:"category,omitempty"`
	Emotion         string          `json:"emotion,omitempty"`
}

type UniversalQueryResponse struct {
	Question        string                 `json:"question"`
	Category        string                 `json:"category"`
	Response        string                 `json:"response"`
	Recommendations []string               `json:"recommendations,omitempty"`
	Observation     string                 `json:"observation,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
	Emotion         string                 `json:"emotion,omitempty"`
}

type Preferences struct {
	Language string  `json:"language"`
	UserId string `json:"user_id"`
	Tone string `json:"tone"`
	Name string `json:"name"`
	Prefrences string `json:"prefrences"`
}

type EmotionLog struct {
	ID        int64     `gorm:"primaryKey"`
	UserID    int64     `gorm:"index"`
	Emotion   string
	CreatedAt time.Time
	UpdatedAt time.Time
}

