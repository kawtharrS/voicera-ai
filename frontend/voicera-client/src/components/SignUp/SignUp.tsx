import React, { useState } from "react";
import styles from "./SignUp.module.css";
import InputField from "../common/InputField";
import Button from "../common/Button";
import {
  UserIcon,
  LockIcon,
  GoogleIcon,
  ChevronLeftIcon,
} from "../common/Icons";

interface SignUpFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface SignUpProps {
  onBack?: () => void;
}

const SignUp: React.FC<SignUpProps> = ({ onBack }) => {
  const [formData, setFormData] = useState<SignUpFormData>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

    if (!formData.name || !formData.email || !formData.password) {
      setError("Please fill in all required fields.");
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setSubmitting(true);
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      const data = (await res.json().catch(() => null)) as {
        ok?: boolean;
        message?: string;
      } | null;

      if (!res.ok) {
        setError(data?.message || "Sign up failed.");
        return;
      }

      setSuccess("Account created successfully.");
      setFormData({ name: "", email: "", password: "", confirmPassword: "" });

      // Optional: go back to Landing after a short delay
      setTimeout(() => {
        onBack?.();
      }, 600);
    } catch {
      setError("Could not connect to server.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleSignIn = () => {
    console.log("Google sign in clicked");
    // Add Google sign-in logic here
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
          <h1 className={styles.title}>SIGN UP</h1>
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
              type="text"
              placeholder="Name"
              icon={<UserIcon />}
              value={formData.name}
              onChange={handleChange}
              name="name"
            />
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
            <InputField
              type="password"
              placeholder="Confirm Password"
              icon={<LockIcon />}
              value={formData.confirmPassword}
              onChange={handleChange}
              name="confirmPassword"
            />
          </div>

          <Button
            variant="secondary"
            fullWidth
            onClick={handleGoogleSignIn}
            type="button"
          >
            <GoogleIcon />
            Sign in with Google
          </Button>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={submitting}
          >
            {submitting ? "SIGNING UP..." : "SIGN UP"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SignUp;
