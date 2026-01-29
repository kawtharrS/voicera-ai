import React, { useState } from "react";
import styles from "./SignUp.module.css";
import InputField from "../common/InputField/InputField";
import Button from "../common/Button/Button";
import type { LoginFormData, LoginProps } from "./types";
import { UserIcon, LockIcon, ChevronLeftIcon } from "../common/Icons/Icons";
import api from "../../api/axios";
import { useNavigate } from "react-router-dom";

const Login: React.FC<LoginProps> = ({ onBack }) => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: "",
    password: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setError(null);
    setSuccess(null);
    try {
      setSubmitting(true);
      await api.post("/login", formData);
      setSuccess("Account logged in successfully.");
      setFormData({ email: "", password: "", });
      // Mark user as authenticated for route guards
      if (typeof window !== "undefined") {
        window.localStorage.setItem("voicera_logged_in", "true");
      }
      // After login, go straight to chat (preferences are already set or optional)
      setTimeout(() => navigate("/chat"), 500);
    } catch {
      setError("Could not connect to server.");
    } finally {
    setSubmitting(false);
  }
  };

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      console.log("Back clicked");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <Button variant="back" onClick={handleBack}>
            <ChevronLeftIcon />
            BACK
          </Button>
          <h1 className={styles.title}>LOGIN</h1>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          {error && (
            <div style={{ color: "#b00020", fontSize: 13 }}>{error}</div>
          )}
          {success && (
            <div style={{ color: "#2e7d32", fontSize: 13 }}>{success}</div>
          )}
          <div className={styles.inputGroup}>
            <InputField
              type="email"
              placeholder="Email ID"
              icon={<UserIcon />}
              value={formData.email}
              onChange={handleChange}
              name="email"
            />
            <InputField
              type="password"
              placeholder="Password"
              icon={<LockIcon />}
              value={formData.password}
              onChange={handleChange}
              name="password"
            />

          </div>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={submitting}
          >
            {submitting ? "LOGGING IN..." : "LOGIN IN"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
