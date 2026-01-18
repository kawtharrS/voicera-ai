import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/Login";     
import LandingPage from "./pages/Landing";  
import SignUpPage from "./pages/SignUp";
import ChatPage from "./pages/Chat";
import PrefrencesPage from "./pages/Prefrences";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />  
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/prefrences" element={<PrefrencesPage />} />
    </Routes>
  );
}

export default App;