import React from "react";
import styles from "./InputField.module.css";

interface InputFieldProps {
  type: string;
  placeholder: string;
  icon: React.ReactNode;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  name: string;
}

const InputField: React.FC<InputFieldProps> = ({
  type,
  placeholder,
  icon,
  value,
  onChange,
  name,
}) => {
  return (
    <div className={styles.inputWrapper}>
      <div className={styles.iconWrapper}>
        <span className={styles.icon}>{icon}</span>
      </div>
      <input
        type={type}
        placeholder={placeholder}
        className={styles.input}
        value={value}
        onChange={onChange}
        name={name}
      />
    </div>
  );
};

export default InputField;
