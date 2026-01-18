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
	UserID int    `json:"user_id"`
	Email  string `json:"email"`
	jwt.RegisteredClaims
}

func GenerateJWT(userID int, email string) (string, error) {
	expirationTime := time.Now().Add(24 * time.Hour)
	claims := &Claims{
		UserID: userID,
		Email:  email,
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

	// Login after register
	user, err := data.GetUserByEmail(req.Email)
	if err == nil {
		token, err := GenerateJWT(user.ID, user.Email)
		if err == nil {
			SetCookie(token, w)
		}
	}

	writeJSON(w, http.StatusCreated, apiResponse{Ok: true, Message: "registered"})
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
	user, err := data.GetUserByEmail(payload.Email)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, apiResponse{Ok: false, Message: "invalid credentials"})
		return
	}
	if user.Password == payload.Password {
		token, err := GenerateJWT(user.ID, user.Email)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, apiResponse{Ok: false, Message: "error generating token"})
			return
		}
		SetCookie(token, w)
		writeJSON(w, http.StatusOK, apiResponse{Ok: true, Message: "logged in"})
		return
	}

	writeJSON(w, http.StatusUnauthorized, apiResponse{Ok: false, Message: "invalid credentials"})
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

func GetUserInfo(request *http.Request) (int, string, error) {
	cookie, err := request.Cookie("access_token")
	if err != nil {
		return 0, "", err
	}

	tokenStr := cookie.Value
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
			return 0, "", fmt.Errorf("invalid signature")
		}
		return 0, "", err
	}

	if !tkn.Valid {
		return 0, "", fmt.Errorf("invalid token")
	}

	return claims.UserID, claims.Email, nil
}
