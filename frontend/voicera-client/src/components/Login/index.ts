export { default } from "./Login";


export interface LoginFormData {
  email: string;
  password: string;
}

export interface LoginProps {
  onBack?: () => void;
}
