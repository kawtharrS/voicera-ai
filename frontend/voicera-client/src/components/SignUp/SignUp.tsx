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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Form submitted:", formData);
    // Add your signup logic here
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

          <button type="submit" className={styles.submitButton}>
            SIGN IN
          </button>
        </form>
      </div>
    </div>
  );
};

export default SignUp;
