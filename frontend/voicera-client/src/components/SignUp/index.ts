export { default } from "./SignUp";

export interface SignUpFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface SignUpProps {
  onBack?: () => void;
}