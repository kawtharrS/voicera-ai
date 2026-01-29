import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/Login";
import LandingPage from "./pages/Landing";
import SignUpPage from "./pages/SignUp";
import PrefrencesPage from "./pages/Prefrences";
import VoiceraSwipeScreen from "./components/chatting/chat";

const isAuthenticated = () => {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem("voicera_logged_in") === "true";
};

function ProtectedRoute({ children }: { children: React.ReactElement }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />  
      <Route path="/signup" element={<SignUpPage />} />
      <Route
        path="/prefrences"
        element={
          <ProtectedRoute>
            <PrefrencesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <VoiceraSwipeScreen />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
