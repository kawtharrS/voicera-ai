// This package contains all HTTP request handlers
package common

import (
	"encoding/json"
	"fmt"
	"net/http"

	"voicera-backend/data"
	"voicera-backend/helpers"

	"github.com/gorilla/securecookie"
)

var cookieHandler = securecookie.New(
	securecookie.GenerateRandomKey(64),
	securecookie.GenerateRandomKey(32))

func LoginPageHandler(response http.ResponseWriter, request *http.Request) {
	var body, _ = helpers.LoadFile("templates/login.html")
	fmt.Fprint(response, body)
}

func LoginHandler(response http.ResponseWriter, request *http.Request) {
	name := request.FormValue("name")
	pass := request.FormValue("password")
	redirectTarget := "/"

	if !helpers.IsEmpty(name) && !helpers.IsEmpty(pass) {
		_userIsValid := data.UserIsValid(name, pass)

		if _userIsValid {
			SetCookie(name, response)
			redirectTarget = "/index"
		} else {
			redirectTarget = "/register"
		}
	}
	http.Redirect(response, request, redirectTarget, 302)
}

func RegisterPageHandler(response http.ResponseWriter, request *http.Request) {
	var body, _ = helpers.LoadFile("templates/register.html")
	fmt.Fprint(response, body)
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
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:5173")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Access-Control-Allow-Credentials", "true")

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

	SetCookie(req.Name, w)

	writeJSON(w, http.StatusCreated, apiResponse{Ok: true, Message: "registered"})
}

func LoginAPIHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "http://localhost:5173")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Access-Control-Allow-Credentials", "true")

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

	// Try email-based login first (frontend sends `email` field)
	if data.UserIsValidByEmail(payload.Email, payload.Password) {
		SetCookie(payload.Email, w)
		writeJSON(w, http.StatusOK, apiResponse{Ok: true, Message: "logged in"})
		return
	}

	// Fallback: treat the provided value as a username
	if data.UserIsValid(payload.Email, payload.Password) {
		SetCookie(payload.Email, w)
		writeJSON(w, http.StatusOK, apiResponse{Ok: true, Message: "logged in"})
		return
	}

	writeJSON(w, http.StatusUnauthorized, apiResponse{Ok: false, Message: "invalid credentials"})
}

func RegisterHandler(w http.ResponseWriter, r *http.Request) {
	r.ParseForm()

	uName := r.FormValue("username")
	email := r.FormValue("email")
	pwd := r.FormValue("password")
	confirmPwd := r.FormValue("confirmPassword")

	_uName, _email, _pwd, _confirmPwd := false, false, false, false
	_uName = !helpers.IsEmpty(uName)
	_email = !helpers.IsEmpty(email)
	_pwd = !helpers.IsEmpty(pwd)
	_confirmPwd = !helpers.IsEmpty(confirmPwd)
	if _uName && _email && _pwd && _confirmPwd {
		fmt.Fprintln(w, "Username for Register : ", uName)
		fmt.Fprintln(w, "Email for Register : ", email)
		fmt.Fprintln(w, "Password for Register : ", pwd)
		fmt.Fprintln(w, "ConfirmPassword for Register : ", confirmPwd)
	} else {
		fmt.Fprintln(w, "This fields can not be blank!")
	}
}

func LogoutHandler(response http.ResponseWriter, request *http.Request) {
	ClearCookie(response)
	http.Redirect(response, request, "/", 302)
}

func SetCookie(userName string, response http.ResponseWriter) {
	value := map[string]string{
		"name": userName,
	}

	if encoded, err := cookieHandler.Encode("cookie", value); err == nil {
		cookie := &http.Cookie{
			Name:   "cookie",
			Value:  encoded,
			Path:   "/",
			MaxAge: 86400, // 24 hours
		}
		http.SetCookie(response, cookie)
	}
}

func ClearCookie(response http.ResponseWriter) {
	cookie := &http.Cookie{
		Name:   "cookie",
		Value:  "",
		Path:   "/",
		MaxAge: -1,
	}
	http.SetCookie(response, cookie)
}

func GetUserName(request *http.Request) (userName string) {
	if cookie, err := request.Cookie("cookie"); err == nil {
		cookieValue := make(map[string]string)

		if err = cookieHandler.Decode("cookie", cookie.Value, &cookieValue); err == nil {
			userName = cookieValue["name"]
		}
	}
	return userName
}