import React from "react";
import styles from "./Navbar.module.css";

interface NavbarProps {
  onSignUpClick?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onSignUpClick }) => {
  return (
    <nav className={styles.navbar}>
      <a href="/" className={styles.logo}>
        <svg
          className={styles.logoIcon}
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="20" cy="20" r="18" fill="#4db6ac" />
          <circle cx="14" cy="16" r="4" fill="#ff9800" />
          <circle cx="26" cy="16" r="4" fill="#ff9800" />
          <path
            d="M12 26 Q20 32 28 26"
            stroke="#ff9800"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />
        </svg>
        Voicera
      </a>

      <div className={styles.navLinks}>
        <a href="#features" className={styles.navLink}>
          Features
        </a>
        <a href="#accessibility" className={styles.navLink}>
          Accessibility
        </a>
        <a href="#contact" className={styles.navLink}>
          Contact
        </a>
      </div>

      <button className={styles.signUpBtn} onClick={onSignUpClick}>
        Sign Up
      </button>
    </nav>
  );
};

export default Navbar;
