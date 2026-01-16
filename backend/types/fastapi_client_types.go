package types 

import(
	"encoding/json"
)

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
}

type UniversalQueryResponse struct {
	Question        string                 `json:"question"`
	Category        string                 `json:"category"`
	Response        string                 `json:"response"`
	Recommendations []string               `json:"recommendations,omitempty"`
	Observation     string                 `json:"observation,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}