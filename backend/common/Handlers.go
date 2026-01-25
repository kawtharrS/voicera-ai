package common

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"voicera-backend/data"
	"voicera-backend/helpers"

	"github.com/golang-jwt/jwt/v5"
)

var jwtKey = []byte(os.Getenv("JWT_SECRET"))

type Claims struct {
	UserID int64  `json:"user_id"`
	Email  string `json:"email"`
	RoleID int    `json:"role_id"`
	jwt.RegisteredClaims
}

func GenerateJWT(userID int64, email string, roleID int) (string, error) {
	expirationTime := time.Now().Add(24 * time.Hour)
	claims := &Claims{
		UserID: userID,
		Email:  email,
		RoleID: roleID,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	key := jwtKey
	if len(key) == 0 {
		key = []byte("default_secret_key")
	}
	return token.SignedString(key)
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

func writeJSON(w http.ResponseWriter, status int, payload apiResponse) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func RegisterAPIHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	var req registerRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "invalid JSON"})
		return
	}

	if helpers.IsEmpty(req.Name) || helpers.IsEmpty(req.Email) || helpers.IsEmpty(req.Password) {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "name, email, and password are required"})
		return
	}

	if req.Password != req.ConfirmPassword {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "passwords do not match"})
		return
	}

	if err := data.RegisterUser(req.Name, req.Email, req.Password); err != nil {
		writeJSON(w, http.StatusConflict, apiResponse{Ok: false, Message: err.Error()})
		return
	}

	var token string
	user, err := data.GetUserByEmail(req.Email)
	if err == nil {
		token, _ = GenerateJWT(user.ID, user.Email, user.RoleID)
		if token != "" {
			SetCookie(token, w)
		}
	}

	writeJSON(w, http.StatusCreated, apiResponse{Ok: true, Message: "registered", Token: token})
}

func LoginAPIHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	var payload struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "invalid JSON"})
		return
	}

	if helpers.IsEmpty(payload.Email) || helpers.IsEmpty(payload.Password) {
		writeJSON(w, http.StatusBadRequest, apiResponse{Ok: false, Message: "email and password are required"})
		return
	}
	if !data.UserIsValidByEmail(payload.Email, payload.Password) {
		writeJSON(w, http.StatusUnauthorized, apiResponse{Ok: false, Message: "invalid credentials"})
		return
	}

	user, err := data.GetUserByEmail(payload.Email)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "could not load user"})
		return
	}

	token, err := GenerateJWT(user.ID, user.Email, user.RoleID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "error generating token"})
		return
	}
	SetCookie(token, w)
	writeJSON(w, http.StatusOK, apiResponse{Ok: true, Message: "logged in", Token: token})
}

func LogoutHandler(response http.ResponseWriter, request *http.Request) {
	ClearCookie(response)
	http.Redirect(response, request, "/", 302)
}

func SetCookie(token string, response http.ResponseWriter) {
	cookie := &http.Cookie{
		Name:     "access_token",
		Value:    token,
		Path:     "/",
		MaxAge:   86400,
		HttpOnly: true,
		Secure:   false,
		SameSite: http.SameSiteLaxMode,
	}
	http.SetCookie(response, cookie)
	fmt.Println("Cookie set")
}

func ClearCookie(response http.ResponseWriter) {
	cookie := &http.Cookie{
		Name:   "access_token",
		Value:  "",
		Path:   "/",
		MaxAge: -1,
	}
	http.SetCookie(response, cookie)
}

func GetUserInfo(request *http.Request) (int64, string, int, error) {
	var tokenStr string

	authHeader := request.Header.Get("Authorization")
	if authHeader != "" && len(authHeader) > 7 && authHeader[:7] == "Bearer " {
		tokenStr = authHeader[7:]
	} else {
		cookie, err := request.Cookie("access_token")
		if err != nil {
			return 0, "", 0, err
		}
		tokenStr = cookie.Value
	}

	claims := &Claims{}

	key := jwtKey
	if len(key) == 0 {
		key = []byte("default_secret_key")
	}

	tkn, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		return key, nil
	})

	if err != nil {
		if err == jwt.ErrSignatureInvalid {
			return 0, "", 0, fmt.Errorf("invalid signature")
		}
		return 0, "", 0, err
	}

	if !tkn.Valid {
		return 0, "", 0, fmt.Errorf("invalid token")
	}

	return claims.UserID, claims.Email, claims.RoleID, nil
}

type UserInfoResponse struct {
	ID     int64  `json:"id"`
	Email  string `json:"email"`
	RoleID int    `json:"role_id"`
}

func UserInfoHandler(w http.ResponseWriter, r *http.Request) {
	helpers.SetHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	userID, email, roleID, err := GetUserInfo(r)
	if err != nil || userID == 0 {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(UserInfoResponse{ID: 0, Email: "", RoleID: 0})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(UserInfoResponse{ID: userID, Email: email, RoleID: roleID})
}
